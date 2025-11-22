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
python api.py
```

### Opção 3: Com reload automático (desenvolvimento)
```bash
source .venv/bin/activate
uvicorn api:app --reload --host 0.0.0.0 --port 8000
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

### ☁️ Google Drive
- **GET** `/api/drive/auth-status` - Verifica autenticação
- **GET** `/api/drive/auth-url` - Gera URL OAuth
- **GET** `/api/drive/oauth2callback` - Callback OAuth (troca código por token)
- **GET** `/api/drive/videos` - Lista vídeos no Drive
- **POST** `/api/drive/upload/{video_path}` - Upload de vídeo individual
- **POST** `/api/drive/sync-all` - Sincroniza todos os vídeos locais
- **GET** `/api/drive/sync-status` - Status de sincronização (local vs Drive)
- **GET** `/api/drive/stream/{file_id}` - Stream de vídeo do Drive
- **GET** `/api/drive/thumbnail/{file_id}` - Thumbnail do Drive
- **DELETE** `/api/drive/videos/{file_id}` - Remove vídeo do Drive

**Documentação completa:** http://localhost:8000/docs

---

## 📁 Estrutura de Arquivos

```
backend/
├── api.py                  # ⭐ Endpoints principais
├── downloader.py           # ⭐ Wrapper do yt-dlp
├── drive_manager.py        # ⭐ Google Drive integration
├── requirements.txt        # Dependências Python
├── run.sh                  # Script de inicialização
├── .venv/                  # Ambiente virtual (gitignored)
├── downloads/              # Vídeos baixados (gitignored)
├── archive.txt             # Controle de duplicatas
├── credentials.json        # OAuth Google (gitignored)
└── token.json              # Token OAuth (gitignored)
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

**Causa:** Executou `python api.py` sem ativar o venv.

**Solução:** Use `./run.sh` ou ative o venv antes:
```bash
source .venv/bin/activate
python api.py
```

### Erro: "address already in use" (porta 8000)

**Causa:** Backend já está rodando ou processo travado.

**Solução:** Matar processos na porta 8000:
```bash
lsof -ti:8000 | xargs kill -9
./run.sh
```

### Erro: "You must pass the application as an import string to enable 'reload'"

**Causa:** Usou `reload=True` ao executar diretamente com `python api.py`.

**Solução:** Use uvicorn como módulo:
```bash
uvicorn api:app --reload
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
- **Python 3.12+** - Runtime

---

## 📝 Notas Técnicas

### Sistema de Jobs Assíncronos
- Jobs rodando em threads separadas
- Progresso reportado via callbacks
- Estado armazenado em memória (limpar com DELETE)

### Streaming de Vídeos
- Suporte a range requests (HTTP 206 Partial Content)
- Chunks de 8KB para streaming eficiente
- MIME type detectado automaticamente (.mp4, .webm, .mkv, etc.)

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
