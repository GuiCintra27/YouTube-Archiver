# CLAUDE.md — YT-Archiver

## 🎯 Contexto do Projeto

Sistema completo de download e arquivamento de vídeos do YouTube com interface web moderna e integração com Google Drive.

**Versão atual:** v2.4
**Stack:** FastAPI (backend) + Next.js 15 (frontend) + yt-dlp (download engine) + SQLite (cache)

### Objetivo Principal
Baixar vídeos do YouTube (canais, playlists, vídeos individuais) e streams HLS sem DRM, com:
- Interface web intuitiva para configuração e monitoramento
- Sistema de jobs assíncronos com progresso em tempo real
- Biblioteca local de vídeos com player integrado
- Sincronização bidirecional com Google Drive
- Controle granular de qualidade, formato e opções anti-ban

---

## 🏗️ Arquitetura Atual

### Backend (`backend/`)
**Framework:** FastAPI + Uvicorn
**Porta:** 8000
**Arquitetura:** Modular (similar ao NestJS)

O backend segue uma arquitetura modular com separação clara de responsabilidades:

```
backend/app/
├── main.py              # Entry point FastAPI (inclui routers)
├── config.py            # Configurações globais (pydantic-settings)
├── core/                # Módulo central compartilhado
│   ├── logging.py       # Sistema de logging estruturado
│   ├── validators.py    # Validação de URLs, paths, filenames
│   ├── errors.py        # Respostas de erro padronizadas (ErrorCode, AppException)
│   ├── rate_limit.py    # Rate limiting com slowapi
│   ├── constants.py     # Constantes centralizadas (MIME types, extensions)
│   ├── types.py         # Type hints e TypedDicts
│   ├── exceptions.py    # Exceções HTTP customizadas (legacy)
│   └── security.py      # Validações de path, sanitização (legacy)
├── downloads/           # Módulo de downloads
│   ├── router.py        # Endpoints /api/download, /api/video-info
│   ├── service.py       # Lógica de negócio
│   ├── schemas.py       # Modelos Pydantic (DownloadRequest, etc.)
│   └── downloader.py    # Engine yt-dlp wrapper
├── jobs/                # Módulo de jobs assíncronos
│   ├── router.py        # Endpoints /api/jobs/*
│   ├── service.py       # Gerenciamento de jobs
│   ├── schemas.py       # Modelos Pydantic
│   ├── store.py         # Storage in-memory
│   └── cleanup.py       # Limpeza automática de jobs antigos
├── library/             # Módulo de biblioteca local
│   ├── router.py        # Endpoints /api/videos/*
│   ├── service.py       # Scan, streaming, exclusão
│   ├── schemas.py       # Modelos Pydantic
│   └── cache.py         # Cache de scan de diretórios (TTL 30s)
├── recordings/          # Módulo de gravações de tela
│   ├── router.py        # Endpoint /api/recordings/upload
│   └── service.py       # Salvamento de gravações
└── drive/               # Módulo Google Drive
    ├── router.py        # Endpoints /api/drive/*
    ├── service.py       # Lógica de negócio
    ├── schemas.py       # Modelos Pydantic
    ├── manager.py       # DriveManager (OAuth, upload, sync)
    └── cache/           # Cache SQLite para metadados
        ├── __init__.py  # Exports do módulo
        ├── database.py  # Schema SQLite, conexão, WAL mode
        ├── repository.py # CRUD operations
        ├── sync.py      # Full/incremental sync
        └── background.py # Task de sync periódico
```

**Padrão de cada módulo:**
- **router.py**: Define endpoints da API (APIRouter)
- **service.py**: Contém lógica de negócio
- **schemas.py**: Modelos Pydantic para request/response
- **Arquivos específicos**: downloader.py, manager.py, store.py

**Dependências principais:**
- `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`
- `yt-dlp` (download engine)
- `google-api-python-client`, `google-auth-oauthlib` (Drive API)
- `aiosqlite` (cache SQLite async)
- `slowapi` (rate limiting)
- `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` (testes)

### Frontend (`frontend/`)
**Framework:** Next.js 15 (App Router) + TypeScript
**Porta:** 3000
**UI Library:** shadcn/ui (Radix UI primitives) + Tailwind CSS
**Linter:** ESLint 9 (flat config)

**Estrutura:**
```
src/
├── app/
│   ├── page.tsx                 # Página principal (downloads)
│   ├── drive/page.tsx           # Página Google Drive
│   ├── library/page.tsx         # Biblioteca de vídeos
│   ├── record/page.tsx          # Gravação de tela
│   ├── layout.tsx               # Layout global
│   └── globals.css
├── components/
│   ├── common/                  # Componentes compartilhados
│   │   ├── error-boundary.tsx   # Error Boundary com retry
│   │   ├── navigation.tsx       # Navegação
│   │   ├── theme-provider.tsx   # Tema dark/light
│   │   ├── pagination.tsx       # Controles de paginação
│   │   └── videos/              # Componentes de vídeo
│   ├── drive/                   # Componentes Google Drive
│   │   ├── drive-auth.tsx
│   │   ├── drive-video-grid.tsx
│   │   ├── drive-video-player.tsx
│   │   └── sync-panel.tsx
│   ├── home/                    # Componentes da Home
│   │   └── download-form.tsx
│   ├── library/                 # Componentes da Biblioteca
│   │   └── paginated-video-grid.tsx
│   ├── record/                  # Gravação de tela
│   │   └── screen-recorder.tsx
│   └── ui/                      # shadcn/ui components
├── hooks/                       # Hooks customizados
│   ├── index.ts                 # Barrel export
│   ├── use-api-url.ts           # URL da API (SSR-safe)
│   └── use-fetch.ts             # Fetch com AbortController
└── lib/
    ├── api-config.ts            # Configuração centralizada da API
    ├── api-client.ts            # Cliente HTTP tipado
    ├── api-urls.ts              # Constantes de endpoints
    ├── url-validator.ts         # Validação de URLs
    └── utils.ts                 # Utilitários (cn, formatBytes)
```

**Arquivos de Configuração:**
- `eslint.config.mjs` - ESLint flat config (ESLint 9)
- `next.config.ts` - Configuração Next.js
- `tailwind.config.ts` - Configuração Tailwind
- `tsconfig.json` - TypeScript config

**Player de vídeo:** Plyr (HTML5 video player)

---

## 🔧 Funcionalidades Implementadas e Testadas

### ✅ Download e Biblioteca Local
- [x] Download de vídeos individuais do YouTube
- [x] Download de playlists completas
- [x] Sistema de jobs assíncronos com polling de progresso
- [x] Biblioteca de vídeos com thumbnails
- [x] Streaming de vídeos locais com range requests (HTTP 206)
- [x] Player de vídeo integrado (Plyr)
- [x] Exclusão de vídeos com limpeza de arquivos relacionados
- [x] Sistema de arquivamento (evita duplicatas)

### ✅ Google Drive Integration
- [x] Autenticação OAuth 2.0 completa
- [x] Listagem de vídeos no Drive
- [x] Upload individual de vídeos
- [x] Upload em lote (sincronização completa)
- [x] Streaming direto do Drive com range requests
- [x] Player de vídeos do Drive
- [x] Painel de sincronização (mostra diferenças local vs Drive)
- [x] Exclusão de vídeos do Drive
- [x] Upload de arquivos relacionados (thumbnails, metadata, legendas)
- [x] Preservação de estrutura de pastas
- [x] **Cache SQLite** para listagem ultrarrápida (~20-50x mais rápido)
- [x] Sync automático a cada 30 minutos
- [x] Sync real-time após upload/delete/rename

### ✅ Opções Avançadas
- [x] Headers customizados (Referer, Origin)
- [x] Suporte a cookies (formato Netscape)
- [x] Rate limiting configurável (anti-ban)
- [x] Nomenclatura customizada de arquivos e pastas
- [x] Controle de qualidade/resolução
- [x] Extração de áudio (MP3)
- [x] Download de legendas e miniaturas

### ✅ Global Player (Background Playback)
- [x] Mini barra de controle fixa no rodapé
- [x] Picture-in-Picture nativo do navegador (Vidstack)
- [x] Controle de volume (mute + slider)
- [x] Persistência entre páginas (player no layout.tsx)
- [x] Transferência de tempo de reprodução ao minimizar
- [x] **Documentação:** `docs/local/GLOBAL-PLAYER-FEATURE.md`

---

## 🐛 Bugs Corrigidos (Histórico)

### BUG #1: Streaming de Vídeos Locais - CORRIGIDO ✅
**Problema:** UnicodeEncodeError ao reproduzir vídeos com caracteres especiais (ex: ⧸ U+29F8)
**Causa:** Header `Content-Disposition` usando encoding latin-1 (padrão HTTP)
**Solução:** Implementado RFC 5987 encoding (`filename*=UTF-8''...`)
**Arquivo:** `backend/app/library/router.py` (função `stream_video()`)

### BUG #2: Upload para Google Drive - CORRIGIDO ✅
**Problema:** Query malformada com aspas simples não escapadas (ex: "60's")
**Causa:** Queries do Drive usam aspas simples como delimitadores
**Solução:** Escape de aspas (`name.replace("'", "\\'")`) em queries
**Arquivo:** `backend/app/drive/manager.py` (métodos `upload_video()` e `ensure_folder()`)

**Referência completa:** Ver `BUGS.md` para detalhes técnicos e testes de validação

---

## 📝 Convenções de Código

### Python (Backend)
- **Estilo:** PEP8 onde aplicável, priorizar estabilidade sobre refatoração agressiva
- **Tipagem:** Completa, usando TypedDicts em `app/core/types.py`
- **Async:** Usar threading para jobs de download (não async/await para yt-dlp)
- **Logging:** Sistema estruturado em `app/core/logging.py`:
  ```python
  from app.core.logging import get_module_logger
  logger = get_module_logger("meu_modulo")
  logger.debug("Debug message")
  logger.info("Info message")
  logger.error("Error message", exc_info=True)
  ```
- **Tratamento de erros:** Usar `app/core/errors.py`:
  ```python
  from app.core.errors import raise_error, ErrorCode
  raise_error(404, ErrorCode.VIDEO_NOT_FOUND, "Video not found")
  ```
- **Configuração:** Via variáveis de ambiente com `pydantic-settings` (ver `.env.example`)

### TypeScript/React (Frontend)
- **Componentes:** Função como default export
- **Hooks:** Preferir hooks modernos (useState, useEffect, useCallback, useMemo)
- **URL da API:** Usar `useApiUrl()` hook de `@/hooks/use-api-url` (SSR-safe)
- **Fetch:** Usar `useFetch()` ou fetch nativo com AbortController
- **Estilo:** Tailwind utility-first + shadcn/ui components
- **Estado:** useState para estado local, sem Redux/Zustand
- **Tipos:** Type safety rigoroso, evitar `any`
- **Linting:** ESLint 9 flat config (`eslint.config.mjs`)

### Naming Conventions
- **Python:** `snake_case` para funções/variáveis, `PascalCase` para classes
- **TypeScript:** `camelCase` para funções/variáveis, `PascalCase` para componentes/tipos
- **Arquivos:** `kebab-case.tsx` para componentes, `kebab-case.py` para módulos

---

## ⚙️ Comandos Úteis

### Desenvolvimento Completo
```bash
./start-dev.sh  # Linux/Mac - Inicia backend + frontend
start-dev.bat   # Windows - Inicia backend + frontend
```

### Backend (API FastAPI)
```bash
cd backend
./run.sh                              # Recomendado (ativa venv + uvicorn com reload)
# OU manualmente:
source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**URLs do Backend:**
- API: http://localhost:8000
- Documentação interativa: http://localhost:8000/docs
- Health check: http://localhost:8000/

### Frontend (Next.js)
```bash
cd frontend
npm install          # Primeira vez
npm run dev          # Desenvolvimento (porta 3000)
npm run build        # Build de produção
npm start            # Servir build de produção
```

**URL do Frontend:** http://localhost:3000

### Testes do Backend (pytest)
```bash
cd backend
source .venv/bin/activate

# Rodar todos os testes
pytest tests/ -v

# Rodar com cobertura
pytest tests/ --cov=app --cov-report=html

# Rodar apenas um arquivo de teste
pytest tests/test_validators.py -v

# Rodar teste específico
pytest tests/test_library.py::TestListVideos::test_list_videos_empty_directory -v
```

**Testes disponíveis (46 testes):**
- `test_cache.py` - Cache de diretórios (7 testes)
- `test_health.py` - Health check (2 testes)
- `test_jobs.py` - Jobs e cancelamento (8 testes)
- `test_library.py` - Vídeos, streaming, exclusão (13 testes)
- `test_validators.py` - Validação de URLs e paths (16 testes)

### Reiniciar Backend em Caso de Mudanças
```bash
# Matar processos na porta 8000
lsof -ti:8000 | xargs kill -9

# Reiniciar
cd backend && ./run.sh
```

### Git e Commits (Commitizen)
```bash
# Setup inicial (primeira vez na raiz do projeto)
npm install

# Fazer commits usando Commitizen
npm run commit       # Opção 1 (recomendado)
npx cz              # Opção 2
git cz              # Opção 3 (se instalado globalmente)

# O wizard interativo irá guiar a criação de commits padronizados
# seguindo a convenção Conventional Commits (feat, fix, docs, etc.)
```

**IMPORTANTE:** O Commitizen requer `node_modules` instalado na raiz. Se não funcionar, rode `npm install` primeiro.

---

## 🚨 Gotchas Importantes

### Backend
1. **SEMPRE use `./run.sh`** para iniciar o backend
   - ❌ NÃO: `python app/main.py` (não ativa o venv, sem reload)
   - ✅ SIM: `./run.sh` (ativa venv + uvicorn com hot reload)

2. **Hot reload do uvicorn**
   - `./run.sh` já inclui `--reload` automaticamente
   - Mudanças em arquivos `.py` são detectadas e recarregadas
   - Comando usado: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

3. **Encoding de Caracteres Especiais**
   - Sempre usar RFC 5987 para headers HTTP com Unicode
   - Formato: `filename*=UTF-8''{quote(filename)}`
   - Importar `quote` de `urllib.parse`

4. **Google Drive API Queries**
   - SEMPRE escapar aspas simples: `name.replace("'", "\\'")`
   - Queries usam aspas simples como delimitadores
   - Aplicar em: verificação de arquivos, pastas e uploads

5. **Range Requests**
   - Player de vídeo requer suporte a HTTP 206 Partial Content
   - Implementado tanto para streaming local quanto Drive
   - Usar `StreamingResponse` com chunks de 8KB

### Frontend
1. **Next.js 15 App Router**
   - Usar `"use client"` para componentes interativos
   - Server Components por padrão
   - `suppressHydrationWarning` necessário para temas dinâmicos

2. **URL da API (SSR-safe)**
   - Usar `useApiUrl()` hook de `@/hooks/use-api-url`
   - Retorna string vazia no servidor, URL real no cliente
   - Evita erros de hidratação

3. **Plyr CSS**
   - Importar em `layout.tsx`: `import "plyr-react/plyr.css"`
   - Necessário para estilos corretos do player

4. **API Calls**
   - Backend em `http://localhost:8000`
   - Usar paths absolutos: `/api/videos` não `api/videos`
   - Polling de jobs com cleanup (pollingCleanupRef)

5. **ESLint**
   - Flat config em `eslint.config.mjs` (ESLint 9)
   - Comando: `npm run lint` (usa ESLint CLI diretamente)
   - Warnings de `any` são aceitáveis para refs do Plyr

6. **shadcn/ui**
   - Componentes instalados sob demanda em `components/ui/`
   - Usar Radix UI primitives via shadcn CLI
   - Não modificar arquivos em `components/ui/` diretamente

---

## 📂 Arquivos e Pastas Importantes

### Backend
```
backend/
├── app/                        # ⭐ Pacote principal da aplicação
│   ├── main.py                 # ⭐ Entry point FastAPI
│   ├── config.py               # ⭐ Configurações (pydantic-settings)
│   ├── core/                   # ⭐ Módulo central
│   │   ├── logging.py          # Sistema de logging estruturado
│   │   ├── validators.py       # Validação de URLs, paths, filenames
│   │   ├── errors.py           # ⭐ ErrorCode, AppException, raise_error()
│   │   ├── rate_limit.py       # Rate limiting com slowapi
│   │   ├── constants.py        # Constantes (MIME types, extensions)
│   │   ├── types.py            # TypedDicts e type aliases
│   │   ├── exceptions.py       # Exceções HTTP (legacy)
│   │   └── security.py         # Validações e sanitização (legacy)
│   ├── downloads/              # Módulo de downloads
│   │   ├── router.py           # Endpoints /api/download, /api/video-info
│   │   ├── service.py          # Lógica de negócio
│   │   ├── schemas.py          # ⭐ DownloadRequest e outros modelos
│   │   └── downloader.py       # ⭐ Engine yt-dlp wrapper
│   ├── jobs/                   # Módulo de jobs
│   │   ├── router.py           # Endpoints /api/jobs/*
│   │   ├── service.py          # Gerenciamento de jobs
│   │   ├── schemas.py          # Modelos de jobs
│   │   ├── store.py            # Storage in-memory
│   │   └── cleanup.py          # ⭐ Limpeza automática de jobs
│   ├── library/                # Módulo de biblioteca local
│   │   ├── router.py           # ⭐ Endpoints /api/videos/* (streaming)
│   │   ├── service.py          # Scan de diretórios
│   │   ├── schemas.py          # Modelos de vídeos
│   │   └── cache.py            # ⭐ Cache de scan (TTL 30s)
│   ├── recordings/             # Módulo de gravações
│   │   ├── router.py           # Endpoint /api/recordings/upload
│   │   └── service.py          # Salvamento de gravações
│   └── drive/                  # Módulo Google Drive
│       ├── router.py           # Endpoints /api/drive/*
│       ├── service.py          # Lógica de negócio
│       ├── schemas.py          # Modelos do Drive
│       └── manager.py          # ⭐ DriveManager (OAuth, upload, sync)
├── tests/                      # ⭐ Testes automatizados (pytest)
│   ├── conftest.py             # Fixtures compartilhadas
│   ├── test_cache.py           # Testes do cache
│   ├── test_health.py          # Testes do health check
│   ├── test_jobs.py            # Testes de jobs
│   ├── test_library.py         # Testes da biblioteca
│   └── test_validators.py      # Testes de validação
├── requirements.txt            # Dependências Python
├── pytest.ini                  # Configuração do pytest
├── .env.example                # ⭐ Exemplo de variáveis de ambiente
├── run.sh                      # Script de inicialização
├── .venv/                      # Ambiente virtual (gitignored)
├── downloads/                  # Vídeos baixados (gitignored)
├── archive.txt                 # Controle de duplicatas
├── credentials.json            # OAuth Google (gitignored)
├── token.json                  # Token OAuth (gitignored)
└── docs/project/               # Documentações específicas
    ├── ANTI-BAN.md
    ├── EXPORT-COOKIES-GUIDE.md
    └── PERFORMANCE-OPTIMIZATION.md
```

### Frontend
```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx                  # ⭐ Página principal (downloads)
│   │   ├── drive/page.tsx            # ⭐ Página Google Drive
│   │   ├── library/page.tsx          # Biblioteca de vídeos
│   │   ├── record/page.tsx           # Gravação de tela
│   │   ├── layout.tsx                # ⭐ Layout global
│   │   └── globals.css
│   ├── components/
│   │   ├── common/                   # Componentes compartilhados
│   │   │   ├── error-boundary.tsx    # ⭐ Error Boundary
│   │   │   ├── navigation.tsx        # Navegação
│   │   │   ├── theme-provider.tsx    # Tema dark/light
│   │   │   └── videos/               # VideoCard, VideoPlayer
│   │   ├── drive/                    # Componentes Google Drive
│   │   ├── home/                     # Componentes da Home
│   │   │   └── download-form.tsx     # ⭐ Formulário de download
│   │   ├── library/                  # Biblioteca
│   │   │   └── paginated-video-grid.tsx
│   │   └── ui/                       # shadcn/ui components
│   ├── hooks/                        # ⭐ Hooks customizados
│   │   ├── index.ts                  # Barrel export
│   │   ├── use-api-url.ts            # ⭐ URL da API (SSR-safe)
│   │   └── use-fetch.ts              # Fetch com AbortController
│   └── lib/
│       ├── api-config.ts             # ⭐ Configuração da API
│       ├── api-client.ts             # Cliente HTTP tipado
│       ├── api-urls.ts               # Constantes de endpoints
│       ├── url-validator.ts          # Validação de URLs
│       └── utils.ts                  # Helpers (cn, formatBytes)
├── eslint.config.mjs                 # ⭐ ESLint flat config
├── package.json
├── next.config.ts
├── tailwind.config.ts
└── docs/local/                       # Documentações locais
    └── IMPROVEMENTS.md               # Status das melhorias
```

### Documentação
```
├── CLAUDE.md                    # ⭐ Este arquivo (instruções para Claude)
├── README.md                    # ⭐ Documentação principal do projeto
├── CHANGELOG.md                 # Changelog principal
├── start-dev.sh                 # Script de início rápido
└── docs/project/                # Documentações gerais
    ├── BUGS.md                  # ⭐ Bug tracking e correções
    ├── CHANGELOG-v2.2.md
    ├── FEATURES-V2.1.md
    ├── GOOGLE-DRIVE-FEATURES.md # Features do Google Drive
    ├── GOOGLE-DRIVE-SETUP.md    # Guia de configuração OAuth
    ├── MCP-README.md            # Configuração MCP
    ├── QUICK-FIX.md
    ├── QUICK-START.md
    ├── TECHNICAL-REFERENCE.md   # ⭐ Referência técnica rápida
    └── TESTING.md
```

---

## 🔐 Configuração do Google Drive

### Setup Inicial (necessário para usar funcionalidades do Drive)

1. **Criar projeto no Google Cloud Console:**
   - Acessar: https://console.cloud.google.com/
   - Criar novo projeto: "YT Archiver"

2. **Ativar Google Drive API:**
   - Library → "Google Drive API" → Enable

3. **Criar credenciais OAuth 2.0:**
   - Credentials → Create Credentials → OAuth client ID
   - Application type: **Desktop app**
   - Nome: "YT Archiver Desktop"
   - Download JSON → Salvar como `backend/credentials.json`

4. **Configurar OAuth consent screen:**
   - User Type: External
   - Adicionar scope: `https://www.googleapis.com/auth/drive.file`
   - Test users: seu email

5. **Primeiro uso:**
   - Acessar http://localhost:3000/drive
   - Clicar em "Conectar com Google Drive"
   - Autorizar no navegador
   - Token salvo automaticamente em `backend/token.json`

**Guia completo:** Ver `GOOGLE-DRIVE-SETUP.md`

---

## 🎯 Pedidos Típicos e Como Resolver

### "Adicionar uma nova opção ao formulário de download"
1. Adicionar campo no componente `frontend/src/components/download-form.tsx`
2. Adicionar parâmetro no modelo Pydantic em `backend/app/downloads/schemas.py` (classe `DownloadRequest`)
3. Passar parâmetro para `Settings` em `backend/app/downloads/service.py` (função `create_download_settings`)
4. Implementar lógica em `_base_opts()` do `Downloader` em `backend/app/downloads/downloader.py`

### "Corrigir bug de encoding/Unicode"
- Verificar se headers HTTP estão usando RFC 5987 (`filename*=UTF-8''...`)
- Usar `urllib.parse.quote()` para percent-encoding
- Aplicar em `Content-Disposition`, `Content-Type`, etc.

### "Adicionar suporte a nova plataforma além do YouTube"
- yt-dlp suporta 1000+ sites automaticamente
- Basta garantir que `url_validator.ts` aceita a URL
- Testar com cookies se necessário

### "Melhorar performance de streaming"
- Ajustar chunk size em `MediaFileUpload` (padrão: 8MB)
- Verificar range requests estão implementados
- Considerar cache de thumbnails

### "Adicionar novo módulo ao backend"
1. Criar pasta em `backend/app/<nome_modulo>/`
2. Criar arquivos:
   - `__init__.py` (exportar router)
   - `router.py` (APIRouter com endpoints)
   - `service.py` (lógica de negócio)
   - `schemas.py` (modelos Pydantic, se necessário)
3. Registrar router em `backend/app/main.py`:
   ```python
   from app.<nome_modulo>.router import router as nome_router
   app.include_router(nome_router)
   ```

### "Adicionar componente shadcn/ui novo"
```bash
cd frontend
npx shadcn@latest add <component-name>
# Ex: npx shadcn@latest add dialog
```

---

## 🚫 Restrições e Limitações

### DRM
- **NÃO suportar conteúdo protegido por DRM** (Widevine, FairPlay, PlayReady)
- Apenas streams não criptografados (HLS sem DRM, YouTube público)

### Rate Limiting
- **NÃO remover controles de rate limiting** (risco de ban)
- **NÃO encorajar downloads massivos** sem delays
- Manter presets "Seguro", "Moderado", "Rápido"

### Compatibilidade
- **NÃO forçar formato mp4** quando não solicitado
- Preferir `bestvideo+bestaudio/best` (decisão do yt-dlp)
- Respeitar escolha do usuário de qualidade/formato

### Segurança
- **NÃO commitar** `credentials.json`, `token.json`, `cookies.txt`
- **NÃO expor** tokens OAuth em logs
- Usar `.gitignore` corretamente

---

## 🧪 Testing e Debugging

### Testes Automatizados (Backend)
```bash
cd backend && source .venv/bin/activate

# Rodar todos os 68 testes
pytest tests/ -v

# Rodar com cobertura de código
pytest tests/ --cov=app --cov-report=html
```

### Testar Endpoint da API
```bash
# Health check
curl http://localhost:8000/

# Listar vídeos locais
curl http://localhost:8000/api/videos

# Status de autenticação Drive
curl http://localhost:8000/api/drive/auth-status
```

### Logs do Backend
- **Sistema estruturado:** Logs com timestamp, nível, módulo e mensagem
- **Formato:** `2025-11-29 10:30:00 | INFO     | yt-archiver.downloads:start:42 | Download started`
- **Níveis:** DEBUG, INFO, WARNING, ERROR (configurável via `LOG_LEVEL` em `.env`)
- **Localização:** Terminal onde `./run.sh` foi executado

### Logs do Frontend
- Console do navegador (F12)
- Network tab para inspecionar requests
- React DevTools para inspecionar componentes

### Verificar Bugs Conhecidos
```bash
# Ver lista completa de bugs e correções
cat BUGS.md
```

---

## 💡 Boas Práticas

### Ao Modificar Backend
1. ✅ Sempre testar com venv ativado (`./run.sh`)
2. ✅ Adicionar try/except com traceback em endpoints críticos
3. ✅ Validar entrada com Pydantic
4. ✅ Documentar endpoint na docstring (aparece em `/docs`)
5. ✅ Testar com caracteres especiais (acentos, símbolos, emojis)

### Ao Modificar Frontend
1. ✅ Usar componentes shadcn/ui quando disponível
2. ✅ Manter Tailwind utility-first (evitar CSS customizado)
3. ✅ Type safety rigoroso (sem `any`)
4. ✅ Testar responsividade (desktop + mobile)
5. ✅ Acessibilidade (aria-labels, roles, etc.)

### Ao Adicionar Features
1. ✅ Verificar se já existe similar no yt-dlp
2. ✅ Documentar no README.md
3. ✅ Adicionar exemplos de uso
4. ✅ Testar edge cases (URLs inválidas, erros de rede, etc.)
5. ✅ Considerar impacto em Google Drive (sincronização)

---

## 📚 Recursos e Referências

### Documentação Oficial
- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js 15 Docs](https://nextjs.org/docs)
- [shadcn/ui](https://ui.shadcn.com/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Google Drive API](https://developers.google.com/drive/api/guides/about-sdk)

### Arquivos de Documentação do Projeto
- `README.md` - Documentação principal completa
- `GOOGLE-DRIVE-SETUP.md` - Setup detalhado do Google Drive
- `GOOGLE-DRIVE-FEATURES.md` - Features do Drive
- `BUGS.md` - Bug tracking e correções aplicadas

---

## 🎓 Resumo para Claude

**Quando trabalhar neste projeto:**

1. **Arquitetura Backend:** Modular (similar NestJS) em `backend/app/`
   - Cada módulo tem: `router.py`, `service.py`, `schemas.py`
   - Entry point: `app/main.py`
   - Configurações: `app/config.py` (pydantic-settings + `.env`)
2. **Iniciar Backend:** `./run.sh` (nunca `python app/main.py` diretamente)
3. **Testes Backend:** `pytest tests/ -v` (68 testes)
4. **Arquitetura Frontend:** Next.js 15 + shadcn/ui + Tailwind
5. **Unicode/Encoding:** Sempre RFC 5987 para headers, sempre escapar `'` em queries Drive
6. **Bugs conhecidos:** Todos corrigidos (ver BUGS.md para histórico)
7. **Google Drive:** OAuth em `app/drive/manager.py`, streaming funcionando
8. **Drive Cache:** SQLite em `app/drive/cache/` (~20-50x mais rápido que API)
9. **Player:** Plyr com range requests (HTTP 206) funcionando local + Drive
10. **Sistema de jobs:** Em `app/jobs/`, assíncrono com polling + limpeza automática

**Localização dos arquivos principais:**
- Downloads: `app/downloads/` (schemas.py tem DownloadRequest)
- Jobs: `app/jobs/` (store.py tem storage, cleanup.py tem limpeza automática)
- Streaming: `app/library/router.py`
- Cache de scan local: `app/library/cache.py`
- Google Drive: `app/drive/manager.py`
- **Drive Cache SQLite:** `app/drive/cache/` (database.py, repository.py, sync.py, background.py)
- **Logging:** `app/core/logging.py` (usar `get_module_logger()`)
- **Erros:** `app/core/errors.py` (usar `raise_error()`, `ErrorCode`)
- **Validação:** `app/core/validators.py` (URLs, paths, filenames)
- **Rate Limiting:** `app/core/rate_limit.py` (slowapi)
- **Constantes:** `app/core/constants.py` (MIME types, extensions)
- **Types:** `app/core/types.py` (TypedDicts)
- Exceções (legacy): `app/core/exceptions.py`
- Validações (legacy): `app/core/security.py`

**Nunca:**
- Suportar DRM
- Remover rate limiting
- Commitar credenciais
- Quebrar funcionalidades existentes sem justificativa

**Sempre:**
- Testar com caracteres especiais
- Validar entradas com `app/core/validators.py`
- Usar logging estruturado (`get_module_logger()`)
- Usar erros padronizados (`raise_error()`)
- Documentar mudanças
- Preservar estabilidade
- Seguir o padrão modular ao criar novos endpoints
- Rodar testes antes de commitar (`pytest tests/ -v`)

---

**Última atualização:** 2025-12-04
**Status:** ✅ Aplicação 100% funcional, arquitetura modular implementada, cache SQLite para Drive
