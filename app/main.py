import argparse
from pathlib import Path
import re

from app.ai.script_generator import generate_script
from app.config.settings import settings
from app.video.renderer import render_complete_video


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9à-ÿ]+", "-", value, flags=re.IGNORECASE)
    return value.strip("-")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera um vídeo motivacional vertical.")
    parser.add_argument("--tema", required=True, help="Tema do vídeo.")
    parser.add_argument("--duracao", type=int, default=8, help="Mantido por compatibilidade; a duração final acompanha a narração.")
    args = parser.parse_args()

    print(f"Gerando roteiro para: {args.tema}")
    script = generate_script(args.tema)
    print(f"Título: {script.title}")
    print("Gerando voz, legendas e vídeo final...")

    output_dir = Path(settings.output_dir) / "videos"
    output_path = output_dir / f"{slugify(script.title)}.mp4"
    render_complete_video(script, output_path)
    print(f"Vídeo criado: {output_path}")


if __name__ == "__main__":
    main()
