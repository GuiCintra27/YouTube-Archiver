# CLAUDE.md — yt-archiver

## Contexto do projeto
- **Objetivo**: baixar vídeos (YouTube/HLS sem DRM) com `yt-dlp` via script Python `main.py`,
  com suporte a headers/cookies, nome customizado e upload opcional ao Google Drive.
- **UI**: app React + Vite + Tailwind que gera comandos para o script/yt-dlp. Vamos migrar/usar **shadcn/ui** onde fizer sentido.

## Arquitetura
- `python/main.py` (neste repo raiz) — usa `yt-dlp` + `ffmpeg`.
  - Flags importantes: `--cookies-file`, `--referer`, `--origin`, `--concurrent-fragments`, `--path`, `--file-name`, `--archive-id`.
- `yt-archiver-ui/` — UI Vite/React/TS com Tailwind. Podemos adicionar shadcn/ui (components on-demand) e presets.

## Convenções de código
- **Python**: tipagem leve, mudanças mínimas (evitar regressão). PEP8 onde der, mas priorize estabilidade.
- **TS/React**: função como default export, hooks, sem libs de estilo além de Tailwind/shadcn.
- **UI/UX**: acessível, foco em clareza; evitar mutações bruscas na API do script.

## Pedidos típicos
- _“Adicionar uma flag nova à CLI”_: atualizar apenas `Settings`, `_base_opts` (se necessário) e assinatura de `download(...)` + passagem ao `Settings`.
- _“Baixar site X (HLS)”_: garantir headers/cookies opcionais; nunca burlar DRM.
- _“Atualizar UI para shadcn/ui”_: preferir `Button`, `Card`, `Input`, `Label`, `Select`, `Textarea`, `DropdownMenu`, etc. Manter Tailwind utility-first.

## Restrições
- **Não** remover opções existentes da CLI.
- **Não** forçar `mp4` quando não pedido; preferir `bestvideo+bestaudio/best`.
- **DRM**: sem suporte.

## Comandos úteis
- Python venv: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Baixar exemplo (HLS): `python main.py download "<playlist.m3u8>" --referer ... --origin ... --cookies-file ./cookies.txt --path "Curso/Módulo" --file-name "Aula 01" --archive-id "Aula 01" --concurrent-fragments 10`
- UI: `cd yt-archiver-ui && npm i && npm run dev`
