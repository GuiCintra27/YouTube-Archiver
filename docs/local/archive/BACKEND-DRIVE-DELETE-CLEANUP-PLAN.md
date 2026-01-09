BACKEND-DRIVE-DELETE-CLEANUP-PLAN

Objetivo
- Corrigir a exclusao no Drive para remover video + arquivos relacionados e limpar pastas vazias sem travar a resposta da API.
- Manter a experiencia rapida para o usuario, delegando a limpeza recursiva de pastas para um job em background.

Premissas
- O catalogo local e a fonte primaria de file_id para assets (video, thumbnail, info.json, legendas, transcricao).
- Quando o catalogo nao tiver assets, usar fallback pontual no Drive (listagem no parent com base no nome).
- Nao deletar nada fora da raiz do app (Drive root) e nunca mexer na pasta ".catalog".

Fluxo proposto
1) DELETE (drive)
   - Resolver assets no catalogo (drive_file_id por kind).
   - Obter metadados do video (parents) para descobrir o folder pai real no Drive.
   - Deletar video + assets relacionados via Drive API.
   - Retornar resposta imediata ao cliente.
   - Enfileirar job para limpeza de pastas vazias (async).

2) Job de limpeza de pastas (async)
   - Recebe lista de folder_ids candidatos (pais dos videos deletados).
   - Para cada folder:
     - Verificar se esta vazio com listagem pageSize=1.
     - Se vazio, deletar e subir para o pai.
     - Parar no root do app e nunca deletar ".catalog".
   - Logar resultado (pastas removidas e ignoradas).

Implementacao (passos curtos)
1) DriveManager
   - Novo metodo delete_video_with_related(file_id, related_ids, parent_ids?) que:
     - consulta metadados do arquivo (parents) se necessario,
     - deleta arquivos (video + assets),
     - retorna lista de folder_ids candidatos para limpeza.
   - Novo metodo cleanup_empty_folders(folder_ids, root_id) com regra de parada e listagem minima.

2) Jobs
   - Adicionar JobType.DRIVE_CLEANUP no store (fila interna em memoria, sem Redis por enquanto).
   - Criar task async que roda cleanup_empty_folders via run_blocking + drive semaphore.
   - Retornar cleanup_job_id na resposta do delete (para debug).

3) Services
   - Substituir delete_video/delete_videos_batch para usar o novo fluxo.
   - Manter write-through do catalogo + publish do snapshot como ja esta.
   - Se for batch, deduplicar folders e disparar um unico job.

Observacoes
- Se no futuro precisarmos de Redis, basta trocar a implementacao do store mantendo a mesma interface.
- O job de cleanup eh melhor effort: falhas nao quebram o delete do video, apenas logam warning.
