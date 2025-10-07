# Changelog

## [2.0.0] - 2025-10-06

### 🎉 Major Release - Interface Web Completa

**Nova arquitetura com separação frontend/backend para uso visual e intuitivo.**

### ✨ Adicionado

#### Backend (Novo)
- **API REST com FastAPI** (`backend/`)
  - Endpoints para download, status e histórico
  - Sistema de jobs para gerenciar downloads em background
  - Server-Sent Events (SSE) para progresso em tempo real
  - Documentação automática com Swagger (OpenAPI)
  - CORS configurado para desenvolvimento local

#### Frontend Web (Novo)
- **Interface Next.js 15** (`web-ui/`)
  - Design moderno com shadcn/ui e Tailwind CSS
  - Formulário intuitivo para download de vídeos
  - Barra de progresso em tempo real
  - Opções avançadas expansíveis (accordion)
  - Switches para configurações booleanas
  - Feedback visual de sucesso/erro
  - Responsivo e compatível com mobile

#### Componentes UI
- Button, Card, Input, Label (shadcn/ui)
- Progress bar animada
- Switch toggles
- Accordion para opções avançadas
- Ícones com Lucide React

#### Utilitários
- Formatação de bytes (KB, MB, GB)
- Formatação de velocidade (MB/s)
- Formatação de tempo (ETA)
- Helpers para merge de classes CSS

#### Documentação
- `WEB-UI-README.md` - Guia completo da interface web
- `QUICK-START.md` - Início rápido em 3 passos
- `CHANGELOG.md` - Histórico de versões

#### Scripts
- `start-dev.sh` - Iniciar backend + frontend (Linux/Mac)
- `start-dev.bat` - Iniciar backend + frontend (Windows)

### 🔧 Modificado

#### CLI Python
- Refatorado para ser importável como biblioteca
- Funções expostas em `downloader.py` para uso na API
- Mantém 100% de compatibilidade com versão anterior
- Todas as funcionalidades preservadas

#### README
- Adicionada seção "Interface Web Moderna"
- Reorganizado para destacar nova interface
- Links para documentação específica

### 📦 Dependências

#### Backend
- `fastapi>=0.115.0` - Framework web assíncrono
- `uvicorn[standard]>=0.32.0` - Servidor ASGI
- `python-multipart>=0.0.9` - Upload de arquivos
- `pydantic>=2.9.0` - Validação de dados

#### Frontend
- `next@15.0.0` - Framework React
- `@radix-ui/*` - Componentes UI primitivos
- `tailwindcss@3.4.17` - Estilização utility-first
- `lucide-react` - Ícones
- `class-variance-authority` - Variantes de componentes

### 🎯 Funcionalidades Principais

1. **Interface Visual Completa**
   - Usuários não-técnicos podem usar sem conhecer CLI
   - Todas as opções do CLI disponíveis na UI
   - Progresso em tempo real com estatísticas

2. **API REST**
   - Integração com outras aplicações
   - Endpoints RESTful bem documentados
   - Swagger UI interativo

3. **Arquitetura Moderna**
   - Backend/Frontend desacoplados
   - Comunicação assíncrona
   - Escalável e manutenível

### 🔄 Compatibilidade

- ✅ CLI Python 100% compatível (nenhuma breaking change)
- ✅ Todos os parâmetros existentes mantidos
- ✅ Frontend antigo (`frontend/`) ainda funcional
- ✅ Google Drive upload suportado via CLI

### 📊 Estrutura do Projeto

```
yt-archiver/
├── backend/              # API FastAPI (NOVO)
│   ├── api.py
│   ├── downloader.py
│   └── requirements.txt
├── web-ui/               # Interface Next.js (NOVO)
│   ├── src/
│   └── package.json
├── python/               # CLI original
│   └── main.py
├── frontend/             # CLI generator (legado)
├── start-dev.sh          # Script Linux/Mac (NOVO)
├── start-dev.bat         # Script Windows (NOVO)
├── README.md             # Atualizado
├── WEB-UI-README.md      # Novo
└── QUICK-START.md        # Novo
```

### 🚀 Como Usar

**Interface Web:**
```bash
./start-dev.sh
# Acesse http://localhost:3000
```

**CLI (inalterado):**
```bash
python python/main.py download "URL"
```

**API (novo):**
```bash
cd backend
python api.py
# Acesse http://localhost:8000/docs
```

---

## [1.0.0] - 2024-09-14

### Inicial Release

- CLI Python com yt-dlp
- Download de YouTube e HLS
- Upload para Google Drive
- Headers e cookies customizados
- Nomenclatura personalizada
- Frontend gerador de comandos

---

**Legenda:**
- ✨ Adicionado - Novas funcionalidades
- 🔧 Modificado - Mudanças em funcionalidades existentes
- 🐛 Corrigido - Bug fixes
- 🗑️ Removido - Funcionalidades descontinuadas
- 🔒 Segurança - Vulnerabilidades corrigidas
