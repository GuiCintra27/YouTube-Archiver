# YT-Archiver - Relatório de Bugs
**Data**: 2025-11-29 (atualizado)
**Testado em**: localhost:3000
**Backend**: FastAPI rodando em http://0.0.0.0:8000
**Frontend**: Next.js 15 rodando em http://localhost:3000

---

## ✅ BUG #1: Falha no Streaming de Vídeos Locais - **CORRIGIDO**

### Descrição
A reprodução de vídeos da biblioteca local estava falhando. Quando o usuário clicava em um vídeo, o player abria corretamente mas não conseguia carregar a mídia.

### Causa Raiz
**UnicodeEncodeError** no header `Content-Disposition` do HTTP. O caractere '⧸' (U+29F8) presente em alguns nomes de arquivo não podia ser codificado em latin-1, que é o encoding padrão para headers HTTP.

### Solução Implementada
1. **RFC 5987 Encoding**: Alterado o formato do header `Content-Disposition` de `filename="..."` para `filename*=UTF-8''...` com percent-encoding
2. **Suporte a Requisições de Range**: Implementado suporte completo a HTTP 206 Partial Content para streaming com seek
3. **Detecção de Tipo MIME**: Adicionado mapeamento correto de extensões (.mp4, .webm, .mkv, etc.)
4. **Logging Detalhado**: Adicionados logs de depuração para solução de problemas
5. **Tratamento de Exceções**: Envolvido código em try/except com traceback

### Arquivo Modificado
- **Backend**: `backend/app/library/router.py` - Função `stream_video()`

### Código da Correção
```python
from urllib.parse import quote

# Para FileResponse completa
encoded_filename = quote(full_path.name)
headers = {
    "Accept-Ranges": "bytes",
    "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
}

# Para StreamingResponse com range requests
headers = {
    "Content-Range": f"bytes {start}-{end}/{file_size}",
    "Accept-Ranges": "bytes",
    "Content-Length": str(chunk_size),
    "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
}
```

### Teste de Validação
✅ Testado com vídeo: `2021-04-26 - John Park - I'm Always by Your Side (tradução⧸legendado) [1_NcRcvXCqo].webm`
- Player carregou corretamente
- Vídeo reproduziu (duração: 3:48)
- Todos os controles funcionando (play, volume, seek, fullscreen)
- Range requests funcionando (HTTP 206)

---

## ✅ BUG #2: Falha no Upload de Vídeos para Google Drive - **CORRIGIDO**

### Descrição
O upload individual de vídeos para o Google Drive estava falhando. Quando o usuário clicava no botão de sincronização de um vídeo específico, a operação falhava e exibia mensagem de erro.

### Causa Raiz
**Query malformada da Google Drive API** devido a aspas simples (`'`) não escapadas em nomes de arquivo. A API do Google Drive usa aspas simples como delimitadores na query (ex: `name='filename'`), então arquivos com nomes como "Gibson Les Paul 60's Standard" quebravam a query.

### Solução Implementada
1. **Escape de Aspas Simples**: Adicionado `escaped_name = name.replace("'", "\\'")` antes de construir queries
2. **Aplicado em 3 Locais**:
   - `upload_video()`: Para verificação de arquivo existente (linha 196)
   - `upload_video()`: Para verificação de arquivos relacionados (linha 268)
   - `ensure_folder()`: Para verificação de pastas existentes (linha 142)
3. **Logging Detalhado**: Adicionados logs de depuração mostrando queries construídas
4. **Tratamento de Exceções**: Envolvido código em try/except com traceback completo

### Arquivos Modificados
- **Backend**: `backend/app/drive/manager.py`
  - Método `ensure_folder()`
  - Método `upload_video()`

### Código da Correção
```python
# Em upload_video() - linha 196
escaped_file_name = file_name.replace("'", "\\'")
query = f"name='{escaped_file_name}' and '{current_parent}' in parents and trashed=false"

# Em ensure_folder() - linha 142
escaped_name = name.replace("'", "\\'")
query = f"name='{escaped_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"

# Em upload_video() para arquivos relacionados - linha 268
escaped_related_name = related_file.name.replace("'", "\\'")
query = f"name='{escaped_related_name}' and '{current_parent}' in parents and trashed=false"
```

### Teste de Validação
✅ Testado com vídeo: `2025-04-24 - The Kind of Solo You Play With Your Eyes Closed ｜ Gibson Les Paul 60's Standard [UJ0_1SYixVQ].mp4`
- Upload concluído com sucesso
- Alert exibido: "Upload concluído com sucesso!"
- Arquivo criado no Google Drive com ID: `1kQC-ofyeVtPT0sM1JDUUYHX1OkXUu0AV`
- Query escapada corretamente: `name='...60\'s Standard...'`
- HTTP 200 OK

---

## ✅ BUG #3: Drive Sync Panel lento / travando - **CORRIGIDO**

### Descrição
O painel de sincronização do Drive ficava lento/travado ao carregar.

### Causa Raiz
- O sync fazia listagem completa do Drive a cada request.
- IO bloqueante rodando no event loop.

### Solução Implementada
1. **Catálogo persistente (SQLite + snapshot)** para evitar listagens diretas.
2. **Sync paginado** via `/api/drive/sync-items`.
3. **IO bloqueante offload** com `core/blocking.py`.

### Arquivos Modificados
- `backend/app/drive/service.py`
- `backend/app/drive/router.py`
- `backend/app/catalog/*`
- `frontend/src/components/drive/sync-panel.tsx`

### Teste de Validação
✅ Painel abre instantaneamente com listas paginadas.

---

## ✅ BUG #4: Download em lote do Drive não atualizava catálogo local - **CORRIGIDO**

### Descrição
Downloads em lote concluíam, mas os vídeos não apareciam na biblioteca local.

### Causa Raiz
Batch download não fazia write-through no catálogo local.

### Solução Implementada
1. **Write-through após cada download** (`upsert_local_video_from_fs`).
2. **Atualização de thumbnails** quando existirem.

### Arquivo Modificado
- `backend/app/drive/service.py`

### Teste de Validação
✅ Vídeos aparecem imediatamente após o download em lote.

---

## ✅ BUG #5: Crash nativo no download do Drive - **CORRIGIDO**

### Descrição
Erro ocasional: `double free or corruption (!prev)` durante downloads do Drive.

### Causa Raiz
Uso concorrente de `googleapiclient` + `MediaIoBaseDownload` + `BytesIO`.

### Solução Implementada
1. **Download via REST + streaming para disco** (sem `BytesIO`).
2. **Arquivo `.part`** + validação de tamanho.

### Arquivo Modificado
- `backend/app/drive/manager.py`

### Teste de Validação
✅ Downloads em lote sem crash.

---

## ✅ BUG #6: Cleanup job quebrando com jobs_db - **CORRIGIDO**

### Descrição
Erro em logs: `module 'app.jobs.store' has no attribute 'jobs_db'`.

### Causa Raiz
Refactor renomeou o dict interno, mas cleanup ainda referenciava `jobs_db`.

### Solução Implementada
Aliases compatíveis:
- `jobs_db = _jobs_db`
- `active_tasks = _active_tasks`

### Arquivo Modificado
- `backend/app/jobs/store.py`

### Teste de Validação
✅ Loop de cleanup executa sem erros.

---

## Status da Aplicação

### ✅ Funcionalidades Testadas e Funcionando
- [x] Inicialização do backend (FastAPI)
- [x] Inicialização do frontend (Next.js)
- [x] Listagem de vídeos locais (`GET /api/videos` - 200 OK, retorna 72 vídeos)
- [x] Navegação entre páginas (Home ↔ Google Drive)
- [x] Interface do Google Drive (página de autenticação carrega corretamente)
- [x] **Download de vídeos do YouTube** - Testado com sucesso
  - URL testada: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
  - Status: Download concluído com 100% de progresso
  - Backend processou requisição corretamente (`POST /api/download` - 200 OK)
  - Sistema de jobs assíncrono funcionando (polling de status via `GET /api/jobs/{id}`)
- [x] Carregamento de thumbnails dos vídeos (todas as thumbnails carregaram corretamente)
- [x] Sistema de progresso em tempo real para downloads
- [x] **Autenticação OAuth Google Drive** ✅
  - Fluxo de autenticação completo funcionando
  - Token armazenado corretamente
  - Status de autenticação verificado com sucesso
- [x] **Listagem de vídeos do Google Drive** ✅
  - Endpoint `GET /api/drive/videos` retornando 3 vídeos
  - Thumbnails do Drive carregando corretamente
- [x] **Status de sincronização** ✅
  - Endpoint `GET /api/drive/sync-status` funcionando
  - Mostrando corretamente: 72 Local, 3 Drive, 3 Sincronizados
  - Cálculo de progresso (4%) correto
- [x] **Streaming de vídeos do Google Drive** ✅
  - Endpoint `GET /api/drive/stream/{file_id}` funcionando perfeitamente
  - Vídeo reproduzido com sucesso (duração 05:48)
  - Range requests funcionando (206 Partial Content)
  - Player Vidstack funcionando corretamente com vídeos do Drive
- [x] **Reprodução de vídeos locais** ✅ **[CORRIGIDO]**
  - Endpoint `GET /api/videos/stream/{video_path}` funcionando perfeitamente
  - Fix: RFC 5987 encoding para Content-Disposition header
  - Suporte completo a range requests (HTTP 206)
  - Testado com caracteres especiais (⧸, acentos, etc.)
- [x] **Upload individual de vídeos para Google Drive** ✅ **[CORRIGIDO]**
  - Endpoint `POST /api/drive/upload/{video_path}` funcionando
  - Fix: Escape de aspas simples em queries do Google Drive
  - Testado com nomes complexos (|, ', acentos)
  - Upload de arquivos relacionados funcionando (thumbnails, metadata, legendas)
- [x] **Painel de Sync do Drive** ✅ **[CORRIGIDO]**
  - Status e itens paginados funcionando
  - Sem travas no carregamento
- [x] **Download em lote do Drive** ✅ **[CORRIGIDO]**
  - Catálogo local atualizado após cada download

### ❌ Funcionalidades com Problemas
*Nenhum bug crítico identificado no momento*

### ⏳ Funcionalidades Pendentes de Teste
- [x] Upload em lote ("Sincronizar Todos")
- [ ] Deleção de vídeos locais
- [x] Deleção de vídeos do Google Drive
- [ ] Download de playlists completas
- [ ] Opções avançadas de download (qualidade, formato, legendas)

---

## Notas Adicionais
- **Console do Navegador**: Apenas warnings de acessibilidade (DialogContent sem Description)
- **Backend Logs**: ✅ Todos os erros 500 corrigidos
  1. ~~Streaming de vídeos locais (BUG #1)~~ → **CORRIGIDO** (RFC 5987 encoding)
  2. ~~Upload individual para Google Drive (BUG #2)~~ → **CORRIGIDO** (Query escaping)
- **Performance**: Interface responsiva, thumbnails (local e Drive) carregam rapidamente
- **UI/UX**: Aplicação está funcional e visualmente correta
- **Total de vídeos**: 72 vídeos locais, 4 vídeos no Drive (1 novo upload testado)
- **Sistema de Jobs**: Funcionando corretamente com polling automático e atualização de progresso
- **Google Drive Integration**: ✅ 100% funcional
  - OAuth funcionando perfeitamente
  - Streaming do Drive funcionando
  - Listagem e thumbnails do Drive funcionando
  - Upload individual funcionando (corrigido)
  - Suporta caracteres especiais em nomes de arquivo
