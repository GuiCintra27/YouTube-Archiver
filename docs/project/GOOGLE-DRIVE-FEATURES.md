# 🚀 Nova Funcionalidade: Integração com Google Drive

## ✨ O que foi implementado

### Backend (API)

1. **Novo módulo `drive_manager.py`**
   - Gerenciamento completo do Google Drive
   - Autenticação OAuth 2.0
   - Upload de vídeos mantendo estrutura de pastas
   - Listagem de vídeos no Drive
   - Sincronização Local <-> Drive
   - Remoção de vídeos do Drive

2. **Novos endpoints na API:**
   - `GET /api/drive/auth-status` - Verificar autenticação
   - `GET /api/drive/auth-url` - Obter URL de autenticação OAuth
   - `GET /api/drive/oauth2callback` - Callback OAuth
   - `GET /api/drive/videos` - Listar vídeos no Drive
   - `POST /api/drive/upload/{path}` - Upload de vídeo individual
   - `GET /api/drive/sync-status` - Status de sincronização
   - `POST /api/drive/sync-all` - Sincronizar todos os vídeos
   - `DELETE /api/drive/videos/{id}` - Remover vídeo do Drive
   - `POST /api/drive/videos/delete-batch` - Excluir múltiplos vídeos em lote
   - `POST /api/drive/download/{id}` - Download de vídeo para local
   - `PATCH /api/drive/videos/{id}/rename` - Renomear vídeo no Drive
   - `POST /api/drive/videos/{id}/thumbnail` - Atualizar thumbnail no Drive

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
   - Componente VideoCard unificado (mesmo usado na biblioteca local)

5. **Componente `Navigation`**
   - Menu de navegação Local / Drive
   - Ícones intuitivos
   - Indicador de página ativa

## 📁 Estrutura de Arquivos Criados

```
backend/
├── drive_manager.py           # Módulo de gerenciamento do Drive
├── credentials.json.example   # Exemplo de credenciais
└── api.py (modificado)        # Novos endpoints

web-ui/src/
├── app/
│   ├── layout.tsx (modificado)  # Navegação adicionada
│   └── drive/
│       └── page.tsx             # Página do Drive
└── components/
    ├── navigation.tsx           # Menu Local / Drive
    ├── drive-auth.tsx           # Autenticação
    ├── drive-video-grid.tsx     # Grid de vídeos do Drive
    └── sync-panel.tsx           # Painel de sincronização

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
cd web-ui
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
- Escopo mínimo: `drive.file` (apenas arquivos criados pelo app)

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
- [ ] Sincronização bidirecional automática
- [ ] Conflitos de versão
- [ ] Progress bar durante uploads grandes
- [ ] Compressão antes do upload
- [ ] Compartilhamento de links do Drive
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

**Aproveite!** 🚀
