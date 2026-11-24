from pathlib import Path
import re
import subprocess


def _timestamp(seconds: float) -> str:
    total_ms = max(0, int(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _audio_duration(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def create_srt(text: str, audio_path: Path, output_path: Path) -> Path:
    duration = _audio_duration(audio_path)
    words = re.findall(r"\S+", text.strip())
    if not words:
        raise ValueError("Texto da narração vazio.")

    # MVP: distribuição proporcional por quantidade de palavras.
    # Na próxima etapa podemos trocar por timestamps reais via transcrição.
    chunk_size = 5
    chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
    total_words = sum(len(chunk) for chunk in chunks)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []

    cursor = 0
    for index, chunk in enumerate(chunks, start=1):
        start = duration * cursor / total_words
        cursor += len(chunk)
        end = duration * cursor / total_words
        lines.extend([
            str(index),
            f"{_timestamp(start)} --> {_timestamp(end)}",
            " ".join(chunk),
            "",
        ])

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def audio_duration(audio_path: Path) -> float:
    return _audio_duration(audio_path)
