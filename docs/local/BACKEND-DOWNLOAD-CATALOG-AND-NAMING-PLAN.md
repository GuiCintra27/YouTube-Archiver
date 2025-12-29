BACKEND-DOWNLOAD-CATALOG-AND-NAMING-PLAN

Objetivo
- Garantir write-through do catalogo local apos downloads (video unico e playlist).
- Ajustar naming: remover data e ID do nome do arquivo.
- Prevenir conflitos de arquivos com mensagem amigavel.
- Garantir que "Videos recentes" sejam atualizados apos download.

Problemas observados
- Download conclui, mas catalogo local nao e atualizado (biblioteca e recentes vazios).
- Naming atual adiciona data + ID, mesmo com catalogo tendo IDs.
- Baixar para nome repetido pode sobrescrever ou confundir.

Plano (passos curtos)
1) Diagnostico do write-through
   - Revisar jobs/service.py: progress_callback e coleta de finished_files.
   - Verificar se os paths retornados pelo yt-dlp estao sendo normalizados para DOWNLOADS_DIR.
   - Validar tratamento de playlist (multi video) e download unico.

2) Write-through robusto
   - Garantir que os arquivos finalizados sejam registrados mesmo quando o callback nao retorna "filepath".
   - Usar resultado final do yt-dlp para listar saidas finais.
   - Normalizar todos os paths para o base_dir do backend (DOWNLOADS_DIR).
   - Atualizar catalogo apenas para arquivos de video e com thumbnail detectada.

3) Atualizar naming de saida
   - Alterar template DEFAULT_TEMPLATE para remover data e ID.
   - Para nomes customizados, manter a extensao adicionada automaticamente.
   - Ajustar padrao para: "{uploader}/{playlist}/{title}.ext" (sem data/ID).

4) Regra de conflito
   - Antes de baixar, resolver o caminho final e checar se ja existe.
   - Se existir, abortar com erro claro para o usuario (sem sobrescrever).

5) UI e docs
   - Confirmar atualizacao de "Recentes" depende do catalogo.
   - Ajustar docs/testes se necessario.

Notas
- Evitar alterar o comportamento de subpastas (custom_path) nesta fase.
- Nao mudar o fluxo do Drive, apenas o fluxo local de downloads.
