DRIVE-SHARE-LINKS-FRONTEND-PLAN

Objetivo
- Adicionar gestao de compartilhamento de videos do Drive via UI.
- UI deve aparecer apenas na pagina do Drive (na biblioteca local nao faz sentido).

Estrutura atual (observacoes)
- VideoCard e reutilizado em:
  - Drive: frontend/src/components/drive/drive-video-grid.tsx
  - Local: frontend/src/components/library/paginated-video-grid.tsx
  - Recentes: frontend/src/components/common/videos/recent-videos.tsx
- VideoCard renderiza o menu de "tres pontinhos" (dropdown) e modais.
- Hoje o VideoCard ja recebe props de contexto (ex: deleteScope).

Abordagem recomendada
- Manter o VideoCard reutilizavel e adicionar prop opcional para compartilhar:
  - shareScope?: "drive" | "none"
  - ou driveShare?: { enabled: boolean, fileId: string }
- Somente DriveVideoGrid passa essa prop; Local/Recentes nao.

UI/Fluxo
1) VideoCard (Drive):
   - Menu de 3 pontos incluir item: "Opcoes de compartilhamento".
   - Ao clicar, abrir modal "Compartilhamento".
2) Modal de Compartilhamento:
   - Toggle: "Compartilhavel publicamente".
   - Campo de link (read-only) + botao "Copiar".
   - Descricao explicando: link publico, sem expiracao, revogavel pelo app.
3) Estados:
   - loading/erro ao consultar status do share.
   - loading/erro ao ativar/desativar.
   - sucesso ao copiar link.

Integracao com API
- GET /api/drive/videos/{id}/share
  - carregar estado inicial do modal.
- POST /api/drive/videos/{id}/share
  - habilitar compartilhamento + receber link.
- DELETE /api/drive/videos/{id}/share
  - revogar compartilhamento.

Pontos de implementacao (arquivos)
1) frontend/src/components/common/videos/video-card.tsx
   - Adicionar prop para share scope do Drive.
   - Incluir item no dropdown apenas quando shareScope="drive".
   - Modal de compartilhamento (shadcn/ui).
2) frontend/src/components/drive/drive-video-grid.tsx
   - Passar shareScope="drive" para VideoCard.
   - Se necessario, repassar file_id do Drive.
3) frontend/src/components/common/videos/recent-videos.tsx
   - Sem mudancas (share desabilitado).

Mensagens e UX
- Toggle "Compartilhavel publicamente" indica estado atual.
- Link so aparece quando compartilhado.
- Copiar link com feedback visual (toast simples ou texto).

Notas
- Evitar alterar componentes da biblioteca local.
- Manter comportamento do menu existente.
