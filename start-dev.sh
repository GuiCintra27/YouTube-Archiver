#!/bin/bash

# Script para iniciar backend e frontend em modo desenvolvimento

echo "🚀 Iniciando YT-Archiver..."

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

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
echo -e "${GREEN}✅ Backend iniciado em http://localhost:8000${NC}"
python api.py &
BACKEND_PID=$!

# Voltar para raiz
cd ..

# Iniciar frontend
echo -e "${BLUE}🎨 Iniciando Frontend (Next.js)...${NC}"
cd web-ui || exit

# Instalar dependências se necessário
if [ ! -d "node_modules" ]; then
    echo "📥 Instalando dependências do frontend..."
    npm install
fi

# Iniciar Next.js
echo -e "${GREEN}✅ Frontend iniciado em http://localhost:3000${NC}"
npm run dev &
FRONTEND_PID=$!

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
