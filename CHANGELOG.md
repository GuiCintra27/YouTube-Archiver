# Registro de Alterações

## [2.4.0] - 2025-12-04

### ⚡ Performance - Cache SQLite para Google Drive

**Sistema de cache local para metadados de vídeos do Google Drive, otimizando listagem e busca.**

### ✨ Adicionado

#### Cache SQLite para Metadados do Drive
- **Banco de dados local** (`drive_cache.db`) armazena metadados de vídeos e pastas
- **Listagem ~10x mais rápida** - consultas locais em vez de chamadas de API para cada requisição
- **Modo WAL** habilitado para melhor performance de leitura concorrente
- **Paginação otimizada** com índices SQLite

#### Sincronização Inteligente
- **Sincronização completa** - Reconstrução completa do cache (primeira autenticação ou recuperação)
- **Sincronização incremental** - Apenas mudanças desde a última sincronização (a cada 30 min)
- **Sincronização em tempo real** - Atualização imediata após upload/delete/rename
- **Auto-recuperação** - Detecção de corrupção com reconstrução automática

#### Novos Endpoints de Cache
- `POST /api/drive/cache/sync` - Disparar sincronização manual (`?full=true` para reconstrução)
- `GET /api/drive/cache/stats` - Estatísticas do cache (contagem, tamanho, última sync)
- `POST /api/drive/cache/rebuild` - Força rebuild completo
- `DELETE /api/drive/cache` - Limpa o cache

#### Configurações
- `DRIVE_CACHE_ENABLED` - Habilitar/desabilitar cache (padrão: true)
- `DRIVE_CACHE_DB_PATH` - Caminho do banco SQLite (padrão: `./drive_cache.db`)
- `DRIVE_CACHE_SYNC_INTERVAL` - Intervalo de sync em minutos (padrão: 30)
- `DRIVE_CACHE_FALLBACK_TO_API` - Fallback automático se cache falhar (padrão: true)

#### Testes
- **22 novos testes** para o sistema de cache
- Cobertura de CRUD de repositório, sincronização, gerenciador de banco e estatísticas
- Total de testes do projeto: **68 testes**

### 🔧 Modificado

#### Backend
- `app/drive/cache/` - Novo submódulo com:
  - `database.py` - Esquema SQLite, conexão e migrações
  - `repository.py` - Operações CRUD para vídeos/pastas
  - `sync.py` - Sincronização completa, incremental e em tempo real
  - `background.py` - Tarefa de sincronização periódica
- `app/drive/service.py` - Integração com cache em `list_videos_paginated()`
- `app/drive/router.py` - Novos endpoints de cache, sync inicial no OAuth callback
- `app/main.py` - Tarefa em segundo plano de sincronização no lifespan
- `app/config.py` - Novas configurações de cache

### 📦 Dependências

#### Backend
- `aiosqlite>=0.19.0` - SQLite assíncrono para operações de banco

### 📊 Ganhos de Performance

| Operação | Antes (API) | Depois (Cache) | Melhoria |
|----------|-------------|----------------|----------|
| Listar 100 vídeos | ~2-3s | ~50-100ms | **~20-30x** |
| Listar 500 vídeos | ~8-10s | ~100-200ms | **~40-50x** |
| Paginação | ~1-2s/página | ~20-50ms | **~30-40x** |

*Nota: Tempos aproximados, variam conforme latência de rede e carga da API do Drive*

### 🔄 Fluxo de Cache

```
GET /api/drive/videos
    │
    ├─► Cache habilitado?
    │       │
    │       ├─► Sim → Busca no SQLite
    │       │           │
    │       │           ├─► Acerto de cache → Retorna (~50ms)
    │       │           │
    │       │           └─► Cache vazio → Sincronização completa + retornar
    │       │
    │       └─► Não → API direta (~2-3s)
    │
    └─► Erro no cache? → Fallback automático para API
```

---

## [2.3.0] - 2025-12-01

### 🎨 UI/UX - Redesenho dos Cards de Vídeo

**Cards de vídeo estilo YouTube com experiência aprimorada.**

### ✨ Adicionado

#### Cards de Vídeo Redesenhados
- **Layout estilo YouTube** com thumbnails arredondadas e efeito de zoom no hover
- **Duração do vídeo** exibida como badge sobre a thumbnail
- **Modal de informações** com detalhes do vídeo (título, duração, tamanho, data)
- **Seleção múltipla** com checkboxes que aparecem suavemente no hover
- **Card clicável** - clicar em qualquer área inicia o player
- **Grid 3 colunas** - layout mais espaçoso e visual

#### Exclusão em Lote
- **Biblioteca local** (`POST /api/videos/delete-batch`)
  - Selecionar múltiplos vídeos com checkboxes
  - Barra de ações flutuante com contador de selecionados
  - Botões "Selecionar todos", "Limpar" e "Excluir"
  - Confirmação antes da exclusão
- **Google Drive** (`POST /api/drive/videos/delete-batch`)
  - Mesma funcionalidade da biblioteca local
  - Exclusão em lote de vídeos no Drive

#### Duração de Vídeos
- **Extração automática** usando ffprobe no backend
- **Formato inteligente** - exibe HH:MM:SS ou MM:SS conforme duração
- **Badge visual** sobre a thumbnail do vídeo

#### Componente VideoCard Unificado
- **Componente único** usado tanto na biblioteca local quanto no Drive
- **Props flexíveis** - aceita thumbnail por path ou URL direta
- **Menu de ações** com opções de Editar, Info e Excluir
- **Transições suaves** em todos os estados interativos

#### Edição de Vídeos
- **Renomear vídeos** na biblioteca local e no Google Drive
- **Atualizar thumbnail** com upload de nova imagem
- **Modal de edição** com preview da thumbnail
- **Renomeação automática** de arquivos relacionados (legendas, metadados)
- **Endpoints novos:**
  - `PATCH /api/videos/{path}/rename` - Renomear vídeo local
  - `POST /api/videos/{path}/thumbnail` - Atualizar thumbnail local
  - `PATCH /api/drive/videos/{id}/rename` - Renomear vídeo no Drive
  - `POST /api/drive/videos/{id}/thumbnail` - Atualizar thumbnail no Drive

### 🔧 Modificado

#### Backend
- `library/service.py` - Adicionado `get_video_duration()` e `format_duration()`
- `library/service.py` - Adicionado `delete_videos_batch()` para exclusão em lote
- `library/router.py` - Novo endpoint `POST /api/videos/delete-batch`
- `drive/service.py` - Adicionado `delete_videos_batch()` para exclusão em lote
- `drive/router.py` - Novo endpoint `POST /api/drive/videos/delete-batch`
- `drive/manager.py` - Adicionado `delete_files_batch()` para exclusão em lote

#### Frontend
- `video-card.tsx` - Redesenhado completamente com novo layout e modal de edição
- `paginated-video-grid.tsx` - Adicionada seleção múltipla, exclusão em lote e edição
- `drive-video-grid.tsx` - Refatorado para usar VideoCard unificado com edição
- `api-urls.ts` - Adicionadas constantes `VIDEOS_DELETE_BATCH` e `DRIVE_DELETE_BATCH`

### 📦 Dependências

#### Frontend
- `@/components/ui/checkbox` - Novo componente shadcn/ui para seleção

---

## [2.0.0] - 2025-10-06

### 🎉 Lançamento Principal - Interface Web Completa

**Nova arquitetura com separação frontend/backend para uso visual e intuitivo.**

### ✨ Adicionado

#### Backend (Novo)
- **API REST com FastAPI** (`backend/`)
  - Endpoints para download, status e histórico
  - Sistema de jobs para gerenciar downloads em background
  - Server-Sent Events (SSE) para progresso em tempo real
  - Documentação automática com Swagger (OpenAPI)
  - CORS configurado para desenvolvimento local

#### Frontend (Web) (Novo)
- **Interface Next.js 15** (`frontend/`)
  - Design moderno com shadcn/ui e Tailwind CSS
  - Formulário intuitivo para download de vídeos
  - Barra de progresso em tempo real
  - Opções avançadas expansíveis (accordion)
  - Switches para configurações booleanas
  - Feedback visual de sucesso/erro
  - Responsivo e compatível com mobile

#### Componentes UI
- Button, Card, Input, Label (shadcn/ui)
- Progress bar animada
- Switch toggles
- Accordion para opções avançadas
- Ícones com Lucide React

#### Utilitários
- Formatação de bytes (KB, MB, GB)
- Formatação de velocidade (MB/s)
- Formatação de tempo (ETA)
- Helpers para merge de classes CSS

#### Documentação
- `WEB-UI-README.md` - Guia completo da interface web
- `QUICK-START.md` - Início rápido em 3 passos
- `CHANGELOG.md` - Histórico de versões

#### Scripts
- `start-dev.sh` - Iniciar backend + frontend (Linux/Mac)
- `start-dev.bat` - Iniciar backend + frontend (Windows)

### 🔧 Modificado

#### CLI Python
- Refatorado para ser importável como biblioteca
- Funções expostas em `downloader.py` para uso na API
- Mantém 100% de compatibilidade com versão anterior
- Todas as funcionalidades preservadas

#### README
- Adicionada seção "Interface Web Moderna"
- Reorganizado para destacar nova interface
- Links para documentação específica

### 📦 Dependências

#### Backend
- `fastapi>=0.115.0` - Framework web assíncrono
- `uvicorn[standard]>=0.32.0` - Servidor ASGI
- `python-multipart>=0.0.9` - Upload de arquivos
- `pydantic>=2.9.0` - Validação de dados

#### Frontend
- `next@15.0.0` - Framework React
- `@radix-ui/*` - Componentes UI primitivos
- `tailwindcss@3.4.17` - Estilização utility-first
- `lucide-react` - Ícones
- `class-variance-authority` - Variantes de componentes

### 🎯 Funcionalidades Principais

1. **Interface Visual Completa**
   - Usuários não-técnicos podem usar sem conhecer CLI
   - Todas as opções do CLI disponíveis na UI
   - Progresso em tempo real com estatísticas

2. **API REST**
   - Integração com outras aplicações
   - Endpoints RESTful bem documentados
   - Swagger UI interativo

3. **Arquitetura Moderna**
   - Backend/Frontend desacoplados
   - Comunicação assíncrona
   - Escalável e manutenível

### 🔄 Compatibilidade

- ✅ CLI Python 100% compatível (nenhuma breaking change)
- ✅ Todos os parâmetros existentes mantidos
- ✅ Frontend Next.js (`frontend/`) disponível
- ✅ Google Drive upload suportado via CLI

### 📊 Estrutura do Projeto

```
yt-archiver/
├── backend/              # API FastAPI (NOVO)
│   ├── app/
│   │   ├── main.py
│   │   └── downloads/
│   │       └── downloader.py
│   └── requirements.txt
├── frontend/             # Interface Next.js (NOVO)
│   ├── src/
│   └── package.json
├── docs/                 # Documentação
├── start-dev.sh          # Script Linux/Mac (NOVO)
├── start-dev.bat         # Script Windows (NOVO)
├── README.md             # Atualizado
├── WEB-UI-README.md      # Novo
└── QUICK-START.md        # Novo
```

### 🚀 Como Usar

**Interface Web:**
```bash
./start-dev.sh
# Acesse http://localhost:3000
```

**CLI (legado):** removido do monorepo atual (use tags antigas, se necessário)

**API (novo):**
```bash
cd backend
./run.sh
# Acesse http://localhost:8000/docs
```

---

## [1.0.0] - 2024-09-14

### Lançamento Inicial

- CLI Python com yt-dlp
- Download de YouTube e HLS
- Upload para Google Drive
- Headers e cookies customizados
- Nomenclatura personalizada
- Frontend gerador de comandos

---

**Legenda:**
- ✨ Adicionado - Novas funcionalidades
- 🔧 Modificado - Mudanças em funcionalidades existentes
- 🐛 Corrigido - Bug fixes
- 🗑️ Removido - Funcionalidades descontinuadas
- 🔒 Segurança - Vulnerabilidades corrigidas
