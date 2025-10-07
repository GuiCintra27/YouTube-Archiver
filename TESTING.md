# 🧪 Guia de Testes - YT-Archiver

## Status dos Testes

✅ **Backend API** - Funcionando
✅ **CLI Python** - Funcionando
🔄 **Frontend Next.js** - Pronto para teste

---

## ⚡ Testes Rápidos

### Backend (API)

```bash
./test-backend.sh
```

**O que testa:**
- ✅ Servidor inicia corretamente
- ✅ Health check endpoint
- ✅ API Docs (Swagger)
- ✅ Endpoints REST

### CLI Python

```bash
./test-cli.sh
```

**O que testa:**
- ✅ Comandos disponíveis
- ✅ Help funcionando
- ✅ List e Download commands

---

## 🚀 Executar Manualmente

### 1. Backend (API FastAPI)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8000
```

**Acesse:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

### 2. Frontend (Next.js)

```bash
cd web-ui
npm install
npm run dev
```

**Acesse:**
- Web UI: http://localhost:3000

### 3. CLI Python

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --help
```

**Exemplo:**
```bash
python main.py download "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --out-dir ./downloads \
  --max-res 720
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

### CLI Python

#### 1. Listar Vídeos de Playlist
```bash
cd python
source .venv/bin/activate
python main.py list "https://www.youtube.com/playlist?list=PLx..."
```

#### 2. Download com Opções
```bash
python main.py download "URL" \
  --out-dir ./test-downloads \
  --max-res 480 \
  --audio-only \
  --file-name "teste"
```

#### 3. Download com Headers (HLS)
```bash
python main.py download "https://example.com/video.m3u8" \
  --referer "https://example.com" \
  --origin "https://example.com" \
  --cookies-file ./cookies.txt \
  --concurrent-fragments 15
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

### CLI não funciona

**Erro: typer not found**
```bash
cd python
source .venv/bin/activate
pip install -r requirements.txt
```

**Erro: ffmpeg not found**
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
2. Verificar arquivo `web-ui/.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. Reiniciar frontend: `npm run dev`

### CORS Error

Se aparecer erro de CORS no navegador:
1. Verificar se o backend está configurado para aceitar `localhost:3000`
2. Arquivo `backend/api.py` linha 29-33 deve ter:
   ```python
   allow_origins=["http://localhost:3000", "http://localhost:3001"]
   ```

---

## 📊 Estrutura de Testes

```
yt-archiver/
├── test-backend.sh      # Testa API FastAPI
├── test-cli.sh          # Testa CLI Python
├── backend/
│   ├── .venv/          # Ambiente virtual Python
│   └── api.py          # API FastAPI
├── python/
│   ├── .venv/          # Ambiente virtual Python
│   └── main.py         # CLI original
└── web-ui/
    ├── node_modules/   # Dependências Node
    └── src/            # Código Next.js
```

---

## ✅ Checklist de Testes

Antes de usar em produção, verifique:

- [ ] Backend inicia sem erros
- [ ] API responde em `/` e `/docs`
- [ ] CLI mostra `--help` corretamente
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
# Logs em tempo real
tail -f /tmp/yt-archiver-api.log
```

### Frontend
- Console do navegador (F12)
- Terminal onde rodou `npm run dev`

### CLI
- Saída direta no terminal
- Rich progress bars com `--help`

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
