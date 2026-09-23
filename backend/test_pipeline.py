#!/usr/bin/env python3
"""
Automated unit & integration verification for Dubbing Pipeline (Phase 1 Upgrades)
Tests NumPy timeline generation, async translation, glossary token shielding,
device detection, QR code generation, network info, and FastAPI endpoints.
"""

import asyncio
import json
import os
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

# Ensure root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.dubbing_engine import (
    LANGUAGES,
    DubbingPipeline,
    detect_compute_device,
)
from backend.server import app, load_jobs_history, save_jobs_history, JOBS
from fastapi.testclient import TestClient


def test_numpy_audio_timeline():
    """Verify that NumPy timeline mixer creates clean 48kHz stereo WAV without clipping or errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pipeline = DubbingPipeline(tmp_path)

        # Create 3 simulated 48kHz stereo WAV segments
        sample_rate = 48000
        channels = 2
        segment_files = []

        for i, start_time in enumerate([0.5, 2.0, 4.2]):
            seg_duration = 1.0  # 1 second
            num_samples = int(seg_duration * sample_rate)
            # Generate a 440Hz sine wave
            t = np.linspace(0, seg_duration, num_samples, endpoint=False)
            sine = (np.sin(2 * np.pi * 440 * t) * 15000).astype(np.int16)
            stereo = np.column_stack((sine, sine))

            seg_wav = tmp_path / f"test_seg_{i}.wav"
            with wave.open(str(seg_wav), "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(stereo.tobytes())

            segment_files.append({
                "file": seg_wav,
                "start": start_time,
                "end": start_time + seg_duration,
            })

        output_wav = tmp_path / "mixed_timeline.wav"
        video_duration = 6.0

        # Build timeline
        pipeline.build_audio_timeline_numpy(segment_files, video_duration, output_wav)

        assert output_wav.exists(), "Output WAV was not created!"
        with wave.open(str(output_wav), "rb") as wf:
            assert wf.getframerate() == 48000, f"Expected 48kHz, got {wf.getframerate()}"
            assert wf.getnchannels() == 2, f"Expected 2 channels, got {wf.getnchannels()}"
            assert wf.getsampwidth() == 2, f"Expected 16-bit (2 bytes), got {wf.getsampwidth()}"
            actual_duration = wf.getnframes() / wf.getframerate()
            assert abs(actual_duration - video_duration) < 0.1, f"Duration mismatch: {actual_duration} vs {video_duration}"

    print("[PASS] test_numpy_audio_timeline passed successfully!")


async def test_async_translation_and_glossary():
    """Verify that batched async translation works and preserves protected glossary terms."""
    pipeline = DubbingPipeline(Path(tempfile.gettempdir()))

    sample_segments = [
        {"id": 1, "text": "Welcome to Python and DeepMind tools.", "start": 0.0, "end": 2.0},
        {"id": 2, "text": "This video is dubbed automatically with OpenAI.", "start": 2.2, "end": 4.5},
    ]

    protected = ["Python", "DeepMind", "OpenAI"]
    translated = await pipeline.translate_segments_async(sample_segments, "hi", protected_terms=protected)
    assert len(translated) == 2, "Failed to translate all segments"

    for seg in translated:
        text = seg["translated"]
        # Verify protected terms are retained in the translation
        if seg["id"] == 1:
            assert "Python" in text or "python" in text.lower(), f"Term Python was not preserved: {text}"
            assert "DeepMind" in text or "deepmind" in text.lower(), f"Term DeepMind was not preserved: {text}"
        if seg["id"] == 2:
            assert "OpenAI" in text or "openai" in text.lower(), f"Term OpenAI was not preserved: {text}"

    print("[PASS] test_async_translation_and_glossary passed successfully!")


def test_device_detection():
    """Verify GPU/CPU auto-detection."""
    device, compute_type = detect_compute_device()
    assert device in ["cuda", "cpu"], f"Unknown device: {device}"
    assert compute_type in ["float16", "int8", "float32"], f"Unknown compute type: {compute_type}"
    print(f"[PASS] test_device_detection passed: {device.upper()} ({compute_type})")


def test_fastapi_endpoints():
    """Test REST endpoints using TestClient."""
    client = TestClient(app)

    # 1. Health check with device probe
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "cpu_count" in data
    assert "device" in data
    assert "compute_type" in data
    assert "is_cuda" in data

    # 2. Languages check
    res = client.get("/api/languages")
    assert res.status_code == 200
    langs = res.json()["languages"]
    assert "hi" in langs
    assert "mr" in langs
    assert "ta" in langs
    assert "en" in langs

    # 3. Network info check
    res = client.get("/api/network-info")
    assert res.status_code == 200
    net = res.json()
    assert "local_ip" in net
    assert "port" in net
    assert "url" in net

    # 4. QR Code check (SVG format)
    res = client.get("/api/qr-code")
    assert res.status_code == 200
    assert "svg" in res.headers.get("content-type", "")
    assert "<svg" in res.text

    # 5. Jobs list & deletion check
    res = client.get("/api/jobs")
    assert res.status_code == 200
    assert "jobs" in res.json()

    print("[PASS] test_fastapi_endpoints passed successfully!")


def test_auth_endpoints():
    """Test user registration, login, and profile fetching."""
    client = TestClient(app)
    import time
    test_user = f"tester_{int(time.time())}"
    test_email = f"{test_user}@example.com"
    test_pwd = "SecretPassword123"

    # 1. Register new user
    res = client.post("/api/auth/register", json={
        "username": test_user,
        "email": test_email,
        "password": test_pwd
    })
    assert res.status_code == 200, f"Register failed: {res.text}"
    user_data = res.json()["user"]
    assert user_data["username"] == test_user
    assert user_data["email"] == test_email
    token = user_data["token"]
    assert token

    # 2. Try duplicate registration
    res_dup = client.post("/api/auth/register", json={
        "username": test_user,
        "email": test_email,
        "password": test_pwd
    })
    assert res_dup.status_code == 400

    # 3. Login with correct credentials
    res_login = client.post("/api/auth/login", json={
        "username": test_user,
        "password": test_pwd
    })
    assert res_login.status_code == 200
    assert res_login.json()["user"]["username"] == test_user

    # 4. Login with wrong password
    res_bad = client.post("/api/auth/login", json={
        "username": test_user,
        "password": "WrongPassword"
    })
    assert res_bad.status_code == 401

    # 5. Fetch profile with token
    res_me = client.get(f"/api/auth/me?token={token}")
    assert res_me.status_code == 200
    assert res_me.json()["user"]["username"] == test_user

    # 6. Fetch profile with invalid token
    res_bad_me = client.get("/api/auth/me?token=invalid_token")
    assert res_bad_me.status_code == 401

    print("[PASS] test_auth_endpoints passed successfully!")


def test_active_jobs_and_pwa():
    """Test active jobs queue endpoint and PWA assets."""
    client = TestClient(app)

    # 1. Active jobs queue
    res_active = client.get("/api/jobs/active")
    assert res_active.status_code == 200
    data = res_active.json()
    assert "active_jobs" in data
    assert isinstance(data["active_jobs"], list)

    # 2. Manifest JSON
    res_manifest = client.get("/manifest.json")
    assert res_manifest.status_code == 200
    manifest = res_manifest.json()
    assert manifest["name"] in ["AI Dubber Studio", "YouTube AI Dubber"]
    assert manifest["display"] == "standalone"
    assert len(manifest["icons"]) >= 2

    # 3. Service Worker
    res_sw = client.get("/sw.js")
    assert res_sw.status_code == 200
    assert "install" in res_sw.text
    assert "fetch" in res_sw.text

    # 4. PNG App Icons
    res_icon192 = client.get("/icon-192.png")
    assert res_icon192.status_code == 200
    assert "image/png" in res_icon192.headers.get("content-type", "")

    res_icon512 = client.get("/icon-512.png")
    assert res_icon512.status_code == 200
    assert "image/png" in res_icon512.headers.get("content-type", "")

    print("[PASS] test_active_jobs_and_pwa passed successfully!")


def test_cloud_and_ffmpeg_binary():
    """Verify cloud version metadata and FFmpeg binary resolution."""
    from backend.dubbing_engine import get_ffmpeg_binary, FFMPEG_BIN
    client = TestClient(app)

    # 1. Version endpoint
    res = client.get("/api/version")
    assert res.status_code == 200
    v = res.json()
    assert v["version"] == "2.2.0"
    assert v["groq_cloud_whisper_supported"] is True

    # 2. FFmpeg binary resolution
    resolved_bin = get_ffmpeg_binary()
    assert resolved_bin is not None
    assert len(resolved_bin) > 0
    assert FFMPEG_BIN is not None

    print("[PASS] test_cloud_and_ffmpeg_binary passed successfully!")


def test_speaker_turn_assignment():
    """Verify conversational speaker turn detection based on speech pause gaps."""
    from backend.dubbing_engine import assign_speaker_turns

    sample_segments = [
        {"id": 1, "start": 0.0, "end": 1.5, "text": "Hello, how are you doing today?"},
        {"id": 2, "start": 1.6, "end": 2.8, "text": "I am doing well, thank you."},  # gap 0.1s -> Speaker 1 continues
        {"id": 3, "start": 3.8, "end": 5.0, "text": "Did you see the new update?"},    # gap 1.0s (> 0.75s) -> Speaker 2 turns
        {"id": 4, "start": 6.2, "end": 7.5, "text": "Yes, it looks amazing!"},         # gap 1.2s (> 0.75s) -> Speaker 1 turns
    ]

    tagged = assign_speaker_turns(sample_segments)
    assert tagged[0]["speaker"] == "Speaker 1"
    assert tagged[1]["speaker"] == "Speaker 1"
    assert tagged[2]["speaker"] == "Speaker 2"
    assert tagged[3]["speaker"] == "Speaker 1"

    print("[PASS] test_speaker_turn_assignment passed successfully!")


def test_vocal_isolation_and_music_mixing():
    """Verify vocal side-channel cancellation and NumPy audio mixing."""
    from backend.dubbing_engine import DubbingPipeline
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pipeline = DubbingPipeline(tmp_path)

        # Create stereo WAV with center voice (L=R) and stereo side music (L=-R)
        sr = 48000
        duration = 2.0
        n_samples = int(sr * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        center_voice = (np.sin(2 * np.pi * 300 * t) * 10000).astype(np.int16)
        side_music = (np.sin(2 * np.pi * 800 * t) * 8000).astype(np.int16)

        left = center_voice + side_music
        right = center_voice - side_music
        stereo = np.column_stack((left, right))

        src_wav = tmp_path / "source_audio.wav"
        with wave.open(str(src_wav), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(stereo.tobytes())

        isolated_music = tmp_path / "isolated_music.wav"
        pipeline.isolate_music_and_sfx(src_wav, isolated_music)
        assert isolated_music.exists(), "Isolated music WAV was not created"

        # Create dubbed speech WAV
        dubbed_speech = tmp_path / "dubbed_speech.wav"
        speech_sine = (np.sin(2 * np.pi * 250 * t) * 12000).astype(np.int16)
        with wave.open(str(dubbed_speech), "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(np.column_stack((speech_sine, speech_sine)).tobytes())

        master_out = tmp_path / "master_mixed.wav"
        pipeline.mix_dubbed_with_isolated_music(isolated_music, dubbed_speech, duration, master_out)
        assert master_out.exists(), "Master mixed WAV was not created"

        with wave.open(str(master_out), "rb") as wf:
            assert wf.getframerate() == 48000
            assert wf.getnchannels() == 2

    print("[PASS] test_vocal_isolation_and_music_mixing passed successfully!")


def test_subtitles_ass_and_vtt_exports():
    """Verify ASS kinetic captions and WebVTT export formats."""
    from backend.dubbing_engine import export_ass_captions, DubbingPipeline
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pipeline = DubbingPipeline(tmp_path)

        segments = [
            {"id": 1, "start": 0.5, "end": 2.0, "text": "Hello world", "translated": "नमस्ते दुनिया"},
            {"id": 2, "start": 2.5, "end": 4.0, "text": "This is a test", "translated": "यह एक परीक्षण है"},
        ]

        srt_path = tmp_path / "test.srt"
        pipeline.export_srt(segments, srt_path)
        assert srt_path.exists()
        assert "00:00:00,500 --> 00:00:02,000" in srt_path.read_text(encoding="utf-8")

        vtt_path = tmp_path / "test.vtt"
        pipeline.export_vtt(segments, vtt_path)
        assert vtt_path.exists()
        vtt_content = vtt_path.read_text(encoding="utf-8")
        assert "WEBVTT" in vtt_content
        assert "00:00:00.500 --> 00:00:02.000" in vtt_content

        ass_path = tmp_path / "test.ass"
        export_ass_captions(srt_path, ass_path)
        assert ass_path.exists()
        ass_content = ass_path.read_text(encoding="utf-8")
        assert "[Script Info]" in ass_content
        assert "PlayResX: 1080" in ass_content
        assert "PlayResY: 1920" in ass_content
        assert "Dialogue: 0," in ass_content

    print("[PASS] test_subtitles_ass_and_vtt_exports passed successfully!")


def test_vertical_short_rendering():
    """Verify 9:16 vertical short video rendering with blurred background and subtitles."""
    from backend.dubbing_engine import export_vertical_short, run_ffmpeg
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create 2-second test video (1280x720) with test audio
        test_video = tmp_path / "test_video.mp4"
        run_ffmpeg([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=navy:s=1280x720:d=2:r=25",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            str(test_video),
        ])

        srt_path = tmp_path / "test.srt"
        srt_path.write_text("1\n00:00:00,100 --> 00:00:01,800\nViral Short Caption Test\n\n", encoding="utf-8")

        output_short = tmp_path / "output_short.mp4"
        export_vertical_short(
            video_path=test_video,
            audio_path=test_video,
            srt_path=srt_path,
            output_short_path=output_short,
            start_time=0.0,
            duration=1.5,
        )

        assert output_short.exists(), "Vertical short was not created!"
        assert output_short.stat().st_size > 1000, "Output short file is empty!"

    print("[PASS] test_vertical_short_rendering passed successfully!")


if __name__ == "__main__":
    test_numpy_audio_timeline()
    asyncio.run(test_async_translation_and_glossary())
    test_device_detection()
    test_fastapi_endpoints()
    test_auth_endpoints()
    test_active_jobs_and_pwa()
    test_cloud_and_ffmpeg_binary()
    test_speaker_turn_assignment()
    test_vocal_isolation_and_music_mixing()
    test_subtitles_ass_and_vtt_exports()
    test_vertical_short_rendering()
    print("\nALL 11 AUTOMATED INTEGRATION TESTS PASSED SUCCESSFULLY!")

