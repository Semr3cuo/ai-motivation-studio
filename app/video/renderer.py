from pathlib import Path
import textwrap
import subprocess

from PIL import Image, ImageDraw, ImageFont

from app.config.settings import settings
from app.ai.script_generator import Script


def _font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold
        else "C:/Windows/Fonts/arial.ttf",
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

    margin = 90
    y = 230

    draw.text((margin, y), "MOTIVAÇÃO", font=_font(34, bold=True), fill=(180, 190, 210))
    y += 130

    for line in textwrap.wrap(script.title, width=22):
        draw.text((margin, y), line, font=title_font, fill="white")
        y += 92

    y += 90
    for line in textwrap.wrap(script.hook, width=34):
        draw.text((margin, y), line, font=body_font, fill=(225, 230, 240))
        y += 58

    y = settings.video_height - 260
    for line in textwrap.wrap(script.cta, width=30):
        draw.text((margin, y), line, font=cta_font, fill="white")
        y += 64

    image.save(path)


def render_video(script: Script, output_path: Path, duration: int = 8) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cover = output_path.with_suffix(".png")
    create_cover(script, cover)

    command = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", str(cover),
        "-t", str(duration),
        "-r", str(settings.video_fps),
        "-vf", f"scale={settings.video_width}:{settings.video_height}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path),
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "FFmpeg não foi encontrado. Instale o FFmpeg e deixe o executável no PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"FFmpeg falhou: {exc.stderr}") from exc
    finally:
        cover.unlink(missing_ok=True)

    return output_path
