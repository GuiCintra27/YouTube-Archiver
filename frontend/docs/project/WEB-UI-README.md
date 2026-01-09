# YT-Archiver - Interface Web 2.0

Interface web moderna para o YT-Archiver, permitindo downloads de vídeos de forma visual e intuitiva.

## 🎨 Arquitetura

```
yt-archiver/
├── backend/              # API FastAPI
│   ├── app/             # Código da API
│   └── requirements.txt
├── frontend/             # Frontend Next.js 15
│   ├── src/
│   │   ├── app/         # Páginas (App Router)
│   │   ├── components/  # Componentes React
│   │   └── lib/         # Utilitários
│   └── package.json
└── docs/                 # Documentação oficial
```

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.12+
- Node.js 18+
- ffmpeg instalado

### 1. Instalar Backend (API)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Instalar Frontend

```bash
cd frontend
npm install
```

### 3. Executar (Desenvolvimento)

**Atalho (recomendado):**

```bash
./start-dev.sh
```

**Terminal 1 - Backend:**

```bash
cd backend
./run.sh
# API rodando em http://localhost:8000
```

**Terminal 2 - Frontend:**

```bash
cd frontend
npm run dev
# Interface em http://localhost:3000
```

### 4. Acessar Interface

Abra o navegador em: **http://localhost:3000**

---

## 📖 Guia de Uso

### Download Básico

1. Cole a URL do vídeo/playlist no campo principal
2. Clique em **Baixar**
3. Acompanhe o progresso em tempo real

### Biblioteca, Drive e Gravação

- **Biblioteca (`/library`)**: lista vídeos locais com edição, thumbnail e player.
- **Drive (`/drive`)**: upload/sync local↔Drive, compartilhamento e upload externo com thumbnail customizada.
- **Gravar (`/record`)**: grava a tela e salva direto na biblioteca (ou baixa no navegador).

### Opções Avançadas

Clique em "Opções Avançadas" para configurar:

- **Diretório de Saída**: Onde os arquivos serão salvos
- **Resolução Máxima**: Limitar qualidade (ex: 1080)
- **Subpasta Personalizada**: Organizar por curso/módulo
- **Nome do Arquivo**: Nome customizado
- **Headers**: Referer, Origin (para streams HLS)
- **Arquivo de Cookies**: Para conteúdo que requer login
- **Legendas**: Ativar/desativar legendas e legendas automáticas
- **Miniaturas**: Baixar thumbnails
- **Apenas Áudio**: Extrair MP3

---

## 🔌 API Endpoints

### `POST /api/download`

Inicia um novo download.

**Request:**

```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "max_res": 1080,
  "subs": true,
  "audio_only": false
}
```

**Nota:** o diretório de saída é fixo e usa o padrão configurado no backend (`DOWNLOADS_DIR`).

**Response:**

```json
{
  "status": "success",
  "job_id": "uuid-here",
  "message": "Download iniciado"
}
```

**Notas:**

- Diretório de saída é fixo e usa `DOWNLOADS_DIR` do backend.
- Arquivos são salvos como `Uploader/Playlist/Titulo.ext` (sem data/ID).
- Se o nome já existir, o download falha sem sobrescrever.

### `GET /api/jobs/{job_id}`

Obtém status de um download.

**Response:**

```json
{
  "job_id": "uuid",
  "status": "downloading",
  "progress": {
    "percentage": 45.2,
    "speed": 1048576,
    "eta": 120
  }
}
```

### `GET /api/jobs`

Lista todos os downloads.

### `GET /api/video-info`

Obtém informações sobre um vídeo sem baixar.

**Request:**

```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

**Response:**

```json
{
  "status": "success",
  "type": "video",
  "title": "Título do Vídeo",
  "uploader": "Nome do Canal",
  "duration": 360
}
```

---

## 🎯 Funcionalidades

### ✅ Implementadas

- [x] Next.js 15 com SSR + cache por tags
- [x] Biblioteca local com edição, thumbnails e player Vidstack
- [x] Google Drive com sync, upload em lote e compartilhamento público
- [x] Upload externo com thumbnail, legendas e transcrição
- [x] Gravação de tela no navegador com salvamento na biblioteca
- [x] Global Player com Picture-in-Picture
- [x] Jobs em background com progresso em tempo real
- [x] UI moderna com shadcn/ui + Tailwind

### 🔜 Futuras Melhorias

- [ ] Notificações de conclusão (desktop)
- [ ] Fila persistente de downloads

---

## 🛠️ Desenvolvimento

### Tecnologias

**Backend:**

- FastAPI - Framework web assíncrono
- yt-dlp - Motor de download
- Uvicorn - Servidor ASGI

**Frontend:**

- Next.js 15 - Framework React
- TypeScript - Tipagem estática
- Tailwind CSS - Estilização
- shadcn/ui - Componentes
- Lucide React - Ícones

### Rotas e Endpoints Centralizados

- Prefira os enums já disponíveis a strings literais:
  - `frontend/src/lib/paths.ts` → `PATHS` para caminhos de páginas (`/`, `/drive`, `/record`, `/library`).
  - `frontend/src/lib/api-urls.ts` → `APIURLS` para paths de API (`download`, `jobs`, `drive/auth-status`, etc.).
- Motivos: evita typos, facilita refactors e mantém URLs coerentes entre chamadas e navegação.

### SSR + Cache (App Router)

- Páginas principais usam Server Components com dados iniciais:
  - `/library`, `/drive`, `/record` e `/` (recentes).
- Fetch server-side com cache nativo do Next:
  - `frontend/src/lib/server/api.ts`
  - tags em `frontend/src/lib/server/tags.ts`
- Mutações passam por Route Handlers do Next (BFF) com invalidacao de tags:
  - `frontend/src/app/api/*`
  - helper: `frontend/src/lib/server/route-utils.ts`

### Client API Unificado

- Operacoes de mutacao no client usam um wrapper unico:
  - `frontend/src/lib/client/api.ts`
- Evita repeticao de fetch e padroniza erros.

### Estrutura de Componentes

```
src/
├── app/
│   ├── layout.tsx       # Layout principal
│   ├── page.tsx         # Página inicial
│   ├── drive/page.tsx   # Página Drive
│   ├── library/page.tsx # Biblioteca
│   ├── record/page.tsx  # Gravação de tela
│   └── globals.css      # Estilos globais
├── components/
│   ├── common/            # Componentes compartilhados
│   ├── drive/             # Drive (auth, grid, sync, upload externo)
│   ├── home/              # Home (download form)
│   ├── library/           # Biblioteca (grid paginado)
│   ├── record/            # Gravação de tela
│   └── ui/                # Componentes shadcn/ui
└── lib/
    ├── api-urls.ts        # Endpoints da API
    ├── paths.ts           # Rotas do app
    ├── client/api.ts      # Cliente HTTP (frontend)
    ├── server/api.ts      # Fetch SSR + cache tags
    ├── server/tags.ts     # Tags de cache
    └── utils.ts           # Funções utilitárias
```

### Adicionar Novos Componentes shadcn/ui

```bash
cd frontend
npx shadcn@latest add [component-name]
```

Exemplo:

```bash
npx shadcn@latest add dialog
npx shadcn@latest add table
```

---

## 🐳 Deploy com Docker

**Nota:** os exemplos abaixo são templates e podem exigir ajuste (Dockerfiles não estão incluídos por padrão).

### Backend

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM node:18-alpine

WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
```

### Docker Compose

```yaml
version: "3.8"

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./downloads:/app/downloads
      - ./cookies.txt:/app/cookies.txt
    environment:
      - PYTHONUNBUFFERED=1

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
```

---

## 🔧 Troubleshooting

### Backend não inicia

```bash
# Verificar se todas as dependências estão instaladas
cd backend
pip install -r requirements.txt

# Verificar se o Python path está correto
python -c "import sys; print(sys.path)"
```

### Frontend não conecta ao backend

1. Verificar se o backend está rodando em `http://localhost:8000`
2. Verificar arquivo `.env.local` na raiz de `frontend/` (use `frontend/.env.example` como base)
3. Verificar CORS no backend (já configurado para localhost:3000)

### Erro "Module not found"

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Download não inicia

1. Verificar logs do backend
2. Verificar se ffmpeg está instalado: `ffmpeg -version`
3. Verificar permissões da pasta de downloads

---

## 📊 Monitoramento

### Logs do Backend

```bash
cd backend
./run.sh
# Logs aparecem no terminal
```

### Logs do Frontend

```bash
cd frontend
npm run dev
# Abrir DevTools do navegador (F12) > Console
```

### API Docs (Swagger)

Acesse: **http://localhost:8000/docs**

Interface interativa para testar todos os endpoints.

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto é fornecido "como está", sem garantias. Use por sua conta e risco, respeitando os direitos autorais e termos de serviço das plataformas de origem.

---

**Desenvolvido para arquivamento ético de conteúdo público** 🎥
