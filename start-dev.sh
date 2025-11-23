#!/bin/bash

# Script para iniciar backend e frontend em modo desenvolvimento
set -euo pipefail

echo "🚀 Iniciando YT-Archiver..."

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    local exit_code=$?

    if [ -n "${FRONTEND_PID}" ] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
        echo -e "${YELLOW}🛑 Encerrando frontend (PID ${FRONTEND_PID})...${NC}"
        kill "${FRONTEND_PID}" 2>/dev/null || true
    fi

    if [ -n "${BACKEND_PID}" ] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
        echo -e "${YELLOW}🛑 Encerrando backend (PID ${BACKEND_PID})...${NC}"
        kill "${BACKEND_PID}" 2>/dev/null || true
    fi

    # Aguarda término para evitar processos órfãos
    wait 2>/dev/null || true

    exit ${exit_code}
}

trap cleanup EXIT

# Verificar se ffmpeg está instalado
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg não encontrado. Por favor, instale ffmpeg primeiro."
    exit 1
fi

# Iniciar backend
echo -e "${BLUE}📡 Iniciando Backend (FastAPI)...${NC}"
cd backend || exit

# Criar venv se não existir
if [ ! -d ".venv" ]; then
    echo "📦 Criando ambiente virtual Python..."
    python3 -m venv .venv
fi

# Ativar venv
source .venv/bin/activate

# Instalar dependências
echo "📥 Instalando dependências do backend..."
pip install -q -r requirements.txt

# Iniciar API em background
python api.py &
BACKEND_PID=$!

sleep 2
if ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Backend falhou ao iniciar. Verifique logs acima.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend iniciado em http://localhost:8000${NC}"

# Voltar para raiz
cd ..

# Iniciar frontend
echo -e "${BLUE}🎨 Iniciando Frontend (Next.js)...${NC}"
cd frontend || exit

# Instalar dependências se necessário
if [ ! -d "node_modules" ]; then
    echo "📥 Instalando dependências do frontend..."
    npm install
fi

# Iniciar Next.js
npm run dev &
FRONTEND_PID=$!

sleep 3
if ! kill -0 "${FRONTEND_PID}" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Frontend falhou ao iniciar. Verifique logs acima.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Frontend iniciado em http://localhost:3000${NC}"

# Mensagem final
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ YT-Archiver está rodando!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "📡 Backend (API):  ${BLUE}http://localhost:8000${NC}"
echo -e "📚 API Docs:       ${BLUE}http://localhost:8000/docs${NC}"
echo -e "🎨 Frontend (Web): ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "Para parar os servidores, pressione ${GREEN}Ctrl+C${NC}"
echo ""

# Aguardar interrupção
wait $BACKEND_PID $FRONTEND_PID
