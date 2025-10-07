@echo off
REM Script para iniciar backend e frontend em modo desenvolvimento (Windows)

echo 🚀 Iniciando YT-Archiver...

REM Verificar ffmpeg
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ ffmpeg não encontrado. Por favor, instale ffmpeg primeiro.
    exit /b 1
)

REM Iniciar backend
echo 📡 Iniciando Backend (FastAPI)...
cd backend

REM Criar venv se não existir
if not exist ".venv" (
    echo 📦 Criando ambiente virtual Python...
    python -m venv .venv
)

REM Ativar venv
call .venv\Scripts\activate.bat

REM Instalar dependências
echo 📥 Instalando dependências do backend...
pip install -q -r requirements.txt

REM Iniciar API em nova janela
echo ✅ Backend iniciado em http://localhost:8000
start "Backend - FastAPI" cmd /k "python api.py"

REM Voltar para raiz
cd ..

REM Iniciar frontend
echo 🎨 Iniciando Frontend (Next.js)...
cd web-ui

REM Instalar dependências se necessário
if not exist "node_modules" (
    echo 📥 Instalando dependências do frontend...
    npm install
)

REM Iniciar Next.js em nova janela
echo ✅ Frontend iniciado em http://localhost:3000
start "Frontend - Next.js" cmd /k "npm run dev"

cd ..

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ✨ YT-Archiver está rodando!
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 📡 Backend (API):  http://localhost:8000
echo 📚 API Docs:       http://localhost:8000/docs
echo 🎨 Frontend (Web): http://localhost:3000
echo.
echo Para parar, feche as janelas do terminal.
echo.
pause
