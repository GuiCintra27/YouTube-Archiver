#!/bin/bash

# Script para rodar o backend com venv ativado e hot-reload

cd "$(dirname "$0")"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar se venv existe
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment não encontrado!${NC}"
    echo -e "${YELLOW}Execute: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt${NC}"
    exit 1
fi

# Matar processo existente na porta 8000 (se houver)
EXISTING_PID=$(lsof -ti:8000 2>/dev/null)
if [ -n "$EXISTING_PID" ]; then
    echo -e "${YELLOW}⚠️  Processo existente na porta 8000 (PID: $EXISTING_PID). Encerrando...${NC}"
    kill -9 $EXISTING_PID 2>/dev/null
    sleep 1
fi

# Ativar venv
source .venv/bin/activate

echo -e "${GREEN}🚀 Iniciando Backend API...${NC}"
echo -e "${BLUE}   URL: http://localhost:8000${NC}"
echo -e "${BLUE}   Docs: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}   Hot-reload ativado - alterações serão detectadas automaticamente${NC}"
echo ""

# Rodar uvicorn com hot-reload
# --reload: reinicia quando arquivos mudam
# --reload-dir: monitora apenas o diretório app (mais eficiente)
# --reload-include: inclui arquivos .py e .env
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir app \
    --reload-include "*.py" \
    --reload-include ".env"
