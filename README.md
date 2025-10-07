# YT-Archiver

Sistema completo para download e arquivamento de vídeos do YouTube e streams HLS (sem DRM), com suporte opcional a upload automático para Google Drive.

## 📋 Visão Geral

O YT-Archiver é uma ferramenta que combina:

- **Script Python** (`python/main.py`): CLI poderosa baseada em `yt-dlp` para download de vídeos
- **API REST** (`backend/`): FastAPI com endpoints para integração web
- **Interface Web Moderna** (`web-ui/`): Next.js 15 com shadcn/ui para download visual e intuitivo
- **Frontend CLI Generator** (`frontend/`): Interface web para geração de comandos CLI

### Principais Funcionalidades

- ✅ Download de vídeos do YouTube (canais, playlists, vídeos individuais)
- ✅ Suporte a streams HLS (M3U8) sem DRM
- ✅ Headers customizados (Referer, Origin, User-Agent)
- ✅ Cookies personalizados via arquivo Netscape
- ✅ Upload automático para Google Drive com espelhamento de estrutura de pastas
- ✅ Sistema de arquivamento para evitar downloads duplicados
- ✅ Download paralelo com workers
- ✅ Controle de qualidade e formato de saída
- ✅ Extração de áudio (MP3)
- ✅ Download de legendas e miniaturas
- ✅ Nomes de arquivo customizados
- ✅ Interface web moderna com progresso em tempo real
- ✅ API REST para integração com outras aplicações

---

## 🌐 Interface Web Moderna

**Novidade!** Agora você pode usar o YT-Archiver através de uma interface web moderna e intuitiva.

### Início Rápido (Web UI)

```bash
# Executar script de desenvolvimento (Linux/Mac)
./start-dev.sh

# Ou no Windows
start-dev.bat
```

Acesse: **http://localhost:3000**

Para mais detalhes sobre a interface web, consulte [WEB-UI-README.md](./WEB-UI-README.md)

### Funcionalidades da Interface Web

- ✨ Interface moderna e responsiva com Next.js
- 📊 Barra de progresso em tempo real
- ⚙️ Todas as opções avançadas acessíveis via formulário
- 🎯 Design intuitivo para usuários não-técnicos
- 🔄 Feedback visual de sucesso/erro
- 📱 Compatível com mobile

---

## 🚀 Início Rápido (CLI)

### Pré-requisitos

- Python 3.12+
- ffmpeg instalado no sistema
- (Opcional) Node.js 18+ para executar o frontend

### Instalação

#### 1. Clone o repositório

```bash
git clone <seu-repositorio>
cd yt-archiver
```

#### 2. Configure o ambiente Python

```bash
cd python
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. (Opcional) Configure o Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 📖 Uso do Script Python

### Comandos Básicos

#### Listar vídeos de uma playlist

```bash
python main.py list "https://www.youtube.com/playlist?list=PLx..."
```

#### Download simples de um vídeo

```bash
python main.py download "https://www.youtube.com/watch?v=..."
```

#### Download de playlist completa

```bash
python main.py download "https://www.youtube.com/playlist?list=PLx..." \
  --out-dir ./downloads \
  --workers 3
```

### Exemplos Avançados

#### Download de stream HLS com headers customizados

```bash
python main.py download "https://example.com/playlist.m3u8" \
  --referer "https://example.com" \
  --origin "https://example.com" \
  --cookies-file ./cookies.txt \
  --concurrent-fragments 10
```

#### Download com nome e caminho customizados

```bash
python main.py download "https://example.com/aula.m3u8" \
  --path "Curso/Módulo 01" \
  --file-name "Aula 01 - Introdução" \
  --archive-id "aula-01"
```

#### Extrair apenas áudio em MP3

```bash
python main.py download "https://www.youtube.com/watch?v=..." \
  --audio-only \
  --out-dir ./music
```

#### Download com upload automático para Google Drive

```bash
python main.py download "https://www.youtube.com/playlist?list=..." \
  --drive-upload \
  --drive-root "MeusVideos" \
  --drive-credentials ./credentials.json
```

---

## ⚙️ Parâmetros da CLI

### Comando `download`

| Parâmetro        | Tipo | Padrão          | Descrição                                            |
| ---------------- | ---- | --------------- | ---------------------------------------------------- |
| `source`         | str  | _obrigatório_   | URL do vídeo/playlist/canal ou arquivo .txt com URLs |
| `--out-dir`      | str  | `./downloads`   | Diretório de saída para downloads                    |
| `--archive-file` | str  | `./archive.txt` | Arquivo para rastrear downloads e evitar duplicatas  |
| `--fmt`          | str  | `bv*+ba/b`      | Seletor de formato do yt-dlp                         |
| `--max-res`      | int  | `None`          | Limita altura máxima do vídeo (ex: 1080)             |
| `--subs`         | bool | `True`          | Baixar legendas                                      |
| `--auto-subs`    | bool | `True`          | Baixar legendas automáticas                          |
| `--sub-langs`    | str  | `pt,en`         | Idiomas de legendas (separados por vírgula)          |
| `--thumbnails`   | bool | `True`          | Baixar miniaturas                                    |
| `--audio-only`   | bool | `False`         | Extrair apenas áudio (MP3)                           |
| `--workers`      | int  | `1`             | Número de downloads paralelos                        |
| `--limit`        | int  | `None`          | Limitar número de itens de playlist/canal            |
| `--dry-run`      | bool | `False`         | Simular sem baixar                                   |

### Headers e Cookies

| Parâmetro                | Tipo | Padrão        | Descrição                                           |
| ------------------------ | ---- | ------------- | --------------------------------------------------- |
| `--cookies-file`         | str  | `None`        | Caminho para arquivo cookies.txt (formato Netscape) |
| `--referer`              | str  | `None`        | Header Referer customizado                          |
| `--origin`               | str  | `None`        | Header Origin customizado                           |
| `--user-agent`           | str  | `yt-archiver` | Header User-Agent                                   |
| `--concurrent-fragments` | int  | `10`          | Fragmentos HLS simultâneos                          |

### Nomenclatura Customizada

| Parâmetro      | Tipo | Padrão | Descrição                                  |
| -------------- | ---- | ------ | ------------------------------------------ |
| `--path`       | str  | `None` | Subpasta relativa ao `--out-dir`           |
| `--file-name`  | str  | `None` | Nome base do arquivo (extensão automática) |
| `--archive-id` | str  | `None` | ID manual para controle de duplicatas      |

### Google Drive

| Parâmetro             | Tipo | Padrão               | Descrição                       |
| --------------------- | ---- | -------------------- | ------------------------------- |
| `--drive-upload`      | bool | `False`              | Ativar upload para Google Drive |
| `--drive-root`        | str  | `YouTubeArchive`     | Nome da pasta raiz no Drive     |
| `--drive-credentials` | str  | `./credentials.json` | Credenciais OAuth do Google     |
| `--drive-token`       | str  | `./token.json`       | Cache do token OAuth            |
| `--uploaded-log`      | str  | `./uploaded.jsonl`   | Log de arquivos já enviados     |

---

## 🔐 Configuração do Google Drive

### 1. Criar projeto no Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto
3. Ative a **Google Drive API**
4. Crie credenciais OAuth 2.0 (tipo "Desktop app")
5. Baixe o JSON de credenciais e salve como `credentials.json`

### 2. Primeira autenticação

```bash
python main.py download "URL" --drive-upload
```

O navegador abrirá automaticamente para autorização. Após autorizar, o token será salvo em `token.json`.

---

## 📁 Estrutura de Pastas

### Padrão de Nomenclatura

Quando `--path` e `--file-name` **não** são especificados:

```
downloads/
  └── NomeDoCanal/
      └── NomePlaylist/
          └── 2024-01-15 - Título do Vídeo [VIDEO_ID].mp4
```

Quando `--path` e `--file-name` **são** especificados:

```
downloads/
  └── Curso/
      └── Módulo 01/
          └── Aula 01 - Introdução.mp4
```

### Espelhamento no Google Drive

A estrutura de pastas local é espelhada no Google Drive:

```
GoogleDrive/
  └── MeusVideos/  (--drive-root)
      └── Curso/
          └── Módulo 01/
              └── Aula 01 - Introdução.mp4
```

---

## 🐳 Usando Docker

### Build da imagem

```bash
cd python
docker build -t yt-archiver .
```

### Executar com Docker

```bash
docker run --rm -v $(pwd)/downloads:/downloads yt-archiver \
  download "https://www.youtube.com/watch?v=..." \
  --out-dir /downloads
```

### Com cookies e credenciais

```bash
docker run --rm \
  -v $(pwd)/downloads:/downloads \
  -v $(pwd)/cookies.txt:/app/cookies.txt \
  -v $(pwd)/credentials.json:/app/credentials.json \
  yt-archiver download "URL" \
  --cookies-file /app/cookies.txt \
  --drive-upload
```

---

## 🛠️ Desenvolvimento

### Estrutura do Projeto

```
yt-archiver/
├── python/
│   ├── main.py              # Script principal
│   ├── requirements.txt     # Dependências Python
│   ├── Dockerfile          # Imagem Docker
│   └── .venv/              # Ambiente virtual Python
├── frontend/               # UI React (opcional)
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── CLAUDE.md              # Instruções para Claude Code
└── README.md              # Esta documentação
```

### Tecnologias Utilizadas

**Backend (Python):**

- `yt-dlp`: Motor de download
- `typer`: Framework CLI
- `rich`: Interface colorida no terminal
- `google-api-python-client`: Integração com Google Drive
- `ffmpeg`: Processamento de vídeo/áudio

**Frontend (React):**

- Vite
- React + TypeScript
- Tailwind CSS
- shadcn/ui (componentes)

---

## 📝 Sistema de Arquivamento

### Arquivo `archive.txt`

O yt-dlp mantém um registro de vídeos baixados para evitar duplicatas:

```
youtube VIDEO_ID1
youtube VIDEO_ID2
custom aula-01
```

### Comportamento

- **Padrão**: yt-dlp registra automaticamente cada vídeo baixado
- **Com `--archive-id`**: sistema customizado que:
  - Desativa o registro automático do yt-dlp
  - Usa o ID fornecido para controle manual
  - Útil para streams HLS sem ID do YouTube

---

## 🍪 Usando Cookies

### Exportar cookies do navegador

Use extensões como:

- **Chrome/Edge**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/)
- **Firefox**: [cookies.txt](https://addons.mozilla.org/firefox/addon/cookies-txt/)

### Formato esperado (Netscape)

```
# Netscape HTTP Cookie File
.example.com	TRUE	/	FALSE	1735689600	session_id	abc123
```

### Uso

```bash
python main.py download "URL" --cookies-file ./cookies.txt
```

---

## ⚠️ Limitações e Notas

### DRM

Este projeto **NÃO** suporta conteúdo protegido por DRM (Widevine, FairPlay, etc.). Apenas streams HLS não criptografados são suportados.

### Rate Limiting

Ao baixar grandes quantidades de vídeos:

- Use `--workers` com cautela (máx. 3-5)
- Considere adicionar delays entre requests
- Respeite os termos de serviço das plataformas

### Espaço em Disco

- Vídeos em alta qualidade ocupam muito espaço
- Use `--max-res` para limitar qualidade
- Configure limpeza automática ou use `--drive-upload` + exclusão local

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto é fornecido "como está", sem garantias. Use por sua conta e risco, respeitando os direitos autorais e termos de serviço das plataformas de origem.

---

## 🆘 Troubleshooting

### Erro: "ffmpeg not found"

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Baixe de https://ffmpeg.org/download.html
```

### Erro: "No video formats found"

- Verifique se a URL está acessível
- Tente adicionar `--cookies-file` se o conteúdo requer login
- Verifique se não há proteção DRM

### Upload para Drive falha

- Verifique se `credentials.json` é válido
- Delete `token.json` e reautentique
- Confirme que a API do Google Drive está ativada

### Downloads muito lentos

- Aumente `--concurrent-fragments` (padrão: 10, tente 15-20)
- Use `--workers` para paralelizar múltiplos vídeos
- Verifique sua conexão de internet

---

## 📚 Recursos Adicionais

- [Documentação do yt-dlp](https://github.com/yt-dlp/yt-dlp#readme)
- [Google Drive API](https://developers.google.com/drive/api/guides/about-sdk)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

---

**Desenvolvido para arquivamento ético de conteúdo público**
