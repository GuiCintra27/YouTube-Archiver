# 🧪 Guia de Testes - YT-Archiver

## Status dos Testes

✅ **Backend API** - 46 testes automatizados (pytest)
✅ **Frontend Next.js** - Build funcionando

---

## ⚡ Testes Automatizados (Backend)

### Rodar Todos os Testes
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

**Resultado esperado:** `46 passed in ~1.5s`

### Testes com Cobertura
```bash
pytest tests/ --cov=app --cov-report=html
# Abrir htmlcov/index.html no navegador
```

### Testes Disponíveis (46 total)

| Arquivo | Testes | Descrição |
|---------|--------|-----------|
| `test_cache.py` | 7 | Cache de diretórios (TTL, invalidação, thread-safety) |
| `test_health.py` | 2 | Health check e versão |
| `test_jobs.py` | 8 | Jobs, cancelamento, exclusão |
| `test_library.py` | 13 | Vídeos, streaming, thumbnails, exclusão |
| `test_validators.py` | 16 | Validação de URLs, paths, filenames |

### Rodar Teste Específico
```bash
# Um arquivo
pytest tests/test_validators.py -v

# Um teste específico
pytest tests/test_library.py::TestListVideos::test_list_videos_empty_directory -v
```

---

## 🚀 Executar Manualmente

### 1. Backend (API FastAPI)

```bash
cd backend
./run.sh
# Ou manualmente:
# source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Acesse:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

### 2. Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

**Acesse:**
- Web UI: http://localhost:3000

### 3. Ambos (Script Automático)

```bash
./start-dev.sh
```

---

## 🔍 Testes Manuais Detalhados

### Backend API

#### 1. Health Check
```bash
curl http://localhost:8000/
# Esperado: {"status":"ok","service":"YT-Archiver API","version":"2.0.0"}
```

#### 2. Listar Jobs
```bash
curl http://localhost:8000/api/jobs
# Esperado: {"total":0,"jobs":[]}
```

#### 3. Obter Info de Vídeo
```bash
curl -X POST http://localhost:8000/api/video-info \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

#### 4. Iniciar Download (Dry Run)
```bash
curl -X POST http://localhost:8000/api/download \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "out_dir": "./downloads",
    "max_res": 720
  }'
# Retorna: {"status":"success","job_id":"..."}
```

#### 5. Verificar Status do Job
```bash
# Substitua JOB_ID pelo ID retornado acima
curl http://localhost:8000/api/jobs/JOB_ID
```

### Frontend Next.js

1. Abrir http://localhost:3000
2. Colar URL de teste: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
3. Clicar em "Baixar"
4. Verificar progresso em tempo real
5. Testar opções avançadas

---

## 🐛 Troubleshooting

### Backend não inicia

**Erro: ModuleNotFoundError**
```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
```

**Erro: Address already in use (porta 8000)**
```bash
# Linux/Mac
pkill -f uvicorn
# ou
lsof -ti:8000 | xargs kill

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### ffmpeg não encontrado

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Baixar de https://ffmpeg.org/download.html
```

### Frontend não conecta ao backend

1. Verificar se backend está rodando: `curl http://localhost:8000/`
2. Verificar arquivo `frontend/.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. Reiniciar frontend: `npm run dev`

### CORS Error

Se aparecer erro de CORS no navegador:
1. Verificar se o backend está configurado para aceitar `localhost:3000`
2. Verificar `backend/.env` ou `backend/app/config.py`:
   ```
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

---

## 📊 Estrutura de Testes

```
yt-archiver/
├── backend/
│   ├── tests/           # ⭐ Testes automatizados (pytest)
│   │   ├── conftest.py  # Fixtures compartilhadas
│   │   ├── test_cache.py
│   │   ├── test_health.py
│   │   ├── test_jobs.py
│   │   ├── test_library.py
│   │   └── test_validators.py
│   ├── app/             # Código da aplicação
│   ├── pytest.ini       # Configuração do pytest
│   ├── .venv/           # Ambiente virtual Python
│   └── run.sh           # Script de inicialização
└── frontend/
    ├── node_modules/    # Dependências Node
    └── src/             # Código Next.js
```

---

## ✅ Checklist de Testes

Antes de usar em produção, verifique:

- [ ] Testes automatizados passam (`pytest tests/ -v` → 46 passed)
- [ ] Backend inicia sem erros (`./run.sh`)
- [ ] API responde em `/` e `/docs`
- [ ] Frontend carrega em localhost:3000
- [ ] Download de teste funciona (vídeo pequeno)
- [ ] Barra de progresso atualiza
- [ ] Opções avançadas aparecem
- [ ] Arquivo é salvo no diretório correto
- [ ] ffmpeg está instalado e acessível

---

## 📝 Logs

### Backend
```bash
# Logs aparecem no terminal onde ./run.sh foi executado
# Formato: TIMESTAMP | LEVEL | MODULE:FUNCTION:LINE | MESSAGE

# Exemplo de saída:
# 2025-11-29 10:30:00 | INFO     | yt-archiver:main:27 | Starting YT-Archiver API
# 2025-11-29 10:30:01 | DEBUG    | yt-archiver.downloads:start:42 | Download started
```

**Configurar nível de log:** Editar `LOG_LEVEL` em `backend/.env` (DEBUG, INFO, WARNING, ERROR)

### Frontend
- Console do navegador (F12)
- Terminal onde rodou `npm run dev`

---

## 🎯 URLs de Teste Seguras

Use estes vídeos públicos para testar:

**YouTube:**
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

**Playlist Pequena:**
```
https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf
```

**Vídeo Curto (domínio público):**
```
https://www.youtube.com/watch?v=jNQXAC9IVRw
```

---

**Todos os testes passaram! ✨**
