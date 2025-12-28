# Plano de Concorrencia (ASGI + to_thread)

Objetivo: manter o backend responsivo com 1 worker mesmo quando rotas fazem IO bloqueante
(requests/googleapiclient/FS/sqlite3), evitando que uma requisição trave todas as outras.

## Contexto

- Hoje usamos 1 worker (uvicorn com --reload) e jobs em memoria.
- Quando um endpoint async chama IO bloqueante, o event loop fica preso.
- Resultado: uma rota lenta impede outras rotas de responderem.

## Escopo (fase atual)

- Aplicar `asyncio.to_thread` onde ha IO bloqueante dentro de `async def`.
- Limitar concorrencia com semaforos em operacoes pesadas.
- Garantir que rotas de streaming nao bloqueiem o loop.

## Fora de escopo (por agora)

- Trocar libs sync por libs async em massa (ex.: googleapiclient -> httpx).
- Migrar jobs em memoria para Redis/DB.
- Rodar multiplos workers em producao sem storage compartilhado.

## Passos (fase 1)

1) **Auditoria rapida de IO bloqueante**
   - Catalogar chamadas sync dentro de `async def`:
     - `requests.get(...)`
     - `drive_manager.list_videos()` / `get_sync_state()`
     - scans de FS / rglob / os.walk
     - sqlite3 sincronizado em loops longos

2) **Criar utilitario de execucao em thread**
   - Funcao helper (ex.: `run_blocking(...)`) com logging basico.
   - Semaforos por dominio (Drive, FS, catalog) para limitar threads.

3) **Aplicar nos endpoints criticos**
   - Drive:
     - listagens ou sync que ainda chamem Drive API.
     - rotas que usam `requests` direto dentro do async.
   - Library:
     - scans locais de videos.
   - Outros endpoints com IO pesado.

4) **Streaming sem travar o loop**
   - Preparar o request em thread e devolver `StreamingResponse`.
   - Evitar abrir conexao HTTP sync no thread principal do event loop.

5) **Checagem rapida**
   - Abrir 2 requests longas em paralelo e confirmar que ambas respondem.
   - Logar tempo de resposta e garantir que nao ha bloqueio total.

## Riscos e mitigacoes

- **Excesso de threads**: usar semaforos (limite baixo e ajustavel).
- **CPU bound**: `to_thread` nao ajuda CPU pesada, apenas IO bloqueante.
- **Jobs em memoria**: continuar com 1 worker ate mover jobs para storage compartilhado.

## Observabilidade (minima)

- Logar inicio/fim das funcoes envoltas em `to_thread`.
- Logar tempo total de execucao nas rotas criticas.

## Proximo passo (fase 2, opcional)

- Migrar operacoes de rede para `httpx.AsyncClient`.
- Mover jobs em memoria para Redis/DB e liberar multiplos workers.

## Status (implementado)

- Criado `backend/app/core/blocking.py` com `run_blocking(...)` e semaforos por dominio.
- Novas settings: `BLOCKING_DRIVE_CONCURRENCY`, `BLOCKING_FS_CONCURRENCY`, `BLOCKING_CATALOG_CONCURRENCY`.
- Endpoints criticos (Drive/Library/Catalog/Recordings) agora usam `to_thread` + limites.
- `stream_video` do Drive evita `requests.get` no event loop (abre stream dentro do generator).
