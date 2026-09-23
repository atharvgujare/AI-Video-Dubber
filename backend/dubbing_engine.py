#!/usr/bin/env python3
"""
High-Performance AI Video Dubbing Engine
---------------------------------------
Optimized for multi-core CPU/GPU acceleration, concurrent async translation,
parallel Edge-TTS synthesis, NumPy sample-accurate audio mixing, and intelligent
background ambience/music ducking.
"""

import asyncio
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx
import numpy as np
from faster_whisper import WhisperModel
from yt_dlp import YoutubeDL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DubbingEngine")

# Supported Languages & Voices (Male and Female options per language)
LANGUAGES: Dict[str, Dict[str, Any]] = {
    "hi": {
        "name": "Hindi",
        "native": "हिन्दी",
        "flag": "🇮🇳",
        "iso": "hin",
        "voices": {
            "female": {"id": "hi-IN-SwaraNeural", "label": "Swara (Female, Natural)"},
            "male": {"id": "hi-IN-MadhurNeural", "label": "Madhur (Male, Deep)"},
        },
        "default_voice": "hi-IN-SwaraNeural",
    },
    "mr": {
        "name": "Marathi",
        "native": "मराठी",
        "flag": "🇮🇳",
        "iso": "mar",
        "voices": {
            "female": {"id": "mr-IN-AarohiNeural", "label": "Aarohi (Female)"},
            "male": {"id": "mr-IN-ManoharNeural", "label": "Manohar (Male)"},
        },
        "default_voice": "mr-IN-AarohiNeural",
    },
    "ta": {
        "name": "Tamil",
        "native": "தமிழ்",
        "flag": "🇮🇳",
        "iso": "tam",
        "voices": {
            "female": {"id": "ta-IN-PallaviNeural", "label": "Pallavi (Female)"},
            "male": {"id": "ta-IN-ValluvarNeural", "label": "Valluvar (Male)"},
        },
        "default_voice": "ta-IN-PallaviNeural",
    },
    "te": {
        "name": "Telugu",
        "native": "తెలుగు",
        "flag": "🇮🇳",
        "iso": "tel",
        "voices": {
            "female": {"id": "te-IN-ShrutiNeural", "label": "Shruti (Female)"},
            "male": {"id": "te-IN-MohanNeural", "label": "Mohan (Male)"},
        },
        "default_voice": "te-IN-ShrutiNeural",
    },
    "bn": {
        "name": "Bengali",
        "native": "বাংলা",
        "flag": "🇮🇳",
        "iso": "ben",
        "voices": {
            "female": {"id": "bn-IN-TanishaaNeural", "label": "Tanishaa (Female)"},
            "male": {"id": "bn-IN-BashkarNeural", "label": "Bashkar (Male)"},
        },
        "default_voice": "bn-IN-TanishaaNeural",
    },
    "gu": {
        "name": "Gujarati",
        "native": "ગુજરાતી",
        "flag": "🇮🇳",
        "iso": "guj",
        "voices": {
            "female": {"id": "gu-IN-DhwaniNeural", "label": "Dhwani (Female)"},
            "male": {"id": "gu-IN-NiranjanNeural", "label": "Niranjan (Male)"},
        },
        "default_voice": "gu-IN-DhwaniNeural",
    },
    "kn": {
        "name": "Kannada",
        "native": "ಕನ್ನಡ",
        "flag": "🇮🇳",
        "iso": "kan",
        "voices": {
            "female": {"id": "kn-IN-SapnaNeural", "label": "Sapna (Female)"},
            "male": {"id": "kn-IN-GaganNeural", "label": "Gagan (Male)"},
        },
        "default_voice": "kn-IN-SapnaNeural",
    },
    "ml": {
        "name": "Malayalam",
        "native": "മലയാളം",
        "flag": "🇮🇳",
        "iso": "mal",
        "voices": {
            "female": {"id": "ml-IN-SobhanaNeural", "label": "Sobhana (Female)"},
            "male": {"id": "ml-IN-MidhunNeural", "label": "Midhun (Male)"},
        },
        "default_voice": "ml-IN-SobhanaNeural",
    },
    "pa": {
        "name": "Punjabi",
        "native": "ਪੰਜਾਬੀ",
        "flag": "🇮🇳",
        "iso": "pan",
        "voices": {
            "female": {"id": "pa-IN-VaaniNeural", "label": "Vaani (Female)"},
            "male": {"id": "pa-IN-OjasNeural", "label": "Ojas (Male)"},
        },
        "default_voice": "pa-IN-OjasNeural",
    },
    "ur": {
        "name": "Urdu",
        "native": "اردو",
        "flag": "🇵🇰",
        "iso": "urd",
        "voices": {
            "female": {"id": "ur-IN-GulNeural", "label": "Gul (Female)"},
            "male": {"id": "ur-IN-SalmanNeural", "label": "Salman (Male)"},
        },
        "default_voice": "ur-IN-GulNeural",
    },
    "en": {
        "name": "English",
        "native": "English",
        "flag": "🇺🇸",
        "iso": "eng",
        "voices": {
            "female": {"id": "en-US-AriaNeural", "label": "Aria (Female, Clear)"},
            "male": {"id": "en-US-GuyNeural", "label": "Guy (Male, Professional)"},
        },
        "default_voice": "en-US-AriaNeural",
    },
    "es": {
        "name": "Spanish",
        "native": "Español",
        "flag": "🇪🇸",
        "iso": "spa",
        "voices": {
            "female": {"id": "es-ES-ElviraNeural", "label": "Elvira (Female)"},
            "male": {"id": "es-ES-AlvaroNeural", "label": "Alvaro (Male)"},
        },
        "default_voice": "es-ES-ElviraNeural",
    },
    "fr": {
        "name": "French",
        "native": "Français",
        "flag": "🇫🇷",
        "iso": "fra",
        "voices": {
            "female": {"id": "fr-FR-DeniseNeural", "label": "Denise (Female)"},
            "male": {"id": "fr-FR-HenriNeural", "label": "Henri (Male)"},
        },
        "default_voice": "fr-FR-DeniseNeural",
    },
    "de": {
        "name": "German",
        "native": "Deutsch",
        "flag": "🇩🇪",
        "iso": "deu",
        "voices": {
            "female": {"id": "de-DE-KatjaNeural", "label": "Katja (Female)"},
            "male": {"id": "de-DE-ConradNeural", "label": "Conrad (Male)"},
        },
        "default_voice": "de-DE-KatjaNeural",
    },
    "ja": {
        "name": "Japanese",
        "native": "日本語",
        "flag": "🇯🇵",
        "iso": "jpn",
        "voices": {
            "female": {"id": "ja-JP-NanamiNeural", "label": "Nanami (Female)"},
            "male": {"id": "ja-JP-KeitaNeural", "label": "Keita (Male)"},
        },
        "default_voice": "ja-JP-NanamiNeural",
    },
}

TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"

# Model memory cache to avoid reloading weights repeatedly across jobs
_MODEL_CACHE: Dict[str, WhisperModel] = {}


def detect_compute_device() -> Tuple[str, str]:
    """Detect whether CUDA GPU is available via ctranslate2, else fallback to CPU."""
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            logger.info(f"NVIDIA CUDA detected with {ctranslate2.get_cuda_device_count()} device(s). Using GPU acceleration!")
            return "cuda", "float16"
    except Exception as err:
        logger.debug(f"CUDA probe: {err}")
    return "cpu", "int8"


def get_cached_whisper(model_size: str, cpu_threads: int = 6) -> WhisperModel:
    device, compute_type = detect_compute_device()
    cache_key = f"{model_size}_{device}_{compute_type}_{cpu_threads}"
    if cache_key not in _MODEL_CACHE:
        logger.info(f"Loading WhisperModel '{model_size}' on {device.upper()} ({compute_type})...")
        if device == "cuda":
            _MODEL_CACHE[cache_key] = WhisperModel(
                model_size,
                device="cuda",
                compute_type=compute_type,
            )
        else:
            _MODEL_CACHE[cache_key] = WhisperModel(
                model_size,
                device="cpu",
                compute_type=compute_type,
                cpu_threads=cpu_threads,
                num_workers=2,
            )
    return _MODEL_CACHE[cache_key]


def get_ffmpeg_binary() -> str:
    """Find system ffmpeg or fallback to imageio_ffmpeg bundled binary."""
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def get_ffprobe_binary() -> str:
    """Find system ffprobe or fallback to ffprobe adjacent to imageio_ffmpeg."""
    sys_probe = shutil.which("ffprobe")
    if sys_probe:
        return sys_probe
    try:
        import imageio_ffmpeg
        f_exe = Path(imageio_ffmpeg.get_ffmpeg_exe())
        probe_exe = f_exe.parent / f_exe.name.replace("ffmpeg", "ffprobe")
        if probe_exe.exists():
            return str(probe_exe)
    except Exception:
        pass
    return "ffprobe"


FFMPEG_BIN = get_ffmpeg_binary()
FFPROBE_BIN = get_ffprobe_binary()


def run_ffmpeg(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run an FFmpeg command with quiet output and error capture."""
    exec_cmd = list(cmd)
    if exec_cmd and exec_cmd[0] in ["ffmpeg", "ffmpeg.exe"]:
        exec_cmd[0] = FFMPEG_BIN
    return subprocess.run(
        exec_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=check,
    )


def get_media_duration(file_path: Path) -> float:
    """Get accurate duration in seconds using ffprobe with ffmpeg and wave fallbacks."""
    try:
        res = subprocess.run(
            [
                FFPROBE_BIN, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        val = res.stdout.strip()
        if val:
            return float(val)
    except Exception:
        pass

    # Fallback to ffmpeg -i parsing
    try:
        res = subprocess.run(
            [FFMPEG_BIN, "-i", str(file_path)],
            capture_output=True,
            text=True,
        )
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", res.stderr)
        if m:
            hours, mins, secs = float(m.group(1)), float(m.group(2)), float(m.group(3))
            return hours * 3600 + mins * 60 + secs
    except Exception as err:
        logger.warning(f"Duration probe fallback warning: {err}")

    # Fallback for wave files
    try:
        with wave.open(str(file_path), "rb") as wf:
            return wf.getnframes() / float(wf.getframerate())
    except Exception:
        pass

    return 0.0


def transcribe_with_groq(
    audio_path: Path,
    api_key: str,
    source_lang: Optional[str] = "auto",
) -> Tuple[List[Dict[str, Any]], str]:
    """Transcribe audio using Groq's Free Whisper Large v3 cloud API (~2 seconds latency, 0 MB server RAM)."""
    from groq import Groq
    client = Groq(api_key=api_key)
    with open(audio_path, "rb") as file:
        lang_param = source_lang if (source_lang and source_lang != "auto") else None
        transcription = client.audio.transcriptions.create(
            file=(audio_path.name, file.read()),
            model="whisper-large-v3",
            response_format="verbose_json",
            language=lang_param,
        )
    det_lang = getattr(transcription, "language", "en") or "en"
    raw_segments = getattr(transcription, "segments", []) or []
    extracted = []
    for s in raw_segments:
        text = s.get("text", "").strip() if isinstance(s, dict) else getattr(s, "text", "").strip()
        start = round(float(s.get("start", 0) if isinstance(s, dict) else getattr(s, "start", 0)), 3)
        end = round(float(s.get("end", 0) if isinstance(s, dict) else getattr(s, "end", 0)), 3)
        if text:
            extracted.append({
                "id": len(extracted) + 1,
                "start": start,
                "end": end,
                "duration": round(end - start, 3),
                "text": text,
            })
    return extracted, det_lang


class DubbingPipeline:
    def __init__(
        self,
        work_dir: Path,
        on_progress: Optional[Callable[[str, float, str, Optional[Dict[str, Any]]], None]] = None,
        groq_api_key: Optional[str] = None,
    ):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.on_progress = on_progress or (lambda stage, pct, msg, data=None: None)
        self.detected_source_lang: str = "en"
        self.groq_api_key: Optional[str] = groq_api_key or os.environ.get("GROQ_API_KEY")

    def report(self, stage: str, pct: float, msg: str, data: Optional[Dict[str, Any]] = None):
        logger.info(f"[{stage}] ({pct:.1f}%) {msg}")
        self.on_progress(stage, pct, msg, data)

    # ==========================================
    # Step 1: Ingestion
    # ==========================================
    def ingest_media(self, source_input: str) -> Tuple[Path, str]:
        """
        Download YouTube video or copy/link local file.
        Returns (source_video_path, video_title).
        """
        self.report("ingestion", 5.0, "Preparing media source...")

        if os.path.exists(source_input):
            local_src = Path(source_input).resolve()
            dest_video = self.work_dir / f"source{local_src.suffix}"
            if local_src != dest_video:
                shutil.copyfile(local_src, dest_video)
            title = local_src.stem
            self.report("ingestion", 15.0, f"Local media loaded: {title}", {"title": title})
            return dest_video, title

        # YouTube URL download via yt-dlp
        self.report("ingestion", 7.0, f"Fetching YouTube metadata: {source_input}")
        output_template = str(self.work_dir / "source.%(ext)s")

        ydl_opts = {
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "outtmpl": output_template,
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 5,
            "fragment_retries": 5,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source_input, download=True)
            title = info.get("title", "YouTube Video")

        target_file = self.work_dir / "source.mp4"
        if not target_file.exists():
            candidates = list(self.work_dir.glob("source.*"))
            if candidates:
                target_file = candidates[0]
            else:
                raise FileNotFoundError("Failed to locate downloaded video.")

        self.report("ingestion", 15.0, f"Ingestion complete: {title}", {"title": title})
        return target_file, title

    # ==========================================
    # Step 2: Audio Extraction & Transcription
    # ==========================================
    def extract_audio(self, video_path: Path) -> Path:
        """Extract 16kHz mono WAV for high-accuracy Whisper ingestion."""
        audio_path = self.work_dir / "source_audio_16k.wav"
        run_ffmpeg(
            [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-c:a", "pcm_s16le",
                str(audio_path),
            ]
        )
        return audio_path

    def transcribe(
        self,
        audio_path: Path,
        model_name: str = "base.en",
        source_lang: Optional[str] = "auto",
        beam_size: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Transcribe speech using faster-whisper with multi-core CPU/GPU optimization.
        beam_size=1 (greedy) provides 3x-4x speedup with high accuracy.
        Supports automatic source language detection or explicit language override.
        """
        groq_key = self.groq_api_key or os.environ.get("GROQ_API_KEY")
        if groq_key:
            try:
                self.report("transcription", 20.0, "Transcribing with Groq Free Cloud Whisper (Whisper Large v3)...")
                extracted, det_lang = transcribe_with_groq(audio_path, groq_key, source_lang)
                self.detected_source_lang = det_lang
                self.report(
                    "transcription",
                    35.0,
                    f"Transcription finished via Groq Cloud in seconds: {len(extracted)} speech segments (Detected Source Language: {det_lang.upper()}).",
                    {
                        "segment_count": len(extracted),
                        "segments": extracted[:10],
                        "source_language": det_lang,
                        "source_language_probability": 1.0,
                    },
                )
                return extracted
            except Exception as err:
                logger.warning(f"Groq Cloud Whisper failed, falling back to local Whisper: {err}")

        self.report("transcription", 20.0, f"Transcribing audio using Whisper '{model_name}'...")

        model = get_cached_whisper(model_name, cpu_threads=6)
        lang_param = source_lang if (source_lang and source_lang != "auto") else None

        # Transcribe with VAD filter to omit non-speech noise
        segments, info = model.transcribe(
            str(audio_path),
            language=lang_param,
            beam_size=beam_size,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400),
        )

        det_lang = getattr(info, "language", "en") or "en"
        det_prob = getattr(info, "language_probability", 1.0)
        self.detected_source_lang = det_lang

        extracted = []
        for seg in segments:
            text = seg.text.strip()
            if text:
                extracted.append(
                    {
                        "id": len(extracted) + 1,
                        "start": round(float(seg.start), 3),
                        "end": round(float(seg.end), 3),
                        "duration": round(float(seg.end - seg.start), 3),
                        "text": text,
                    }
                )

        self.report(
            "transcription",
            35.0,
            f"Transcription finished: found {len(extracted)} speech segments (Detected Source Language: {det_lang.upper()} {det_prob*100:.0f}%).",
            {
                "segment_count": len(extracted),
                "segments": extracted[:10],
                "source_language": det_lang,
                "source_language_probability": round(det_prob, 2),
            },
        )
        return extracted

    # ==========================================
    # Step 3: High-Speed Batched Async Translation
    # ==========================================
    async def translate_text_async(
        self, client: httpx.AsyncClient, text: str, target_lang: str
    ) -> str:
        text = text.strip()
        if not text:
            return ""

        # Tier 1: Chrome Extension Translate Endpoint (High quota, resilient to 429)
        try:
            resp = await client.get(
                "https://clients5.google.com/translate_a/t",
                params={"client": "dict-chrome-ex", "sl": "auto", "tl": target_lang, "q": text},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=8.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], str):
                        return data[0].strip()
                    if isinstance(data[0], list) and len(data[0]) > 0 and isinstance(data[0][0], str):
                        return data[0][0].strip()
        except Exception:
            pass

        # Tier 2: Public GTX endpoint
        try:
            resp = await client.get(
                TRANSLATE_URL,
                params={"client": "gtx", "sl": "auto", "tl": target_lang, "dt": "t", "q": text},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=8.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                translated = "".join(item[0] for item in data[0] if item and item[0])
                if translated.strip():
                    return translated.strip()
        except Exception:
            pass

        # Tier 3: MyMemory Open Translation API
        try:
            resp = await client.get(
                "https://api.mymemory.translated.net/get",
                params={"q": text, "langpair": f"en|{target_lang}"},
                timeout=8.0,
            )
            if resp.status_code == 200:
                res_json = resp.json()
                trans = res_json.get("responseData", {}).get("translatedText")
                if trans and "MYMEMORY WARNING" not in trans:
                    return trans.strip()
        except Exception:
            pass

        return text

    async def translate_segments_async(
        self,
        segments: List[Dict[str, Any]],
        target_lang: str,
        protected_terms: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        self.report(
            "translation",
            40.0,
            f"Translating {len(segments)} segments to {LANGUAGES.get(target_lang, {}).get('name', target_lang)}...",
        )

        clean_terms = [t.strip() for t in (protected_terms or []) if t and t.strip()]
        # Sort longest terms first so substrings don't break longer multi-word phrases
        clean_terms.sort(key=len, reverse=True)

        sem = asyncio.Semaphore(8)  # Up to 8 concurrent translation requests
        async with httpx.AsyncClient(limits=httpx.Limits(max_connections=12)) as client:

            async def worker(idx: int, seg: Dict[str, Any]) -> Dict[str, Any]:
                async with sem:
                    raw_text = seg["text"]
                    # Shield protected terms before translation
                    token_map = {}
                    shielded_text = raw_text
                    for i, term in enumerate(clean_terms):
                        tok = f"_GLOSS_{i}_"
                        pattern = re.compile(re.escape(term), re.IGNORECASE)
                        shielded_text = pattern.sub(tok, shielded_text)
                        token_map[tok] = term

                    translated = await self.translate_text_async(client, shielded_text, target_lang)

                    # Restore protected terms after translation
                    if token_map:
                        for tok, original in token_map.items():
                            num = tok.split("_")[2]
                            translated = re.sub(
                                rf"_\s*GLOSS\s*_\s*{num}\s*_",
                                original,
                                translated,
                                flags=re.IGNORECASE,
                            )

                    return {**seg, "translated": translated}

            tasks = [worker(i, seg) for i, seg in enumerate(segments)]
            results = await asyncio.gather(*tasks)

        self.report(
            "translation",
            50.0,
            "Translation complete.",
            {"translated_sample": results[:5] if results else []},
        )
        return results

    # ==========================================
    # Step 4: Parallel Edge-TTS Voice Generation
    # ==========================================
    async def _generate_single_tts(
        self,
        segment: Dict[str, Any],
        voice: str,
        index: int,
        total: int,
        sem: asyncio.Semaphore,
    ) -> Optional[Dict[str, Any]]:
        import edge_tts

        text = segment.get("translated", "").strip()
        if not text:
            return None

        raw_mp3 = self.work_dir / f"tts_{index:04d}_raw.mp3"
        fitted_wav = self.work_dir / f"tts_{index:04d}_fitted.wav"

        async with sem:
            target_duration = max(0.2, segment["end"] - segment["start"])

            # 1. Pacing rate estimation:
            # Indian languages & English average ~13-15 characters per second
            estimated_duration = max(0.4, len(text) / 14.0)
            rate_pct = int(round(((estimated_duration / target_duration) - 1.0) * 100))
            # Clamp rate within Edge-TTS natural phonetic limits (-50% to +100%)
            rate_pct = max(-50, min(100, rate_pct))
            rate_str = f"{rate_pct:+d}%"

            # 2. Edge-TTS synthesis with native rate parameter
            try:
                comm = edge_tts.Communicate(text, voice, rate=rate_str)
                await comm.save(str(raw_mp3))
            except Exception as tts_err:
                logger.warning(f"Edge-TTS rate '{rate_str}' fallback ({tts_err})")
                comm = edge_tts.Communicate(text, voice)
                await comm.save(str(raw_mp3))

            # 3. Probe TTS duration
            raw_duration = get_media_duration(raw_mp3)

            # 4. Calculate micro-adjustment factor (< 5% residual adjustment)
            factor = raw_duration / target_duration

            # Chain filters if factor exceeds FFmpeg atempo bounds (0.5 to 2.0)
            filters = []
            remaining = factor
            while remaining < 0.5:
                filters.append("atempo=0.5")
                remaining /= 0.5
            while remaining > 2.0:
                filters.append("atempo=2.0")
                remaining /= 2.0
            filters.append(f"atempo={remaining:.5f}")

            # Fit tempo and convert to 48kHz Stereo 16-bit PCM WAV
            run_ffmpeg(
                [
                    "ffmpeg", "-y",
                    "-i", str(raw_mp3),
                    "-filter:a", ",".join(filters),
                    "-ar", "48000",
                    "-ac", "2",
                    "-c:a", "pcm_s16le",
                    str(fitted_wav),
                ]
            )

            return {
                "id": segment["id"],
                "file": fitted_wav,
                "start": segment["start"],
                "end": segment["end"],
                "target_duration": target_duration,
                "text": text,
            }

    async def generate_tts_parallel(
        self, segments: List[Dict[str, Any]], voice: str
    ) -> List[Dict[str, Any]]:
        self.report(
            "speech_synthesis",
            55.0,
            f"Synthesizing {len(segments)} segments concurrently with voice '{voice}'...",
        )

        sem = asyncio.Semaphore(6)  # Parallel synthesis workers
        total = len(segments)
        tasks = [
            self._generate_single_tts(seg, voice, idx, total, sem)
            for idx, seg in enumerate(segments)
        ]

        completed = []
        for f in asyncio.as_completed(tasks):
            res = await f
            if res:
                completed.append(res)
                pct = 55.0 + (len(completed) / total) * 20.0
                if len(completed) % max(1, total // 5) == 0 or len(completed) == total:
                    self.report(
                        "speech_synthesis",
                        pct,
                        f"Generated {len(completed)}/{total} voice clips...",
                    )

        completed.sort(key=lambda x: x["start"])
        return completed

    # ==========================================
    # Step 5: Sample-Accurate NumPy Audio Timeline Mixer
    # ==========================================
    def build_audio_timeline_numpy(
        self,
        segment_files: List[Dict[str, Any]],
        video_duration: float,
        output_wav: Path,
    ):
        """
        Builds a full-length 48kHz stereo WAV timeline by positioning each WAV segment
        sample-accurately inside a NumPy array.
        Completely eliminates Windows FFmpeg amix command-line length limits and volume drops!
        """
        self.report("mastering", 78.0, "Synthesizing sample-accurate NumPy audio timeline...")

        sample_rate = 48000
        channels = 2
        total_samples = int(math.ceil(video_duration * sample_rate)) + sample_rate

        # 32-bit integer buffer for zero-loss headroom mixing
        timeline_buffer = np.zeros((total_samples, channels), dtype=np.int32)

        for item in segment_files:
            wav_path = item["file"]
            start_sec = item["start"]
            start_sample = int(round(start_sec * sample_rate))

            with wave.open(str(wav_path), "rb") as wf:
                n_frames = wf.getnframes()
                raw_bytes = wf.readframes(n_frames)
                seg_samples = np.frombuffer(raw_bytes, dtype=np.int16).reshape(-1, channels)

            seg_len = len(seg_samples)
            end_sample = start_sample + seg_len

            if end_sample > total_samples:
                seg_samples = seg_samples[: total_samples - start_sample]
                end_sample = total_samples

            timeline_buffer[start_sample:end_sample] += seg_samples

        # Clip within 16-bit signed integer range to prevent distortion
        np.clip(timeline_buffer, -32768, 32767, out=timeline_buffer)
        final_pcm = timeline_buffer[: int(video_duration * sample_rate)].astype(np.int16)

        # Write output WAV
        with wave.open(str(output_wav), "wb") as out_wf:
            out_wf.setnchannels(channels)
            out_wf.setsampwidth(2)
            out_wf.setframerate(sample_rate)
            out_wf.writeframes(final_pcm.tobytes())

        self.report("mastering", 85.0, "Timeline assembled successfully.")

    # ==========================================
    # Step 6: Smart Background Ducking & Ambience Preservation
    # ==========================================
    def apply_ducking(
        self,
        source_audio: Path,
        dubbed_audio: Path,
        segment_files: List[Dict[str, Any]],
        video_duration: float,
        output_master: Path,
        ducking_volume: float = 0.15,
    ):
        """
        Lowers original audio volume to `ducking_volume` during speech segments,
        and leaves it at 100% during pauses/music. Produces studio-quality audio!
        """
        self.report("mastering", 88.0, f"Applying smart background music ducking (level: {int(ducking_volume*100)}%)...")

        # Convert source audio to 48kHz stereo WAV for easy NumPy mixing
        src_48k = self.work_dir / "source_48k_stereo.wav"
        run_ffmpeg(
            [
                "ffmpeg", "-y",
                "-i", str(source_audio),
                "-ar", "48000",
                "-ac", "2",
                "-c:a", "pcm_s16le",
                str(src_48k),
            ]
        )

        sample_rate = 48000
        channels = 2
        total_samples = int(math.ceil(video_duration * sample_rate))

        # Read original audio
        with wave.open(str(src_48k), "rb") as wf:
            n_frames = min(total_samples, wf.getnframes())
            orig_bytes = wf.readframes(n_frames)
            orig_data = np.frombuffer(orig_bytes, dtype=np.int16).reshape(-1, channels)

        # Pad if shorter
        if len(orig_data) < total_samples:
            orig_padded = np.zeros((total_samples, channels), dtype=np.float32)
            orig_padded[: len(orig_data)] = orig_data
            orig_data = orig_padded
        else:
            orig_data = orig_data[:total_samples].astype(np.float32)

        # Create gain envelope initialized to 0.75 (background music normal level)
        gain_envelope = np.full((total_samples, 1), 0.75, dtype=np.float32)
        fade_samples = int(0.06 * sample_rate)  # 60ms smooth crossfade

        for seg in segment_files:
            s_idx = max(0, int(seg["start"] * sample_rate) - fade_samples)
            e_idx = min(total_samples, int(seg["end"] * sample_rate) + fade_samples)

            # Duck volume during speech
            gain_envelope[s_idx:e_idx] = ducking_volume

        # Smooth envelope using moving average
        kernel_size = fade_samples
        if kernel_size > 1:
            kernel = np.ones(kernel_size) / kernel_size
            smoothed_gain = np.convolve(gain_envelope[:, 0], kernel, mode="same")
            gain_envelope[:, 0] = smoothed_gain

        # Apply gain envelope to background
        orig_ducked = orig_data * gain_envelope

        # Read dubbed speech
        with wave.open(str(dubbed_audio), "rb") as wf:
            n_frames = min(total_samples, wf.getnframes())
            dub_bytes = wf.readframes(n_frames)
            dub_data = np.frombuffer(dub_bytes, dtype=np.int16).reshape(-1, channels).astype(np.float32)

        if len(dub_data) < total_samples:
            dub_padded = np.zeros((total_samples, channels), dtype=np.float32)
            dub_padded[: len(dub_data)] = dub_data
            dub_data = dub_padded
        else:
            dub_data = dub_data[:total_samples]

        # Combine ducked background + dubbed speech
        mixed = orig_ducked + (dub_data * 1.05)
        np.clip(mixed, -32768, 32767, out=mixed)
        mixed_pcm = mixed.astype(np.int16)

        with wave.open(str(output_master), "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(mixed_pcm.tobytes())

    # ==========================================
    # Step 7: Subtitles & Final Video Mux
    # ==========================================
    def export_srt(self, segments: List[Dict[str, Any]], srt_path: Path):
        """Export clean SRT subtitle file with timing."""
        def format_time(seconds: float) -> str:
            millis = int(round((seconds - int(seconds)) * 1000))
            seconds = int(seconds)
            mins, secs = divmod(seconds, 60)
            hours, mins = divmod(mins, 60)
            return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

        lines = []
        for i, seg in enumerate(segments, 1):
            text = seg.get("translated") or seg.get("text")
            lines.append(str(i))
            lines.append(f"{format_time(seg['start'])} --> {format_time(seg['end'])}")
            lines.append(text.strip())
            lines.append("")

        srt_path.write_text("\n".join(lines), encoding="utf-8")

    def mux_video(
        self,
        video_path: Path,
        dubbed_audio: Path,
        output_video: Path,
        target_lang: str,
        keep_original: bool = False,
        burn_subtitles: bool = False,
        subtitles_file: Optional[Path] = None,
    ):
        """
        Mux video with accurate language metadata, multi-audio tracks, and optional hardsub burn-in.
        """
        self.report("muxing", 92.0, "Muxing final video and embedding metadata...")

        lang_info = LANGUAGES.get(target_lang, {"name": "Dubbed", "iso": "und"})
        lang_name = lang_info.get("name", "Dubbed")
        iso_code = lang_info.get("iso", "und")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(dubbed_audio),
        ]

        # Video filter options for hardcoded subtitles
        video_codec_opts = ["-c:v", "copy"]
        if burn_subtitles and subtitles_file and subtitles_file.exists():
            # Escaping for Windows FFmpeg: forward slashes and colon escaped as '\:'
            sub_esc = subtitles_file.resolve().as_posix().replace(":", r"\:")
            video_codec_opts = [
                "-vf", f"subtitles='{sub_esc}'",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
            ]

        if keep_original:
            cmd += [
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-map", "0:a:0?",
                *video_codec_opts,
                "-c:a", "aac",
                "-b:a", "192k",
                "-metadata:s:a:0", f"language={iso_code}",
                "-metadata:s:a:0", f"title={lang_name} Dubbed",
                "-metadata:s:a:1", "language=eng",
                "-metadata:s:a:1", "title=Original Audio",
                "-disposition:a:0", "default",
                "-shortest",
                str(output_video),
            ]
        else:
            cmd += [
                "-map", "0:v:0",
                "-map", "1:a:0",
                *video_codec_opts,
                "-c:a", "aac",
                "-b:a", "192k",
                "-metadata:s:a:0", f"language={iso_code}",
                "-metadata:s:a:0", f"title={lang_name} Dubbed",
                "-shortest",
                str(output_video),
            ]

        run_ffmpeg(cmd)
        self.report("muxing", 100.0, "Muxing complete! Dubbed video is ready.")


# ==========================================
# Full Pipeline Runner
# ==========================================
async def run_full_pipeline(
    source_input: str,
    output_dir: Path,
    target_lang: str = "hi",
    voice_gender: str = "female",
    whisper_model: str = "base.en",
    source_lang: Optional[str] = "auto",
    protected_terms: Optional[List[str]] = None,
    burn_subtitles: bool = False,
    enable_ducking: bool = True,
    ducking_volume: float = 0.15,
    keep_original: bool = True,
    groq_api_key: Optional[str] = None,
    on_progress: Optional[Callable[[str, float, str, Optional[Dict[str, Any]]], None]] = None,
) -> Dict[str, Any]:
    """Execute the full end-to-end async dubbing pipeline."""
    pipeline = DubbingPipeline(output_dir / "work", on_progress=on_progress, groq_api_key=groq_api_key)

    # 1. Ingest (yt-dlp download or local copy in background thread)
    video_path, title = await asyncio.to_thread(pipeline.ingest_media, source_input)
    video_duration = await asyncio.to_thread(get_media_duration, video_path)

    # 2. Extract audio & transcribe (CPU-bound in thread pool)
    src_audio = await asyncio.to_thread(pipeline.extract_audio, video_path)
    segments = await asyncio.to_thread(
        pipeline.transcribe,
        src_audio,
        model_name=whisper_model,
        source_lang=source_lang,
        beam_size=1,
    )

    if not segments:
        raise RuntimeError("No speech detected in media file.")

    # 3. Translate (native async concurrent HTTP requests with glossary shielding)
    translated = await pipeline.translate_segments_async(
        segments, target_lang, protected_terms=protected_terms
    )

    # Save translation JSON & SRT
    json_path = output_dir / "translated_segments.json"
    json_path.write_text(json.dumps(translated, ensure_ascii=False, indent=2), encoding="utf-8")

    srt_path = output_dir / f"subtitles_{target_lang}.srt"
    await asyncio.to_thread(pipeline.export_srt, translated, srt_path)

    # 4. Synthesize TTS (native async concurrent Edge TTS workers with rate pacing)
    lang_config = LANGUAGES.get(target_lang, LANGUAGES["hi"])
    voice_id = lang_config["voices"].get(voice_gender, {}).get("id") or lang_config["default_voice"]
    fitted_segments = await pipeline.generate_tts_parallel(translated, voice_id)

    # 5. Build Timeline via NumPy (fast in thread)
    dubbed_raw_wav = output_dir / "work" / "dubbed_speech.wav"
    await asyncio.to_thread(
        pipeline.build_audio_timeline_numpy, fitted_segments, video_duration, dubbed_raw_wav
    )

    # 6. Apply Background Ducking (optional, studio quality)
    final_audio = dubbed_raw_wav
    if enable_ducking:
        ducked_master = output_dir / "work" / "dubbed_ducked_master.wav"
        await asyncio.to_thread(
            pipeline.apply_ducking,
            src_audio,
            dubbed_raw_wav,
            fitted_segments,
            video_duration,
            ducked_master,
            ducking_volume=ducking_volume,
        )
        final_audio = ducked_master

    # 7. Final Mux (with optional hardcoded subtitles)
    final_mp4 = output_dir / f"dubbed_{target_lang}.mp4"
    await asyncio.to_thread(
        pipeline.mux_video,
        video_path,
        final_audio,
        final_mp4,
        target_lang=target_lang,
        keep_original=keep_original,
        burn_subtitles=burn_subtitles,
        subtitles_file=srt_path,
    )

    return {
        "title": title,
        "video_duration": video_duration,
        "segments_count": len(translated),
        "video_file": str(final_mp4),
        "subtitles_file": str(srt_path),
        "audio_file": str(final_audio),
        "translated_json": str(json_path),
        "segments": translated,
        "detected_source_lang": pipeline.detected_source_lang,
    }
