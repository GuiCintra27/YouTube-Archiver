# 🚀 Nova Funcionalidade: Integração com Google Drive

## ✨ O que foi implementado

### Backend (API)

1. **DriveManager (`backend/app/drive/manager.py`)**
   - Gerenciamento completo do Google Drive
   - Autenticação OAuth 2.0
   - Upload de vídeos mantendo estrutura de pastas
   - Listagem de vídeos no Drive
   - Sincronização Local <-> Drive
   - Remoção de vídeos do Drive (inclui arquivos relacionados + limpeza de pastas em background)

2. **Novos endpoints na API:**
   - `GET /api/drive/auth-status` - Verificar autenticação
   - `GET /api/drive/auth-url` - Obter URL de autenticação OAuth
   - `GET /api/drive/oauth2callback` - Callback OAuth
   - `GET /api/drive/videos` - Listar vídeos no Drive
   - `POST /api/drive/upload/{path}` - Upload de vídeo individual
   - `POST /api/drive/upload-external` - Upload externo (vídeo + thumbnail + extras)
   - `GET /api/drive/sync-status` - Status de sincronização
   - `GET /api/drive/sync-items` - Itens paginados (local_only/drive_only/synced)
   - `POST /api/drive/sync-all` - Sincronizar todos os vídeos
   - `DELETE /api/drive/videos/{id}` - Remover vídeo do Drive (retorna cleanup_job_id)
   - `POST /api/drive/videos/delete-batch` - Excluir múltiplos vídeos em lote
   - `GET /api/drive/videos/{id}/share` - Status do compartilhamento público
   - `POST /api/drive/videos/{id}/share` - Habilitar link público de compartilhamento
   - `DELETE /api/drive/videos/{id}/share` - Revogar compartilhamento público
   - `GET /api/drive/custom-thumbnail/{id}` - Thumbnail customizada
   - `POST /api/drive/download` - Download de vídeo para local (por path ou file_id)
   - `POST /api/drive/download-all` - Download em lote (Drive -> local)
   - `PATCH /api/drive/videos/{id}/rename` - Renomear vídeo no Drive
   - `POST /api/drive/videos/{id}/thumbnail` - Atualizar thumbnail no Drive

3. **Cache SQLite para metadados (v2.4)**
   - `POST /api/drive/cache/sync` - Sync manual (`?full=true` para rebuild)
   - `GET /api/drive/cache/stats` - Estatísticas do cache
   - `POST /api/drive/cache/rebuild` - Rebuild completo
   - `DELETE /api/drive/cache` - Limpar cache

### Frontend (Web UI)

1. **Nova página `/drive`**
   - Visualização de vídeos do Google Drive
   - Interface similar à página local
   - Gerenciamento de vídeos no Drive

2. **Componente `DriveAuth`**
   - Tela de autenticação OAuth
   - Popup para login no Google
   - Validação de credenciais

3. **Componente `SyncPanel`**
   - Painel de sincronização Local <-> Drive
   - Estatísticas (Local, Drive, Sincronizados)
   - Barra de progresso visual
   - Upload individual ou em lote
   - Listagem detalhada:
     - Vídeos apenas locais (com botão de upload)
     - Vídeos apenas no Drive
     - Vídeos sincronizados

4. **Componente `DriveVideoGrid`**
   - Grid de vídeos do Drive (3 colunas, estilo YouTube)
   - Thumbnails automáticas com efeito de zoom no hover
   - Informações de tamanho e duração
   - Modal de informações detalhadas do vídeo
   - Seleção múltipla com checkboxes
   - Exclusão individual ou em lote
   - Edição de vídeos (renomear e atualizar thumbnail)
   - Compartilhamento público (link com toggle de ativação)
   - Componente VideoCard unificado (mesmo usado na biblioteca local)

5. **Componente `ExternalUploadModal`**
   - Upload de vídeo externo direto para o Drive
   - Thumbnail customizada (JPG/PNG/WebP)
   - Legendas e transcrição opcionais

5. **Componente `Navigation`**
   - Menu de navegação Local / Drive
   - Ícones intuitivos
   - Indicador de página ativa

## ⚡ Cache SQLite para Performance (v2.4)

### O que é?

Sistema de cache local que armazena metadados de vídeos do Google Drive em SQLite,
eliminando a necessidade de chamadas à API do Drive para cada listagem.

**Nota:** o catálogo persistente (snapshot + SQLite) é o fluxo principal atual.
O cache permanece como opção/legado para cenários específicos.

### Ganhos de Performance

| Operação | Antes (API) | Depois (Cache) | Melhoria |
|----------|-------------|----------------|----------|
| Listar 100 vídeos | ~2-3s | ~50-100ms | **~20-30x** |
| Listar 500 vídeos | ~8-10s | ~100-200ms | **~40-50x** |
| Paginação | ~1-2s/página | ~20-50ms | **~30-40x** |

### Como funciona?

1. **Primeira autenticação**: Full sync automático popula o cache
2. **Listagem de vídeos**: Busca no SQLite local (~50ms)
3. **A cada 30 minutos**: Incremental sync detecta mudanças no Drive
4. **Upload/Delete/Rename**: Atualização imediata no cache (real-time sync)
5. **Erro no cache**: Fallback automático para API do Drive

### Configurações (.env)

```bash
DRIVE_CACHE_ENABLED=true           # Habilitar cache (padrão: true)
DRIVE_CACHE_DB_PATH=./drive_cache.db  # Caminho do banco
DRIVE_CACHE_SYNC_INTERVAL=30       # Intervalo em minutos
DRIVE_CACHE_FALLBACK_TO_API=true   # Fallback se cache falhar
```

### Endpoints de Gerenciamento

```bash
# Sync manual (incremental)
curl -X POST http://localhost:8000/api/drive/cache/sync

# Full rebuild
curl -X POST "http://localhost:8000/api/drive/cache/sync?full=true"

# Ver estatísticas
curl http://localhost:8000/api/drive/cache/stats

# Limpar cache
curl -X DELETE http://localhost:8000/api/drive/cache
```

---

## 📦 Catálogo do Drive (Snapshot + SQLite)

Além do cache, o Drive agora usa um **catálogo persistente**:
- SQLite local (`backend/database.db`)
- Snapshot versionado no Drive (`catalog-drive.json.gz`)

### Primeiro uso / Máquina nova

1) **Importar snapshot existente**
```
POST /api/catalog/drive/import
```

2) **Rebuild inicial (Drive já populado, sem snapshot)**
```
POST /api/catalog/drive/rebuild
```

3) **Indexar vídeos locais**
```
POST /api/catalog/bootstrap-local
```

### Endpoints de catálogo

- `GET /api/catalog/status`
- `POST /api/catalog/bootstrap-local`
- `POST /api/catalog/drive/import`
- `POST /api/catalog/drive/publish`
- `POST /api/catalog/drive/rebuild`

## 📁 Estrutura de Arquivos Criados

```
backend/
├── app/drive/manager.py       # DriveManager (OAuth, upload, download)
├── app/drive/cache/           # Cache SQLite do Drive (opcional)
├── app/catalog/               # Catálogo persistente (SQLite + snapshot)
├── credentials.json.example   # Exemplo de credenciais
├── drive_cache.db             # Cache SQLite (opcional)
└── database.db                # Catálogo SQLite (local + drive)

frontend/src/
├── app/
│   ├── layout.tsx (modificado)  # Navegação adicionada
│   └── drive/
│       └── page.tsx             # Página do Drive
└── components/
    ├── common/navigation.tsx    # Menu Local / Drive
    └── drive/                   # Componentes do Drive
        ├── drive-auth.tsx       # Autenticação
        ├── drive-video-grid.tsx # Grid de vídeos do Drive
        └── sync-panel.tsx       # Painel de sincronização

docs/
├── GOOGLE-DRIVE-SETUP.md      # Guia completo de setup
└── GOOGLE-DRIVE-FEATURES.md   # Este arquivo
```

## 🎯 Como Usar

### 1. Configurar Google Drive

Siga o guia: [GOOGLE-DRIVE-SETUP.md](./GOOGLE-DRIVE-SETUP.md)

**Resumo:**
1. Criar projeto no Google Cloud Console
2. Ativar Google Drive API
3. Criar credenciais OAuth 2.0
4. Baixar `credentials.json` → `backend/credentials.json`

### 2. Acessar Interface

```bash
# Terminal 1 - Backend
cd backend
./run.sh

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Acesse: http://localhost:3000

### 3. Fluxo de Uso

1. **Página Local (/):**
   - Baixe vídeos normalmente
   - Visualize biblioteca local
   - Reproduza vídeos localmente

2. **Página Drive (/drive):**
   - Clique em "Conectar com Google Drive"
   - Autorize no Google (popup)
   - Veja status de sincronização
   - Faça upload de vídeos individuais ou todos
   - Visualize e gerencie vídeos no Drive

## 📊 Funcionalidades Detalhadas

### Sincronização Inteligente

O sistema compara automaticamente:

- **Local Only**: Vídeos que só existem localmente
  - Botão para upload individual
  - Botão para sincronizar todos de uma vez

- **Drive Only**: Vídeos que só existem no Drive
  - Informativo (não permite download automático)

- **Synced**: Vídeos em ambos os locais
  - Indicador visual ✓

### Estrutura no Drive

```
Google Drive/
└── YouTube Archiver/          # Pasta raiz (automática)
    └── [sua estrutura local]  # Espelhada automaticamente
```

Exemplo:
```
downloads/
├── Canal A/
│   └── Video 1.mp4
└── Canal B/
    └── Playlist/
        └── Video 2.mp4
```

Vira:
```
Google Drive/YouTube Archiver/
├── Canal A/
│   └── Video 1.mp4
└── Canal B/
    └── Playlist/
        └── Video 2.mp4
```

## 🔐 Segurança

### Arquivos Sensíveis

**NÃO commitar:**
- ❌ `backend/credentials.json` - Credenciais OAuth
- ❌ `backend/token.json` - Token de acesso
- ❌ `backend/uploaded.jsonl` - Log de uploads

Todos já estão no `.gitignore`!

### OAuth 2.0

- Autenticação segura via Google
- Tokens com renovação automática
- Escopo atual: `drive` (necessário para gerenciar permissões de compartilhamento)

## 🐛 Troubleshooting

### "Credentials file not found"

```bash
# Certifique-se de ter:
ls backend/credentials.json

# Se não existir, siga GOOGLE-DRIVE-SETUP.md
```

### "redirect_uri_mismatch"

No Google Cloud Console:
1. Edite seu OAuth Client ID
2. Adicione: `http://localhost:8000/api/drive/oauth2callback`

### "Access blocked"

No Google Cloud Console:
1. Vá em "Tela de consentimento OAuth"
2. Adicione seu email em "Usuários de teste"

### Token expirado

```bash
# Delete e reautentique:
rm backend/token.json
# Depois vá em /drive e conecte novamente
```

## 📈 Próximas Melhorias Possíveis

- [x] Download de vídeos do Drive para local ✅ (v2.2)
- [x] Exclusão em lote de vídeos do Drive ✅ (v2.3)
- [x] Cards estilo YouTube com duração e info modal ✅ (v2.3)
- [x] Cache SQLite para listagem ultrarrápida ✅ (v2.4)
- [ ] Sincronização bidirecional automática
- [ ] Conflitos de versão
- [ ] Progress bar durante uploads grandes
- [ ] Compressão antes do upload
- [x] Compartilhamento de links do Drive ✅ (v2.4.x)
- [ ] Backup automático agendado

## 🎉 Conclusão

Agora você tem:
- ✅ Visualização de vídeos locais e do Drive (cards estilo YouTube)
- ✅ Upload manual ou automático
- ✅ Download de vídeos do Drive para local
- ✅ Status de sincronização em tempo real
- ✅ Gerenciamento completo via interface web
- ✅ Seleção múltipla e exclusão em lote
- ✅ Modal de informações detalhadas do vídeo
- ✅ Autenticação segura OAuth 2.0
- ✅ **Cache SQLite para listagem ultrarrápida** (~20-50x mais rápido)

**Aproveite!** 🚀
