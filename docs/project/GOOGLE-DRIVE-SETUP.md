# Configuração do Google Drive

Este guia explica como configurar a integração com Google Drive para sincronizar seus vídeos.

## 📋 Pré-requisitos

- Conta Google
- Acesso ao Google Cloud Console
- Backend rodando (API na porta 8000)

## 🔧 Passo 1: Criar Projeto no Google Cloud

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Clique em **"Selecionar projeto"** → **"Novo projeto"**
3. Nome do projeto: `YT-Archiver` (ou outro nome de sua preferência)
4. Clique em **"Criar"**

## 🔑 Passo 2: Ativar Google Drive API

1. No menu lateral, vá em **"APIs e Serviços"** → **"Biblioteca"**
2. Pesquise por **"Google Drive API"**
3. Clique em **"Google Drive API"**
4. Clique em **"Ativar"**

## 🎫 Passo 3: Criar Credenciais OAuth 2.0

### 3.1 Configurar Tela de Consentimento

1. Vá em **"APIs e Serviços"** → **"Tela de consentimento OAuth"**
2. Selecione **"Externo"** (a menos que tenha Google Workspace)
3. Clique em **"Criar"**
4. Preencha:
   - **Nome do app**: YT-Archiver
   - **E-mail de suporte do usuário**: seu email
   - **Logotipo do app**: (opcional)
   - **Domínios autorizados**: `localhost` (para desenvolvimento)
   - **E-mail do desenvolvedor**: seu email
5. Clique em **"Salvar e continuar"**

### 3.2 Adicionar Escopos

1. Clique em **"Adicionar ou remover escopos"**
2. Adicione o escopo:
   - `https://www.googleapis.com/auth/drive.file`
   - (Permite criar e modificar arquivos que o app criou)
3. Clique em **"Atualizar"** e depois **"Salvar e continuar"**

### 3.3 Adicionar Usuários de Teste

1. Clique em **"Adicionar usuários"**
2. Adicione seu email do Google
3. Clique em **"Salvar e continuar"**

### 3.4 Criar Credenciais

1. Vá em **"APIs e Serviços"** → **"Credenciais"**
2. Clique em **"Criar credenciais"** → **"ID do cliente OAuth"**
3. Tipo de aplicativo: **"Aplicativo para computador"**
4. Nome: **"YT-Archiver Desktop"**
5. Clique em **"Criar"**

### 3.5 Baixar Credenciais

1. Após criar, aparecerá um popup com seu **Client ID** e **Client Secret**
2. Clique em **"Baixar JSON"**
3. Salve o arquivo como **`credentials.json`**

## 📁 Passo 4: Configurar no Projeto

1. Copie o arquivo `credentials.json` para a pasta `backend/`:

```bash
cp ~/Downloads/credentials.json ./backend/credentials.json
```

2. Verifique se está no `.gitignore`:

```bash
# O arquivo já deve estar ignorado
cat .gitignore | grep credentials.json
```

## 🚀 Passo 5: Autenticar na Interface Web

1. Inicie o backend:

```bash
cd backend
./run.sh
```

2. Inicie o frontend (em outro terminal):

```bash
cd frontend
npm run dev
```

3. Acesse http://localhost:3000/drive

4. Clique em **"Conectar com Google Drive"**

5. Autorize o aplicativo na tela do Google:
   - Escolha sua conta
   - Clique em **"Permitir"** para dar acesso ao Drive

6. Após autorizar, você será redirecionado de volta e verá seus vídeos!

### Primeiro uso do catálogo (recomendado)

- **Máquina nova (snapshot já existe no Drive):**
  - `POST /api/catalog/drive/import`
- **Drive já populado, sem snapshot:**
  - `POST /api/catalog/drive/rebuild`
- **Indexar vídeos locais existentes:**
  - `POST /api/catalog/bootstrap-local`

## 🔐 Segurança

### Arquivos Sensíveis (NÃO commitar)

Estes arquivos contêm informações sensíveis e **NÃO** devem ser commitados ao Git:

- `backend/credentials.json` - Credenciais OAuth
- `backend/token.json` - Token de acesso gerado após autenticação
- `backend/uploaded.jsonl` - Log de uploads

Todos já estão no `.gitignore`.

### Rotação de Credenciais

Se você acidentalmente expor suas credenciais:

1. Vá ao Google Cloud Console
2. **"APIs e Serviços"** → **"Credenciais"**
3. Clique no lixeira ao lado das credenciais comprometidas
4. Crie novas credenciais seguindo o Passo 3 novamente

## 📊 Estrutura no Drive

Após autenticar, o sistema criará automaticamente:

```
Google Drive/
└── YouTube Archiver/           # Pasta raiz
    ├── Canal A/
    │   ├── Video 1.mp4
    │   └── Video 2.mp4
    └── Canal B/
        └── Playlist/
            └── Video 3.mp4
```

A estrutura de pastas local será espelhada no Drive.

## ❓ Troubleshooting

### Erro: "Credentials file not found"

**Solução:** Certifique-se de que `credentials.json` está em `backend/credentials.json`.

### Erro: "redirect_uri_mismatch"

**Causa:** O redirect URI não está configurado no Google Cloud.

**Solução:**
1. Vá em **"Credenciais"** no Google Cloud Console
2. Edite seu OAuth Client ID
3. Em **"URIs de redirecionamento autorizados"**, adicione:
   - `http://localhost:8000/api/drive/oauth2callback`
4. Salve

### Erro: "Access blocked: Authorization Error"

**Causa:** App está em modo de teste e você não é um usuário autorizado.

**Solução:**
1. Vá em **"Tela de consentimento OAuth"**
2. Em **"Usuários de teste"**, adicione seu email
3. Ou, publique o app (não recomendado para uso pessoal)

### Token expirado

O token expira após algum tempo. O sistema automaticamente renovará o token usando o `refresh_token`. Se isso falhar:

1. Delete `backend/token.json`
2. Autentique novamente no `/drive`

## 🎯 Próximos Passos

Após configurar:

1. ✅ Acesse `/drive` na interface web
2. ✅ Veja status de sincronização (Local vs Drive)
3. ✅ Faça upload de vídeos individuais ou em lote
4. ✅ Gerencie seus vídeos no Drive

## 📚 Recursos Adicionais

- [Google Drive API Documentation](https://developers.google.com/drive/api/v3/about-sdk)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [YT-Archiver README](./README.md)
