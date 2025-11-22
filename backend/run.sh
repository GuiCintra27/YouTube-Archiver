#!/bin/bash

# Script para rodar o backend com venv ativado

cd "$(dirname "$0")"

# Verificar se venv existe
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment não encontrado!"
    echo "Execute: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Ativar venv e rodar API
echo "🚀 Iniciando Backend API..."
source .venv/bin/activate
python api.py
