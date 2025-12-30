FRONTEND-SSR-CACHE-PHASE2

Objetivo
- Implementar SSR na pagina /drive com cache nativo do Next.
- Separar autenticacao (server) e interacao (client).
- Injetar dados iniciais no DriveVideoGrid para evitar fetch duplicado.

Escopo
- Server fetch do auth status (no-store).
- Server fetch do primeiro page de videos do Drive (revalidate 60s + tag).
- Criar DrivePageClient para gerenciar estado e interacoes no client.
- Atualizar DriveVideoGrid para aceitar initialData.
- Adicionar loading/error boundaries do segmento /drive.

Arquitetura
1) Server data
   - fetchDriveAuthStatus() com cache "no-store".
   - fetchDriveVideosPage(1, 12) com revalidate 60s e tag "videos:drive".
2) Page SSR
   - frontend/src/app/drive/page.tsx vira Server Component.
   - Renderiza <DrivePageClient initialAuthenticated initialVideos>.
3) Client hydration
   - frontend/src/components/drive/drive-page-client.tsx (novo).
   - DriveAuth permanece client e dispara onAuthenticated.
   - DriveVideoGrid recebe initialData quando autenticado.
4) UX streaming
   - frontend/src/app/drive/loading.tsx
   - frontend/src/app/drive/error.tsx

Cache e invalidacao
- Auth status sem cache (no-store).
- Videos do Drive: revalidate 60s com tag "videos:drive".
- Invalidacao via revalidateTag fica para fase seguinte (mutacoes no Next).

Testes recomendados
- Abrir /drive autenticado: grid renderiza sem flash.
- Abrir /drive sem auth: mostra DriveAuth direto.
- Paginar: fetch client continua funcional.
