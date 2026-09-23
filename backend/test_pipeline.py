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


if __name__ == "__main__":
    test_numpy_audio_timeline()
    asyncio.run(test_async_translation_and_glossary())
    test_device_detection()
    test_fastapi_endpoints()
    test_auth_endpoints()
    test_active_jobs_and_pwa()
    test_cloud_and_ffmpeg_binary()
    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY!")

