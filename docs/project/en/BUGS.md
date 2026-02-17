# YT-Archiver - Bug Report

[PT-BR](../BUGS.md) | **EN**
**Date**: 2025-11-29 (updated)
**Tested on**: localhost:3000
**Backend**: FastAPI running at http://0.0.0.0:8000
**Frontend**: Next.js 15 running at http://localhost:3000

---

## ✅ BUG #1: Failed to Stream Local Videos - **FIXED**

### Description
Video playback from the local library was failing. When the user clicked on a video, the player opened correctly but was unable to load the media.

### Root Cause
**UnicodeEncodeError** in the HTTP header `Content-Disposition`. The character '⧸' (U+29F8) present in some file names could not be encoded in Latin-1, which is the standard encoding for HTTP headers.

### Implemented Solution
1. **RFC 5987 Encoding**: Changed the format of the `Content-Disposition` header from `filename="..."` to `filename*=UTF-8''...` with percent-encoding
2. **Range Request Support**: Implemented full HTTP 206 Partial Content support for streaming with seek
3. **MIME Type Detection**: Added correct mapping of extensions (.mp4, .webm, .mkv, etc.)
4. **Detailed Logging**: Added debug logs for troubleshooting
5. **Exception Handling**: Code involved in try/except with traceback

### Modified File
- **Backend**: `backend/app/library/router.py` - Function `stream_video()`

### Correction Code
```python
from urllib.parse import quote

# Para FileResponse completa
encoded_filename = quote(full_path.name)
headers = {
    "Accept-Ranges": "bytes",
    "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
}

# Para StreamingResponse com range requests
headers = {
    "Content-Range": f"bytes {start}-{end}/{file_size}",
    "Accept-Ranges": "bytes",
    "Content-Length": str(chunk_size),
    "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
}
```

### Validation Test
✅ Tested with video: `2021-04-26 - John Park - I'm Always by Your Side (tradução⧸legendado) [1_NcRcvXCqo].webm`
- Player loaded correctly
- Video played (duration: 3:48)
- All controls working (play, volume, seek, fullscreen)
- Range requests working (HTTP 206)

---

## ✅ BUG #2: Failed to Upload Videos to Google Drive - **FIXED**

### Description
Uploading individual videos to Google Drive was failing. When the user clicked the sync button for a specific video, the operation failed and displayed an error message.

### Root Cause
**Malformed Google Drive API Query** due to unescaped single quotes (`'`) in file names. The Google Drive API uses single quotes as delimiters in the query (e.g. `name='filename'`), so files with names like "Gibson Les Paul 60's Standard" would break the query.

### Implemented Solution
1. **Single Quote Escape**: Added `escaped_name = name.replace("'", "\\'")` before building queries
2. **Applied in 3 Locations**:
- `upload_video()`: For checking existing file (line 196)
- `upload_video()`: For checking related files (line 268)
- `ensure_folder()`: For checking existing folders (line 142)
3. **Detailed Logging**: Added debug logs showing constructed queries
4. **Exception Handling**: Code involved in try/except with full traceback

### Modified Files
- **Backend**: `backend/app/drive/manager.py`
- `ensure_folder()` method
- `upload_video()` method

### Correction Code
```python
# In upload_video() - line 196
escaped_file_name = file_name.replace("'", "\\'")
query = f"name='{escaped_file_name}' and '{current_parent}' in parents and trashed=false"

# In ensure_folder() - line 142
escaped_name = name.replace("'", "\\'")
query = f"name='{escaped_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"

# In upload_video() for related files - line 268
escaped_related_name = related_file.name.replace("'", "\\'")
query = f"name='{escaped_related_name}' and '{current_parent}' in parents and trashed=false"
```

### Validation Test
✅ Tested with video: `2025-04-24 - The Kind of Solo You Play With Your Eyes Closed ｜ Gibson Les Paul 60's Standard [UJ0_1SYixVQ].mp4`
- Upload completed successfully
- Alert displayed: "Upload completed successfully!"
- File created on Google Drive with ID: `1kQC-ofyeVtPT0sM1JDUUYHX1OkXUu0AV`
- Query escaped correctly: `name='...60\'s Standard...'`
- HTTP 200 OK

---

## ✅ BUG #3: Drive Sync Panel slow / freezing - **FIXED**

### Description
Drive sync panel was slow/stuck when loading.

### Root Cause
- Sync made a complete list of the Drive with each request.
- Blocking IO running in the event loop.

### Implemented Solution
1. **Persistent catalog (SQLite + snapshot)** to avoid direct listings.
2. **Paginated Sync** via `/api/drive/sync-items`.
3. **IO blocking offload** with `core/blocking.py`.

### Modified Files
- `backend/app/drive/service.py`
- `backend/app/drive/router.py`
- `backend/app/catalog/*`
- `frontend/src/components/drive/sync-panel.tsx`

### Validation Test
✅ Dashboard opens instantly with paginated lists.

---

## ✅ BUG #4: Batch download from Drive did not update local catalog - **FIXED**

### Description
Batch downloads completed, but videos did not appear in the local library.

### Root Cause
Batch download did not write through the local catalog.

### Implemented Solution
1. **Write-through after each download** (`upsert_local_video_from_fs`).
2. **Update thumbnails** when they exist.

### Modified File
- `backend/app/drive/service.py`

### Validation Test
✅ Videos appear immediately after batch downloading.

---

## ✅ BUG #5: Native crash when downloading from Drive - **FIXED**

### Description
Occasional error: `double free or corruption (!prev)` during Drive downloads.

### Root Cause
Concurrent use of `googleapiclient` + `MediaIoBaseDownload` + `BytesIO`.

### Implemented Solution
1. **Download via REST + streaming to disk** (without `BytesIO`).
2. **File `.part`** + size validation.

### Modified File
- `backend/app/drive/manager.py`

### Validation Test
✅ Crash-free batch downloads.

---

## ✅ BUG #6: Cleanup job breaking with jobs_db - **FIXED**

### Description
Error in logs: `module 'app.jobs.store' has no attribute 'jobs_db'`.

### Root Cause
Refactor renamed the internal dict, but cleanup still referenced `jobs_db`.

### Implemented Solution
Supported aliases:
- `jobs_db = _jobs_db`
- `active_tasks = _active_tasks`

### Modified File
- `backend/app/jobs/store.py`

### Validation Test
✅ Cleanup loop runs without errors.

---

## Application Status

### ✅ Features Tested and Working
- [x] Backend initialization (FastAPI)
- [x] Frontend initialization (Next.js)
- [x] Local video listing (`GET /api/videos` - 200 OK, returns 72 videos)
- [x] Navigation between pages (Home ↔ Google Drive)
- [x] Google Drive interface (authentication page loads correctly)
- [x] **Download YouTube videos** - Tested successfully
- Tested URL: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- Status: Download completed with 100% progress
- Backend processed request correctly (`POST /api/download` - 200 OK)
- Asynchronous job system working (status polling via `GET /api/jobs/{id}`)
- [x] Loading video thumbnails (all thumbnails loaded correctly)
- [x] Real-time progress system for downloads
- [x] **Google Drive OAuth Authentication** ✅
- Complete authentication flow working
- Token stored correctly
- Authentication status verified successfully
- [x] **Google Drive video listing** ✅
- Endpoint `GET /api/drive/videos` returning 3 videos
- Drive thumbnails loading correctly
- [x] **Sync Status** ✅
- Endpoint `GET /api/drive/sync-status` working
- Correctly showing: 72 Local, 3 Drive, 3 Synchronized
- Progress calculation (4%) correct
- [x] **Streaming videos from Google Drive** ✅
- Endpoint `GET /api/drive/stream/{file_id}` working perfectly
- Video played successfully (duration 05:48)
- Range requests working (206 Partial Content)
- Vidstack Player working correctly with Drive videos
- [x] **Local video playback** ✅ **[FIXED]**
- Endpoint `GET /api/videos/stream/{video_path}` working perfectly
- Fix: RFC 5987 encoding for Content-Disposition header
- Full support for range requests (HTTP 206)
- Tested with special characters (⧸, accents, etc.)
- [x] **Individual video upload to Google Drive** ✅ **[FIXED]**
- Endpoint `POST /api/drive/upload/{video_path}` working
- Fix: Escape single quotes in Google Drive queries
- Tested with complex names (|, ', accents)
- Upload of related files working (thumbnails, metadata, subtitles)
- [x] **Drive Sync Panel** ✅ **[FIXED]**
- Status and paginated items working
- No loading locks
- [x] **Batch Download from Drive** ✅ **[FIXED]**
- Local catalog updated after each download

### ❌ Problematic Features
*No critical bugs identified at this time*

### ⏳ Pending Test Features
- [x] Batch upload ("Sync All")
- [ ] Deleting local videos
- [x] Deleting videos from Google Drive
- [ ] Download complete playlists
- [ ] Advanced download options (quality, format, subtitles)

---

## Additional Notes
- **Browser Console**: Only accessibility warnings (DialogContent without Description)
- **Backend Logs**: ✅ All 500 errors fixed
1. ~~Local video streaming (BUG #1)~~ → **FIXED** (RFC 5987 encoding)
2. ~~Individual upload to Google Drive (BUG #2)~~ → **FIXED** (Query escaping)
- **Performance**: Responsive interface, thumbnails (local and Drive) load quickly
- **UI/UX**: Application is functional and visually correct
- **Total videos**: 72 local videos, 4 Drive videos (1 new upload tested)
- **Job System**: Working correctly with automatic polling and progress update
- **Google Drive Integration**: ✅ 100% functional
- OAuth working perfectly
- Drive streaming working
- Working Drive listing and thumbnails
- Individual upload working (fixed)
- Supports special characters in file names
