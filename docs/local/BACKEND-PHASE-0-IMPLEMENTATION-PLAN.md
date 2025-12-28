# Plano de Implementação — Fase 0 (Backend)

Este documento descreve **o que** vamos modificar no backend para executar a **Fase 0** do roadmap (`docs/local/BACKEND-ARCHITECTURE-ROADMAP.md`), antes de iniciar o refactor de fato.

## Escopo da Fase 0

1. **Erros padronizados**: todas as falhas retornam payload consistente (`ErrorResponse`) e ficam bem logadas.
2. **Validações centralizadas**: reduzir duplicidade entre `core/validators.py` e `core/security.py` e padronizar a estratégia.
3. **Correlação (Request ID)**: adicionar `X-Request-Id` nos requests/responses e propagar para logs e respostas de erro.

## Não-objetivos (para evitar “big bang”)

- Não reestruturar módulos (`downloads/jobs/library/drive`) nem mover rotas.
- Não alterar contratos de sucesso (responses 2xx) nem endpoints.
- Evitar mudanças de comportamento observável; quando inevitável, fazer **de forma configurável** e com rollout seguro.

## Estado atual (baseline)

- `backend/app/main.py` já registra handlers via `register_exception_handlers(app)`.
- `backend/app/core/errors.py`:
  - possui handlers para `AppException`, `HTTPException`, `RequestValidationError`;
  - possui handler genérico (`generic_exception_handler`), **mas não está registrado** (comentado).
- Muitos `router.py` usam `try/except Exception` e levantam `HTTPException(status_code=500, detail=str(e))`, o que:
  - padroniza via `http_exception_handler`, mas
  - espalha lógica, perde stacktrace (só fica no log se o router logar) e pode vazar detalhes no `detail`.
- Validações:
  - `downloads/schemas.py` usa `core/validators.py` (bom).
  - `library/drive/recordings` ainda usam `core/security.py` (paths) e `core/exceptions.py` (AppException especializado).

## Decisões arquiteturais da Fase 0

### D1) Request ID como “mínimo essencial”

- Header padrão: `X-Request-Id`
- Comportamento:
  - se o cliente mandar `X-Request-Id`, o backend preserva;
  - caso contrário, gera um novo id (UUID4).
  - sempre retorna `X-Request-Id` na resposta.
- Request ID deve estar disponível para logs e handlers de erro (via `contextvars`).

### D2) Erros 4xx/5xx com payload consistente (contrato compatível)

- Manter o shape atual (`{error_code, message, details}`), permitindo **adições compatíveis**.
- Adição proposta: `request_id` (opcional) em `ErrorResponse`.
  - Não quebra clientes existentes (campo novo).

### D3) Handler genérico (catch-all) configurável

Registrar handler global para `Exception` ajuda a:
- garantir payload consistente para exceptions não tratadas,
- manter stacktrace no log,
- reduzir `try/except` duplicado em routers.

Trade-off:
- em dev, FastAPI normalmente mostra debug/trace melhor sem catch-all.

**Proposta:** introduzir uma flag de configuração para controlar:
- `ENABLE_GENERIC_EXCEPTION_HANDLER` (default: `True`)
- e/ou `DEBUG` (default: `False`) para controlar nível de detalhe no payload.

### D4) Validação/segurança de paths: centralizar sem quebrar imports

Objetivo: reduzir duplicidade e tornar a “API interna” de validação mais clara, **sem** quebrar os imports atuais.

**Estratégia:**
- Criar um novo módulo de “paths/IO validation” em `core/` com funções bem nomeadas.
- Fazer `core/security.py` virar **compat layer** (wrappers), chamando as funções novas.
- Migrar chamadas aos poucos (services/routers) para o módulo novo.

## Mudanças propostas (por arquivo)

### 1) Request ID e contexto

**Adicionar**
- `backend/app/core/request_context.py`
  - `ContextVar[str]` para `request_id`
  - helpers: `get_request_id()`, `set_request_id(id)`, `clear_request_id()`
- `backend/app/core/middleware/request_id.py`
  - middleware Starlette/FastAPI que:
    - lê/gera `X-Request-Id`
    - seta no `request.state.request_id` e no `ContextVar`
    - adiciona `X-Request-Id` na response
    - garante `clear_request_id()` ao final

**Modificar**
- `backend/app/main.py`
  - registrar o middleware logo após criar o app (antes/independente dos routers).

**Critérios de aceite**
- Toda resposta 2xx/4xx/5xx inclui `X-Request-Id`.
- Se o request incluir `X-Request-Id: abc`, a resposta retorna o mesmo valor.

### 2) Logging com request_id

**Modificar**
- `backend/app/core/logging.py`
  - adicionar `logging.Filter` (ou `LogRecordFactory`) para injetar `record.request_id`
    - valor vindo do `ContextVar`, default `"-"`.
  - atualizar `format_string` default para incluir o campo:
    - exemplo: `... | %(request_id)s | ...`
  - garantir que `setup_logging()` aplique o filter no handler.

**Critérios de aceite**
- Logs de requests exibem o mesmo request id retornado na response.
- Logs de background tasks exibem request_id `"-"` (ou similar), sem erro de formatação.

### 3) Erros padronizados + request_id

**Modificar**
- `backend/app/core/errors.py`
  - estender `ErrorResponse` para incluir `request_id: Optional[str] = None`
  - alterar `create_error_response()` para aceitar `request_id` e preenchê-lo
  - em cada handler:
    - extrair request id de `request.state` (fallback header/contextvar)
    - incluir request id em `extra` do logger
    - retornar `ErrorResponse` com `request_id`
  - em `register_exception_handlers(app)`:
    - registrar `Exception` → `generic_exception_handler` condicionado por config (ver abaixo).

**Modificar**
- `backend/app/config.py`
  - adicionar setting(s) para controlar o catch-all:
    - `ENABLE_GENERIC_EXCEPTION_HANDLER: bool = True`
    - opcional: `DEBUG: bool = False` (ou inferir por `LOG_LEVEL == "DEBUG"`)

**Critérios de aceite**
- `RequestValidationError` continua retornando `error_code=VALIDATION_ERROR`.
- `AppException` e `HTTPException` retornam `ErrorResponse` (como hoje).
- Exceções não tratadas retornam `ErrorResponse` com `error_code=INTERNAL_ERROR` (quando habilitado).
- Resposta de erro inclui `request_id` (campo novo) + header `X-Request-Id`.

### 4) Centralização de validações (paths/segurança)

**Adicionar (proposta)**
- `backend/app/core/paths.py` (nome sugerido)
  - funções “source of truth”:
    - `decode_url_path(path: str) -> str` (substitui `sanitize_path`)
    - `encode_filename_rfc5987(filename: str) -> str` (substitui `encode_filename_for_header`)
    - `ensure_relative_path(path: str) -> Path` (substitui `get_safe_relative_path`)
    - `ensure_within_base(file_path: Path, base_dir: Path) -> None` (substitui `validate_path_within_base`)
    - `ensure_file_exists(file_path: Path) -> None` (substitui `validate_file_exists`)
  - manter semântica atual na Fase 0 (sem mudanças “inteligentes” de segurança).

**Modificar**
- `backend/app/core/security.py`
  - virar wrapper/compat:
    - manter funções atuais, mas implementar chamando `core/paths.py`
    - adicionar docstring “LEGACY: preferir app.core.paths”

**Modificar (migração mínima nesta fase)**
- `backend/app/library/router.py` e `backend/app/library/service.py`
- `backend/app/drive/service.py`
- `backend/app/recordings/service.py`
  - trocar imports (quando mexermos nesses arquivos na Fase 0) para usar `app.core.paths` ao invés de `app.core.security`.

**Critérios de aceite**
- Nenhuma mudança de endpoint; apenas refactor interno.
- Todas as funções antigas de `core/security.py` continuam funcionando (backward compat).

### 5) Redução de try/except duplicado em routers (opcional dentro da Fase 0)

Objetivo: reduzir `try/except Exception` que só converte para `HTTPException(500, str(e))`.

**Proposta incremental**
- Após o catch-all global estar habilitado:
  - remover `except Exception` em `downloads/router.py` e `drive/router.py` onde não há tratamento específico.
  - manter `except FileNotFoundError`/exceções de domínio quando houver (ex.: `DriveCredentialsNotFoundException`).

**Critérios de aceite**
- Erros inesperados continuam retornando `ErrorResponse` (via handler global).
- Stacktrace fica no log (via `generic_exception_handler`).

## Plano de execução (ordem recomendada)

1. Implementar `Request ID` (middleware + contextvar).
2. Integrar `request_id` ao logging.
3. Propagar `request_id` ao `ErrorResponse` e habilitar catch-all com flag.
4. Introduzir `core/paths.py` e transformar `core/security.py` em wrapper.
5. Migrar 1–2 módulos (sugestão: `recordings/service.py` e `drive/service.py`) para usar `core/paths.py`.
6. (Opcional) Limpar `try/except` redundantes em routers afetados.

## Testes e validação (após implementação)

### Automatizado
- Rodar: `cd backend && source .venv/bin/activate && pytest -q`
- Adicionar testes direcionados (se não existirem):
  - request id em response (`X-Request-Id`) no endpoint `/`
  - request id em erro (`/api/jobs/nonexistent`) retornando `request_id`

### Manual rápido
- `curl -i http://localhost:8000/` e conferir `X-Request-Id`
- `curl -i -H 'X-Request-Id: teste-123' http://localhost:8000/` e conferir echo
- Forçar erro 404: `curl -i http://localhost:8000/api/jobs/nonexistent-job`

## Observações / desvios durante a implementação

Durante a execução da Fase 0 neste workspace, apareceram limitações do ambiente que exigiram pequenos ajustes para manter testes e endpoints funcionando de forma determinística:

1) **Testes HTTP (pytest)**
- O `fastapi.testclient.TestClient` travou neste ambiente (bloqueio no `anyio.from_thread` / portal).
- Ajuste aplicado: testes passaram a usar `httpx.AsyncClient` com `ASGITransport` e `app.router.lifespan_context(app)` para garantir startup/shutdown corretos.
- Arquivos afetados: `backend/tests/conftest.py`, `backend/tests/test_health.py`, `backend/tests/test_jobs.py`, `backend/tests/test_library.py`.

2) **Drive cache e `aiosqlite`**
- `aiosqlite.connect()` travou neste ambiente, causando travas em `tests/test_drive_cache.py`.
- Ajuste aplicado: rodamos baseline com `pytest -k "not drive_cache"` e desabilitamos Drive cache por default nos testes.
- Observação: isso não impede o desenvolvimento do catálogo (que será SQLite local), mas sugere que devemos evitar dependências do `anyio.to_thread` e revisar como o `aiosqlite` é utilizado quando chegarmos na parte de persistência do catálogo.

3) **Streaming e `FileResponse`**
- `FileResponse` usa threadpool/anyio internamente e, por conta do problema com worker threads, o streaming local travou em testes.
- Ajuste aplicado: `backend/app/library/router.py` foi adaptado para servir vídeo via `StreamingResponse` (inclusive para resposta “full”, sem Range) e thumbnails via `Response(content=read_bytes())`.
- Nota: essa alteração é compatível com o comportamento esperado (206 + headers), mas pode ser revisitada mais tarde para otimizar I/O quando o ambiente suportar threadpool normalmente.

4) **`asyncio.to_thread`**
- Chamadas que usavam `asyncio.to_thread` no path de request causaram travamento/intermitência em teardown de processos de teste neste ambiente.
- Ajuste aplicado: para o Catálogo, evitamos `asyncio.to_thread` e executamos operações SQLite de forma síncrona dentro dos handlers `async` (mantendo o endpoint `async` para não cair no threadpool do FastAPI).

5) **Circular import (`app.library.__init__`)**
- `backend/app/library/__init__.py` exportava `router`, o que passou a causar import circular quando o Catálogo precisou importar helpers de `library/service.py`.
- Ajuste aplicado: `backend/app/library/__init__.py` agora exporta apenas `video_cache`; routers devem ser importados diretamente de `app.library.router`.

## Riscos conhecidos

- Alterar o formato de log pode impactar parsing externo (se houver). Mitigar com campo opcional e default `"-"`.
- Ativar catch-all pode “esconder” detalhes no dev. Mitigar com flag e/ou `DEBUG`.
- Adicionar `request_id` em `ErrorResponse` é compatível, mas o frontend pode exibir mensagens; evitar mudar `message` nesta fase.
