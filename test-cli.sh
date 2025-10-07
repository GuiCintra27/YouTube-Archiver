#!/bin/bash

# Script para testar o CLI Python

set -e

echo "🧪 Testando CLI Python YT-Archiver..."
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

cd python

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

echo ""

# Testar comandos
echo -e "${BLUE}🧪 Testando comandos...${NC}"
echo ""

# Test 1: Help
echo -n "1. Help (--help)... "
if python main.py --help > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    exit 1
fi

# Test 2: List command
echo -n "2. List command... "
if python main.py list --help > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    exit 1
fi

# Test 3: Download command
echo -n "3. Download command... "
if python main.py download --help > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC}"
else
    echo -e "${RED}❌${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ CLI está funcionando!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "Exemplo de uso:"
echo -e "  ${BLUE}python main.py download 'https://youtube.com/watch?v=...'${NC}"
echo ""
