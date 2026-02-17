# 🚀 New Feature: Integration with Google Drive

[PT-BR](../GOOGLE-DRIVE-FEATURES.md) | **EN**

## ✨ What was implemented

### Backend (API)

1. **DriveManager (`backend/app/drive/manager.py`)**
- Complete Google Drive management
- OAuth 2.0 authentication
- Upload videos while maintaining folder structure
- Video listing in Drive
- Local <-> Drive Sync
- Removal of videos from Drive (includes related files + background folder cleaning)

2. **New API endpoints:**
- `GET /api/drive/auth-status` - Check authentication
- `GET /api/drive/auth-url` - Get OAuth authentication URL
- `GET /api/drive/oauth2callback` - OAuth Callback
- `GET /api/drive/videos` - List videos in Drive
- `POST /api/drive/upload/{path}` - Individual video upload
- `POST /api/drive/upload-external` - External upload (video + thumbnail + extras)
- `GET /api/drive/sync-status` - Sync status
- `GET /api/drive/sync-items` - Paged items (local_only/drive_only/synced)
- `POST /api/drive/sync-all` - Sync all videos
- `DELETE /api/drive/videos/{id}` - Remove video from Drive (returns cleanup_job_id)
- `POST /api/drive/videos/delete-batch` - Delete multiple videos in batch
- `GET /api/drive/videos/{id}/share` - Public sharing status
- `POST /api/drive/videos/{id}/share` - Enable public sharing link
- `DELETE /api/drive/videos/{id}/share` - Revoke public sharing
- `GET /api/drive/custom-thumbnail/{id}` - Custom thumbnail
- `POST /api/drive/download` - Download video to location (by path or file_id)
- `POST /api/drive/download-all` - Batch download (Drive -> local)
- `PATCH /api/drive/videos/{id}/rename` - Rename video in Drive
- `POST /api/drive/videos/{id}/thumbnail` - Update thumbnail in Drive

3. **SQLite cache for metadata (v2.4)**
- `POST /api/drive/cache/sync` - manual synchronization (`?full=true` for rebuild)
- `GET /api/drive/cache/stats` - Cache statistics
- `POST /api/drive/cache/rebuild` - complete rebuild
- `DELETE /api/drive/cache` - Clear cache

### Frontend (Web Interface)

1. **New page `/drive`**
- View videos from Google Drive
- Interface similar to the local page
- Video management in Drive

2. **Component `DriveAuth`**
- OAuth authentication screen
- Popup for Google login
- Validation of credentials

3. **Component `SyncPanel`**
- Location <-> Drive sync panel
- Statistics (Local, Drive, Synced)
- Visual progress bar
- Individual or batch upload
- Detailed listing:
- Local only videos (with upload button)
- Videos only in Drive
- Synchronized videos

4. **Component `DriveVideoGrid`**
- Drive video grid (3 columns, YouTube style)
- Automatic thumbnails with zoom effect on hover
- Size and duration information
- Detailed video information modal
- Multiple selection with checkboxes
- Individual or batch deletion
- Video editing (rename and update thumbnail)
- Public sharing (link with activation toggle)
- Unified VideoCard component (same as used in local library)

5. **Component `ExternalUploadModal`**
- Upload external video directly to Drive
- Custom thumbnail (JPG/PNG/WebP)
- Optional subtitles and transcription

5. **Component `Navigation`**
- Location/Drive navigation menu
- Intuitive icons
- Active page indicator

## ⚡ SQLite Cache for Performance (v2.4)

### What is it?

Local cache system that stores Google Drive video metadata in SQLite,
eliminating the need for Drive API calls for each listing.

**Note:** Persistent catalog (snapshot + SQLite) is the current main stream.
The cache remains an option/legacy for specific scenarios.

### Performance Gains

| Operation | Before (API) | After (Cache) | Improvement |
|----------|-------------|----------------|----------|
| List 100 videos | ~2-3s | ~50-100ms | **~20-30x** |
| List 500 videos | ~8-10s | ~100-200ms | **~40-50x** |
| Pagination | ~1-2s/page | ~20-50ms | **~30-40x** |

### How does it work?

1. **First time authentication**: Automatic full sync populates cache
2. **Video listing**: Local SQLite search (~50ms)
3. **Every 30 minutes**: Incremental sync detects changes in Drive
4. **Upload/Delete/Rename**: immediate update in cache (real-time synchronization)
5. **Cache Error**: Automatic fallback to Drive API

### Settings (.env)

```bash
DRIVE_CACHE_ENABLED=true           # Habilitar cache (padrão: true)
DRIVE_CACHE_DB_PATH=./drive_cache.db  # Caminho do banco
DRIVE_CACHE_SYNC_INTERVAL=30       # Intervalo em minutos
DRIVE_CACHE_FALLBACK_TO_API=true   # alternativa se cache falhar
```

### Management Endpoints

```bash
# manual sync (incremental)
curl -X POST http://localhost:8000/api/drive/cache/sync

# Full rebuild
curl -X POST "http://localhost:8000/api/drive/cache/sync?full=true"

# View stats
curl http://localhost:8000/api/drive/cache/stats

# Limpar cache
curl -X DELETE http://localhost:8000/api/drive/cache
```

---

## 📦 Drive Catalog (Snapshot + SQLite)

In addition to caching, Drive now uses a **persistent catalog**:
- Local SQLite (`backend/database.db`)
- Snapshot versioned in Drive (`catalog-drive.json.gz`)

### First use / New machine

1) **Import existing snapshot**
```
POST /api/catalog/drive/import
```

2) **Initial rebuild (Drive already populated, without snapshot)**
```
POST /api/catalog/drive/rebuild
```

3) **Index local videos**
```
POST /api/catalog/bootstrap-local
```

### Catalog endpoints

- `GET /api/catalog/status`
- `POST /api/catalog/bootstrap-local`
- `POST /api/catalog/drive/import`
- `POST /api/catalog/drive/publish`
- `POST /api/catalog/drive/rebuild`

## 📁 Created File Structure

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
│       └── page.tsx             # Drive page
└── components/
    ├── common/navigation.tsx    # Menu Local / Drive
    └── drive/                   # Componentes do Drive
        ├── drive-auth.tsx       # Autenticação
        ├── drive-video-grid.tsx # Drive videos grid
        └── sync-panel.tsx       # Sync panel

docs/
├── GOOGLE-DRIVE-SETUP.md      # Guia completo de setup
└── GOOGLE-DRIVE-FEATURES.md   # This file
```

## 🎯 How to Use

### 1. Configure Google Drive

Follow the guide: [GOOGLE-DRIVE-SETUP.md](./GOOGLE-DRIVE-SETUP.md)

**Summary:**
1. Create project in Google Cloud Console
2. Activate Google Drive API
3. Create OAuth 2.0 credentials
4. Download `credentials.json` → `backend/credentials.json`

### 2. Access Interface

```bash
# Terminal 1 - Backend
cd backend
./run.sh

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Visit: http://localhost:3000

### 3. Usage Flow

1. **Local Page (/):**
- Download videos normally
- View local library
- Play videos locally

2. **Drive Page (/drive):**
- Click on "Connect with Google Drive"
- Authorize on Google (popup)
- See sync status
- Upload individual or all videos
- View and manage videos in Drive

## 📊 Detailed Features

### Smart Sync

The system automatically compares:

- **Local Only**: Videos that only exist locally
- Individual upload button
- Button to sync all at once

- **Drive Only**: Videos that only exist in Drive
- Informative (does not allow automatic download)

- **Synced**: Videos in both locations
- Visual indicator ✓

### Drive Structure

```
Google Drive/
└── YouTube Archiver/          # Pasta raiz (automática)
    └── [sua estrutura local]  # Espelhada automaticamente
```

Example:
```
downloads/
├── Canal A/
│   └── Video 1.mp4
└── Canal B/
    └── Playlist/
        └── Video 2.mp4
```

Turn:
```
Google Drive/YouTube Archiver/
├── Canal A/
│   └── Video 1.mp4
└── Canal B/
    └── Playlist/
        └── Video 2.mp4
```

## 🔐 Security

### Sensitive Files

**DO NOT commit:**
- ❌ `backend/credentials.json` - OAuth Credentials
- ❌ `backend/token.json` - Access token
- ❌ `backend/uploaded.jsonl` - Upload log

Everyone is already on `.gitignore`!

### OAuth 2.0

- Secure authentication via Google
- Tokens with automatic renewal
- Current scope: `drive` (required to manage sharing permissions)

## 🐛 Troubleshooting

### "Credentials file not found"

```bash
# Make sure you have:
ls backend/credentials.json

# If it does not exist, follow GOOGLE-DRIVE-SETUP.md
```

### "redirect_uri_mismatch"

In the Google Cloud Console:
1. Edit your OAuth Client ID
2. Add: `http://localhost:8000/api/drive/oauth2callback`

### "Access blocked"

In the Google Cloud Console:
1. Go to "OAuth Consent Screen"
2. Add your email in "Test users"

### Expired token

```bash
# Delete e reautentique:
rm backend/token.json
# Depois vá em /drive e conecte novamente
```

## 📈 Possible Upcoming Improvements

- [x] Download videos from Drive to local ✅ (v2.2)
- [x] Batch Deleting Videos from Drive ✅ (v2.3)
- [x] YouTube style cards with duration and modal info ✅ (v2.3)
- [x] SQLite cache for lightning-fast listing ✅ (v2.4)
- [ ] Automatic two-way sync
- [ ] Version conflicts
- [ ] Progress bar during large uploads
- [ ] Compression before upload
- [x] Drive Link Sharing ✅ (v2.4.x)
- [ ] Scheduled automatic backup

## 🎉 Conclusion

Now you have:
- ✅ View local and Drive videos (YouTube style cards)
- ✅ Manual or automatic upload
- ✅ Download videos from Drive to local
- ✅ Real-time sync status
- ✅ Complete management via web interface
- ✅ Multiple selection and batch deletion
- ✅ Detailed video information modal
- ✅ OAuth 2.0 secure authentication
- ✅ **SQLite cache for lightning-fast listing** (~20-50x faster)

**Enjoy!** 🚀
