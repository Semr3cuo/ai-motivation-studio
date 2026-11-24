# AI Motivation Studio

Automated AI motivation video creation and publishing studio.

## MVP atual

A primeira versão implementa:
- geração de roteiro motivacional com IA;
- fallback local sem API;
- criação de arte vertical 1080x1920;
- renderização de MP4 usando FFmpeg.

O objetivo desta etapa é validar o pipeline antes de adicionar voz, mídia dinâmica,
legendas sincronizadas e publicação automática.

## Requisitos

- Python 3.11+
- FFmpeg disponível no PATH
- Chave da API da OpenAI para geração real de roteiros

## Instalação

```
python -m venv .venv
```

Windows:

```
.venv\\Scripts\\activate
```

Linux/macOS:

```
source .venv/bin/activate
```

Instale as dependências:

```
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e informe `OPENAI_API_KEY`.

## Executar

```
python -m app.main --tema "Nunca desista dos seus objetivos"
```

Sem chave da OpenAI, o sistema usa um roteiro local de fallback.

O vídeo será criado em `output/videos/`.

## Próximas etapas

- TTS/narração;
- mídia de fundo;
- legendas sincronizadas;
- trilha sonora;
- banco de conteúdos;
- validação de qualidade e repetição;
- publicação no YouTube Shorts;
- publicação no TikTok;
- agendamento;
- métricas e otimização por IA.
