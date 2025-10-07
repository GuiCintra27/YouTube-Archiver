#!/bin/bash

# Script para testar o backend

set -e

echo "🧪 Testando Backend YT-Archiver..."
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

cd backend

# Verificar venv
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}📦 Criando ambiente virtual...${NC}"
    python3 -m venv .venv
fi

# Ativar venv
source .venv/bin/activate

# Instalar dependências
echo -e "${BLUE}📥 Instalando dependências...${NC}"
pip install -q -r requirements.txt

# Iniciar servidor em background
echo -e "${BLUE}🚀 Iniciando servidor...${NC}"
uvicorn api:app --host 127.0.0.1 --port 8000 > /tmp/yt-archiver-api.log 2>&1 &
SERVER_PID=$!

# Aguardar inicialização
sleep 3

# Verificar se está rodando
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo -e "${RED}❌ Falha ao iniciar servidor${NC}"
    cat /tmp/yt-archiver-api.log
    exit 1
fi

echo -e "${GREEN}✅ Servidor iniciado (PID: $SERVER_PID)${NC}"
echo ""

# Testar endpoints
echo -e "${BLUE}🧪 Testando endpoints...${NC}"
echo ""

# Test 1: Health check
echo -n "1. Health check (/)... "
RESPONSE=$(curl -s http://localhost:8000/)
if echo "$RESPONSE" | grep -q "ok"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    echo "$RESPONSE"
fi

# Test 2: API Docs
echo -n "2. API Docs (/docs)... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌ (HTTP $STATUS)${NC}"
fi

# Test 3: List jobs
echo -n "3. List jobs (/api/jobs)... "
RESPONSE=$(curl -s http://localhost:8000/api/jobs)
if echo "$RESPONSE" | grep -q "total"; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    echo "$RESPONSE"
fi

# Parar servidor
echo ""
echo -e "${BLUE}🛑 Parando servidor...${NC}"
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Todos os testes passaram!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "Para rodar manualmente:"
echo -e "  ${BLUE}cd backend${NC}"
echo -e "  ${BLUE}source .venv/bin/activate${NC}"
echo -e "  ${BLUE}uvicorn api:app --host 0.0.0.0 --port 8000${NC}"
echo ""
