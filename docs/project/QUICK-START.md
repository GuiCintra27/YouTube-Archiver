# 🚀 Quick Start - YT-Archiver Web Interface

## Teste em 3 Passos

### 1️⃣ Instalar Dependências

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Frontend
cd frontend
npm install
cd ..
```

### 2️⃣ Iniciar Servidores

**Opção A - Script Automático (Recomendado)**

```bash
# Linux/Mac
./start-dev.sh

# Windows
start-dev.bat
```

**Opção B - Manual**

Terminal 1:
```bash
cd backend
./run.sh
# Ou: source .venv/bin/activate && uvicorn app.main:app --reload
```

Terminal 2:
```bash
cd frontend
npm run dev
```

### 3️⃣ Testar

1. Abra o navegador em: **http://localhost:3000**
2. Cole uma URL de teste (exemplo abaixo)
3. Clique em "Baixar"
4. Veja o progresso em tempo real!

## 🎬 URLs de Teste

### YouTube (Vídeo Público)

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### YouTube (Playlist Pública)

```
https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
```

### Testar com Opções Avançadas

1. Clique em "Opções Avançadas"
2. Configure:
   - **Resolução Máxima**: 720
   - **Apenas Áudio**: ON
   - **Nome do Arquivo**: "Teste Download"
3. Baixe e veja o resultado!

## 📊 Verificar API

Abra: **http://localhost:8000/docs**

Interface Swagger interativa com todos os endpoints.

## 🐛 Troubleshooting Rápido

### Backend não inicia

```bash
# Verificar ffmpeg
ffmpeg -version

# Se não instalado:
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Baixar de: https://ffmpeg.org/download.html
```

### Frontend não conecta

Verificar se o backend está rodando:
```bash
curl http://localhost:8000/
```

### Porta já em uso

```bash
# Matar processo na porta
lsof -ti:8000 | xargs kill -9

# Ou mudar porta do backend
cd backend
source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## 📸 Interface Preview

```
┌─────────────────────────────────────────────────────────┐
│  YT-Archiver                                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Baixe vídeos de forma simples                         │
│  Suporte para YouTube, playlists e streams HLS         │
│                                                         │
│  ┌───────────────────────────────────┐  ┌──────────┐  │
│  │ https://youtube.com/watch?v=...   │  │  Baixar  │  │
│  └───────────────────────────────────┘  └──────────┘  │
│                                                         │
│  ▼ Opções Avançadas                                    │
│                                                         │
│  ╔═══════════════════════════════════════════════════╗ │
│  ║ Baixando...                              45%      ║ │
│  ║ ████████████████░░░░░░░░░░░░░░░░░░░░░░░░         ║ │
│  ║                                                   ║ │
│  ║ Arquivo: video.mp4                                ║ │
│  ║ Tamanho: 45 MB / 100 MB                           ║ │
│  ║ Velocidade: 2.5 MB/s                              ║ │
│  ║ Tempo Restante: 22s                               ║ │
│  ╚═══════════════════════════════════════════════════╝ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Próximos Passos

Após testar, explore:

1. **Opções Avançadas** - Headers customizados, cookies, etc
2. **API Docs** - http://localhost:8000/docs
3. **Histórico** - Ver downloads anteriores via API
4. **CLI Original** - `python python/main.py --help`

## 📚 Documentação Completa

- [README.md](./README.md) - Documentação completa do projeto
- [WEB-UI-README.md](./WEB-UI-README.md) - Detalhes da interface web
- [CLAUDE.md](./CLAUDE.md) - Instruções para desenvolvimento

---

**Divirta-se! 🎉**
