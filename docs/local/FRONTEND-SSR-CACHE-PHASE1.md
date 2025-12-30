FRONTEND-SSR-CACHE-PHASE1

Objetivo
- Implementar SSR na pagina /library com cache nativo do Next.
- Entregar dados iniciais no HTML para reduzir flash e duplicacao de fetch.
- Manter interacoes no client (paginacao, selecao, modais).

Escopo
- Server fetch com revalidate + tags para videos locais.
- Pagina /library vira Server Component.
- PaginatedVideoGrid aceita initialData e evita fetch inicial duplicado.
- Adicionar loading/error boundaries do segmento /library.

Arquitetura (fase 1)
1) Server data
   - frontend/src/lib/server/api.ts
   - fetchLocalVideosPage(page=1, limit=12) com revalidate 60s e tag "videos:local".
2) Page SSR
   - frontend/src/app/library/page.tsx (Server Component)
   - injeta initialData -> <PaginatedVideoGrid initialData=... />
3) Client hydration
   - frontend/src/components/library/paginated-video-grid.tsx
   - usa initialData e pula o primeiro fetch quando ainda esta na pagina 1.
4) UX streaming
   - frontend/src/app/library/loading.tsx
   - frontend/src/app/library/error.tsx

Cache e invalidacao
- Cache: revalidate 60s via fetch server-side.
- Tag: "videos:local" (futuramente revalidateTag em mutacoes).
- Nesta fase nao ha invalidacao ativa via route handlers (fica para fase 2/3).

Testes recomendados
- Abrir /library e confirmar render com dados sem flash.
- Paginar para outras paginas (client fetch continua funcional).
- Confirmar loading.tsx aparece em refresh rapido (cache cold).

Riscos
- Backend indisponivel pode impactar SSR (ver logs).
- Dados stale ate revalidate (60s).
