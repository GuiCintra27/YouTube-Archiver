# Backend API - YT-Archiver

API REST para download e gerenciamento de vídeos do YouTube com integração ao Google Drive.

**Framework:** FastAPI + Uvicorn
**Porta:** 8000
**Documentação Interativa:** http://localhost:8000/docs

---

## 🚀 Como Rodar

### Opção 1: Script automático (✅ Recomendado)
```bash
./run.sh
```
Ativa o ambiente virtual automaticamente e inicia o servidor.

### Opção 2: Manual
```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Opção 3: Com reload automático (desenvolvimento)
```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📡 Endpoints Principais

### 🏥 Health Check
- **GET** `/` - Status da API

### 📥 Download e Jobs
- **POST** `/api/download` - Inicia download de vídeo/playlist
- **GET** `/api/jobs/{job_id}` - Obtém status e progresso de um job
- **GET** `/api/jobs` - Lista todos os jobs (histórico)
- **POST** `/api/jobs/{job_id}/cancel` - Cancela job em andamento
- **DELETE** `/api/jobs/{job_id}` - Remove job do histórico
- **POST** `/api/video-info` - Obtém metadados sem baixar

### 📚 Biblioteca Local
- **GET** `/api/videos` - Lista vídeos baixados localmente
- **GET** `/api/videos/stream/{video_path}` - Stream de vídeo (range requests)
- **GET** `/api/videos/thumbnail/{thumbnail_path}` - Serve thumbnail
- **DELETE** `/api/videos/{video_path}` - Exclui vídeo e arquivos relacionados

**Nota:** downloads sempre usam o diretório padrão configurado em `DOWNLOADS_DIR` (default `./downloads`).

### 📦 Catálogo (SQLite)
- **GET** `/api/catalog/status` - Status do catálogo (local/drive)
- **POST** `/api/catalog/bootstrap-local` - Indexa vídeos locais
- **POST** `/api/catalog/drive/import` - Importa snapshot do Drive
- **POST** `/api/catalog/drive/publish` - Publica snapshot do Drive
- **POST** `/api/catalog/drive/rebuild` - Reconstrói catálogo lendo o Drive

### ☁️ Google Drive
- **GET** `/api/drive/auth-status` - Verifica autenticação
- **GET** `/api/drive/auth-url` - Gera URL OAuth
- **GET** `/api/drive/oauth2callback` - Callback OAuth (troca código por token)
- **GET** `/api/drive/videos` - Lista vídeos no Drive
- **POST** `/api/drive/upload/{video_path}` - Upload de vídeo individual
- **POST** `/api/drive/sync-all` - Sincroniza todos os vídeos locais
- **GET** `/api/drive/sync-status` - Status de sincronização (local vs Drive)
- **GET** `/api/drive/sync-items` - Itens paginados (local_only/drive_only/synced)
- **GET** `/api/drive/stream/{file_id}` - Stream de vídeo do Drive
- **GET** `/api/drive/thumbnail/{file_id}` - Thumbnail do Drive
- **DELETE** `/api/drive/videos/{file_id}` - Remove vídeo do Drive (vídeo + arquivos relacionados)
- **POST** `/api/drive/videos/delete-batch` - Exclui múltiplos vídeos em lote
- **POST** `/api/drive/download` - Download de vídeo do Drive (por path ou file_id)
- **POST** `/api/drive/download-all` - Download em lote (Drive -> local)

**Notas do delete (Drive):**
- A exclusão remove o vídeo e arquivos relacionados (thumb, legendas, metadata).
- A limpeza de pastas vazias ocorre em background e retorna `cleanup_job_id`.

**Documentação completa:** http://localhost:8000/docs

---

## 📁 Estrutura de Arquivos

```
backend/
├── app/                    # ⭐ Pacote principal
│   ├── main.py             # Entry point FastAPI
│   ├── config.py           # Settings globais
│   ├── core/               # Utilitários (logging, blocking, errors)
│   ├── catalog/            # Catálogo SQLite (local + drive)
│   ├── downloads/          # Downloads (yt-dlp)
│   ├── jobs/               # Jobs assíncronos (in-memory)
│   ├── library/            # Biblioteca local
│   ├── recordings/         # Upload de gravações
│   └── drive/              # Drive (router/service/manager/cache)
├── requirements.txt        # Dependências Python
├── run.sh                  # Script de inicialização
├── .venv/                  # Ambiente virtual (gitignored)
├── downloads/              # Vídeos baixados (gitignored)
├── archive.txt             # Controle de duplicatas
├── credentials.json        # OAuth Google (gitignored)
├── token.json              # Token OAuth (gitignored)
├── database.db             # Catálogo SQLite (gitignored)
└── drive_cache.db          # Cache SQLite do Drive (opcional)
```

---

## 🔐 Configuração do Google Drive

### Pré-requisitos
1. Criar projeto no Google Cloud Console
2. Ativar Google Drive API
3. Criar credenciais OAuth 2.0 (Desktop app)
4. Baixar JSON → salvar como `credentials.json`

**Guia completo:** Ver `../GOOGLE-DRIVE-SETUP.md`

### Primeiro Uso
1. Colocar `credentials.json` na pasta `backend/`
2. Iniciar backend: `./run.sh`
3. Acessar frontend: http://localhost:3000/drive
4. Clicar em "Conectar com Google Drive"
5. Autorizar no navegador
6. `token.json` será criado automaticamente

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'fastapi'"

**Causa:** Executou o backend sem ativar o venv ou fora do script `./run.sh`.

**Solução:** Use `./run.sh` ou ative o venv antes:
```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Erro: "address already in use" (porta 8000)

**Causa:** Backend já está rodando ou processo travado.

**Solução:** Matar processos na porta 8000:
```bash
lsof -ti:8000 | xargs kill -9
./run.sh
```

### Erro: "You must pass the application as an import string to enable 'reload'"

**Causa:** Usou `reload=True` sem passar o app como import string.

**Solução:** Use uvicorn como módulo:
```bash
uvicorn app.main:app --reload
```

### Erro: "FileNotFoundError: credentials.json"

**Causa:** Tentou usar funcionalidades do Drive sem configurar OAuth.

**Solução:**
1. Ver guia completo: `../GOOGLE-DRIVE-SETUP.md`
2. Obter `credentials.json` do Google Cloud Console
3. Colocar em `backend/credentials.json`

### Erro 500 ao fazer streaming de vídeos locais

**Status:** ✅ CORRIGIDO (ver `../BUGS.md`)

**Causa anterior:** UnicodeEncodeError com caracteres especiais (⧸, acentos, etc.)

**Solução aplicada:** RFC 5987 encoding em headers HTTP

### Erro 500 ao fazer upload para Google Drive

**Status:** ✅ CORRIGIDO (ver `../BUGS.md`)

**Causa anterior:** Aspas simples não escapadas em queries do Drive API

**Solução aplicada:** Escape de aspas simples (`name.replace("'", "\\'")`)

---

## 🔧 Tecnologias

- **FastAPI** - Framework web assíncrono
- **yt-dlp** - Motor de download de vídeos
- **Uvicorn** - Servidor ASGI
- **Pydantic** - Validação de dados
- **Google API Client** - Integração com Google Drive
- **SQLite** - Catálogo persistente (local + drive)
- **Python 3.12+** - Runtime

---

## 📝 Notas Técnicas

### Sistema de Jobs Assíncronos
- Jobs rodando em threads separadas
- Progresso reportado via callbacks
- Estado armazenado em memória (limpar com DELETE)

### Concorrência (ASGI)
- Operações bloqueantes (Drive/FS/SQLite) são movidas para threads via `core/blocking.py`.
- Limites configuráveis: `BLOCKING_DRIVE_CONCURRENCY`, `BLOCKING_FS_CONCURRENCY`, `BLOCKING_CATALOG_CONCURRENCY`.
- Para múltiplos workers em produção, migre o storage de jobs para Redis/DB.

### Streaming de Vídeos
- Suporte a range requests (HTTP 206 Partial Content)
- Chunks de 8KB para streaming eficiente
- MIME type detectado automaticamente (.mp4, .webm, .mkv, etc.)

### Catálogo (SQLite)
- Mantém índice local e do Drive para listagens rápidas.
- Primeira execução: use `POST /api/catalog/drive/rebuild` (Drive já populado) ou `POST /api/catalog/drive/import` (snapshot existente).
- Para indexar vídeos locais existentes: `POST /api/catalog/bootstrap-local`.

### Google Drive API
- OAuth 2.0 flow completo
- Escopo: `https://www.googleapis.com/auth/drive.file`
- Pasta raiz: "YouTube Archiver" (criada automaticamente)
- Upload preserva estrutura de pastas local
- Arquivos relacionados (thumbnails, legendas, metadata) enviados junto

### Controle de Duplicatas
- Arquivo `archive.txt` registra vídeos baixados
- Formato: `youtube VIDEO_ID` ou `custom CUSTOM_ID`
- Remoção automática ao excluir vídeo via API

---

## 📚 Recursos

- [Documentação FastAPI](https://fastapi.tiangolo.com/)
- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [Google Drive API Docs](https://developers.google.com/drive/api/guides/about-sdk)
- [Documentação Principal do Projeto](../README.md)
- [Bug Tracking](../BUGS.md)

---

**Última atualização:** 2025-10-08
**Status:** ✅ Todos os endpoints funcionando corretamente
