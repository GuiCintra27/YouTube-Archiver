# MCP Configuration Guide

Este arquivo contém a configuração do Model Context Protocol (MCP) para usar com sua aplicação de nuvem.

## Servidores Incluídos

### 🐍 Python
- **Servidor**: `mcp-server-python`
- **Funcionalidade**: Execução de código Python e gerenciamento de ambiente
- **Instalação**: `pip install mcp-server-python`

### 📁 Filesystem
- **Servidor**: `@modelcontextprotocol/server-filesystem`
- **Funcionalidade**: Operações de sistema de arquivos
- **Caminho configurado**: `/home/guilherme-cintra`

### 🔍 Brave Search
- **Servidor**: `@modelcontextprotocol/server-brave-search`
- **Funcionalidade**: Busca na web para documentação e exemplos
- **Requer**: API key do Brave Search

### 🔄 Git
- **Servidor**: `mcp-server-git`
- **Funcionalidade**: Gerenciamento de repositórios Git
- **Instalação**: `pip install mcp-server-git`

### 🗄️ SQLite
- **Servidor**: `mcp-server-sqlite`
- **Funcionalidade**: Operações com banco de dados SQLite
- **Instalação**: `pip install mcp-server-sqlite`

### 🧠 Memory
- **Servidor**: `@modelcontextprotocol/server-memory`
- **Funcionalidade**: Memória persistente entre sessões

### 🤖 Puppeteer
- **Servidor**: `@modelcontextprotocol/server-puppeteer`
- **Funcionalidade**: Automação de navegador (alternativa ao Chrome DevTools)
- **Nota**: Pode ser usado para testes e scraping de componentes shadcn/ui

### 🐙 GitHub
- **Servidor**: `@modelcontextprotocol/server-github`
- **Funcionalidade**: Integração com API do GitHub
- **Requer**: Personal Access Token do GitHub

## Configuração de Tokens

Antes de usar, você precisa configurar os seguintes tokens:

1. **Brave API Key**: 
   - Obtenha em: https://api.search.brave.com/
   - Substitua `your_brave_api_key_here` no arquivo

2. **GitHub Personal Access Token**:
   - Crie em: GitHub → Settings → Developer settings → Personal access tokens
   - Substitua `your_github_token_here` no arquivo

## Instalação dos Servidores

Execute os seguintes comandos para instalar os servidores necessários:

```bash
# Servidores Python (via uvx/pip)
pip install mcp-server-python mcp-server-git mcp-server-sqlite

# Servidores Node.js serão instalados automaticamente via npx quando necessário
```

## Como Usar

1. **Para Claude Desktop**: Copie o conteúdo de `mcp-config.json` para seu arquivo de configuração do Claude Desktop
2. **Para outras aplicações MCP**: Use o arquivo `mcp-config.json` como referência para configurar sua aplicação

## Notas Especiais

### Para shadcn/ui:
- Não existe um servidor MCP específico para shadcn/ui
- Use o servidor **Puppeteer** para automatizar testes de componentes
- Use o servidor **Filesystem** para gerenciar arquivos de componentes
- Use o servidor **Brave Search** para buscar documentação

### Para Chrome DevTools:
- Não existe um servidor MCP específico para DevTools
- Use o servidor **Puppeteer** como alternativa para automação de navegador
- Combine com **Filesystem** para salvar/carregar dados de debug

### Para desenvolvimento Python:
- O servidor **Python** permite execução direta de código
- Combine com **Filesystem** para gerenciar arquivos .py
- Use **SQLite** para persistência de dados
- Use **Git** para controle de versão

## Exemplo de Uso

Depois de configurado, você poderá:
- Executar código Python diretamente
- Gerenciar arquivos do seu projeto
- Fazer commits Git
- Buscar documentação online
- Automatizar tarefas do navegador
- Armazenar dados em SQLite

## Troubleshooting

Se algum servidor não funcionar:
1. Verifique se está instalado corretamente
2. Confirme se os tokens estão configurados
3. Teste individualmente cada servidor
4. Consulte os logs para erros específicos