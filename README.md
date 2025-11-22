# YT-Archiver

Sistema completo para download e arquivamento de vídeos do YouTube e streams HLS (sem DRM), com interface web moderna e integração opcional com Google Drive.

## 📋 Visão Geral

O YT-Archiver combina uma API REST robusta com uma interface web moderna para facilitar o download e gerenciamento de vídeos:

- **API REST** (`backend/`): FastAPI com sistema de jobs assíncronos e integração com Google Drive
- **Interface Web** (`web-ui/`): Next.js 15 + shadcn/ui para uma experiência visual intuitiva
- **Motor de Download**: yt-dlp para downloads de YouTube, playlists e streams HLS

### Principais Funcionalidades

- ✅ Download de vídeos do YouTube (canais, playlists, vídeos individuais)
- ✅ Suporte a streams HLS (M3U8) sem DRM
- ✅ Headers customizados (Referer, Origin, User-Agent)
- ✅ Cookies personalizados via arquivo Netscape
- ✅ **Biblioteca de vídeos local** - Visualize, reproduza e gerencie vídeos baixados
- ✅ **Sincronização com Google Drive** - Upload, visualização e streaming de vídeos no Drive
- ✅ **Sistema de jobs assíncronos** - Downloads em background com progresso em tempo real
- ✅ Sistema de arquivamento para evitar downloads duplicados
- ✅ Controle de qualidade e formato de saída
- ✅ Rate limiting configurável (anti-ban para playlists grandes)
- ✅ Extração de áudio (MP3)
- ✅ Download de legendas, miniaturas e metadados
- ✅ Nomes de arquivo e caminhos customizados
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
1. Configurar e ativar o ambiente virtual do backend
2. Instalar dependências Python
3. Iniciar o backend na porta 8000
4. Iniciar o frontend na porta 3000

**Acesse:** http://localhost:3000

#### Opção 2: Manual

**Backend:**
```bash
cd backend
./run.sh  # Ou: source .venv/bin/activate && python api.py
```

**Frontend:**
```bash
cd web-ui
npm install
npm run dev
```

**Acesse:**
- Interface Web: http://localhost:3000
- API: http://localhost:8000
- Documentação da API: http://localhost:8000/docs

---

## 🌐 Interface Web

### Funcionalidades da UI

**Página Principal (`/`):**
- 📥 Formulário de download com todas as opções configuráveis
- 📊 Barra de progresso em tempo real durante downloads
- 📚 Biblioteca de vídeos locais com thumbnails
- ▶️ Player de vídeo integrado (Plyr)
- 🗑️ Exclusão de vídeos com limpeza automática de arquivos relacionados
- ⚙️ Opções avançadas: headers, cookies, rate limiting, nomenclatura customizada

**Página Google Drive (`/drive`):**
- ☁️ Autenticação OAuth2 com Google Drive
- 📂 Visualização de vídeos sincronizados no Drive
- ⬆️ Upload individual ou em lote de vídeos locais
- 🔄 Painel de sincronização mostrando diferenças entre local e Drive
- ▶️ Streaming direto do Google Drive com suporte a seek/skip
- 🗑️ Exclusão de vídeos do Drive

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
- Subpasta personalizada (ex: `Curso/Módulo 01`)
- Nome do arquivo customizado (ex: `Aula 01 - Introdução`)

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

1. Siga o guia completo: **[GOOGLE-DRIVE-SETUP.md](./GOOGLE-DRIVE-SETUP.md)**
2. Resumo rápido:
   - Criar projeto no Google Cloud Console
   - Ativar Google Drive API
   - Criar credenciais OAuth 2.0 (Desktop app)
   - Baixar `credentials.json` → `backend/credentials.json`

**Usando o Drive:**

1. Acesse http://localhost:3000/drive
2. Clique em "Conectar com Google Drive"
3. Autorize o aplicativo no navegador
4. Gerencie vídeos:
   - 📤 Upload individual ou sincronização completa
   - 📊 Visualize status de sincronização
   - ▶️ Reproduza vídeos diretamente do Drive
   - 🗑️ Exclua vídeos do Drive

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

**GET** `/api/videos` - Lista vídeos baixados localmente

**GET** `/api/videos/stream/{video_path}` - Stream de vídeo local (com range requests)

**GET** `/api/videos/thumbnail/{thumbnail_path}` - Serve thumbnail de vídeo local

**DELETE** `/api/videos/{video_path}` - Exclui vídeo e arquivos relacionados

### Endpoints Google Drive

**GET** `/api/drive/auth-status` - Verifica status de autenticação

**GET** `/api/drive/auth-url` - Gera URL de autenticação OAuth

**GET** `/api/drive/oauth2callback?code=...` - Callback OAuth (troca código por token)

**GET** `/api/drive/videos` - Lista vídeos no Google Drive

**POST** `/api/drive/upload/{video_path}` - Upload de vídeo local para Drive

**GET** `/api/drive/sync-status` - Status de sincronização (local vs Drive)

**POST** `/api/drive/sync-all` - Sincroniza todos os vídeos locais para Drive

**GET** `/api/drive/stream/{file_id}` - Stream de vídeo do Drive (com range requests)

**GET** `/api/drive/thumbnail/{file_id}` - Thumbnail de vídeo do Drive

**DELETE** `/api/drive/videos/{file_id}` - Remove vídeo do Drive

**Documentação Interativa:** http://localhost:8000/docs

---

## 📁 Estrutura do Projeto

```
yt-archiver/
├── backend/                 # API FastAPI
│   ├── api.py              # API principal com endpoints
│   ├── downloader.py       # Lógica de download (yt-dlp wrapper)
│   ├── drive_manager.py    # Gerenciamento do Google Drive
│   ├── requirements.txt    # Dependências Python
│   ├── run.sh             # Script para iniciar backend com venv
│   ├── .venv/             # Ambiente virtual Python
│   ├── downloads/         # Vídeos baixados (padrão)
│   ├── archive.txt        # Controle de downloads
│   ├── credentials.json   # Credenciais OAuth Google (gitignored)
│   └── token.json         # Token OAuth (gitignored)
│
├── web-ui/                 # Interface Next.js
│   ├── src/
│   │   ├── app/           # App Router (Next.js 15)
│   │   │   ├── page.tsx          # Página principal
│   │   │   ├── drive/page.tsx    # Página Google Drive
│   │   │   ├── layout.tsx        # Layout raiz
│   │   │   └── globals.css       # Estilos globais
│   │   ├── components/    # Componentes React
│   │   │   ├── download-form.tsx       # Formulário de download
│   │   │   ├── video-grid.tsx          # Grid de vídeos locais
│   │   │   ├── video-player.tsx        # Player de vídeo
│   │   │   ├── drive-auth.tsx          # Autenticação Drive
│   │   │   ├── drive-video-grid.tsx    # Grid de vídeos do Drive
│   │   │   ├── sync-panel.tsx          # Painel de sincronização
│   │   │   ├── navigation.tsx          # Navegação entre páginas
│   │   │   └── ui/                     # Componentes shadcn/ui
│   │   └── lib/           # Utilitários
│   │       ├── utils.ts             # Funções helper
│   │       └── url-validator.ts     # Validação de URLs
│   ├── package.json
│   └── next.config.ts
│
├── start-dev.sh           # Script de início rápido (Linux/Mac)
├── start-dev.bat          # Script de início rápido (Windows)
├── CLAUDE.md             # Instruções para Claude Code
├── GOOGLE-DRIVE-SETUP.md # Guia de configuração do Drive
├── GOOGLE-DRIVE-FEATURES.md # Documentação de features do Drive
└── README.md             # Esta documentação
```

---

## 🔧 Tecnologias

### Backend
- **FastAPI** - Framework web assíncrono
- **yt-dlp** - Motor de download de vídeos
- **Uvicorn** - Servidor ASGI
- **Google API Client** - Integração com Google Drive
- **Pydantic** - Validação de dados

### Frontend
- **Next.js 15** - Framework React com App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **shadcn/ui** - Componentes acessíveis (Radix UI)
- **Plyr** - Player de vídeo HTML5
- **Lucide React** - Ícones

### Infraestrutura
- **ffmpeg** - Processamento de vídeo/áudio (requerido)
- **Python 3.12+** - Runtime backend
- **Node.js 18+** - Runtime frontend

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
- Downloads do YouTube são automaticamente registrados por ID de vídeo
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
        └── 2024-01-15 - Título do Vídeo [VIDEO_ID].mp4
        └── 2024-01-15 - Título do Vídeo [VIDEO_ID].jpg
        └── 2024-01-15 - Título do Vídeo [VIDEO_ID].pt-BR.vtt
        └── 2024-01-15 - Título do Vídeo [VIDEO_ID].info.json
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

## 🤝 Contribuindo

Contribuições são bem-vindas!

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

### Áreas de melhoria

- [ ] Suporte a mais plataformas além do YouTube
- [ ] Sistema de filas mais robusto (com prioridades)
- [ ] Testes automatizados (backend e frontend)
- [ ] Docker Compose para deploy simplificado
- [ ] Suporte a múltiplos usuários (autenticação)
- [ ] Compressão automática de vídeos
- [ ] Notificações push quando downloads completam

---

## 📄 Licença

Este projeto é fornecido "como está", sem garantias. Use por sua conta e risco.

**Importante:** Respeite direitos autorais e termos de serviço das plataformas. Este projeto é destinado para arquivamento ético de conteúdo público e educacional.

---

## 📚 Recursos Adicionais

- [Documentação do yt-dlp](https://github.com/yt-dlp/yt-dlp#readme)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Google Drive API](https://developers.google.com/drive/api/guides/about-sdk)

---

**Desenvolvido para arquivamento ético de conteúdo público** 📼✨
