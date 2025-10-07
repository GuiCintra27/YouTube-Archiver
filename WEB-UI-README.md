# YT-Archiver - Interface Web 2.0

Interface web moderna para o YT-Archiver, permitindo downloads de vídeos de forma visual e intuitiva.

## 🎨 Arquitetura

```
yt-archiver/
├── backend/              # API FastAPI
│   ├── api.py           # Endpoints REST
│   ├── downloader.py    # Lógica de download
│   └── requirements.txt
├── web-ui/              # Frontend Next.js
│   ├── src/
│   │   ├── app/        # Páginas Next.js
│   │   ├── components/ # Componentes React
│   │   └── lib/        # Utilitários
│   └── package.json
└── python/              # Script CLI original
    └── main.py
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
cd web-ui
npm install
```

### 3. Executar (Desenvolvimento)

**Terminal 1 - Backend:**
```bash
cd backend
source .venv/bin/activate
python api.py
# API rodando em http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd web-ui
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
  "out_dir": "./downloads",
  "max_res": 1080,
  "subs": true,
  "audio_only": false
}
```

**Response:**
```json
{
  "status": "success",
  "job_id": "uuid-here",
  "message": "Download iniciado"
}
```

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

- [x] Interface web moderna com Next.js 15
- [x] Componentes UI com shadcn/ui
- [x] Download de vídeos e playlists
- [x] Barra de progresso em tempo real
- [x] Configurações avançadas (headers, cookies, qualidade)
- [x] API REST com FastAPI
- [x] Sistema de jobs para gerenciar downloads
- [x] Feedback visual de sucesso/erro
- [x] Nomenclatura customizada de arquivos
- [x] Suporte a streams HLS

### 🔜 Futuras Melhorias

- [ ] Upload automático para Google Drive via interface
- [ ] Histórico de downloads persistente
- [ ] Fila de downloads
- [ ] Cancelamento de downloads
- [ ] Dark mode toggle
- [ ] Preview de vídeo antes de baixar
- [ ] Download de múltiplas URLs simultâneas
- [ ] Agendamento de downloads
- [ ] Notificações por email quando concluir

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

### Estrutura de Componentes

```
src/
├── app/
│   ├── layout.tsx       # Layout principal
│   ├── page.tsx         # Página inicial
│   └── globals.css      # Estilos globais
├── components/
│   ├── download-form.tsx  # Formulário principal
│   └── ui/               # Componentes shadcn/ui
└── lib/
    └── utils.ts          # Funções utilitárias
```

### Adicionar Novos Componentes shadcn/ui

```bash
cd web-ui
npx shadcn@latest add [component-name]
```

Exemplo:
```bash
npx shadcn@latest add dialog
npx shadcn@latest add table
```

---

## 🐳 Deploy com Docker

### Backend

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY python/ ./python/

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY web-ui/package*.json ./
RUN npm ci

COPY web-ui/ ./
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
version: '3.8'

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
      dockerfile: web-ui/Dockerfile
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
2. Verificar arquivo `.env.local` na raiz de `web-ui/`
3. Verificar CORS no backend (já configurado para localhost:3000)

### Erro "Module not found"

```bash
cd web-ui
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
python api.py
# Logs aparecem no terminal
```

### Logs do Frontend

```bash
cd web-ui
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
