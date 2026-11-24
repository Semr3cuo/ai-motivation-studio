from pathlib import Path

from app.config.settings import settings


def generate_voice(text: str, output_path: Path) -> Path:
    """Generate narration audio with OpenAI TTS."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY é necessária para gerar a voz.")

    from openai import OpenAI

    output_path.parent.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=settings.openai_api_key)

    with client.audio.speech.with_streaming_response.create(
        model=settings.tts_model,
        voice=settings.tts_voice,
        input=text,
        response_format="mp3",
    ) as response:
        response.stream_to_file(output_path)

    return output_path
