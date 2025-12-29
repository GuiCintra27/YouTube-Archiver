DRIVE-SHARE-LINKS-BACKEND-PLAN

Escopo
- Criar API para gerar/revogar link publico do Drive.
- Persistir status/link no catalogo local para resposta rapida.
- Exigir OAuth com escopo ampliado.

Dependencias e impacto
- Atualizar SCOPES em app/drive/manager.py para incluir:
  https://www.googleapis.com/auth/drive
- Reautenticacao obrigatoria (token atual nao cobre permissions).

Fluxo principal (share)
1) API: POST /api/drive/videos/{file_id}/share
2) DriveManager.share_video(file_id):
   - Se ja houver permission_id salvo, validar se ainda existe.
   - Caso nao exista, criar permission:
     {type: "anyone", role: "reader"}
   - Buscar webViewLink (fields: webViewLink, permissions)
3) Catalog: salvar em extra_json do video:
   - share_link
   - share_permission_id
4) Retornar {status, shared: true, link}

Fluxo principal (unshare)
1) API: DELETE /api/drive/videos/{file_id}/share
2) DriveManager.unshare_video(file_id, permission_id):
   - Deletar a permissao (permissions.delete).
3) Catalog: remover share_link/permission_id do extra_json.
4) Retornar {status, shared: false}

Fluxo status
- GET /api/drive/videos/{file_id}/share
- Resposta preferencial via catalogo (extra_json).
- Se ausente, opcionalmente checar Drive API (permissions.list + webViewLink).

Persistencia no catalogo
- Reutilizar extra_json do video (location=drive).
- Metodos utilitarios em CatalogRepository:
  - get_drive_share_metadata(file_id) -> {link, permission_id}
  - set_drive_share_metadata(file_id, link, permission_id)
  - clear_drive_share_metadata(file_id)

Erros e mensagens
- 401/403: token sem escopo drive.
- 404: video inexistente no catalogo.
- 500: falha ao criar permissao.
- Mensagens claras para UI.

Endpoints
- POST /api/drive/videos/{id}/share
- DELETE /api/drive/videos/{id}/share
- GET /api/drive/videos/{id}/share

Notas de seguranca
- Link publico nao expira automaticamente.
- Permissao e por arquivo (nao pasta).
