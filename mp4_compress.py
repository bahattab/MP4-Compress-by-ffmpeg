#!/usr/bin/env python3
"""Compress MP4 videos with FFmpeg using practical H.264/H.265 presets."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def ffmpeg_duration(path: Path) -> float:
    """Read input duration in seconds with ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise ValueError("تعذر قراءة مدة الفيديو من ffprobe.") from exc
    if duration <= 0:
        raise ValueError("مدة الفيديو غير صالحة.")
    return duration


def build_video_filters(height: int | None, fps: float | None) -> list[str]:
    filters: list[str] = []
    if height:
        filters.append(f"scale=-2:{height}")
    if filters:
        return ["-vf", ",".join(filters)]
    if fps:
        return ["-vf", f"fps={fps:g}"]
    return []


def compress(args: argparse.Namespace) -> None:
    source = args.input.expanduser().resolve()
    destination = args.output.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"ملف الإدخال غير موجود: {source}")
    if source == destination:
        raise ValueError("يجب أن يكون ملف الإخراج مختلفاً عن ملف الإدخال.")
    destination.parent.mkdir(parents=True, exist_ok=True)

    encoder = "libx265" if args.codec == "h265" else "libx264"
    filters = build_video_filters(args.height, args.fps)
    audio_args = ["-an"] if args.no_audio else ["-c:a", "aac", "-b:a", args.audio_bitrate]
    common = ["-i", str(source), "-c:v", encoder, "-preset", args.preset, *filters]

    if args.target_size_mb:
        duration = ffmpeg_duration(source)
        target_bits_per_second = args.target_size_mb * 1_000_000 * 8 / duration
        audio_bits_per_second = 0 if args.no_audio else args.audio_bitrate_kbps * 1000
        # Reserve 5% for container overhead and subtract audio from the total.
        video_kbps = int((target_bits_per_second * 0.95 - audio_bits_per_second) / 1000)
        if video_kbps < 100:
            raise ValueError("الحجم المستهدف صغير جداً لمدة الفيديو ومعدل الصوت المحددين.")
        with tempfile.TemporaryDirectory(prefix="ffmpeg-pass-") as temp_dir:
            passlog = str(Path(temp_dir) / "ffmpeg2pass")
            first_pass = [
                "ffmpeg", "-y", "-i", str(source), "-c:v", encoder,
                "-b:v", f"{video_kbps}k", "-preset", args.preset,
                *filters, "-pass", "1", "-passlogfile", passlog,
                "-an", "-f", "null", "NUL" if sys.platform == "win32" else "/dev/null",
            ]
            second_pass = [
                "ffmpeg", "-y", *common, "-b:v", f"{video_kbps}k",
                "-pass", "2", "-passlogfile", passlog, *audio_args, str(destination),
            ]
            subprocess.run(first_pass, check=True)
            subprocess.run(second_pass, check=True)
        print(f"تم الضغط بمعدل فيديو مستهدف {video_kbps} kbps: {destination}")
        return

    command = [
        "ffmpeg", "-y", *common, "-crf", str(args.crf),
        *audio_args, str(destination),
    ]
    subprocess.run(command, check=True)
    print(f"اكتمل الضغط: {destination}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ضغط ملفات MP4 باستخدام FFmpeg وترميز H.264 أو H.265."
    )
    parser.add_argument("input", type=Path, help="ملف الفيديو الأصلي")
    parser.add_argument("output", type=Path, help="مسار ملف MP4 الناتج")
    parser.add_argument("--codec", choices=("h264", "h265"), default="h264")
    parser.add_argument("--crf", type=int, default=24, help="قيمة CRF، والأقل يعني جودة أعلى (افتراضي 24)")
    parser.add_argument("--preset", default="medium", help="سرعة الترميز: ultrafast إلى veryslow (افتراضي medium)")
    parser.add_argument("--height", type=int, choices=(1080, 720), help="تغيير ارتفاع الفيديو مع الحفاظ على النسبة")
    parser.add_argument("--fps", type=float, help="تحديد معدل الإطارات، مثلاً 24")
    parser.add_argument("--audio-bitrate", default="128k", help="معدل صوت AAC (افتراضي 128k)")
    parser.add_argument("--no-audio", action="store_true", help="حذف الصوت")
    parser.add_argument("--target-size-mb", type=float, help="استهداف حجم تقريبي بالميجابايت باستخدام ترميز على مرحلتين")
    args = parser.parse_args()
    if args.crf < 0 or args.crf > 51:
        parser.error("يجب أن تكون قيمة CRF بين 0 و51.")
    if args.height and args.fps:
        parser.error("اختر --height أو --fps في كل مرة لتفادي استبدال أحد المرشحات.")
    if args.fps is not None and args.fps <= 0:
        parser.error("يجب أن يكون معدل الإطارات أكبر من صفر.")
    if args.target_size_mb is not None and args.target_size_mb <= 0:
        parser.error("يجب أن يكون الحجم المستهدف أكبر من صفر.")
    if args.target_size_mb is not None and args.codec == "h265":
        parser.error("وضع الحجم المستهدف يستخدم H.264 ثنائي المرور حالياً؛ أزل --codec h265.")
    if not shutil.which("ffmpeg"):
        parser.error("لم يتم العثور على ffmpeg. شغّل ملف الإعداد المناسب لنظامك.")
    if args.target_size_mb and not args.no_audio:
        try:
            args.audio_bitrate_kbps = int(args.audio_bitrate.lower().removesuffix("k"))
        except ValueError:
            parser.error("اكتب معدل الصوت بوحدة kbps مثل 128k.")
    else:
        args.audio_bitrate_kbps = 0
    return args


if __name__ == "__main__":
    try:
        compress(parse_args())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"خطأ: {error}", file=sys.stderr)
        sys.exit(1)
