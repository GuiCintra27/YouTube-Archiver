# CLAUDE.md — YT-Archiver

## 🎯 Contexto do Projeto

Sistema completo de download e arquivamento de vídeos do YouTube com interface web moderna e integração com Google Drive.

**Versão atual:** v2.0
**Stack:** FastAPI (backend) + Next.js 15 (frontend) + yt-dlp (download engine)

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
**Principais módulos:**

- **`api.py`** (endpoint principal)
  - Endpoints de download (`/api/download`, `/api/jobs/*`)
  - Endpoints de biblioteca local (`/api/videos`, `/api/videos/stream/*`)
  - Endpoints Google Drive (`/api/drive/*`)
  - Sistema de jobs assíncronos com threading

- **`downloader.py`** (motor de download)
  - Wrapper do yt-dlp com suporte a:
    - Headers customizados (Referer, Origin, User-Agent, cookies)
    - Rate limiting (delays, batches, randomização)
    - Controle de qualidade e formato
    - Sistema de arquivamento (evita duplicatas)
  - Callbacks de progresso em tempo real

- **`drive_manager.py`** (integração Google Drive)
  - OAuth 2.0 flow completo
  - Upload/download de vídeos
  - Streaming com range requests (HTTP 206)
  - Sincronização de estrutura de pastas
  - Upload de arquivos relacionados (thumbnails, metadata, legendas)

**Dependências principais:**
- `fastapi`, `uvicorn`, `pydantic`
- `yt-dlp` (download engine)
- `google-api-python-client`, `google-auth-oauthlib` (Drive API)

### Frontend (`frontend/`)
**Framework:** Next.js 15 (App Router) + TypeScript
**Porta:** 3000
**UI Library:** shadcn/ui (Radix UI primitives) + Tailwind CSS

**Estrutura:**
```
src/
├── app/
│   ├── page.tsx                 # Página principal (downloads + biblioteca)
│   ├── drive/page.tsx           # Página Google Drive
│   ├── layout.tsx               # Layout global
│   └── globals.css
├── components/
│   ├── download-form.tsx        # Formulário de download
│   ├── video-grid.tsx           # Grid de vídeos locais + player
│   ├── drive-auth.tsx           # Autenticação OAuth
│   ├── drive-video-grid.tsx     # Grid de vídeos do Drive
│   ├── drive-video-player.tsx   # Player de vídeos do Drive
│   ├── sync-panel.tsx           # Painel de sincronização
│   ├── navigation.tsx           # Navegação entre páginas
│   └── ui/                      # Componentes shadcn/ui
└── lib/
    ├── utils.ts                 # Funções helper
    └── url-validator.ts         # Validação de URLs
```

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

### ✅ Opções Avançadas
- [x] Headers customizados (Referer, Origin)
- [x] Suporte a cookies (formato Netscape)
- [x] Rate limiting configurável (anti-ban)
- [x] Nomenclatura customizada de arquivos e pastas
- [x] Controle de qualidade/resolução
- [x] Extração de áudio (MP3)
- [x] Download de legendas e miniaturas

---

## 🐛 Bugs Corrigidos (Histórico)

### BUG #1: Streaming de Vídeos Locais - CORRIGIDO ✅
**Problema:** UnicodeEncodeError ao reproduzir vídeos com caracteres especiais (ex: ⧸ U+29F8)
**Causa:** Header `Content-Disposition` usando encoding latin-1 (padrão HTTP)
**Solução:** Implementado RFC 5987 encoding (`filename*=UTF-8''...`)
**Arquivo:** `backend/api.py:412-511` (função `stream_video()`)

### BUG #2: Upload para Google Drive - CORRIGIDO ✅
**Problema:** Query malformada com aspas simples não escapadas (ex: "60's")
**Causa:** Queries do Drive usam aspas simples como delimitadores
**Solução:** Escape de aspas (`name.replace("'", "\\'")`) em queries
**Arquivo:** `backend/drive_manager.py:136-301` (métodos `upload_video()` e `ensure_folder()`)

**Referência completa:** Ver `BUGS.md` para detalhes técnicos e testes de validação

---

## 📝 Convenções de Código

### Python (Backend)
- **Estilo:** PEP8 onde aplicável, priorizar estabilidade sobre refatoração agressiva
- **Tipagem:** Leve, usando Pydantic para validação de dados
- **Async:** Usar threading para jobs de download (não async/await para yt-dlp)
- **Logging:** Debug logs com `print(f"[DEBUG] ...")` e `print(f"[ERROR] ...")`
- **Tratamento de erros:** Try/except com traceback completo + HTTPException com mensagens claras

### TypeScript/React (Frontend)
- **Componentes:** Função como default export
- **Hooks:** Preferir hooks modernos (useState, useEffect, etc.)
- **Estilo:** Tailwind utility-first + shadcn/ui components
- **Estado:** useState para estado local, sem Redux/Zustand
- **Fetch:** Usar fetch nativo, sem libraries adicionais
- **Tipos:** Type safety rigoroso, evitar `any`

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
./run.sh                              # Recomendado (ativa venv automaticamente)
# OU manualmente:
source .venv/bin/activate && python api.py
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
   - ❌ NÃO: `python api.py` (não ativa o venv)
   - ✅ SIM: `./run.sh` (ativa venv automaticamente)

2. **Hot reload do uvicorn**
   - Funciona APENAS com `uvicorn api:app --reload`
   - NÃO funciona com `python api.py`
   - Backend atual usa `reload=True` no `uvicorn.run()` mas requer restart manual

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

2. **Plyr CSS**
   - Importar em `layout.tsx`: `import "plyr-react/plyr.css"`
   - Necessário para estilos corretos do player

3. **API Calls**
   - Backend em `http://localhost:8000`
   - Usar paths absolutos: `/api/videos` não `api/videos`
   - Polling de jobs a cada 1 segundo durante downloads

4. **shadcn/ui**
   - Componentes instalados sob demanda em `components/ui/`
   - Usar Radix UI primitives via shadcn CLI
   - Não modificar arquivos em `components/ui/` diretamente

---

## 📂 Arquivos e Pastas Importantes

### Backend
```
backend/
├── api.py                  # ⭐ Endpoint principal (FastAPI)
├── downloader.py           # ⭐ Lógica de download (yt-dlp wrapper)
├── drive_manager.py        # ⭐ Google Drive manager
├── requirements.txt        # Dependências Python
├── run.sh                  # Script de inicialização
├── .venv/                  # Ambiente virtual (gitignored)
├── downloads/              # Vídeos baixados (gitignored)
├── archive.txt             # Controle de duplicatas
├── credentials.json        # OAuth Google (gitignored, usar credentials.json.example)
├── token.json              # Token OAuth (gitignored, gerado automaticamente)
└── docs/project/           # Documentações específicas do backend
    ├── ANTI-BAN.md
    ├── EXPORT-COOKIES-GUIDE.md
    └── PERFORMANCE-OPTIMIZATION.md
```

### Frontend
```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx                  # ⭐ Página principal
│   │   ├── drive/page.tsx            # ⭐ Página Google Drive
│   │   ├── layout.tsx                # ⭐ Layout global
│   │   └── globals.css
│   ├── components/
│   │   ├── download-form.tsx         # Formulário de download
│   │   ├── video-grid.tsx            # ⭐ Grid + player local
│   │   ├── drive-video-grid.tsx      # Grid de vídeos do Drive
│   │   ├── sync-panel.tsx            # Painel de sincronização
│   │   └── ui/                       # shadcn/ui components
│   └── lib/
│       └── utils.ts                  # Helpers (cn, etc.)
├── package.json
├── next.config.ts
├── tailwind.config.ts
└── docs/project/           # Documentações específicas do frontend
    └── WEB-UI-README.md
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
2. Adicionar parâmetro no modelo Pydantic em `backend/api.py` (classe `DownloadRequest`)
3. Passar parâmetro para `Settings` em `backend/downloader.py`
4. Implementar lógica em `_base_opts()` do `Downloader`

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
- Logs aparecem no terminal onde `./run.sh` foi executado
- Debug logs: `[DEBUG] mensagem`
- Error logs: `[ERROR] mensagem` + traceback

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

1. **Arquitetura:** Backend FastAPI + Frontend Next.js 15 + yt-dlp
2. **Pasta backend:** `./run.sh` para iniciar, nunca `python api.py`
3. **Unicode/Encoding:** Sempre RFC 5987 para headers, sempre escapar `'` em queries Drive
4. **Bugs conhecidos:** Todos corrigidos (ver BUGS.md para histórico)
5. **Google Drive:** OAuth configurado, streaming funcionando, upload funcionando
6. **UI:** shadcn/ui + Tailwind, componentes já existentes em `components/ui/`
7. **Player:** Plyr com range requests (HTTP 206) funcionando local + Drive
8. **Sistema de jobs:** Assíncrono com polling, progresso em tempo real

**Nunca:**
- Suportar DRM
- Remover rate limiting
- Commitar credenciais
- Quebrar funcionalidades existentes sem justificativa

**Sempre:**
- Testar com caracteres especiais
- Validar entradas
- Documentar mudanças
- Preservar estabilidade

---

**Última atualização:** 2025-10-08
**Status:** ✅ Aplicação 100% funcional, todos os bugs críticos corrigidos
