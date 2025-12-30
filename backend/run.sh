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

# Configuracoes
BACKEND_PORT="${PORT:-8000}"
WORKER_ROLE="${WORKER_ROLE:-both}"
RUN_WORKER="${RUN_WORKER:-false}"
WORKER_PORT="${WORKER_PORT:-8001}"
WORKER_PID=""

cleanup() {
    if [ -n "${WORKER_PID}" ] && kill -0 "${WORKER_PID}" 2>/dev/null; then
        echo -e "${YELLOW}🛑 Encerrando worker (PID ${WORKER_PID})...${NC}"
        kill "${WORKER_PID}" 2>/dev/null || true
    fi
}

trap cleanup EXIT

# Matar processo existente na porta principal (se houver)
EXISTING_PID=$(lsof -ti:${BACKEND_PORT} 2>/dev/null)
if [ -n "$EXISTING_PID" ]; then
    echo -e "${YELLOW}⚠️  Processo existente na porta ${BACKEND_PORT} (PID: $EXISTING_PID). Encerrando...${NC}"
    kill -9 $EXISTING_PID 2>/dev/null
    sleep 1
fi

# Matar processo existente na porta do worker (se houver)
if [ "${RUN_WORKER}" = "true" ] && [ "${WORKER_PORT}" != "${BACKEND_PORT}" ]; then
    WORKER_EXISTING_PID=$(lsof -ti:${WORKER_PORT} 2>/dev/null)
    if [ -n "$WORKER_EXISTING_PID" ]; then
        echo -e "${YELLOW}⚠️  Processo existente na porta ${WORKER_PORT} (PID: $WORKER_EXISTING_PID). Encerrando...${NC}"
        kill -9 $WORKER_EXISTING_PID 2>/dev/null
        sleep 1
    fi
fi

# Ativar venv
source .venv/bin/activate

API_ROLE="${WORKER_ROLE}"
if [ "${RUN_WORKER}" = "true" ]; then
    API_ROLE="api"
fi

if [ "${RUN_WORKER}" = "true" ]; then
    echo -e "${GREEN}🚀 Iniciando Worker...${NC}"
    echo -e "${BLUE}   Role: worker${NC}"
    echo -e "${BLUE}   URL: http://localhost:${WORKER_PORT}${NC}"
    echo -e "${YELLOW}   Hot-reload ativado - alterações serão detectadas automaticamente${NC}"
    echo ""

    WORKER_ROLE=worker uvicorn app.main:app \
        --host 0.0.0.0 \
        --port "${WORKER_PORT}" \
        --reload \
        --reload-dir app &
    WORKER_PID=$!
    sleep 1
fi

echo -e "${GREEN}🚀 Iniciando Backend API...${NC}"
echo -e "${BLUE}   Role: ${API_ROLE}${NC}"
echo -e "${BLUE}   URL: http://localhost:${BACKEND_PORT}${NC}"
echo -e "${BLUE}   Docs: http://localhost:${BACKEND_PORT}/docs${NC}"
echo -e "${YELLOW}   Hot-reload ativado - alterações serão detectadas automaticamente${NC}"
echo ""

# Rodar uvicorn com hot-reload
# --reload: reinicia quando arquivos mudam
# --reload-dir: monitora apenas o diretório app (mais eficiente)
# --reload-include: inclui arquivos .py e .env
WORKER_ROLE="${API_ROLE}" uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${BACKEND_PORT}" \
    --reload \
    --reload-dir app \
    --reload-include "*.py" \
    --reload-include ".env"
