#!/usr/bin/env python3
"""
YouTube AI Dubber - High Performance CLI
---------------------------------------
Accelerated multi-threaded pipeline for creating studio-quality dubbed videos.

Usage:
    python dub_video.py "https://www.youtube.com/watch?v=VIDEO_ID" --language hi
    python dub_video.py video.mp4 --language mr --voice-gender male --ducking
"""

import argparse
import asyncio
import os
import shutil
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.dubbing_engine import LANGUAGES, run_full_pipeline


def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("\n[ERROR] FFmpeg was not found in PATH.")
        print("Please install FFmpeg and make sure ffmpeg and ffprobe are in your environment PATH.")
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="YouTube AI Dubber - High-performance AI Video Dubbing CLI"
    )
    parser.add_argument(
        "source",
        help="YouTube video URL or path to local media file (MP4/MKV/MOV/WebM)",
    )
    parser.add_argument(
        "--language",
        "-l",
        default="hi",
        choices=sorted(LANGUAGES.keys()),
        help="Target dubbing language (default: hi)",
    )
    parser.add_argument(
        "--voice-gender",
        "-g",
        default="female",
        choices=["female", "male"],
        help="Voice gender (female or male, default: female)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="base.en",
        choices=["tiny.en", "base.en", "small.en", "medium.en", "tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model. Default: base.en (Fast & accurate)",
    )
    parser.add_argument(
        "--ducking",
        action="store_true",
        default=True,
        help="Enable background music & ambience ducking (default: enabled)",
    )
    parser.add_argument(
        "--no-ducking",
        dest="ducking",
        action="store_false",
        help="Disable background audio ducking (speech-only output)",
    )
    parser.add_argument(
        "--ducking-volume",
        type=float,
        default=0.15,
        help="Background music volume during speech (0.05 to 0.4, default: 0.15)",
    )
    parser.add_argument(
        "--keep-original",
        action="store_true",
        default=True,
        help="Keep original audio as secondary audio track in MP4",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="output",
        help="Output directory (default: output)",
    )
    return parser.parse_args()


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    check_ffmpeg()
    args = parse_args()

    target_lang = args.language
    lang_meta = LANGUAGES.get(target_lang, {"name": target_lang, "native": ""})
    output_path = Path(args.output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("           YOUTUBE AI DUBBER STUDIO (HIGH-SPEED ENGINE)")
    print("=" * 65)
    native_str = f" ({lang_meta['native']})" if lang_meta.get("native") else ""
    print(f"Target Language   : {lang_meta['name']}{native_str}")
    print(f"Voice Character   : {args.voice_gender.capitalize()} Neural Voice")
    print(f"Whisper Model     : {args.model}")
    print(f"Background Ducking: {'Enabled (Volume: ' + str(int(args.ducking_volume*100)) + '%)' if args.ducking else 'Disabled'}")
    print(f"Original Audio    : {'Preserved as Track 2' if args.keep_original else 'Omitted'}")
    print(f"Output Directory  : {output_path}")
    print("=" * 65)

    last_stage = None

    def on_progress(stage, pct, msg, data=None):
        nonlocal last_stage
        if stage != last_stage:
            print(f"\n[{stage.upper()}] ({pct:.0f}%) {msg}")
            last_stage = stage
        else:
            print(f"    -> {msg}")

    try:
        res = asyncio.run(
            run_full_pipeline(
                source_input=args.source,
                output_dir=output_path,
                target_lang=target_lang,
                voice_gender=args.voice_gender,
                whisper_model=args.model,
                enable_ducking=args.ducking,
                ducking_volume=args.ducking_volume,
                keep_original=args.keep_original,
                on_progress=on_progress,
            )
        )

        print("\n" + "=" * 65)
        print("PIPELINE EXECUTION COMPLETE!")
        print("=" * 65)
        print(f"Dubbed Video : {res['video_file']}")
        print(f"Subtitles    : {res['subtitles_file']}")
        print(f"Audio Track  : {res['audio_file']}")
        print(f"Duration     : {res['video_duration']:.1f} seconds")
        print(f"Segments     : {res['segments_count']} speech segments")
        print("=" * 65)

    except KeyboardInterrupt:
        print("\nCancelled by user.")
        sys.exit(130)
    except Exception as exc:
        print(f"\n[ERROR] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
