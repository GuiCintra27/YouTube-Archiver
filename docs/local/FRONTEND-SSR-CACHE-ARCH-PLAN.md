FRONTEND-SSR-CACHE-ARCH-PLAN

Objetivo
- Reestruturar o frontend para demonstrar dominio de SSR/RSC, cache nativo do Next e invalidacao por tags.
- Separar claramente responsabilidades: Server Components para dados e Client Components para interacao.
- Reduzir TTFB e carregamentos duplicados no client com dados iniciais no HTML.

Principios de arquitetura
- Server Components por padrao; "use client" apenas onde necessario.
- BFF no Next (route handlers) para mutacoes + revalidateTag.
- Cache por tags e politicas claras por dominio (local, drive, jobs).
- Paginas com loading.tsx e error.tsx para streaming e resiliencia.
- Evitar bibliotecas extras (SWR/React Query) para manter foco no core do Next.

Estrutura proposta
- frontend/src/app/
  - page.tsx (Server Component)
  - library/page.tsx (Server Component)
  - drive/page.tsx (Server Component)
  - record/page.tsx (Server Component com client islands)
  - (route handlers) app/api/*
- frontend/src/lib/server/
  - api.ts (fetch server-side com cache/tags)
  - tags.ts (constantes de tags)
  - types.ts (tipos compartilhados)
- frontend/src/lib/client/
  - api.ts (fetch client-side para mutacoes via /api/* do Next)
  - hooks.ts (hooks de polling/refresh)

Politica de cache (Next fetch)
- Lista de videos locais: revalidate 30-60s + tag "videos:local".
- Lista de videos do Drive: revalidate 30-60s + tag "videos:drive".
- Auth status do Drive: no-store (ou revalidate 5s, se aceitavel).
- Sync status/jobs: no-store (dados muito dinamicos).
- Recentes: revalidate 10-20s + tag "videos:recent".

Invalicao por tags (Next Route Handlers)
- Mutacoes locais
  - delete/rename/update thumb: revalidateTag("videos:local") + "videos:recent".
- Mutacoes Drive
  - delete/rename/update thumb/share: revalidateTag("videos:drive").
  - upload/download/sync: revalidateTag("videos:drive") e "videos:local" (se afetar local).
- Auth Drive
  - autenticar/desautenticar: revalidateTag("drive:auth") (se usado).

Componentizacao (RSC + Client Islands)
- Paginas (Server)
  - /: renderiza hero estatico + injeta <RecentVideos initialData>.
  - /library: renderiza hero estatico + <PaginatedVideoGrid initialData>.
  - /drive: decide auth no server; se autenticado renderiza hero + <DriveVideoGrid initialData>.
  - /record: hero estatico + <ScreenRecorder /> (client).
- Componentes client permanecem para:
  - DownloadForm (interacao com jobs)
  - SyncPanel (polling)
  - Video grids (paginacao client-side, selecao, modais)

Route Handlers (BFF no Next)
- app/api/videos/*
- app/api/drive/*
- Funcoes:
  - Proxy para backend usando NEXT_PUBLIC_API_URL
  - revalidateTag conforme mutacao
  - padronizar erros (status + message)

Loading/Error boundaries
- app/library/loading.tsx e app/library/error.tsx
- app/drive/loading.tsx e app/drive/error.tsx
- app/record/loading.tsx (opcional)
- Mantem UX de streaming e resiliencia em SSR

Seguranca e performance
- Evitar SSR de dados sensiveis (apenas metadados publicos dos videos).
- Preferir fetch server-side com cache, evitando duplicar chamadas no client.
- Manter polling apenas onde necessario (jobs/sync status).

Plano de fases
Fase 0 (fundacao)
- Criar lib/server (fetch com tags) e tags.ts
- Criar app/api/* (route handlers) para mutacoes principais

Fase 1 (SSR Biblioteca)
- Converter /library para Server Component
- Passar initialData para PaginatedVideoGrid
- Client faz fetch apenas ao paginar

Fase 2 (SSR Drive)
- Server fetch auth status
- Se autenticado: initialData do DriveVideoGrid
- SyncPanel permanece client (no-store)

Fase 3 (SSR Recentes)
- / e /record com initialData em RecentVideos
- Tag "videos:recent" invalida em downloads/recordings

Fase 4 (polimento)
- Adicionar loading.tsx/error.tsx
- Atualizar docs oficiais (README + docs/project)

Riscos e cuidados
- Evitar cache stale para jobs/sync (usar no-store).
- Garantir que route handlers invalidem tags corretas.
- Ajustar revalidate time conforme volume de uso.

Checklist de qualidade
- TTFB com dados iniciais (sem flash de vazio).
- Requests reduzidas no client.
- Invalicao consistente apos mutacoes.
- Observabilidade via logs de route handlers.
