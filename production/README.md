# Produção semanal do Mente Inabalável

O lote recebe quatro narrativas, filmagens, locução, trilhas e uma miniatura, com os comprovantes de uso. A montagem roda com Python 3.11+, FFmpeg, FFprobe e fonte DejaVu Sans. Use um FFmpeg com libass e libx264. A montagem usa mídia local e não consome créditos nem lê credenciais do YouTube.

## Entrada

Duplique `manifesto.exemplo.json` numa pasta privada e complete todos os formatos. Use uma unidade de legenda por cena. Grave ou sintetize a locução aprovada em arquivos separados, com pausas naturais. Cada trecho curto da locução permite que a entrada e a saída da legenda acompanhem a fala; escute o resultado para revisar as pausas. O campo `inicio` indica o segundo inicial da filmagem.

Registre cada tomada, locução, trilha e miniatura em `midias`. Anexe comprovantes adequados ao uso mundial comercial no YouTube, incluindo edição e distribuição. Informe os créditos no formato exigido pela licença ou use `dispensada`. Para produção original, arquive a declaração do titular e as autorizações de voz e imagem aplicáveis. Para voz sintética, verifique os termos do software, do modelo e da voz. Os relatórios copiam comprovantes. Mantenha o lote de revisão em ambiente privado.

O arquivo `disciplina.md` contém o primeiro roteiro e os metadados editoriais. Escolha tomadas que correspondam às ações e organize a mixagem, a cadência e o enquadramento para cada formato.

## Execução

```sh
python -m app.production /caminho/manifesto.json --validar /caminho/lote-001
python -m app.production /caminho/manifesto.json /caminho/lote-001
```

Cada lote entrega quatro MP4, quatro SRT, quatro roteiros de locução, metadados por vídeo, miniatura horizontal, relatório de licenças com comprovantes e controle técnico com SHA-256 para cada MP4. A verificação automática cobre codec, resolução, taxa de quadros e duração. O preenchimento do registro de licenças exige revisão editorial e documental humana.

## Revisão e publicação no canal

1. Assista aos quatro MP4 e revise a conexão entre fala e cena, a naturalidade da voz, as legendas, a mixagem e as licenças. Vincule sua aprovação a cada arquivo pelo SHA-256.
2. No YouTube Studio, envie apenas os arquivos aprovados como **Privado**. Carregue o SRT, aplique os metadados, use a miniatura no vídeo principal e faça a declaração de conteúdo sintético quando se aplicar.
3. Registre no controle a URL/ID de cada vídeo privado, a data, a aprovação e o resultado das verificações do Studio. Aguarde o processamento e a conclusão das verificações. Havendo reivindicação ou licença pendente, mantenha o vídeo privado e substitua o material quando necessário.
4. Após sua confirmação para publicação, agende o vídeo aprovado no próprio Studio. Use o horário de Brasília e confira a data antes de salvar.

| Dia | Versão | Duração | Horário |
| --- | --- | --- | --- |
| Segunda | Principal | 4min45s a 5min15s | 19h |
| Terça | Impacto | 30–45s | 12h |
| Quinta | Reflexão | 60–90s | 19h |
| Sábado | Superação | 120–175s | 9h |
