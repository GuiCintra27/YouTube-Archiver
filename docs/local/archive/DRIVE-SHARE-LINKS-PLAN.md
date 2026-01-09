DRIVE-SHARE-LINKS-PLAN

Objetivo
- Permitir gerar link publico do Google Drive para videos do Drive, com permissao de visualizacao.
- Oferecer um painel de gerenciamento de compartilhamento no UI (toggle publico + link).

UX (Drive page)
1) Card do video -> menu de 3 pontos -> "Opcoes de compartilhamento".
2) Abre modal "Compartilhamento":
   - Toggle "Compartilhavel publicamente".
   - Campo com link (read-only) + botao copiar.
   - Texto explicando que o link e publico e sem expiracao (ate revogar).

Backend (API)
- POST /api/drive/videos/{file_id}/share
  - Cria permissao: type=anyone, role=reader.
  - Retorna link: webViewLink (Drive viewer).
- DELETE /api/drive/videos/{file_id}/share
  - Remove permissao criada.
  - Retorna status de revogacao.
- GET /api/drive/videos/{file_id}/share
  - Retorna status atual (publico ou nao) + link se existir.

Persistencia (catalogo)
- Armazenar share_link + permission_id no catalogo (extra_json do video).
- Motivo: facilitar status rapido sem chamada extra ao Drive.

OAuth / Escopo
- Atualizar escopo para "https://www.googleapis.com/auth/drive" (necessario para permissions.create).
- Reautenticar usuario apos update do escopo.
- Manter fallback: se nao autenticado com novo escopo, retornar erro claro.

Riscos e cuidados
- Link publico: qualquer pessoa com o link pode ver o video.
- Sem expiracao automatica (revogar manualmente no app).
- Evitar criar duplicatas de permissao (reusar permission_id salvo).

Passos de implementacao
1) Atualizar escopo OAuth e fluxo de reauth.
2) DriveManager: criar metodos share/unshare/get_share_status.
3) Catalog: persistir share_link e permission_id no extra_json.
4) Drive service + router: novos endpoints.
5) UI: modal no menu de 3 pontos, toggle + copy.
6) Docs: atualizar TECHNICAL-REFERENCE e GOOGLE-DRIVE-FEATURES.
