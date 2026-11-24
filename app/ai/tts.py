from pathlib import Path

from openai import OpenAI

from app.config.settings import settings


TTS_MODEL = "gpt-4o-mini-tts"
TTS_VOICE = "marin"


def generate_narration(text: str, output_path: Path) -> Path:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY é obrigatório para gerar a narração.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    client = OpenAI(api_key=settings.openai_api_key)
    with client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=TTS_VOICE,
        input=text,
        instructions=(
            "Fale em português do Brasil, com voz natural, motivacional e segura. "
            "Ritmo envolvente, pausas curtas entre ideias e energia de narrador de vídeos curtos."
        ),
        response_format="mp3",
    ) as response:
        response.stream_to_file(output_path)

    return output_path
