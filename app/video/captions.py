from pathlib import Path
import re


def _fmt(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def create_srt(text: str, duration: float, output_path: Path) -> Path:
    words = re.findall(r"\S+", text.strip())
    if not words:
        raise ValueError("Texto vazio para legendas.")

    # Pequenos blocos facilitam leitura em Shorts.
    chunk_size = 7
    chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
    slot = duration / len(chunks)

    lines = []
    for index, chunk in enumerate(chunks, start=1):
        start = (index - 1) * slot
        end = min(duration, index * slot)
        lines.extend([
            str(index),
            f"{_fmt(start)} --> {_fmt(end)}",
            " ".join(chunk),
            "",
        ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
