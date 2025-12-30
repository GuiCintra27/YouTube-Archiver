BACKEND-OPS-OPT-PLAN

Objetivo

- Fortalecer o backend para cenarios de producao (observabilidade, confiabilidade e escalabilidade).
- Manter compatibilidade com o comportamento atual e evitar refactors grandes.
- Demonstrar maturidade tecnica sem aumentar complexidade desnecessaria.

Escopo (itens aprovados)

1) Jobs persistentes com Redis + separacao de worker
2) Timeouts e retry em chamadas externas
3) Observabilidade completa (logs estruturados + metricas Prometheus)
4) Consistencia de response models
5) Testes de integracao criticos

Premissas

- Preservar endpoints existentes e manter respostas compativeis.
- Evitar quebrar o fluxo de execucao atual (FastAPI + threads para IO bloqueante).
- Nenhuma mudanca de infra obrigatoria (Redis opcional, habilitavel por env).

Plano por fases

Fase 0 - Preparacao e configuracao base

- Criar configuracoes via .env para ativar modo prod (ex.: WORKER_ROLE=api|worker).
- Definir feature flags para jobs persistentes e logs estruturados.
- Documentar variaveis e defaults.

Status da fase 0

- Variaveis de WORKER_ROLE e Redis documentadas no .env.example.
- Feature flag JOB_STORE_BACKEND adicionada (memory/redis).

Fase 1 - Jobs persistentes + worker role (Redis)

Problema atual

- jobs_db e active_tasks sao in-memory, perdem estado em restart e nao funcionam bem com multi-workers.
- tasks de background podem duplicar (cada worker inicia lifespan).

Implementacao

- Introduzir um JobStore persistente via Redis.
- Criar interface simples (JobStore) e duas implementacoes:
  - InMemoryJobStore (default, atual)
  - RedisJobStore (habilitavel via env)
- Adicionar variavel WORKER_ROLE:
  - api: inicia API sem loops de background longos
  - worker: inicia apenas os loops (cleanup/cache sync), sem endpoints (ou endpoints limitados)
- Ajustar main.py para iniciar background tasks somente quando WORKER_ROLE=worker (ou quando SINGLE_WORKER=true).
- Documentar modo prod recomendado: 1 worker para API + 1 worker para tarefas.

Status da fase 1

- JobStore Redis com fallback in-memory implementado.
- Lifespan ajustado para respeitar WORKER_ROLE e evitar duplicacao de loops.

Fase 2 - Timeouts e retry em chamadas externas

Problema atual

- Algumas chamadas requests.get nao tem timeout definido.
- Em rede instavel, podem bloquear o worker ou atrasar streaming.

Implementacao

- Centralizar timeouts em settings (DRIVE_HTTP_TIMEOUT, THUMBNAIL_HTTP_TIMEOUT, etc).
- Criar helper para requests com retry (ex.: 2 tentativas, backoff leve, apenas idempotentes GET).
- Aplicar nos pontos criticos:
  - drive.manager list/stream/thumbnail
  - drive.service stream download
- Garantir que streaming continue eficiente (timeouts por fase de conexao/leitura).

Status da fase 2

- Helper HTTP com retry/backoff para GET idempotente.
- Timeouts configuraveis via settings (connect/read/stream).
- Aplicado em Drive manager/service (listagem, thumbnails, streaming).

Fase 3 - Observabilidade (logs + metrics)

Implementacao

- Adicionar logging estruturado opcional (JSON) com toggle LOG_FORMAT=json|text.
- Padronizar campos minimos: request_id, path, status_code, duration_ms.
- Expor endpoint /api/health com detalhes basicos (versao, uptime, settings relevantes).
- Expor endpoint /metrics (Prometheus) com contadores e histogramas de latencia.
- Grafana opcional apenas para visualizacao local (documentado).

Status da fase 3

- LOG_FORMAT suportado (text/json).
- /api/health e /metrics implementados.
- Middleware de métricas com contadores e histogramas.

Fase 4 - Consistencia de response models

Implementacao

- Garantir Pydantic models para respostas principais (jobs, catalog, drive, downloads).
- Remover respostas ad-hoc quando possivel, mantendo campos atuais.
- Alinhar erros com estrutura padronizada.

Fase 5 - Testes de integracao

Implementacao

- Adicionar testes para:
  - catalog bootstrap/rebuild
  - drive list paginado (com catalog habilitado)
  - range streaming (local e drive)
- Usar fixtures minimas e mocks de Drive quando necessario.

Entregaveis

- Documento de config prod
- JobStore Redis opcional (fallback in-memory)
- Requests com timeout/retry
- Logs estruturados opcionais
- Endpoint /metrics (Prometheus)
- Suite basica de integracao

Riscos e mitigacoes

- Redis como dependencia extra: manter opcional e fall back para in-memory.
- Mudancas de logging: tornar opt-in.
- Background tasks duplicadas: garantir WORKER_ROLE e defaults seguros.

Checklist de saida

- Backend roda com WORKER_ROLE=api sem iniciar loops de background.
- WORKER_ROLE=worker roda loops sem expor endpoints criticos (ou expostos via flag).
- Chamadas externas com timeout/retry definido.
- Logs com request_id + duration.
- Testes criticos passando.
