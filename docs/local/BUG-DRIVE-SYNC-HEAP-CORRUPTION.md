BUG-DRIVE-SYNC-HEAP-CORRUPTION

Resumo
- Erro: "free(): corrupted" durante sincronizacao em lote com Drive.
- Impacto: backend travava completamente.

Causa raiz
- O client do Google Drive (google-api-python-client) nao e thread-safe.
- A instancia de service era compartilhada entre threads.
- A sincronizacao roda uploads em paralelo (threads), o que levou a corrupcao de heap
  ao acessar o mesmo client simultaneamente.

Resolucao aplicada
1) Service thread-local
   - Cada thread cria e reutiliza sua propria instancia de service.
   - Evita acesso concorrente a uma unica instancia do client.
2) cache_discovery desabilitado
   - Evita cache global do discovery no client.

Arquivos alterados
- backend/app/drive/manager.py
  - get_service() agora usa threading.local()
  - build(..., cache_discovery=False)

Como validar
- Iniciar o backend e rodar "Sincronizar Todos" com varios videos locais.
- Verificar que o backend nao trava e o job continua com polling normal.

Notas
- O erro e tipico de bibliotecas C nao thread-safe.
- A mudanca nao altera a API, apenas a forma de instanciar o client do Drive.
