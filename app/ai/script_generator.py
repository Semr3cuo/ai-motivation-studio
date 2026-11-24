import json
from dataclasses import dataclass

from app.ai.prompts import SCRIPT_PROMPT
from app.config.settings import settings


@dataclass
class Script:
    title: str
    hook: str
    narration: str
    cta: str
    visual_direction: str


def _fallback_script(theme: str) -> Script:
    return Script(
        title=f"Não desista: {theme}",
        hook="Talvez você esteja mais perto do que imagina.",
        narration=(
            f"Quando o assunto é {theme.lower()}, é fácil olhar para o caminho "
            "e pensar que você não está avançando. Mas progresso nem sempre faz "
            "barulho. Às vezes, ele aparece quando você decide continuar mesmo "
            "sem vontade, mesmo sem aplausos e mesmo sem saber exatamente quando "
            "o resultado vai chegar. Não compare o seu capítulo atual com o "
            "capítulo final de outra pessoa. Faça o que está ao seu alcance hoje. "
            "Um passo pequeno ainda é um passo. E quando você repete esse passo "
            "todos os dias, ele começa a construir algo maior."
        ),
        cta="Continue. Seu próximo passo pode começar hoje.",
        visual_direction="Pessoa caminhando ao amanhecer, cenas urbanas e natureza, ritmo contemplativo.",
    )


def generate_script(theme: str) -> Script:
    if not settings.openai_api_key:
        return _fallback_script(theme)

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        input=SCRIPT_PROMPT.format(theme=theme),
    )

    raw = response.output_text.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"A IA não retornou JSON válido: {raw}") from exc

    required = {"title", "hook", "narration", "cta", "visual_direction"}
    missing = required.difference(data)
    if missing:
        raise ValueError(f"Campos ausentes no roteiro: {', '.join(sorted(missing))}")

    return Script(**{key: str(data[key]).strip() for key in required})
