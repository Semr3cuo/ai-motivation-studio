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

## Enviar vídeos privados ao YouTube

O workflow **Upload private YouTube video** usa o artefato
`motivation-video` de uma execução bem-sucedida de **Generate motivation
video** na branch `main`. O destino é o canal existente Mente Inabalável
(`@the_h4wk`). O workflow valida o ID do canal antes do envio e a
visibilidade privada depois. Ele inclui na descrição os créditos do artefato
e usa o vídeo já renderizado, sem chamar a API da OpenAI.

1. Ative a YouTube Data API v3 no projeto do Google Cloud. Configure o cliente
   OAuth e autorize o canal com acesso offline e os escopos
   `https://www.googleapis.com/auth/youtube.upload` e
   `https://www.googleapis.com/auth/youtube.readonly`.
2. Registre `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` e
   `YOUTUBE_REFRESH_TOKEN` como Actions secrets deste repositório. Um token
   de atualização de um app externo em modo Testing normalmente expira em sete
   dias.
3. Em Actions, execute **Generate motivation video** na branch `main`.
   Abra o resumo da execução e baixe `motivation-video` para revisar o MP4,
   as legendas e os créditos. O resumo informa o ID e o SHA-256 do MP4.
4. Se aprovar o vídeo, abra **Upload private YouTube video** na branch
   `main`, informe `run_id` e `video_sha256`, e marque `approved`.
   O envio só inicia com a aprovação e se o MP4 baixado corresponder ao hash.
   A publicação no canal permanece privada. O artefato dura sete dias.

O histórico está nas tags Git `youtube-upload/<sha256>/uploaded/<video-id>`.
O hash identifica MP4s byte a byte. Cada tentativa grava primeiro a tag
`youtube-upload/<sha256>/pending`. Se a execução parar antes de registrar o
ID, o workflow bloqueia novas tentativas do mesmo arquivo. Confira o Studio
e os metadados do vídeo (tag `ams-sha256:<sha256>`) antes de reconciliar:
registre a tag de sucesso com o ID encontrado, ou remova a reserva somente
depois de confirmar que o upload não foi criado.
