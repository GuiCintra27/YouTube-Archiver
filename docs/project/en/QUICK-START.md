# 🚀 Quick Start - YT-Archiver Web Interface

[PT-BR](../QUICK-START.md) | **EN**

## Test in 3 Steps

### 1️⃣ Install Dependencies

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

### 2️⃣ Start Servers

**Option A - Automatic Script (Recommended)**

```bash
# Linux/Mac
./start-dev.sh

# Windows
start-dev.bat
```

The script:
- install backend dependencies
- install frontend dependencies (if `node_modules` does not exist)
- checks for `ffmpeg` on the system (does not install automatically)

**Option B - Manual**

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

### 3️⃣ Test

1. Open the browser at: **http://localhost:3000**
2. Paste a test URL (example below)
3. Click "Download"
4. See progress in real time!

## 🎬 Test URLs

### YouTube (Public Video)

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### YouTube (Public Playlist)

```
https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
```

### Test with Advanced Options

1. Click on "Advanced Options"
2. Configure:
- **Maximum Resolution**: 720
- **Audio Only**: ON
- **File Name**: "Test Download"
3. Download and see the result!

## 📊 Check API

Open: **http://localhost:8000/docs**

Interactive Swagger interface with all endpoints.

## 📦 Catalog (first run)

If you plan to use Drive or already have local videos:

1. **Index local videos**
- `POST /api/catalog/bootstrap-local`
2. **Drive on new machine (snapshot already exists)**
- `POST /api/catalog/drive/import`
3. **Drive already populated, no snapshot**
- `POST /api/catalog/drive/rebuild`

## 🐛 Quick Troubleshooting

### Backend does not start

```bash
# Check ffmpeg
ffmpeg -version

# If not installed:
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from: https://ffmpeg.org/download.html
```

### Frontend does not connect

Check if the backend is running:
```bash
curl http://localhost:8000/
```

### Port already in use

```bash
# Kill process on port
lsof -ti:8000 | xargs kill -9

# Or change backend port
cd backend
source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## 📸 Interface Preview

```
┌─────────────────────────────────────────────────────────┐
│  YT-Archiver                                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Download videos in a simple way                         │
│  Support for YouTube, playlists and HLS streams         │
│                                                         │
│  ┌───────────────────────────────────┐  ┌──────────┐  │
│  │ https://youtube.com/watch?v=...   │  │  Download  │  │
│  └───────────────────────────────────┘  └──────────┘  │
│                                                         │
│  ▼ Advanced Options                                    │
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

## 🎯 Next Steps

After testing, explore:

1. **Advanced Options** - Custom headers, cookies, etc.
2. **API Docs** - http://localhost:8000/docs
3. **History** - View previous downloads via API
4. **legacy CLI** - removed from current monorepo (use old tags if necessary)

## 📚 Complete Documentation

- [README.md](../../../README.en.md) - Complete project documentation
- [WEB-UI-README.md](../../../frontend/docs/project/WEB-UI-README.md) - Web interface details
- [CLAUDE.md](../../../CLAUDE.md) - Instructions for development

---

**Have fun! 🎉**
