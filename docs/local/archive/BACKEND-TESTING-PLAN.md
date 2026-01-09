BACKEND-TESTING-PLAN

Objetivo

- Expandir a cobertura para demonstrar senioridade sem inflar complexidade.
- Priorizar confiabilidade, regressao e observabilidade do backend.
- Manter execucao rapida no CI local (pytest) e separar suites pesadas.

Principios

- Teste pequeno e deterministico primeiro (unit), depois integracao, e2e opcional.
- Sem rede real nos testes (mock de Drive/requests).
- Fixtures isoladas (tmp_path, db em memoria, env patch).
- Evitar flakes: nada dependente de clock real sem controle.

Estrutura sugerida

- tests/unit/
  - core/ (validators, security, paths, rate_limit helpers)
  - catalog/ (repository, snapshot codec)
  - drive/ (path parsing, helper funcs)
  - jobs/ (store + service)
- tests/integration/
  - api/ (endpoints com AsyncClient e lifespan)
  - streaming/ (range requests e headers)
  - drive-cache/ (cache endpoints e toggles)
- tests/e2e/ (opcional)
  - fluxo UI->API (Playwright) com backend local em modo test

Padrao de nomes

- test_<modulo>_<acao>_<resultado>.py
- marcar com @pytest.mark.integration e @pytest.mark.e2e quando necessario.

Ferramentas

- pytest + pytest-asyncio (ja presentes).
- httpx.AsyncClient (ja usado).
- fakeredis (opcional) para Redis sem infra externa.
- requests mock: monkeypatch (padrao atual) ou responses (opcional).

Cobertura alvo por area

1) Jobs
   - SSE: /api/jobs/{job_id}/stream (progress stream + encerramento).
   - Cancelar job em execucao com task ativa (task cancel + status).
   - Redis JobStore: persistencia entre instancias e lock de job_id.

2) Drive
   - Cache endpoints com DRIVE_CACHE_ENABLED on/off.
   - Sync status quando catalog off (counts, warnings).
   - Rename/thumbnail/delete com write-through e publish.

3) Catalog
   - publish com force/require_import_before_publish.
   - import vazio vs snapshot valido (mensagens de erro).
   - drive rebuild com publish opcional.

4) Library
   - rename/update-thumbnail: atualiza catalogo quando habilitado.
   - delete batch: remove assets e catalogo.
   - range requests invalidas (416, headers).

5) Observabilidade
   - /api/health conteudo esperado (status, version, worker_role).
   - /metrics exposto quando habilitado.
   - request_id preservado em erros.

Fases sugeridas

Fase A - Unit (rapido)
- validators/security/path utils
- catalog snapshot codec
- jobs store/service (memoria + redis opcional)

Fase B - Integracao (API)
- endpoints criticos com AsyncClient
- SSE e streaming
- drive cache e catalog toggles

Fase C - E2E (opcional)
- Playwright cobrindo fluxo de Drive share
- Fluxo download -> aparece na biblioteca -> delete

Checklist de saida

- Suite unit < 30s local.
- Integracao com markers e sem rede real.
- E2E isolado e executado sob demanda.

Status atual

- Fase A concluida: paths core, security wrappers, request context, rate limit helpers,
  error helpers, snapshot codec, validators extra, HTTP retry e jobs store/service cobertos.
- Fase B concluida: SSE de jobs, cache do Drive (enabled/disabled), publish do catalogo,
  status/bootstrap do catalogo, sync status/items, upload job completion e delete batch da library cobertos.
- Fase C concluida: e2e com servidor local (health/root/catalog status) validado.
