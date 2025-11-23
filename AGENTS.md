# AGENTS.md — YT-Archiver

> README for AI Coding Agents: Context and instructions for working on this project.

## 🎯 Project Overview

**YT-Archiver** is a complete YouTube video download and archival system with modern web interface and Google Drive integration.

- **Version**: 2.0.0
- **Stack**: FastAPI (backend) + Next.js 15 (frontend) + yt-dlp (download engine)
- **Architecture**: Monorepo with separate backend (Python) and frontend (TypeScript)

## 📦 Setup Commands

### First-time setup (Complete)
```bash
# Quick start (recommended)
./start-dev.sh

# Or manually:
# Backend setup
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd frontend
npm install

# Root setup (for Commitizen)
npm install
```

### Development servers
```bash
# Backend (FastAPI) - Port 8000
cd backend && ./run.sh

# Frontend (Next.js) - Port 3000
cd frontend && npm run dev

# Both at once
./start-dev.sh
```

### Testing endpoints
```bash
# Health check
curl http://localhost:8000/

# List local videos
curl http://localhost:8000/api/videos

# Check Drive auth
curl http://localhost:8000/api/drive/auth-status
```

## 💻 Code Style

### Python (Backend)
- **Standard**: PEP8 where applicable, prioritize stability over aggressive refactoring
- **Typing**: Light typing, use Pydantic for data validation
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Async**: Use threading for download jobs (NOT async/await for yt-dlp)
- **Logging**: Debug with `print(f"[DEBUG] ...")` and `print(f"[ERROR] ...")`
- **Error handling**: Always use try/except with full traceback + HTTPException with clear messages

**Example endpoint pattern:**
```python
@app.post("/api/endpoint")
async def endpoint_name(request: RequestModel) -> ResponseModel:
    """Endpoint description (appears in /docs)"""
    try:
        # Business logic
        return ResponseModel(data=result)
    except Exception as e:
        import traceback
        print(f"[ERROR] {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
```

### TypeScript/React (Frontend)
- **Components**: Function as default export
- **Hooks**: Prefer modern hooks (useState, useEffect)
- **Styling**: Tailwind utility-first + shadcn/ui components
- **State**: useState for local state, NO Redux/Zustand
- **Fetch**: Use native fetch, no additional libraries
- **Types**: Strict type safety, avoid `any`
- **Naming**: `camelCase` for functions/variables, `PascalCase` for components/types
- **Files**: `kebab-case.tsx` for components, `kebab-case.py` for modules

**Example component pattern:**
```typescript
"use client";

import { useState, useEffect } from "react";

export default function ComponentName() {
  const [state, setState] = useState<Type>(initialValue);

  useEffect(() => {
    // Side effects
  }, [dependencies]);

  const handleAction = async () => {
    try {
      const response = await fetch("/api/endpoint");
      const data = await response.json();
      setState(data);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return <div className="tailwind-classes">{/* JSX */}</div>;
}
```

## 🧪 Testing Instructions

### Manual testing
```bash
# Backend API tests
curl http://localhost:8000/
curl http://localhost:8000/api/videos
curl http://localhost:8000/api/drive/auth-status

# Kill stuck processes
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend
```

### Running the app
```bash
# Start backend
cd backend && ./run.sh

# Start frontend
cd frontend && npm run dev

# Access application
open http://localhost:3000
```

## 🏗️ Project Structure

```
yt-archiver/
├── backend/                     # FastAPI Python backend
│   ├── api.py                  # Main API endpoints
│   ├── downloader.py           # yt-dlp wrapper
│   ├── drive_manager.py        # Google Drive integration
│   ├── requirements.txt
│   ├── run.sh                  # ALWAYS use this to start backend
│   └── docs/project/           # Backend-specific docs
│       ├── ANTI-BAN.md
│       ├── EXPORT-COOKIES-GUIDE.md
│       └── PERFORMANCE-OPTIMIZATION.md
├── frontend/                    # Next.js 15 frontend
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   ├── components/        # React components
│   │   └── lib/               # Utilities
│   ├── package.json
│   └── docs/project/          # Frontend-specific docs
│       └── WEB-UI-README.md
├── docs/project/               # General project docs
│   ├── BUGS.md
│   ├── TECHNICAL-REFERENCE.md
│   ├── GOOGLE-DRIVE-SETUP.md
│   └── ...
├── CLAUDE.md                   # Instructions for Claude Code
├── AGENTS.md                   # This file (for AI agents)
├── README.md                   # Main documentation
└── package.json                # Root package.json (Commitizen)
```

## 🔐 Security Considerations

### Files that must NEVER be committed:
- `backend/credentials.json` - Google OAuth credentials
- `backend/token.json` - Google OAuth token
- `backend/cookies.txt` - User cookies
- `backend/uploaded.jsonl` - Upload logs

All are in `.gitignore` - verify before commits.

### DRM and Legal
- **DO NOT** support DRM-protected content (Widevine, FairPlay, PlayReady)
- Only non-encrypted streams (HLS without DRM, public YouTube)
- Respect copyright and terms of service

### Rate Limiting
- **DO NOT** remove rate limiting controls (risk of ban)
- **DO NOT** encourage massive downloads without delays
- Keep presets: "Safe", "Moderate", "Fast"

## ⚠️ Critical Gotchas

### Backend (Python)
1. **ALWAYS use `./run.sh`** to start backend
   - ❌ NOT: `python api.py` (doesn't activate venv)
   - ✅ YES: `./run.sh` (activates venv automatically)

2. **Unicode/Encoding**
   - Always use RFC 5987 for HTTP headers with Unicode
   - Format: `filename*=UTF-8''{quote(filename)}`
   - Import `quote` from `urllib.parse`

3. **Google Drive queries**
   - ALWAYS escape single quotes: `name.replace("'", "\\'")`
   - Queries use single quotes as delimiters
   - Apply in: file/folder checks and uploads

4. **Range Requests**
   - Video player requires HTTP 206 Partial Content support
   - Implemented for both local and Drive streaming
   - Use `StreamingResponse` with 8KB chunks

### Frontend (TypeScript)
1. **Next.js 15 App Router**
   - Use `"use client"` for interactive components
   - Server Components by default
   - `suppressHydrationWarning` needed for dynamic themes

2. **Plyr CSS**
   - Import in `layout.tsx`: `import "plyr-react/plyr.css"`
   - Required for correct player styles

3. **API Calls**
   - Backend at `http://localhost:8000`
   - Use absolute paths: `/api/videos` NOT `api/videos`
   - Job polling every 1 second during downloads

4. **shadcn/ui**
   - Components installed on-demand in `components/ui/`
   - Use Radix UI primitives via shadcn CLI
   - Don't modify files in `components/ui/` directly

## 🛠️ Common Development Tasks

### Adding a new download option
1. Add field in `frontend/src/components/download-form.tsx`
2. Add parameter in Pydantic model at `backend/api.py` (class `DownloadRequest`)
3. Pass parameter to `Settings` in `backend/downloader.py`
4. Implement logic in `_base_opts()` of `Downloader`

### Adding a shadcn/ui component
```bash
cd frontend
npx shadcn@latest add <component-name>
# Example: npx shadcn@latest add dialog
```

### Fixing Unicode/encoding bugs
- Verify HTTP headers use RFC 5987 (`filename*=UTF-8''...`)
- Use `urllib.parse.quote()` for percent-encoding
- Apply to `Content-Disposition`, `Content-Type`, etc.

### Improving streaming performance
- Adjust chunk size in `MediaFileUpload` (default: 8MB)
- Verify range requests are implemented
- Consider thumbnail caching

## 📝 Git Workflow (Commitizen)

### Making commits
```bash
# Setup (first time)
npm install

# Create conventional commits
npm run commit       # Option 1 (recommended)
npx cz              # Option 2
git cz              # Option 3 (if installed globally)
```

**Commit types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic changes)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Tests
- `chore`: Build tasks, configs

## 📚 Quick Reference

### URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Key Files
- `backend/api.py:1-700` - All REST endpoints
- `backend/downloader.py:1-300` - yt-dlp wrapper
- `backend/drive_manager.py:1-430` - Google Drive manager
- `frontend/src/app/page.tsx` - Main page
- `frontend/src/app/drive/page.tsx` - Drive page
- `frontend/src/components/video-grid.tsx` - Local video player
- `CLAUDE.md` - Detailed instructions for Claude
- `README.md` - Complete project documentation

### Documentation
- **General docs**: `docs/project/`
- **Backend docs**: `backend/docs/project/`
- **Frontend docs**: `frontend/docs/project/`
- **Technical reference**: `docs/project/TECHNICAL-REFERENCE.md`
- **Bug tracking**: `docs/project/BUGS.md`

## 🚀 Best Practices

### When modifying backend:
✅ Always test with venv activated (`./run.sh`)
✅ Add try/except with traceback in critical endpoints
✅ Validate input with Pydantic
✅ Document endpoint in docstring (appears in `/docs`)
✅ Test with special characters (accents, symbols, emojis)

### When modifying frontend:
✅ Use shadcn/ui components when available
✅ Keep Tailwind utility-first (avoid custom CSS)
✅ Strict type safety (no `any`)
✅ Test responsiveness (desktop + mobile)
✅ Accessibility (aria-labels, roles, etc.)

### When adding features:
✅ Check if similar exists in yt-dlp
✅ Document in README.md
✅ Add usage examples
✅ Test edge cases (invalid URLs, network errors, etc.)
✅ Consider impact on Google Drive (sync)

---

**Last Updated**: 2025-11-22
**Status**: ✅ Application 100% functional, all critical bugs fixed
