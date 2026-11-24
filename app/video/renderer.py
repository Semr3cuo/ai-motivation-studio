from pathlib import Path
import subprocess
import textwrap

from PIL import Image, ImageDraw, ImageFont

from app.config.settings import settings
from app.ai.script_generator import Script
from app.ai.tts import generate_narration
from app.video.subtitles import audio_duration, create_srt


def _font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def create_cover(script: Script, path: Path) -> None:
    image = Image.new("RGB", (settings.video_width, settings.video_height), (12, 16, 24))
    draw = ImageDraw.Draw(image)
    title_font = _font(76, bold=True)
    body_font = _font(42)
    cta_font = _font(48, bold=True)
    disclosure_font = _font(24)
    margin, y = 90, 230

    draw.text((margin, y), "MOTIVAÇÃO", font=_font(34, bold=True), fill=(180, 190, 210))
    y += 130
    for line in textwrap.wrap(script.title, width=22):
        draw.text((margin, y), line, font=title_font, fill="white")
        y += 92
    y += 90
    for line in textwrap.wrap(script.hook, width=34):
        draw.text((margin, y), line, font=body_font, fill=(225, 230, 240))
        y += 58
    y = settings.video_height - 300
    for line in textwrap.wrap(script.cta, width=30):
        draw.text((margin, y), line, font=cta_font, fill="white")
        y += 64
    draw.text((margin, settings.video_height - 70), "Voz gerada por IA", font=disclosure_font, fill=(170, 175, 185))
    image.save(path)


def _render_static_video(cover: Path, output_path: Path, duration: float) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(cover),
        "-t", f"{duration:.3f}", "-r", str(settings.video_fps),
        "-vf", f"scale={settings.video_width}:{settings.video_height}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path),
    ], check=True, capture_output=True, text=True)


def render_complete_video(script: Script, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio_path = output_path.with_name(output_path.stem + "-voice.mp3")
    srt_path = output_path.with_name(output_path.stem + ".srt")
    cover = output_path.with_suffix(".png")
    silent_video = output_path.with_name(output_path.stem + "-silent.mp4")

    create_cover(script, cover)
    generate_narration(script.narration, audio_path)
    create_srt(script.narration, audio_path, srt_path)
    duration = audio_duration(audio_path) + 0.25

    try:
        _render_static_video(cover, silent_video, duration)
        subtitle_filter = (
            f"subtitles={srt_path}:force_style="
            "FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,"
            "Alignment=2,MarginV=180"
        )
        subprocess.run([
            "ffmpeg", "-y", "-i", str(silent_video), "-i", str(audio_path),
            "-vf", subtitle_filter, "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p", "-shortest", "-movflags", "+faststart",
            str(output_path),
        ], check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("FFmpeg/FFprobe não foi encontrado no PATH.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"FFmpeg falhou: {exc.stderr}") from exc
    finally:
        for path in (cover, silent_video, audio_path, srt_path):
            path.unlink(missing_ok=True)
    return output_path
