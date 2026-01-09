FRONTEND-SSR-CACHE-PHASE3

Objetivo
- Implementar SSR dos "Recentes" nas paginas / e /record.
- Usar cache nativo do Next com tag dedicada para recentes.
- Manter atualizacao client-side (eventos e refreshToken).

Escopo
- Criar fetch server-side para recentes com revalidate 20s e tag "videos:recent".
- Atualizar RecentVideos para aceitar initialData e evitar fetch duplicado.
- Converter /record para Server Component com client wrapper.

Arquitetura
1) Server data
   - fetchRecentVideos(limit) com revalidate 20s e tag "videos:recent".
2) Page SSR
   - / (home): injeta initialData no RecentVideos.
   - /record: Server Component injeta initialData no client wrapper.
3) Client hydration
   - RecentVideos recebe initialData e pula fetch inicial.
   - Eventos (yt-archiver:videos-updated) continuam funcionando.

Cache e invalidacao
- Cache: revalidate 20s via fetch server-side.
- Tag: "videos:recent".
- Invalidacao via revalidateTag fica para fase seguinte (mutacoes via route handlers).

Testes recomendados
- Home renderiza recentes sem flash.
- Record renderiza recentes e atualiza ao salvar.
- Evento "yt-archiver:videos-updated" ainda refaz fetch.
