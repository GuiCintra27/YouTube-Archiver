#!/bin/bash

# Script para diagnosticar bloqueios do YouTube

echo "🔍 Diagnóstico de Bloqueio do YouTube"
echo "======================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Verificar se cookies.txt existe
echo -e "${BLUE}1. Verificando arquivo de cookies...${NC}"
if [ -f "python/cookies.txt" ]; then
    echo -e "${GREEN}✅ cookies.txt encontrado${NC}"
    echo "   Tamanho: $(wc -l < python/cookies.txt) linhas"

    # Verificar se tem cookies importantes
    if grep -q "youtube.com" python/cookies.txt; then
        echo -e "${GREEN}✅ Contém cookies do YouTube${NC}"
    else
        echo -e "${RED}❌ Não contém cookies do YouTube${NC}"
    fi

    # Verificar cookies específicos importantes
    if grep -q "CONSENT\|VISITOR_INFO1_LIVE\|LOGIN_INFO" python/cookies.txt; then
        echo -e "${GREEN}✅ Contém cookies de autenticação${NC}"
    else
        echo -e "${YELLOW}⚠️  Faltam cookies importantes (CONSENT, VISITOR_INFO1_LIVE)${NC}"
    fi
else
    echo -e "${RED}❌ cookies.txt não encontrado em python/${NC}"
fi

echo ""

# 2. Testar yt-dlp com cookies
echo -e "${BLUE}2. Testando yt-dlp com URL de teste...${NC}"
cd python

if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo -e "${RED}❌ Ambiente virtual não encontrado${NC}"
    exit 1
fi

# URL de teste curta
TEST_URL="https://www.youtube.com/watch?v=jNQXAC9IVRw"

echo "   URL de teste: $TEST_URL"
echo ""

# Testar sem cookies primeiro
echo -e "${YELLOW}   Tentando SEM cookies...${NC}"
yt-dlp --skip-download --print title "$TEST_URL" 2>&1 | head -5

echo ""

# Testar com cookies
if [ -f "cookies.txt" ]; then
    echo -e "${YELLOW}   Tentando COM cookies...${NC}"
    yt-dlp --cookies cookies.txt --skip-download --print title "$TEST_URL" 2>&1 | head -5
fi

echo ""

# 3. Verificar IP/rate limit
echo -e "${BLUE}3. Verificando possíveis causas...${NC}"

# Verificar últimos downloads
if [ -f "archive.txt" ]; then
    COUNT=$(wc -l < archive.txt)
    echo -e "${YELLOW}   Downloads no histórico: $COUNT${NC}"

    if [ $COUNT -gt 100 ]; then
        echo -e "${RED}   ⚠️  Muitos downloads recentes podem ter causado rate limit${NC}"
    fi
fi

echo ""

# 4. Recomendações
echo -e "${BLUE}4. Soluções Recomendadas:${NC}"
echo ""
echo -e "${GREEN}📋 Opção 1: Atualizar Cookies (Recomendado)${NC}"
echo "   1. Abra YouTube no navegador (modo anônimo)"
echo "   2. Faça login na sua conta"
echo "   3. Instale extensão: 'Get cookies.txt LOCALLY'"
echo "   4. Exporte cookies do YouTube"
echo "   5. Substitua python/cookies.txt"
echo ""

echo -e "${GREEN}📋 Opção 2: Usar User-Agent específico${NC}"
echo "   python main.py download 'URL' --user-agent 'Mozilla/5.0 ...'"
echo ""

echo -e "${GREEN}📋 Opção 3: Aguardar (6-24 horas)${NC}"
echo "   Rate limits do YouTube geralmente expiram em algumas horas"
echo ""

echo -e "${GREEN}📋 Opção 4: Usar Proxy/VPN${NC}"
echo "   Mudar IP pode contornar bloqueio temporário"
echo ""

echo -e "${GREEN}📋 Opção 5: yt-dlp com OAuth (Avançado)${NC}"
echo "   yt-dlp --username oauth2 --password '' 'URL'"
echo ""

# 5. Verificar versão do yt-dlp
echo -e "${BLUE}5. Versão do yt-dlp:${NC}"
yt-dlp --version

echo ""
echo "======================================"
echo -e "${BLUE}💡 Dica: Se cookies não funcionarem, aguarde algumas horas${NC}"
echo ""
