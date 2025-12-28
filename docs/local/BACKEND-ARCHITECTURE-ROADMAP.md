# Roadmap de Arquitetura do Backend (FastAPI) — YT-Archiver

Este documento detalha melhorias arquiteturais propostas para o backend (`backend/app/`) com foco em **manutenibilidade**, **testabilidade**, **observabilidade** e **evolução incremental** (sem “big bang refactor”).

## Atualização (Catálogo como eixo central)

Além das melhorias “clássicas” de arquitetura, o projeto vai evoluir a fonte de verdade dos dados:

- Antes: listagens dependem de **scan do disco** e/ou **listagem/busca no Drive**.
- Depois: listagens dependem de um **catálogo persistido**:
  - índice local em SQLite
  - snapshot do catálogo do Drive armazenado no próprio Drive

Documentos relacionados:
- Design: `docs/local/BACKEND-CATALOG-DESIGN.md`
- Plano de implementação: `docs/local/BACKEND-CATALOG-IMPLEMENTATION-PLAN.md`

## Objetivos (o “porquê”)

- Reduzir acoplamento entre `router.py` ↔ lógica de negócio ↔ integrações externas (yt-dlp/Drive/FS/SQLite).
- Tornar o comportamento mais previsível via **contratos explícitos** (schemas/DTOs) e **erros padronizados**.
- Facilitar a introdução de melhorias (ex.: nova engine, persistência de jobs, filas, retries) com mudanças localizadas.
- Manter os “gotchas” do projeto:
  - **Downloads via thread/worker** (evitar `async/await` em cima do yt-dlp).
  - **DRM não suportado**.
  - **Rate limiting não deve ser removido**.
  - Streaming precisa manter **HTTP 206 / Range Requests** e **RFC 5987** em headers com Unicode.

## Leitura recomendada antes de mexer

- Visão geral e mapa: `docs/project/TECHNICAL-REFERENCE.md`
- Histórico de correções críticas: `docs/project/BUGS.md`
- Anti-ban e performance: `backend/docs/project/ANTI-BAN.md`, `backend/docs/project/PERFORMANCE-OPTIMIZATION.md`

## Estado atual (resumo)

O backend já é modular no estilo “router/service/schemas”:

- `backend/app/*/router.py` expõe endpoints (FastAPI `APIRouter`)
- `backend/app/*/service.py` contém regras e orquestração
- `backend/app/*/schemas.py` contém modelos Pydantic
- Integrações: `downloads/downloader.py` (yt-dlp), `drive/manager.py` (Google Drive), cache em `drive/cache/*`
- Cross-cutting: `core/logging.py`, `core/errors.py`, `core/validators.py`, `core/rate_limit.py`

Ponto de atenção: existem módulos “legacy” (`core/exceptions.py`, `core/security.py`) coexistindo com os mais novos (`core/errors.py`, `core/validators.py`), o que tende a gerar duplicidade e inconsistência.

## Principais oportunidades de melhoria (observações)

### 1) Routers ainda carregam decisões demais

Mesmo com services, é comum router fazer:

- parsing + validação + tradução para domínio + tratamento de exceção + formatação de resposta

**Meta:** router = “adaptador HTTP”, service = “caso de uso”.

### 2) Erros/validações podem ficar 100% consistentes

O backend já tem `core/errors.py` e `core/validators.py`. A oportunidade é:

- eliminar caminhos alternativos/legacy
- padronizar payload de erro e códigos
- ter um “ponto único” para traduzir exceções internas → HTTP

### 3) Dependências externas e IO sem boundary explícito

Integrações são fontes de instabilidade:

- yt-dlp (rede, parsing, formatos)
- Drive API (OAuth, quota, queries)
- filesystem (paths/unicode)
- sqlite (locks, WAL, concorrência)

**Meta:** encapsular em “clients/adapters” com contratos e timeouts/retries, facilitando testes.

### 4) Jobs: consolidar em um “motor” bem definido

Hoje jobs são in-memory + cleanup. Funciona, mas limita:

- persistência e retomada
- retry/backoff
- priorização
- diagnósticos (métricas, tracing)

**Meta:** introduzir uma “engine” de jobs com API interna estável; trocar storage depois sem reescrever endpoints.

### 5) Observabilidade: tornar debugging barato

Com downloads e streaming, as perguntas típicas são:

- “onde ficou lento?”
- “qual endpoint está gerando mais 500?”
- “qual job ficou travado?”

**Meta:** request-id/correlation-id + logs consistentes + métricas mínimas.

## Arquitetura-alvo (incremental, compatível com o atual)

Uma evolução natural, sem abandonar a estrutura atual:

1. **API Layer (routers)**: recebe HTTP, valida input (Pydantic), chama service, retorna response.
2. **Application Layer (services / use-cases)**: orquestra regras; decide “o que fazer”.
3. **Domain/Policies (opcional)**: regras puras (ex.: construir opções do yt-dlp; sanitização de path).
4. **Infrastructure (adapters/clients)**: Drive client, yt-dlp runner, filesystem, repositories SQLite.

Na prática no repo:

- Continuar com `*/service.py`, mas extrair dependências para classes/contratos.
- Criar subpastas opcionais por módulo quando fizer sentido:
  - `backend/app/jobs/engine.py` (fila/worker)
  - `backend/app/downloads/adapters/yt_dlp_runner.py`
  - `backend/app/drive/adapters/drive_client.py`

## Roadmap proposto (fases)

### Fase 0 — “Sem mudança de comportamento” (baixo risco)

**Entrega:** consistência e observabilidade sem tocar no core das features.

- Padronizar resposta de erro:
  - garantir que routers usem `core/errors.py` como caminho principal
  - criar/usar um exception handler global (em `main.py`) para `AppException` → JSON estável
- Centralizar validações:
  - mover checks repetidos para `core/validators.py` (path/filename/url)
  - reduzir/encapsular uso de `core/security.py`/`core/exceptions.py` (marcar como legado)
- Middleware de correlação:
  - gerar `X-Request-Id` quando ausente
  - incluir request id em logs (via logger/context)

**Critério de aceite**

- O formato de erro fica uniforme em endpoints novos/alterados.
- Logs permitem correlacionar request → erro/tempo.

### Fase Catálogo (recomendada logo após a Fase 0)

**Entrega:** listagens e buscas passam a ser atendidas por um índice local (SQLite) e o Drive passa a ser “consultado” via snapshot (sem busca/listagem de vídeos na API).

- Implementação incremental (feature-flag), sem quebrar contratos:
  - Catálogo 1: DB + bootstrap local
  - Catálogo 2: import do snapshot do Drive
  - Catálogo 3: publish do snapshot do Drive
  - Catálogo 4: desativar fluxos legados (scan por request, cache/listagem antiga do Drive)

Referência: `docs/local/BACKEND-CATALOG-IMPLEMENTATION-PLAN.md`

### Fase 1 — Contratos e injeção leve de dependências (alto ganho, médio risco)

**Entrega:** services mais testáveis e com acoplamento reduzido.

- Definir “ports” (protocolos/interfaces) para dependências críticas:
  - `JobStore` (ex.: get/update/list)
  - `DownloaderRunner` (ex.: start/download/stop)
  - `DriveClient` / `DriveRepository` (para cache)
  - `LibraryRepository` (scan/stream/delete)
- Fazer os services aceitarem dependências por parâmetros (ou factory/provider em `main.py`).
- Manter routers iguais (apenas chamando factories de services).

**Critério de aceite**

- Testes conseguem substituir dependências por fakes sem monkeypatch pesado.
- Mudança de implementação (ex.: store in-memory → sqlite) não altera routers.

### Fase 2 — Jobs Engine “de verdade” (evolução do atual)

**Entrega:** jobs mais previsíveis, com melhor controle operacional.

- Formalizar o modelo de estado (FSM):
  - `queued → running → completed|failed|canceled`
  - timestamps + last_heartbeat + progress
- Separar:
  - “API de jobs” (HTTP) em `jobs/router.py`
  - “motor” em `jobs/engine.py` (fila, worker thread, cancelamento)
  - “store” (persistência) em `jobs/store.py` (interface + impl)
- Adicionar retry/backoff **apenas onde faz sentido** (ex.: Drive list/cache sync; não re-tentar download indefinidamente).

**Critério de aceite**

- Cancelamento é consistente (estado final + liberação de recursos).
- Jobs não “somem” silenciosamente; falhas ficam registradas com erro e stacktrace (quando aplicável).

### Fase 3 — Persistência opcional e escalabilidade local (opcional)

**Entrega:** sobreviver a restart e suportar filas maiores.

- Persistir jobs (SQLite) com migração simples (sem Alembic inicialmente, se quiser manter leve).
- Opcional: separar “worker process” do “API process” (ainda local), mantendo compatibilidade.
- Preparar caminho para Redis/RQ/Celery (sem obrigar agora).

**Critério de aceite**

- Reiniciar o backend não perde histórico de jobs (se habilitado).

## Recomendações por módulo (guidelines)

### `downloads`

- Tratar “construção de opts do yt-dlp” como policy pura:
  - inputs validados → opts finais
  - fácil de testar com unit tests
- Definir claramente “erro de usuário” vs “erro do motor”:
  - URL inválida, path inválido, cookies ausentes → 4xx
  - falha de rede, throttling, erro inesperado do yt-dlp → 5xx (com código específico)
- Sempre manter o modelo: **download roda em thread/worker**, não no event loop.

### `library`

- Manter streaming como concern especializado:
  - Range requests (206) + chunking + headers RFC 5987
  - MIME types centralizados (idealmente `core/constants.py`)
- Separar “scan/cache” do “stream/delete” (para evitar lock/latência cruzada).

### `drive` + `drive/cache`

- Drive API é boundary com falhas comuns (quota, refresh token, 403/429):
  - encapsular retries com backoff para operações idempotentes (list/sync)
  - evitar retry cego para upload grande (melhor resumable upload com checkpoints, se evoluir)
- Cache SQLite:
  - manter WAL mode (já indicado) e separar “sync job” do request path sempre que possível
  - expor estatísticas e health do cache (já há endpoints; reforçar consistência)

### `core`

- “Single source of truth”:
  - erros → `core/errors.py`
  - validação → `core/validators.py`
  - logging → `core/logging.py`
  - constants → `core/constants.py`
- Marcar módulos legacy como compatibilidade (documentar intenção de deprecar).

## Estratégia de migração (sem quebrar o frontend)

- Não renomear endpoints nem mudar contratos JSON sem necessidade.
- Evoluir internamente por trás dos mesmos routers.
- Quando precisar mudar response:
  - introduzir campos novos mantendo os antigos (deprecar com tempo)
  - versionar apenas se inevitável

## Checklist de validação (prático)

- Rodar testes do backend: `backend/tests/*` (pytest)
- Validar endpoints chave:
  - `GET /` (health)
  - `POST /api/download`, `GET /api/jobs/{id}`
  - `GET /api/videos` e `GET /api/videos/stream/...` (range + unicode)
  - Drive: `GET /api/drive/auth-status`, `GET /api/drive/videos`, stream
- Testar com nomes “difíceis”:
  - Unicode (acentos + símbolos como `⧸`)
  - aspas simples (`60's`) em nomes de arquivos/pastas no Drive

## Riscos e trade-offs

- Mais camadas = mais arquivos: mitigar com mudanças incrementais e templates claros.
- Introduzir DI “pesada” cedo pode complicar: prefira **injeção leve** (factories) antes de frameworks.
- Persistência de jobs muda expectativas (limpeza, storage): manter feature flag/config.

## Sugestões de melhorias futuras (nice-to-have)

- Endpoint `/api/health` com checagens opcionais (fs, cache sqlite, drive auth) além do básico.
- Limites de concorrência por tipo de job (download vs cache sync).
- Métricas Prometheus (opcional) e logs JSON (opcional) para análise.
