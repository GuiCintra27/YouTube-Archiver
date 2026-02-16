# Arquitetura de Autenticação Multiusuário

Documentação de referência para implementação futura de sistema multi-usuário com OAuth e sessões.

**Status:** Planejado (não implementado)
**Última atualização:** 2025-11-29

---

## Visão Geral

### Arquitetura Atual (Usuário Único)

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │────▶│ Backend  │────▶│ Google   │
│          │     │          │     │ Drive    │
└──────────┘     └──────────┘     └──────────┘
                      │
                      ▼
                 token.json (único)
```

**Limitação:** Um único `token.json` armazena credenciais de um usuário.

### Arquitetura Proposta (Multiusuário)

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │────▶│ Backend  │────▶│ Banco de │     │ Google   │
│ (Next.js)│     │ (FastAPI)│     │ Dados    │     │ Drive    │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                 │                │
     │   JWT/Cookie   │                 │                │
     └────────────────┘                 │                │
                                        │                │
                      ┌─────────────────┴────────────────┘
                      │
              Tokens por usuário
```

---

## Componentes Necessários

### 1. Banco de Dados

#### Esquema Proposto

```sql
-- Tabela de usuários
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- NULL se usar apenas OAuth
    name VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Tabela de sessões (se usar sessões server-side)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,  -- Hash do session token
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Tabela de tokens OAuth externos (Google Drive, etc.)
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'google_drive', 'dropbox', etc.
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expiry TIMESTAMP,
    scopes TEXT[],  -- Array de escopos autorizados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, provider)
);

-- Índices
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_oauth_tokens_user_id ON oauth_tokens(user_id);
```

#### Modelo SQLAlchemy (Python)

```python
# models.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    name = Column(String(255))
    avatar_url = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    oauth_tokens = relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(String)

    # Relationships
    user = relationship("User", back_populates="sessions")


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)  # 'google_drive'
    access_token = Column(String, nullable=False)
    refresh_token = Column(String)
    token_expiry = Column(DateTime)
    scopes = Column(ARRAY(String))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="oauth_tokens")

    # Constraint
    __table_args__ = (
        # Um token por provider por usuário
        {"sqlite_autoincrement": True},
    )
```

---

### 2. Sistema de Autenticação de Usuários

#### Opção A: Autenticação Própria (Email/Senha)

```python
# auth.py
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib

from passlib.context import CryptContext
from jose import JWTError, jwt

from models import User, Session
from database import get_db

# Configurações
SECRET_KEY = "your-secret-key-here"  # Usar variável de ambiente!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


async def authenticate_user(db, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
```

#### Opção B: OAuth Social (Google, GitHub, etc.)

```python
# oauth_providers.py
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()

# Google OAuth (para login, não para Drive)
oauth.register(
    name='google',
    client_id='YOUR_GOOGLE_CLIENT_ID',
    client_secret='YOUR_GOOGLE_CLIENT_SECRET',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# GitHub OAuth
oauth.register(
    name='github',
    client_id='YOUR_GITHUB_CLIENT_ID',
    client_secret='YOUR_GITHUB_CLIENT_SECRET',
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    client_kwargs={
        'scope': 'user:email'
    }
)
```

---

### 3. Middleware de Autenticação

```python
# middleware.py
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from auth import verify_token
from database import get_db
from models import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency para obter usuário atual.
    Verifica JWT no header Authorization ou cookie.
    """
    token = None

    # Tentar obter do header Authorization
    if credentials:
        token = credentials.credentials

    # Fallback: tentar obter do cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verificar token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Buscar usuário
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Versão opcional - não levanta erro se não autenticado"""
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None
```

---

### 4. DriveManager Multiusuário

```python
# drive_manager_v2.py
"""
DriveManager adaptado para multi-usuário.
Tokens são carregados do banco de dados ao invés de arquivo.
"""
from typing import Optional, Dict
from datetime import datetime

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from models import User, OAuthToken

SCOPES = ['https://www.googleapis.com/auth/drive.file']
PROVIDER_NAME = 'google_drive'


class DriveManagerV2:
    """DriveManager com suporte a múltiplos usuários"""

    def __init__(
        self,
        db: Session,
        user: User,
        credentials_path: str = "./credentials.json",
    ):
        self.db = db
        self.user = user
        self.credentials_path = credentials_path
        self._service = None

    @classmethod
    def get_auth_url(cls, credentials_path: str, state: str = None) -> str:
        """
        Gera URL de autenticação OAuth.
        O 'state' pode conter o user_id para vincular após callback.
        """
        flow = Flow.from_client_secrets_file(
            credentials_path,
            scopes=SCOPES,
            redirect_uri='http://localhost:8000/api/drive/oauth2callback'
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=state  # Passar user_id ou session_id
        )

        return auth_url

    @classmethod
    def exchange_code_for_user(
        cls,
        db: Session,
        user: User,
        code: str,
        credentials_path: str
    ) -> OAuthToken:
        """
        Troca código por tokens e salva no banco para o usuário.
        """
        flow = Flow.from_client_secrets_file(
            credentials_path,
            scopes=SCOPES,
            redirect_uri='http://localhost:8000/api/drive/oauth2callback'
        )

        flow.fetch_token(code=code)
        creds = flow.credentials

        # Verificar se já existe token para este usuário/provider
        existing_token = db.query(OAuthToken).filter(
            OAuthToken.user_id == user.id,
            OAuthToken.provider == PROVIDER_NAME
        ).first()

        if existing_token:
            # Atualizar token existente
            existing_token.access_token = creds.token
            existing_token.refresh_token = creds.refresh_token or existing_token.refresh_token
            existing_token.token_expiry = creds.expiry
            existing_token.scopes = list(creds.scopes) if creds.scopes else None
            existing_token.updated_at = datetime.utcnow()
            db.commit()
            return existing_token
        else:
            # Criar novo token
            oauth_token = OAuthToken(
                user_id=user.id,
                provider=PROVIDER_NAME,
                access_token=creds.token,
                refresh_token=creds.refresh_token,
                token_expiry=creds.expiry,
                scopes=list(creds.scopes) if creds.scopes else None
            )
            db.add(oauth_token)
            db.commit()
            db.refresh(oauth_token)
            return oauth_token

    def is_authenticated(self) -> bool:
        """Verifica se o usuário tem token válido do Google Drive"""
        oauth_token = self._get_oauth_token()
        if not oauth_token:
            return False

        creds = self._build_credentials(oauth_token)
        if not creds:
            return False

        if creds.valid:
            return True

        # Tentar refresh
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_refreshed_token(oauth_token, creds)
                return True
            except Exception:
                return False

        return False

    def _get_oauth_token(self) -> Optional[OAuthToken]:
        """Busca token do banco para o usuário atual"""
        return self.db.query(OAuthToken).filter(
            OAuthToken.user_id == self.user.id,
            OAuthToken.provider == PROVIDER_NAME
        ).first()

    def _build_credentials(self, oauth_token: OAuthToken) -> Optional[Credentials]:
        """Constrói objeto Credentials a partir do token do banco"""
        try:
            return Credentials(
                token=oauth_token.access_token,
                refresh_token=oauth_token.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self._get_client_id(),
                client_secret=self._get_client_secret(),
                scopes=oauth_token.scopes or SCOPES
            )
        except Exception:
            return None

    def _get_client_id(self) -> str:
        """Obtém client_id do arquivo de credenciais"""
        import json
        with open(self.credentials_path) as f:
            data = json.load(f)
            return data.get('installed', data.get('web', {})).get('client_id')

    def _get_client_secret(self) -> str:
        """Obtém client_secret do arquivo de credenciais"""
        import json
        with open(self.credentials_path) as f:
            data = json.load(f)
            return data.get('installed', data.get('web', {})).get('client_secret')

    def _save_refreshed_token(self, oauth_token: OAuthToken, creds: Credentials):
        """Salva token atualizado após refresh"""
        oauth_token.access_token = creds.token
        oauth_token.token_expiry = creds.expiry
        oauth_token.updated_at = datetime.utcnow()
        self.db.commit()

    def _get_service(self):
        """Obtém serviço autenticado do Google Drive"""
        if self._service:
            return self._service

        oauth_token = self._get_oauth_token()
        if not oauth_token:
            raise Exception("User not authenticated with Google Drive")

        creds = self._build_credentials(oauth_token)
        if not creds:
            raise Exception("Failed to build credentials")

        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self._save_refreshed_token(oauth_token, creds)
            else:
                raise Exception("Token expired and no refresh token available")

        self._service = build('drive', 'v3', credentials=creds)
        return self._service

    # ... resto dos métodos (upload_video, list_videos, etc.)
    # permanecem iguais, apenas usando self._get_service()
```

---

### 5. Endpoints Atualizados

```python
# api.py (endpoints atualizados)
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from middleware import get_current_user
from models import User
from drive_manager_v2 import DriveManagerV2

router = APIRouter(prefix="/api/drive", tags=["drive"])


def get_drive_manager(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DriveManagerV2:
    """Dependency que cria DriveManager para o usuário atual"""
    return DriveManagerV2(db=db, user=current_user)


@router.get("/auth-status")
async def drive_auth_status(
    drive_manager: DriveManagerV2 = Depends(get_drive_manager)
):
    """Verifica se o usuário atual está autenticado no Drive"""
    return {
        "authenticated": drive_manager.is_authenticated(),
    }


@router.get("/auth-url")
async def get_drive_auth_url(
    current_user: User = Depends(get_current_user)
):
    """Gera URL de autenticação OAuth para o usuário"""
    # Passar user_id no state para vincular após callback
    state = str(current_user.id)
    auth_url = DriveManagerV2.get_auth_url(
        credentials_path="./credentials.json",
        state=state
    )
    return {"auth_url": auth_url}


@router.get("/oauth2callback")
async def oauth2callback(
    code: str,
    state: str,  # user_id passado no state
    db: Session = Depends(get_db)
):
    """Callback OAuth - troca código por tokens para o usuário"""
    # Buscar usuário pelo state
    user = db.query(User).filter(User.id == state).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid state")

    # Trocar código por tokens e salvar
    DriveManagerV2.exchange_code_for_user(
        db=db,
        user=user,
        code=code,
        credentials_path="./credentials.json"
    )

    # Redirecionar para frontend
    return RedirectResponse(url="http://localhost:3000/drive?auth=success")


@router.get("/videos")
async def list_drive_videos(
    drive_manager: DriveManagerV2 = Depends(get_drive_manager)
):
    """Lista vídeos do Drive do usuário atual"""
    if not drive_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with Google Drive")

    videos = drive_manager.list_videos()
    return {"videos": videos, "total": len(videos)}


@router.post("/upload/{video_path:path}")
async def upload_to_drive(
    video_path: str,
    drive_manager: DriveManagerV2 = Depends(get_drive_manager)
):
    """Upload de vídeo para o Drive do usuário atual"""
    if not drive_manager.is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with Google Drive")

    # ... lógica de upload
```

---

## Fluxos de Autenticação

### Fluxo 1: Registro e Login (Email/Senha)

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│ Frontend │                    │ Backend  │                    │ Database │
└────┬─────┘                    └────┬─────┘                    └────┬─────┘
     │                               │                               │
     │ POST /api/auth/register       │                               │
     │ {email, password, name}       │                               │
     │──────────────────────────────▶│                               │
     │                               │ INSERT user                   │
     │                               │──────────────────────────────▶│
     │                               │                               │
     │     {user, access_token,      │                               │
     │      refresh_token}           │                               │
     │◀──────────────────────────────│                               │
     │                               │                               │
     │ Salvar tokens (localStorage   │                               │
     │ ou httpOnly cookie)           │                               │
     │                               │                               │
```

### Fluxo 2: Conectar Google Drive (usuário já logado)

```
┌──────────┐              ┌──────────┐              ┌──────────┐              ┌──────────┐
│ Frontend │              │ Backend  │              │ Google   │              │ Database │
└────┬─────┘              └────┬─────┘              └────┬─────┘              └────┬─────┘
     │                         │                         │                         │
     │ GET /api/drive/auth-url │                         │                         │
     │ (com JWT do usuário)    │                         │                         │
     │────────────────────────▶│                         │                         │
     │                         │                         │                         │
     │    {auth_url}           │                         │                         │
     │◀────────────────────────│                         │                         │
     │                         │                         │                         │
     │ Abrir popup com auth_url│                         │                         │
     │─────────────────────────────────────────────────▶│                         │
     │                         │                         │                         │
     │                         │   Redirect com ?code=   │                         │
     │                         │◀────────────────────────│                         │
     │                         │                         │                         │
     │                         │ Trocar code por tokens  │                         │
     │                         │────────────────────────▶│                         │
     │                         │                         │                         │
     │                         │   {access_token,        │                         │
     │                         │    refresh_token}       │                         │
     │                         │◀────────────────────────│                         │
     │                         │                         │                         │
     │                         │ Salvar tokens p/ user   │                         │
     │                         │────────────────────────────────────────────────▶│
     │                         │                         │                         │
     │   Fechar popup          │                         │                         │
     │◀────────────────────────│                         │                         │
     │                         │                         │                         │
```

### Fluxo 3: Requisição autenticada ao Drive

```
┌──────────┐              ┌──────────┐              ┌──────────┐              ┌──────────┐
│ Frontend │              │ Backend  │              │ Database │              │ Google   │
└────┬─────┘              └────┬─────┘              └────┬─────┘              └────┬─────┘
     │                         │                         │                         │
     │ GET /api/drive/videos   │                         │                         │
     │ Authorization: Bearer   │                         │                         │
     │ {JWT do usuário}        │                         │                         │
     │────────────────────────▶│                         │                         │
     │                         │                         │                         │
     │                         │ Validar JWT             │                         │
     │                         │ Extrair user_id         │                         │
     │                         │                         │                         │
     │                         │ Buscar OAuth token      │                         │
     │                         │────────────────────────▶│                         │
     │                         │                         │                         │
     │                         │   {google_tokens}       │                         │
     │                         │◀────────────────────────│                         │
     │                         │                         │                         │
     │                         │ Listar vídeos           │                         │
     │                         │────────────────────────────────────────────────▶│
     │                         │                         │                         │
     │                         │   {videos}              │                         │
     │                         │◀────────────────────────────────────────────────│
     │                         │                         │                         │
     │   {videos}              │                         │                         │
     │◀────────────────────────│                         │                         │
     │                         │                         │                         │
```

---

## Segurança

### Checklist de Implementação

- [ ] **Senhas:** Hash com bcrypt (custo >= 12)
- [ ] **JWT:** Chave secreta forte (256+ bits), rotação periódica
- [ ] **Tokens no banco:** Criptografar access/refresh tokens (AES-256)
- [ ] **HTTPS:** Obrigatório em produção
- [ ] **CORS:** Restringir origens permitidas
- [ ] **Rate limiting:** Endpoints de login/registro
- [ ] **Cookies:** httpOnly, secure, sameSite
- [ ] **Refresh tokens:** Rotação automática, revogação em logout
- [ ] **OAuth state:** Verificar para prevenir CSRF

### Exemplo de Criptografia de Tokens

```python
# crypto.py
from cryptography.fernet import Fernet
import os

# Gerar chave: Fernet.generate_key()
ENCRYPTION_KEY = os.environ.get("TOKEN_ENCRYPTION_KEY")
fernet = Fernet(ENCRYPTION_KEY)


def encrypt_token(token: str) -> str:
    """Criptografa token antes de salvar no banco"""
    return fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """Descriptografa token ao ler do banco"""
    return fernet.decrypt(encrypted.encode()).decode()
```

---

## Dependências Adicionais

```txt
# requirements.txt (adicionar)

# Banco de dados
sqlalchemy>=2.0.0
asyncpg>=0.29.0  # PostgreSQL async
alembic>=1.13.0  # Migrations

# Autenticação
python-jose[cryptography]>=3.3.0  # JWT
passlib[bcrypt]>=1.7.4  # Password hashing
authlib>=1.3.0  # OAuth client (opcional)

# Segurança
cryptography>=42.0.0  # Criptografia de tokens
python-multipart>=0.0.9  # Form data

# Validação
email-validator>=2.1.0
```

---

## Migração do Sistema Atual

### Passo a Passo

1. **Criar banco de dados**
   ```bash
   createdb yt_archiver
   alembic upgrade head
   ```

2. **Migrar token existente** (se houver usuário inicial)
   ```python
   # Script de migração
   import json
   from models import User, OAuthToken
   from database import SessionLocal

   db = SessionLocal()

   # Criar usuário admin
   admin = User(email="admin@local", name="Admin")
   db.add(admin)
   db.commit()

   # Migrar token existente
   if os.path.exists("./token.json"):
       with open("./token.json") as f:
           token_data = json.load(f)

       oauth_token = OAuthToken(
           user_id=admin.id,
           provider="google_drive",
           access_token=token_data["token"],
           refresh_token=token_data.get("refresh_token"),
           token_expiry=token_data.get("expiry"),
       )
       db.add(oauth_token)
       db.commit()
   ```

3. **Atualizar endpoints** para usar novo DriveManager

4. **Adicionar autenticação** no frontend (NextAuth.js recomendado)

5. **Testar** fluxo completo

---

## Alternativas Simplificadas

### Se não quiser implementar autenticação própria:

#### NextAuth.js (Recomendado para Next.js)

```typescript
// frontend/src/app/api/auth/[...nextauth]/route.ts
import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import { PrismaAdapter } from "@auth/prisma-adapter";
import { prisma } from "@/lib/prisma";

export const authOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    session: ({ session, user }) => ({
      ...session,
      user: { ...session.user, id: user.id },
    }),
  },
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
```

#### Clerk / Auth0 / Supabase Auth

Serviços gerenciados que cuidam de toda a autenticação:
- Clerk: https://clerk.com
- Auth0: https://auth0.com
- Supabase: https://supabase.com/auth

---

## Referências

- [Documentação do Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Documentação do NextAuth.js](https://next-auth.js.org/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/)
- [JWT Best Practices](https://auth0.com/blog/jwt-security-best-practices/)

---

**Este documento serve como referência para implementação futura. A arquitetura atual (single-user) permanece funcional e é adequada para uso pessoal.**
