#!/usr/bin/env python3
"""
YouTube AI Dubber Studio - FastAPI Backend Server
Provides REST APIs, WebSocket real-time progress streaming,
file uploads, segment editing, and media playback.
"""

import asyncio
import hashlib
import json
import logging
import os
import shutil
import uuid
from datetime import datetime
import re
import socket
from pathlib import Path
from typing import Any, Dict, List, Optional

import edge_tts
import qrcode
import qrcode.image.svg
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend.dubbing_engine import (
    LANGUAGES,
    DubbingPipeline,
    detect_compute_device,
    export_vertical_short,
    get_media_duration,
    run_full_pipeline,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DubberServer")

app = FastAPI(title="YouTube AI Dubber Studio API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = OUTPUT_DIR / "jobs_history.json"
USERS_FILE = OUTPUT_DIR / "users.json"


def hash_password(password: str) -> str:
    """Generate SHA256 hex digest for password."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users() -> Dict[str, Dict[str, Any]]:
    """Load persistent users from output/users.json."""
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except Exception as err:
            logger.warning(f"Could not load {USERS_FILE.name}: {err}")
    return {}


def save_users(users: Dict[str, Dict[str, Any]]):
    """Save users to output/users.json."""
    try:
        USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as err:
        logger.warning(f"Could not save {USERS_FILE.name}: {err}")


USERS: Dict[str, Dict[str, Any]] = load_users()


def get_local_ip() -> str:
    """Detect LAN IP address for phone connectivity."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.254.254.254", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def load_jobs_history() -> Dict[str, Dict[str, Any]]:
    """Load persistent job history from output/jobs_history.json."""
    if HISTORY_FILE.exists():
        try:
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                logger.info(f"Loaded {len(data)} past jobs from {HISTORY_FILE.name}")
                return data
        except Exception as err:
            logger.warning(f"Could not load {HISTORY_FILE.name}: {err}")
    return {}


def save_jobs_history():
    """Save serializable jobs to output/jobs_history.json."""
    try:
        serializable = {}
        for jid, job in JOBS.items():
            serializable[jid] = {
                "id": job.get("id"),
                "title": job.get("title"),
                "source_input": job.get("source_input"),
                "target_lang": job.get("target_lang"),
                "voice_gender": job.get("voice_gender"),
                "whisper_model": job.get("whisper_model"),
                "source_lang": job.get("source_lang", "auto"),
                "detected_source_lang": job.get("detected_source_lang"),
                "burn_subtitles": job.get("burn_subtitles", False),
                "protected_terms": job.get("protected_terms", []),
                "enable_ducking": job.get("enable_ducking", True),
                "ducking_volume": job.get("ducking_volume", 0.15),
                "keep_original": job.get("keep_original", True),
                "isolate_vocals": job.get("isolate_vocals", False),
                "voice_map": job.get("voice_map"),
                "status": job.get("status"),
                "stage": job.get("stage"),
                "progress": job.get("progress"),
                "created_at": job.get("created_at"),
                "completed_at": job.get("completed_at"),
                "result": job.get("result"),
                "error": job.get("error"),
                "segments": job.get("segments", [])[:200],
                "logs": job.get("logs", [])[-30:],
            }
        HISTORY_FILE.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as err:
        logger.warning(f"Failed to save jobs history: {err}")


# In-memory & persistent store for active and completed jobs
JOBS: Dict[str, Dict[str, Any]] = load_jobs_history()
ACTIVE_CONNECTIONS: Dict[str, List[WebSocket]] = {}


class ConnectionManager:
    """Manages active WebSocket connections per job."""

    @staticmethod
    async def connect(websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in ACTIVE_CONNECTIONS:
            ACTIVE_CONNECTIONS[job_id] = []
        ACTIVE_CONNECTIONS[job_id].append(websocket)

    @staticmethod
    def disconnect(websocket: WebSocket, job_id: str):
        if job_id in ACTIVE_CONNECTIONS and websocket in ACTIVE_CONNECTIONS[job_id]:
            ACTIVE_CONNECTIONS[job_id].remove(websocket)

    @staticmethod
    async def broadcast(job_id: str, message: Dict[str, Any]):
        if job_id in ACTIVE_CONNECTIONS:
            dead = []
            for ws in ACTIVE_CONNECTIONS[job_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                ACTIVE_CONNECTIONS[job_id].remove(ws)


async def run_pipeline_task(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return

    job_dir = OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    loop = asyncio.get_running_loop()

    def on_progress(stage: str, pct: float, msg: str, data: Optional[Dict[str, Any]] = None):
        job["stage"] = stage
        job["progress"] = pct
        log_entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "stage": stage,
            "pct": pct,
            "message": msg,
        }
        job["logs"].append(log_entry)
        if data:
            if "title" in data:
                job["title"] = data["title"]
            if "segments" in data:
                job["segments"] = data["segments"]

        # Thread-safe push through WebSockets
        try:
            payload = {
                "type": "progress",
                "stage": stage,
                "progress": pct,
                "message": msg,
                "logs": job["logs"][-50:],
                "data": data,
            }
            asyncio.run_coroutine_threadsafe(
                ConnectionManager.broadcast(job_id, payload),
                loop,
            )
        except Exception as err:
            logger.warning(f"WS broadcast warning: {err}")

    try:
        job["status"] = "processing"
        save_jobs_history()
        res = await run_full_pipeline(
            source_input=job["source_input"],
            output_dir=job_dir,
            target_lang=job["target_lang"],
            voice_gender=job["voice_gender"],
            whisper_model=job["whisper_model"],
            source_lang=job.get("source_lang", "auto"),
            protected_terms=job.get("protected_terms", []),
            burn_subtitles=job.get("burn_subtitles", False),
            enable_ducking=job["enable_ducking"],
            ducking_volume=job["ducking_volume"],
            keep_original=job["keep_original"],
            isolate_vocals=job.get("isolate_vocals", False),
            voice_map=job.get("voice_map"),
            groq_api_key=job.get("groq_api_key"),
            on_progress=on_progress,
        )

        job["status"] = "completed"
        job["progress"] = 100.0
        job["stage"] = "finished"
        job["result"] = res
        job["segments"] = res.get("segments", [])
        job["detected_source_lang"] = res.get("detected_source_lang", "en")
        job["completed_at"] = datetime.now().isoformat()
        save_jobs_history()

        # Update user stats if associated
        uid = job.get("user_id")
        if uid and uid in USERS:
            USERS[uid]["videos_dubbed"] = USERS[uid].get("videos_dubbed", 0) + 1
            save_users(USERS)

        await ConnectionManager.broadcast(
            job_id,
            {
                "type": "completed",
                "progress": 100.0,
                "stage": "finished",
                "message": "Job finished successfully!",
                "result": {
                    "title": res.get("title"),
                    "duration": res.get("video_duration"),
                    "segments_count": res.get("segments_count"),
                    "detected_source_lang": res.get("detected_source_lang"),
                },
            },
        )
    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)
        save_jobs_history()
        await ConnectionManager.broadcast(
            job_id,
            {
                "type": "error",
                "error": str(e),
                "message": f"Processing failed: {e}",
            },
        )


# ==========================================
# User Authentication & Profile Endpoints
# ==========================================
@app.post("/api/auth/register")
def register_user(data: Dict[str, str]):
    email = data.get("email", "").strip().lower()
    name = (data.get("name") or data.get("username") or "").strip() or "Studio Creator"
    username = (data.get("username") or data.get("name") or "").strip() or name
    password = data.get("password", "")

    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")

    for uid, u in USERS.items():
        if u.get("email", "").lower() == email:
            raise HTTPException(status_code=400, detail="An account with this email already exists.")
        if username and u.get("username", "").lower() == username.lower():
            raise HTTPException(status_code=400, detail="An account with this username already exists.")

    user_id = uuid.uuid4().hex[:12]
    user_record = {
        "id": user_id,
        "name": name,
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "created_at": datetime.now().isoformat(),
        "videos_dubbed": 0,
        "plan": "Pro Studio",
    }
    USERS[user_id] = user_record
    save_users(USERS)

    return {
        "token": user_id,
        "user": {
            "id": user_id,
            "name": name,
            "username": username,
            "email": email,
            "token": user_id,
            "videos_dubbed": 0,
            "plan": "Pro Studio",
        },
    }


@app.post("/api/auth/login")
def login_user(data: Dict[str, str]):
    identifier = (data.get("email") or data.get("username") or "").strip().lower()
    password = data.get("password", "")

    p_hash = hash_password(password)
    for uid, u in USERS.items():
        match_id = (u.get("email", "").lower() == identifier) or (u.get("username", "").lower() == identifier)
        if match_id and u.get("password_hash") == p_hash:
            return {
                "token": uid,
                "user": {
                    "id": uid,
                    "name": u.get("name", "Studio Creator"),
                    "username": u.get("username", u.get("name", "Studio Creator")),
                    "email": u.get("email"),
                    "token": uid,
                    "videos_dubbed": u.get("videos_dubbed", 0),
                    "plan": u.get("plan", "Pro Studio"),
                },
            }

    raise HTTPException(status_code=401, detail="Invalid email/username or password.")


@app.get("/api/auth/me")
def get_current_user(token: Optional[str] = None, authorization: Optional[str] = Header(None)):
    user_token = token
    if not user_token and authorization and authorization.startswith("Bearer "):
        user_token = authorization.split("Bearer ")[1].strip()

    if user_token and user_token in USERS:
        u = USERS[user_token]
        return {
            "user": {
                "id": u["id"],
                "name": u.get("name", "Studio Creator"),
                "username": u.get("username", u.get("name", "Studio Creator")),
                "email": u.get("email"),
                "token": u["id"],
                "videos_dubbed": u.get("videos_dubbed", 0),
                "plan": u.get("plan", "Pro Studio"),
            }
        }
    raise HTTPException(status_code=401, detail="Not authenticated.")



@app.get("/api/jobs/active")
def get_active_jobs():
    """Return running and queued jobs for the multi-project queue switcher."""
    active = []
    for jid, j in JOBS.items():
        if j.get("status") in ["queued", "processing"]:
            active.append({
                "id": j["id"],
                "title": j.get("title", "Dubbing Job"),
                "status": j.get("status"),
                "progress": j.get("progress", 0.0),
                "stage": j.get("stage", "pending"),
                "target_lang": j.get("target_lang", "hi"),
                "created_at": j.get("created_at"),
            })
    active.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return {"active_jobs": active}


@app.get("/api/health")
def get_health():
    device, compute_type = detect_compute_device()
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "cpu_count": os.cpu_count(),
        "device": device,
        "compute_type": compute_type,
        "is_cuda": device == "cuda",
        "ffmpeg": shutil.which("ffmpeg") is not None,
    }


@app.get("/api/network-info")
def get_network_info():
    ip = get_local_ip()
    port = 8000
    url = f"http://{ip}:{port}"
    return {
        "local_ip": ip,
        "port": port,
        "url": url,
    }


@app.get("/api/qr-code")
def get_qr_code(url: Optional[str] = None):
    if not url:
        ip = get_local_ip()
        url = f"http://{ip}:8000"
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage)
    svg_data = img.to_string()
    return Response(content=svg_data, media_type="image/svg+xml")


@app.get("/api/languages")
def get_languages():
    """Return available target languages and their voice profiles."""
    return {"languages": LANGUAGES}


@app.post("/api/test-voice")
async def test_voice(data: Dict[str, str]):
    """Generate a sample TTS audio clip for auditioning voices in the UI."""
    voice_id = data.get("voice_id", "hi-IN-SwaraNeural")
    sample_text = data.get(
        "text", "Hello! This is an AI neural voice sample for your video dubbing project."
    )

    temp_file = OUTPUT_DIR / f"test_voice_{uuid.uuid4().hex[:8]}.mp3"
    comm = edge_tts.Communicate(sample_text, voice_id)
    await comm.save(str(temp_file))

    return FileResponse(
        temp_file,
        media_type="audio/mpeg",
        filename="sample_voice.mp3",
        background=BackgroundTasks(),
    )


@app.post("/api/dub")
async def create_dub_job(
    background_tasks: BackgroundTasks,
    source_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    target_lang: str = Form("hi"),
    voice_gender: str = Form("female"),
    whisper_model: str = Form("base.en"),
    source_lang: Optional[str] = Form("auto"),
    protected_terms: Optional[str] = Form(None),
    burn_subtitles: bool = Form(False),
    enable_ducking: bool = Form(True),
    ducking_volume: float = Form(0.15),
    keep_original: bool = Form(True),
    isolate_vocals: bool = Form(False),
    voice_map: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    groq_api_key: Optional[str] = Form(None),
):
    """Start an AI dubbing job from either a YouTube URL or direct uploaded file."""
    if not source_url and not file:
        raise HTTPException(
            status_code=400, detail="Must provide either a YouTube URL or upload a video file."
        )

    parsed_terms = []
    if protected_terms:
        parsed_terms = [t.strip() for t in re.split(r"[,;\n]", protected_terms) if t.strip()]

    parsed_voice_map = None
    if voice_map:
        try:
            parsed_voice_map = json.loads(voice_map)
        except Exception:
            parsed_voice_map = None

    job_id = uuid.uuid4().hex[:12]
    job_dir = OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    if file:
        ext = Path(file.filename or "uploaded.mp4").suffix or ".mp4"
        local_video_path = job_dir / f"uploaded_source{ext}"
        with open(local_video_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        source_input = str(local_video_path)
        title = Path(file.filename or "Uploaded Video").stem
    else:
        source_input = source_url.strip()
        title = "YouTube Video"

    job_record = {
        "id": job_id,
        "title": title,
        "source_input": source_input,
        "target_lang": target_lang,
        "voice_gender": voice_gender,
        "whisper_model": whisper_model,
        "source_lang": source_lang or "auto",
        "detected_source_lang": None,
        "protected_terms": parsed_terms,
        "burn_subtitles": burn_subtitles,
        "enable_ducking": enable_ducking,
        "ducking_volume": ducking_volume,
        "keep_original": keep_original,
        "isolate_vocals": isolate_vocals,
        "voice_map": parsed_voice_map,
        "user_id": user_id,
        "groq_api_key": groq_api_key or os.environ.get("GROQ_API_KEY"),
        "status": "queued",
        "stage": "pending",
        "progress": 0.0,
        "logs": [],
        "segments": [],
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }

    JOBS[job_id] = job_record
    save_jobs_history()
    background_tasks.add_task(run_pipeline_task, job_id)

    return {"job_id": job_id, "status": "queued", "message": "Dubbing job initiated."}


@app.get("/api/jobs")
def list_jobs():
    """List all recent jobs sorted by creation time."""
    job_list = sorted(JOBS.values(), key=lambda j: j.get("created_at") or "", reverse=True)
    return {
        "jobs": [
            {
                "id": j["id"],
                "title": j.get("title", "Dubbing Job"),
                "target_lang": j.get("target_lang", "hi"),
                "status": j.get("status", "unknown"),
                "progress": j.get("progress", 0.0),
                "stage": j.get("stage", "pending"),
                "created_at": j.get("created_at"),
                "burn_subtitles": j.get("burn_subtitles", False),
                "detected_source_lang": j.get("detected_source_lang"),
            }
            for j in job_list
        ]
    }


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    """Delete a job from history and cleanup its output folder."""
    if job_id in JOBS:
        del JOBS[job_id]
        save_jobs_history()
        job_dir = OUTPUT_DIR / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)
        return {"message": "Job deleted successfully."}
    raise HTTPException(status_code=404, detail="Job not found.")


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.post("/api/jobs/{job_id}/update-segments")
async def update_segments(job_id: str, payload: Dict[str, Any]):
    """
    Allow users to edit translated texts and re-synthesize the final video.
    """
    job = JOBS.get(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Job not in completed state for editing.")

    new_segments = payload.get("segments", [])
    if not new_segments:
        raise HTTPException(status_code=400, detail="No segments provided.")

    job["segments"] = new_segments
    job_dir = OUTPUT_DIR / job_id
    work_dir = job_dir / "work"

    pipeline = DubbingPipeline(work_dir)
    target_lang = job["target_lang"]
    lang_config = LANGUAGES.get(target_lang, LANGUAGES["hi"])
    voice_id = lang_config["voices"].get(job["voice_gender"], {}).get("id") or lang_config["default_voice"]

    # Re-generate TTS for segments
    fitted = await pipeline.generate_tts_parallel(new_segments, voice_id)
    video_path = work_dir / "source.mp4"
    video_dur = get_media_duration(video_path)

    dubbed_wav = work_dir / "dubbed_speech_edited.wav"
    pipeline.build_audio_timeline_numpy(fitted, video_dur, dubbed_wav)

    final_audio = dubbed_wav
    if job["enable_ducking"]:
        src_audio = work_dir / "source_audio_16k.wav"
        ducked_master = work_dir / "dubbed_ducked_master_edited.wav"
        pipeline.apply_ducking(
            src_audio,
            dubbed_wav,
            fitted,
            video_dur,
            ducked_master,
            ducking_volume=job["ducking_volume"],
        )
        final_audio = ducked_master

    final_mp4 = job_dir / f"dubbed_{target_lang}.mp4"
    srt_path = job_dir / f"subtitles_{target_lang}.srt"
    pipeline.export_srt(new_segments, srt_path)

    pipeline.mux_video(
        video_path,
        final_audio,
        final_mp4,
        target_lang=target_lang,
        keep_original=job["keep_original"],
        burn_subtitles=job.get("burn_subtitles", False),
        subtitles_file=srt_path,
    )

    save_jobs_history()

    return {"message": "Segments updated and dubbed video re-rendered successfully!"}


@app.post("/api/jobs/{job_id}/generate-short")
async def generate_short(job_id: str, payload: Optional[Dict[str, Any]] = None):
    """
    Render a 9:16 vertical short (1080x1920) with blurred background padding
    and burned-in kinetic styled captions for YouTube Shorts, Reels, and TikTok.
    """
    job = JOBS.get(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Job must be completed to generate vertical shorts.")

    data = payload or {}
    start_time = float(data.get("start_time", 0.0))
    duration = float(data.get("duration", 30.0))

    job_dir = OUTPUT_DIR / job_id
    target_lang = job.get("target_lang", "hi")
    dubbed_video = job_dir / f"dubbed_{target_lang}.mp4"
    if not dubbed_video.exists():
        candidates = list(job_dir.glob("dubbed_*.mp4"))
        if candidates:
            dubbed_video = candidates[0]
        else:
            raise HTTPException(status_code=404, detail="Dubbed video not found.")

    srt_path = job_dir / f"subtitles_{target_lang}.srt"
    if not srt_path.exists():
        candidates = list(job_dir.glob("*.srt"))
        if candidates:
            srt_path = candidates[0]
        else:
            raise HTTPException(status_code=404, detail="Subtitles not found.")

    output_short = job_dir / "vertical_short.mp4"
    await asyncio.to_thread(
        export_vertical_short,
        dubbed_video,
        dubbed_video,
        srt_path,
        output_short,
        start_time=start_time,
        duration=duration,
    )

    return {
        "status": "success",
        "message": "Vertical short generated successfully!",
        "short_url": f"/api/media/{job_id}/short",
    }


@app.get("/api/media/{job_id}/{media_type}")
def get_media(job_id: str, media_type: str):
    """Serve media files: dubbed video, source video, subtitles, MP3, isolated music, VTT, or shorts."""
    job = JOBS.get(job_id)
    job_dir = OUTPUT_DIR / job_id

    if media_type == "dubbed_video":
        target_lang = job["target_lang"] if job else "hi"
        file_path = job_dir / f"dubbed_{target_lang}.mp4"
        if not file_path.exists():
            candidates = list(job_dir.glob("dubbed_*.mp4"))
            if candidates:
                file_path = candidates[0]
            else:
                raise HTTPException(status_code=404, detail="Dubbed video not ready.")
        return FileResponse(file_path, media_type="video/mp4", filename=file_path.name)

    elif media_type == "source_video":
        src_candidates = list((job_dir / "work").glob("source.*"))
        if not src_candidates:
            raise HTTPException(status_code=404, detail="Source video not found.")
        src_file = src_candidates[0]
        return FileResponse(src_file, media_type="video/mp4", filename=src_file.name)

    elif media_type == "subtitles":
        candidates = list(job_dir.glob("*.srt"))
        if not candidates:
            raise HTTPException(status_code=404, detail="Subtitles not found.")
        return FileResponse(
            candidates[0], media_type="text/plain", filename=candidates[0].name
        )

    elif media_type == "vtt":
        candidates = list(job_dir.glob("*.vtt"))
        if not candidates:
            raise HTTPException(status_code=404, detail="WebVTT subtitles not found.")
        return FileResponse(
            candidates[0], media_type="text/vtt", filename=candidates[0].name
        )

    elif media_type == "transcript_txt":
        candidates = list(job_dir.glob("transcript_*.txt")) + list(job_dir.glob("*.txt"))
        if not candidates:
            raise HTTPException(status_code=404, detail="Transcript text file not found.")
        return FileResponse(
            candidates[0], media_type="text/plain", filename=candidates[0].name
        )

    elif media_type == "mp3":
        mp3_candidates = [
            job_dir / "dubbed_speech.mp3",
            job_dir / f"dubbed_{job.get('target_lang', 'hi')}.mp3" if job else None,
        ]
        for m in mp3_candidates:
            if m and m.exists():
                return FileResponse(m, media_type="audio/mpeg", filename=m.name)
        for a in [job_dir / "work" / "dubbed_ducked_master.wav", job_dir / "work" / "dubbed_speech.wav"]:
            if a.exists():
                return FileResponse(a, media_type="audio/wav", filename="dubbed_speech.wav")
        raise HTTPException(status_code=404, detail="MP3 speech track not found.")

    elif media_type == "music":
        music_candidates = [
            job_dir / "isolated_music.mp3",
            job_dir / "work" / "isolated_music.wav",
        ]
        for m in music_candidates:
            if m.exists():
                m_type = "audio/mpeg" if m.suffix == ".mp3" else "audio/wav"
                return FileResponse(m, media_type=m_type, filename=m.name)
        raise HTTPException(status_code=404, detail="Isolated music track not found.")

    elif media_type == "short":
        short_file = job_dir / "vertical_short.mp4"
        if not short_file.exists():
            raise HTTPException(status_code=404, detail="Vertical short not generated yet.")
        return FileResponse(short_file, media_type="video/mp4", filename="vertical_short.mp4")

    elif media_type == "audio":
        audio_candidates = [
            job_dir / "work" / "dubbed_ducked_master.wav",
            job_dir / "work" / "dubbed_speech.wav",
        ]
        for a in audio_candidates:
            if a.exists():
                return FileResponse(a, media_type="audio/wav", filename="dubbed_audio.wav")
        raise HTTPException(status_code=404, detail="Audio file not found.")

    raise HTTPException(status_code=400, detail="Invalid media type requested.")


@app.websocket("/api/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await ConnectionManager.connect(websocket, job_id)
    # Send current state immediately on connect
    job = JOBS.get(job_id)
    if job:
        await websocket.send_json(
            {
                "type": "state",
                "job": {
                    "id": job["id"],
                    "title": job["title"],
                    "status": job["status"],
                    "stage": job["stage"],
                    "progress": job["progress"],
                    "logs": job["logs"][-50:],
                    "segments": job["segments"][:10],
                },
            }
        )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ConnectionManager.disconnect(websocket, job_id)


@app.get("/api/version")
def get_version():
    """Return version metadata and release channel for in-app updates."""
    return {
        "version": "2.2.0",
        "release_name": "Cloud Studio Edition",
        "platform": "Render Cloud / Local",
        "groq_cloud_whisper_supported": True,
        "pwa_auto_update": True,
        "node_env": os.environ.get("NODE_ENV", "production"),
    }


# Serve frontend if built
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        if full_path:
            candidate = FRONTEND_DIST / full_path
            if candidate.is_file():
                return FileResponse(candidate)
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(index)
        return JSONResponse({"message": "Frontend build not found."})


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting server on port {port}...")
    uvicorn.run("backend.server:app", host="0.0.0.0", port=port, reload=False)


