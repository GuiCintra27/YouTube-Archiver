# YT-Archiver

Sistema completo para download e arquivamento ético de vídeos e streams HLS (sem DRM), com interface web moderna, integração opcional com Google Drive e funcionalidade de gravação de tela.

## 📋 Visão Geral

O YT-Archiver combina uma API REST robusta com uma interface web moderna para facilitar o download e gerenciamento de vídeos:

- **API REST** (`backend/`): FastAPI com arquitetura modular, sistema de jobs assíncronos e integração com Google Drive
- **Interface Web** (`frontend/`): Next.js 15 + shadcn/ui para uma experiência visual intuitiva
- **SSR + Cache nativo**: Server Components com revalidate e invalidação por tags via Route Handlers
- **Motor de Download**: yt-dlp para downloads de YouTube, playlists e streams HLS

### Principais Funcionalidades

- ✅ Download de vídeos do YouTube (canais, playlists, vídeos individuais) e plataformas de vídeos em geral (para alguns casos será necessária a utilização de cookies)
- ✅ Suporte a streams HLS (M3U8) sem DRM
- ✅ Headers customizados (Referer, Origin, User-Agent)
- ✅ Cookies personalizados via arquivo Netscape
- ✅ **Biblioteca de vídeos local** - Visualize, reproduza e gerencie vídeos baixados
- ✅ **Gravação de tela no navegador** - Salve gravações diretamente na biblioteca
- ✅ **Sincronização com Google Drive** - Upload, visualização e streaming de vídeos no Drive
- ✅ **Upload externo para o Drive** - Envie qualquer vídeo com thumbnail, legendas e transcrição
- ✅ **Compartilhamento no Drive** - Gere link público para visualizar vídeos
- ✅ **Catálogo persistente (SQLite)** - Índice local + snapshot no Drive para listagem rápida
- ✅ **Sistema de jobs assíncronos** - Downloads em background com progresso em tempo real
- ✅ Sistema de arquivamento para evitar downloads duplicados
- ✅ Controle de qualidade e formato de saída
- ✅ Rate limiting configurável (anti-ban para playlists grandes)
- ✅ Extração de áudio (MP3)
- ✅ Download de legendas, miniaturas e metadados
- ✅ Nomes de arquivo e caminhos customizados
- ✅ **Global Player com PiP** - Reproduza vídeos em background enquanto navega
- ✅ **SSR e cache inteligente** - Renderização inicial com dados e invalidação por tags
- ✅ **Observabilidade local** - Prometheus + Grafana com dashboards prontos
- ✅ API REST completa para integração

---

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.12+
- Node.js 18+ e npm
- ffmpeg instalado no sistema

### Instalação e Execução

#### Opção 1: Script Automático (Recomendado)

```bash
# Linux/Mac
./start-dev.sh

# Windows
start-dev.bat
```

Isso irá:

1. Verificar se `ffmpeg` está instalado (não instala automaticamente)
2. Configurar e ativar o ambiente virtual do backend
3. Instalar dependências Python
4. Instalar dependências do frontend (se `node_modules` não existir)
5. Iniciar o backend na porta 8000
6. Iniciar o frontend na porta 3000

Para iniciar API + worker no dev:

```bash
START_WORKER=true WORKER_PORT=8001 ./start-dev.sh
```

**Acesse:** http://localhost:3000

#### Opção 2: Manual

Primeiramente, **instale o ffmpeg na sua máquina**.

**Backend:**

```bash
cd backend
./run.sh  # Ou: source .venv/bin/activate && uvicorn app.main:app --reload
```

**API + worker (prod ou dev):**

```bash
# API sem tasks de background
WORKER_ROLE=api ./run.sh

# Worker com tasks de background
WORKER_ROLE=worker PORT=8001 ./run.sh
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Acesse:**

- Interface Web: http://localhost:3000
- API: http://localhost:8000
- Documentação da API: http://localhost:8000/docs

---

## Documentacao

- Index geral: **[INDEX.md](./docs/project/INDEX.md)**
- Arquitetura: **[ARCHITECTURE.md](./docs/project/ARCHITECTURE.md)**
- Observabilidade (Prometheus + Grafana): **[OBSERVABILITY.md](./docs/project/OBSERVABILITY.md)**
- Guia rapido: **[QUICK-START.md](./docs/project/QUICK-START.md)**
- Referencia tecnica: **[TECHNICAL-REFERENCE.md](./docs/project/TECHNICAL-REFERENCE.md)**
- Setup do Google Drive: **[GOOGLE-DRIVE-SETUP.md](./docs/project/GOOGLE-DRIVE-SETUP.md)**
- Recursos do Google Drive: **[GOOGLE-DRIVE-FEATURES.md](./docs/project/GOOGLE-DRIVE-FEATURES.md)**
- Global Player: **[GLOBAL-PLAYER.md](./docs/project/GLOBAL-PLAYER.md)**

---

## 🌐 Interface Web

### Funcionalidades da UI

**Página Principal (`/`):**

- 📥 Formulário de download com todas as opções configuráveis
- 📊 Barra de progresso em tempo real durante downloads
- 📚 Biblioteca de vídeos locais com thumbnails e duração
- ▶️ Player de vídeo integrado (Vidstack)
- 🗑️ Exclusão individual ou em lote de vídeos
- ℹ️ Modal de informações detalhadas do vídeo
- ⚙️ Opções avançadas: headers, cookies, rate limiting, nomenclatura customizada
- ⚡ SSR + cache para vídeos recentes

**Página Google Drive (`/drive`):**

- ☁️ Autenticação OAuth2 com Google Drive
- 📂 Visualização de vídeos sincronizados no Drive com thumbnails
- ⬆️ Upload individual ou em lote de vídeos locais
- 🧩 Upload externo (vídeo + thumbnail + legendas + transcrição)
- ⬇️ Download de vídeos do Drive para armazenamento local
- 🔄 Painel de sincronização mostrando diferenças entre local e Drive
- ▶️ Streaming direto do Google Drive com suporte a seek/skip
- 🗑️ Exclusão individual ou em lote de vídeos do Drive
- 🔗 Compartilhamento público com link (ativar/desativar por vídeo)
- ℹ️ Modal de informações detalhadas do vídeo
- ⚡ SSR + cache com invalidação por tags

**Página Gravar (`/record`):**

- 🎥 Gravação de tela com áudio do sistema e microfone
- 💾 Download local ou salvar direto na biblioteca
- 🧭 Lista de gravações recentes com refresh automático

**Global Player (Background Playback):**

- 🎵 Minimize vídeos para reproduzir em background
- 🖼️ Picture-in-Picture nativo do navegador
- 🔊 Controle de volume na mini barra
- 🔄 Continua tocando ao navegar entre páginas
- 📖 Documentação completa: **[GLOBAL-PLAYER.md](./docs/project/GLOBAL-PLAYER.md)**

**Recursos da Interface:**

- ✨ Design moderno e responsivo (Next.js 15 + Tailwind CSS)
- 🎨 Componentes shadcn/ui (Radix UI primitives)
- 📱 Compatível com desktop e mobile
- 🌙 Suporte a tema escuro (via sistema)
- 🔔 Feedback visual de sucesso/erro
- ⚡ Atualizações de progresso em tempo real via polling

---

## 📖 Uso

### Download Básico

1. Acesse http://localhost:3000
2. Selecione o tipo (Vídeo Único ou Playlist)
3. Cole a URL do YouTube
4. (Opcional) Configure opções avançadas
5. Clique em "Baixar"
6. Acompanhe o progresso em tempo real
7. Vídeo aparecerá automaticamente na biblioteca

### Opções Avançadas

**Configurações de Qualidade:**

- Resolução máxima (altura em pixels)
- Apenas áudio (extração MP3)
- Download de legendas e miniaturas

**Nomenclatura Customizada:**

- Subpasta personalizada (ex: `Músicas/Vídeo 01`)
- Nome do arquivo customizado (ex: `Video 001`)

**Headers HTTP:**

- Referer customizado
- Origin customizado
- Arquivo de cookies (formato Netscape)

**Proteção Anti-Ban (para playlists grandes):**

- Delay entre vídeos (recomendado: 2-5s)
- Agrupamento em batches (ex: 5 vídeos por batch)
- Delay entre batches (recomendado: 10-30s)
- Randomização de delays (simula comportamento humano)
- **Presets:** Seguro, Moderado, Rápido

### Google Drive Integration

**Configuração Inicial:**

1. Siga o guia completo: **[GOOGLE-DRIVE-SETUP.md](./docs/project/GOOGLE-DRIVE-SETUP.md)**
2. Resumo rápido:
   - Criar projeto no Google Cloud Console
   - Ativar Google Drive API
   - Criar credenciais OAuth 2.0 (Desktop app)
   - Baixar `credentials.json`
   - Inserir arquivo de credenciais no backend → `backend/credentials.json`

**Usando o Drive:**

1. Acesse http://localhost:3000/drive
2. Clique em "Conectar com Google Drive"
3. Autorize o aplicativo no navegador
4. Gerencie vídeos:
   - 📤 Upload individual ou sincronização completa
   - 🧩 Upload externo com thumbnail customizada
   - 📊 Visualize status de sincronização
   - ▶️ Reproduza vídeos diretamente do Drive
   - 🗑️ Exclua vídeos do Drive

**Catálogo do Drive (primeira execução / máquina nova):**

- O Drive agora usa um **catálogo persistente** (SQLite local + snapshot no Drive).
- Para o primeiro uso em uma máquina nova, importe o snapshot:
  - `POST /api/catalog/drive/import`
- Para a primeira vez em que o Drive já tem vídeos mas não existe snapshot:
  - `POST /api/catalog/drive/rebuild`
- Para indexar vídeos locais existentes:
  - `POST /api/catalog/bootstrap-local`

---

## 🔌 API REST

A API FastAPI oferece endpoints completos para integração:

### Endpoints de Download

**POST** `/api/download` - Inicia um download em background

```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "max_res": 1080,
  "subs": true,
  "audio_only": false,
  "path": "Curso/Modulo 01",
  "file_name": "Aula 01",
  "delay_between_downloads": 3,
  "batch_size": 5,
  "randomize_delay": true
}
```

**GET** `/api/jobs/{job_id}` - Obtém status e progresso de um job

**GET** `/api/jobs` - Lista todos os jobs

**POST** `/api/jobs/{job_id}/cancel` - Cancela um download em andamento

**DELETE** `/api/jobs/{job_id}` - Remove um job do histórico

**POST** `/api/video-info` - Obtém informações de um vídeo sem baixar

### Endpoints de Biblioteca Local

**GET** `/api/videos` - Lista vídeos baixados localmente (com duração)

**GET** `/api/videos/stream/{video_path}` - Stream de vídeo local (com range requests)

**GET** `/api/videos/thumbnail/{thumbnail_path}` - Serve thumbnail de vídeo local

### Endpoints de Catálogo (SQLite)

**GET** `/api/catalog/status` - Status do catálogo (local/drive)

**POST** `/api/catalog/bootstrap-local` - Indexa vídeos locais (1ª vez)

**POST** `/api/catalog/drive/import` - Importa snapshot do Drive

**POST** `/api/catalog/drive/publish` - Publica snapshot no Drive

**POST** `/api/catalog/drive/rebuild` - Reconstrói catálogo lendo o Drive

**DELETE** `/api/videos/{video_path}` - Exclui vídeo e arquivos relacionados

**POST** `/api/videos/delete-batch` - Exclui múltiplos vídeos em lote

### Endpoints Google Drive

**GET** `/api/drive/auth-status` - Verifica status de autenticação

**GET** `/api/drive/auth-url` - Gera URL de autenticação OAuth

**GET** `/api/drive/oauth2callback?code=...` - Callback OAuth (troca código por token)

**GET** `/api/drive/videos` - Lista vídeos no Google Drive

**POST** `/api/drive/upload/{video_path}` - Upload de vídeo local para Drive

**GET** `/api/drive/sync-status` - Status de sincronização (local vs Drive)

**GET** `/api/drive/sync-items` - Itens paginados (local_only/drive_only/synced)

**POST** `/api/drive/sync-all` - Sincroniza todos os vídeos locais para Drive

**GET** `/api/drive/stream/{file_id}` - Stream de vídeo do Drive (com range requests)

**GET** `/api/drive/thumbnail/{file_id}` - Thumbnail de vídeo do Drive

**GET** `/api/drive/videos/{file_id}/share` - Status de compartilhamento público

**POST** `/api/drive/videos/{file_id}/share` - Habilita compartilhamento público

**DELETE** `/api/drive/videos/{file_id}/share` - Revoga compartilhamento público

**DELETE** `/api/drive/videos/{file_id}` - Remove vídeo do Drive

**POST** `/api/drive/videos/delete-batch` - Exclui múltiplos vídeos do Drive em lote

**POST** `/api/drive/download` - Download de vídeo do Drive para armazenamento local

**POST** `/api/drive/download-all` - Download em lote (Drive -> local)

### Endpoints de Cache do Drive (opcional)

**POST** `/api/drive/cache/sync` - Sincronização manual do cache (`?full=true` para rebuild)

**GET** `/api/drive/cache/stats` - Estatísticas do cache (contagem, tamanho, última sync)

**POST** `/api/drive/cache/rebuild` - Força rebuild completo do cache

**DELETE** `/api/drive/cache` - Limpa todo o cache

**Documentação Interativa:** http://localhost:8000/docs

---

## 📁 Estrutura do Projeto

```
yt-archiver/
├── backend/                      # API FastAPI (arquitetura modular)
│   ├── app/                      # Pacote principal da aplicação
│   │   ├── main.py               # Entry point FastAPI
│   │   ├── config.py             # Configurações globais
│   │   ├── core/                 # Módulo central
│   │   │   ├── blocking.py       # Helper para IO bloqueante (to_thread)
│   │   │   ├── exceptions.py     # Exceções HTTP customizadas
│   │   │   ├── logging.py        # Logging estruturado
│   │   │   └── security.py       # Validações e sanitização
│   │   ├── catalog/              # Catálogo persistente (SQLite)
│   │   │   ├── router.py         # Endpoints /api/catalog/*
│   │   │   ├── service.py        # Regras de catálogo
│   │   │   ├── repository.py     # Acesso ao SQLite
│   │   │   └── database.py       # Schema e conexões
│   │   ├── downloads/            # Módulo de downloads
│   │   │   ├── router.py         # Endpoints /api/download, /api/video-info
│   │   │   ├── service.py        # Lógica de negócio
│   │   │   ├── schemas.py        # Modelos Pydantic
│   │   │   └── downloader.py     # Engine yt-dlp wrapper
│   │   ├── jobs/                 # Módulo de jobs assíncronos
│   │   │   ├── router.py         # Endpoints /api/jobs/*
│   │   │   ├── service.py        # Gerenciamento de jobs
│   │   │   ├── schemas.py        # Modelos de jobs
│   │   │   └── store.py          # Storage in-memory
│   │   ├── library/              # Módulo de biblioteca local
│   │   │   ├── router.py         # Endpoints /api/videos/*
│   │   │   ├── service.py        # Scan de diretórios
│   │   │   └── schemas.py        # Modelos de vídeos
│   │   ├── recordings/           # Módulo de gravações
│   │   │   ├── router.py         # Endpoint /api/recordings/upload
│   │   │   └── service.py        # Salvamento de gravações
│   │   └── drive/                # Módulo Google Drive
│   │       ├── router.py         # Endpoints /api/drive/*
│   │       ├── service.py        # Lógica de negócio
│   │       ├── schemas.py        # Modelos do Drive
│   │       ├── manager.py        # DriveManager (OAuth, upload, sync)
│   │       └── cache/            # Cache SQLite para metadados
│   │           ├── database.py   # Schema e conexão SQLite
│   │           ├── repository.py # CRUD operations
│   │           ├── sync.py       # Full/incremental sync
│   │           └── background.py # Task de sync periódico
│   ├── requirements.txt          # Dependências Python
│   ├── run.sh                    # Script para iniciar backend
│   ├── .venv/                    # Ambiente virtual Python
│   ├── downloads/                # Vídeos baixados (padrão)
│   ├── archive.txt               # Controle de downloads
│   ├── credentials.json          # Credenciais OAuth Google (gitignored)
│   ├── token.json                # Token OAuth (gitignored)
│   ├── drive_cache.db            # Cache SQLite do Drive (legado/opt-in)
│   └── database.db               # Catálogo SQLite local (local + drive)
│
├── frontend/                     # Interface Next.js
│   ├── src/
│   │   ├── app/                  # App Router (Next.js 15)
│   │   │   ├── page.tsx          # Página principal
│   │   │   ├── drive/page.tsx    # Página Google Drive
│   │   │   ├── layout.tsx        # Layout raiz
│   │   │   └── globals.css       # Estilos globais
│   │   ├── components/           # Componentes React
│   │   │   ├── common/                 # Componentes compartilhados
│   │   │   │   ├── navigation.tsx      # Navegação entre páginas
│   │   │   │   └── videos/             # VideoCard / VideoPlayer
│   │   │   ├── home/                   # Home (downloads)
│   │   │   │   └── download-form.tsx   # Formulário de download
│   │   │   ├── library/                # Biblioteca local
│   │   │   │   └── paginated-video-grid.tsx
│   │   │   ├── drive/                  # Google Drive
│   │   │   │   ├── drive-auth.tsx      # Autenticação Drive
│   │   │   │   ├── drive-video-grid.tsx
│   │   │   │   └── sync-panel.tsx      # Painel de sincronização
│   │   │   ├── record/                 # Gravação de tela
│   │   │   │   └── screen-recorder.tsx
│   │   │   └── ui/                     # Componentes shadcn/ui
│   │   └── lib/                  # Utilitários
│   │       ├── utils.ts          # Funções helper
│   │       └── url-validator.ts  # Validação de URLs
│   ├── package.json
│   └── next.config.ts
│
├── docs/
│   ├── project/                  # Documentação oficial
│   │   ├── ARCHITECTURE.md
│   │   ├── QUICK-START.md
│   │   ├── TECHNICAL-REFERENCE.md
│   │   ├── GOOGLE-DRIVE-SETUP.md
│   │   ├── GOOGLE-DRIVE-FEATURES.md
│   │   ├── OBSERVABILITY.md
│   │   └── GLOBAL-PLAYER.md
│   └── local/                    # Notas internas
│       └── archive/              # Planejamentos e historico
├── start-dev.sh                  # Script de início rápido (Linux/Mac)
├── start-dev.bat                 # Script de início rápido (Windows)
├── CLAUDE.md                     # Instruções para Claude Code
└── README.md                     # Esta documentação
```

---

## 🔧 Tecnologias

### Backend

- **FastAPI** - Framework web assíncrono
- **Arquitetura Modular** - Organização similar ao NestJS (router/service/schema)
- **yt-dlp** - Motor de download de vídeos
- **Uvicorn** - Servidor ASGI com hot reload
- **Google API Client** - Integração com Google Drive
- **Pydantic** - Validação de dados e schemas

### Arquitetura do Backend

O backend segue uma arquitetura modular com separação clara de responsabilidades:

| Módulo        | Responsabilidade                         | Endpoints                          |
| ------------- | ---------------------------------------- | ---------------------------------- |
| `downloads`   | Download de vídeos via yt-dlp            | `/api/download`, `/api/video-info` |
| `jobs`        | Gerenciamento de jobs assíncronos        | `/api/jobs/*`                      |
| `library`     | Biblioteca de vídeos locais              | `/api/videos/*`                    |
| `recordings`  | Upload de gravações de tela              | `/api/recordings/upload`           |
| `drive`       | Integração Google Drive                  | `/api/drive/*`                     |
| `drive/cache` | Cache SQLite para metadados              | `/api/drive/cache/*`               |
| `catalog`     | Catálogo persistente (SQLite + snapshot) | `/api/catalog/*`                   |
| `core`        | Exceções, segurança, utilitários         | -                                  |

**Padrão de cada módulo:**

- `router.py` - Define endpoints (APIRouter)
- `service.py` - Lógica de negócio
- `schemas.py` - Modelos Pydantic (request/response)

### Concorrência e IO Bloqueante

- O backend roda em 1 worker por padrão e mantém **jobs em memória**.
- IO bloqueante (Google Drive, filesystem, SQLite) é offload para threads via `core/blocking.py`.
- Para múltiplos workers em produção, é necessário mover o estado dos jobs para storage compartilhado (Redis/DB).

### Frontend

- **Next.js 15** - Framework React com App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **shadcn/ui** - Componentes acessíveis (Radix UI)
- **Vidstack** - Player de vídeo moderno e acessível
- **Lucide React** - Ícones

### Infraestrutura

- **ffmpeg** - Processamento de vídeo/áudio (requerido)
- **Python 3.12+** - Runtime backend
- **Node.js 18+** - Runtime frontend
- **Observabilidade local** - Prometheus + Grafana (**[OBSERVABILITY.md](./docs/project/OBSERVABILITY.md)**)

---

## 📝 Sistema de Arquivamento

### Controle de Duplicatas

O arquivo `backend/archive.txt` mantém registro de vídeos baixados:

```
youtube dQw4w9WgXcQ
youtube j8PxqgliIno
custom aula-01-introducao
```

**Comportamento:**

- Downloads dos vídeos são automaticamente registrados por ID de vídeo
- Com `--archive-id` (via opção customizada), você pode definir IDs manuais
- Vídeos já registrados são pulados automaticamente
- Ao excluir um vídeo pela interface, o registro é removido do archive

---

## 📂 Estrutura de Pastas

### Padrão de Nomenclatura

**Sem customização:**

```
backend/downloads/
└── NomeDoCanal/
    └── NomePlaylist/
        └── Título do Vídeo.mp4
        └── Título do Vídeo.jpg
        └── Título do Vídeo.pt-BR.vtt
        └── Título do Vídeo.info.json
```

**Com path e file_name customizados:**

```
backend/downloads/
└── Curso/
    └── Módulo 01/
        └── Aula 01 - Introdução.mp4
        └── Aula 01 - Introdução.jpg
        └── Aula 01 - Introdução.info.json
```

### Espelhamento no Google Drive

A estrutura de pastas local é preservada no Drive:

```
Google Drive/
└── YouTube Archiver/        (pasta raiz criada automaticamente)
    └── Curso/
        └── Módulo 01/
            ├── Aula 01 - Introdução.mp4
            ├── Aula 01 - Introdução.jpg
            └── Aula 01 - Introdução.info.json
```

**Nota:** Thumbnails, legendas e metadados (.info.json) são automaticamente enviados junto com o vídeo.

---

## 🍪 Usando Cookies

### Quando usar

Necessário para conteúdo que requer autenticação (vídeos privados, conteúdo premium, etc).

### Exportar cookies do navegador

Use extensões:

- **Chrome/Edge**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/)
- **Firefox**: [cookies.txt](https://addons.mozilla.org/firefox/addon/cookies-txt/)

### Formato esperado (Netscape)

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	1735689600	CONSENT	YES+
.youtube.com	TRUE	/	TRUE	1735689600	__Secure-1PSID	xxx...
```

### Uso

1. Exporte cookies do site desejado
2. Salve como `cookies.txt` no backend
3. Na interface web, configure "Arquivo de Cookies" como `./cookies.txt`

---

## ⚠️ Limitações e Boas Práticas

### DRM

Este projeto **NÃO** suporta conteúdo protegido por DRM (Widevine, FairPlay, PlayReady). Apenas streams não criptografados são suportados.

### Rate Limiting

Para evitar bloqueios ao baixar playlists grandes:

✅ **Recomendado:**

- Use o preset "Seguro" (delay 5s, batch 5, delay entre batches 30s)
- Ative "Randomizar Delays"
- Evite baixar mais de 50-100 vídeos de uma vez

⚠️ **Evite:**

- Preset "Rápido" para playlists grandes
- Downloads paralelos massivos (a UI usa 1 worker)
- Ignorar termos de serviço das plataformas

### Espaço em Disco

- Vídeos em alta qualidade (1080p+) ocupam muito espaço
- Use "Resolução Máxima" para limitar (ex: 720)
- Configure upload automático para Drive e exclua localmente
- Monitore espaço disponível regularmente

---

## 🐛 Troubleshooting

### "Erro ao conectar com o servidor"

**Solução:**

```bash
cd backend
./run.sh  # Certifique-se de que o backend está rodando
```

Verifique se http://localhost:8000 responde.

### "ffmpeg not found"

**Instalação:**

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Baixe de https://ffmpeg.org/download.html e adicione ao PATH
```

### "No video formats found"

**Possíveis causas:**

- URL inacessível ou inválida
- Conteúdo protegido por DRM
- Requer cookies (tente adicionar cookies.txt)
- Site não suportado pelo yt-dlp

### Upload para Drive falha

**Soluções:**

1. Verifique se `backend/credentials.json` existe e é válido
2. Delete `backend/token.json` e reautentique
3. Confirme que a Google Drive API está ativada no console
4. Verifique logs do backend para erros detalhados

### Downloads muito lentos

**Otimizações:**

- Configure "Resolução Máxima" menor (720p em vez de 1080p)
- Verifique sua conexão de internet
- Tente outro horário (pode ser throttling do provedor)
- Use `concurrent_fragments` maior (padrão é 10, tente 15-20 via API)

### Vídeos não aparecem na biblioteca

**Checklist:**

1. Aguarde o download completar (veja progresso)
2. Verifique se estão em `backend/downloads/`
3. Atualize a página (F5)
4. Verifique console do navegador para erros

---

### 📝 Commits Convencionais (Commitizen)

Este projeto usa [Commitizen](https://github.com/commitizen/cz-cli) para padronizar mensagens de commit seguindo a convenção [Conventional Commits](https://www.conventionalcommits.org/).

**Setup inicial (primeira vez):**

```bash
# Na raiz do repositório
npm install
```

**Como fazer commits:**

```bash
# Opção 1: Usando o script npm
npm run commit

# Opção 2: Usando npx
npx cz

# Opção 3: Usando git-cz (se instalado globalmente)
git cz
```

O Commitizen irá guiá-lo através de um wizard interativo para criar commits padronizados:

- **feat**: Nova funcionalidade
- **fix**: Correção de bug
- **docs**: Alterações na documentação
- **style**: Formatação, ponto e vírgula, etc (sem mudanças de código)
- **refactor**: Refatoração de código
- **perf**: Melhorias de performance
- **test**: Adição ou correção de testes
- **chore**: Tarefas de build, configurações, etc

---

## 📄 Licença

Este projeto é fornecido "como está", sem garantias. Use por sua conta e risco.

**Importante:** Respeite direitos autorais e termos de serviço das plataformas. Este projeto é destinado para arquivamento ético de conteúdo público.

---

## 📚 Recursos Adicionais

- [Documentação do yt-dlp](https://github.com/yt-dlp/yt-dlp#readme)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Google Drive API](https://developers.google.com/drive/api/guides/about-sdk)

---

**Desenvolvido para arquivamento ético de conteúdo público** 📼✨
