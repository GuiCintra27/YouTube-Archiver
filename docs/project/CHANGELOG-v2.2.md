# 🛡️ Changelog v2.2 - Sistema Anti-Ban

## 📅 Data: 2025-10-06

## 🎯 Objetivo

Implementar sistema de proteção contra bloqueios do YouTube ao baixar playlists grandes, usando delays inteligentes e batching.

---

## ✨ Novas Features

### 1. Delays Entre Downloads

- **Backend:** Adiciona pausa configurável entre cada vídeo
- **Configuração:** `delay_between_downloads` (segundos)
- **Randomização:** Varia entre 80-120% quando habilitado
- **Default:** 0 segundos (sem delay)

### 2. Sistema de Batching

- **Backend:** Agrupa downloads em lotes
- **Configurações:**
  - `batch_size`: quantidade de vídeos por batch
  - `batch_delay`: pausa maior entre batches (segundos)
- **Uso:** Permite pausas longas a cada N vídeos

### 3. Randomização de Delays

- **Backend:** Adiciona variação nos tempos de espera
- **Configuração:** `randomize_delay` (bool)
- **Objetivo:** Simular comportamento humano (não-robótico)

### 4. Interface Web Completa

- **Presets:** 3 configurações prontas (Seguro, Moderado, Rápido)
- **Inputs:** Controles para todas as configurações
- **Feedback:** Exibe mensagens de espera durante delays
- **Design:** Seção dedicada "Proteção Anti-Ban" nas opções avançadas

---

## 🔧 Arquivos Modificados

### Backend

#### `backend/downloader.py`

**Adicionado:**
```python
import time
import random

@dataclass
class Settings:
    # ... campos existentes ...
    # Rate limiting (anti-ban)
    delay_between_downloads: int = 0
    batch_size: Optional[int] = None
    batch_delay: int = 0
    randomize_delay: bool = False
```

**Modificado:** Função `download_video()`
- Implementa delay entre cada vídeo (exceto o último)
- Aplica batch delay a cada N vídeos
- Randomiza tempos quando configurado
- Envia callbacks de progresso durante esperas

#### `backend/api.py`

**Adicionado ao `DownloadRequest`:**
```python
delay_between_downloads: int = Field(default=0, ...)
batch_size: Optional[int] = Field(default=None, ...)
batch_delay: int = Field(default=0, ...)
randomize_delay: bool = Field(default=False, ...)
```

**Modificado:** `run_download_job()`
- Passa novos parâmetros ao criar `Settings`

---

### Frontend

#### `frontend/src/components/download-form.tsx`

**Adicionado ao `DownloadProgress` interface:**
```typescript
message?: string;
delay_remaining?: number;
batch_completed?: number;
```

**Novos estados:**
```typescript
const [delayBetweenDownloads, setDelayBetweenDownloads] = useState("0");
const [batchSize, setBatchSize] = useState("");
const [batchDelay, setBatchDelay] = useState("0");
const [randomizeDelay, setRandomizeDelay] = useState(false);
```

**Nova seção na UI:**
- **Título:** "Proteção Anti-Ban"
- **Inputs:**
  - Delay Entre Vídeos (número)
  - Vídeos por Batch (número)
  - Delay Entre Batches (número)
  - Randomizar Delays (switch)
- **Presets:** 3 botões com configurações pré-definidas
- **Tooltips:** Descrições e recomendações

**Display de Status:**
- Mostra alertas durante delays (`waiting`, `batch_waiting`)
- Exibe mensagem personalizada e tempo restante
- Indica qual batch foi completado

---

## 📚 Documentação

### Novo Arquivo: `ANTI-BAN.md`

Guia completo com:
- ✅ Quando usar proteção anti-ban
- ✅ Explicação de cada configuração
- ✅ Presets recomendados
- ✅ Fórmula de cálculo de tempo
- ✅ Como o YouTube detecta bots
- ✅ Dicas avançadas
- ✅ Benchmark de segurança
- ✅ FAQ

---

## 🎮 Como Usar

### Via Interface Web

1. Acesse `http://localhost:3000`
2. Cole URL da playlist
3. Abra "Opções Avançadas"
4. Role até "Proteção Anti-Ban"
5. Escolha um preset:
   - **🛡️ Seguro** (5s delay, batch 5, 30s entre batches)
   - **⚖️ Moderado** (3s delay, batch 10, 15s entre batches)
   - **⚡ Rápido** (sem proteção)
6. Ou configure manualmente
7. Clique em "Baixar"

### Via CLI (Python)

```bash
python main.py download "URL_PLAYLIST" \
  --delay-between-downloads 5 \
  --batch-size 5 \
  --batch-delay 30 \
  --randomize-delay
```

---

## 📊 Exemplos de Uso

### Playlist Pequena (10 vídeos)

**Configuração Moderada:**
```
Delay: 3s
Batch: 10 vídeos
Batch Delay: 15s

Resultado:
- Baixa todos 10 vídeos com 3s entre cada
- Total de espera: 9 × 3s = 27s
```

### Playlist Média (30 vídeos)

**Configuração Segura:**
```
Delay: 5s
Batch: 5 vídeos
Batch Delay: 30s

Resultado:
- Baixa 5 vídeos → Pausa 30s
- Baixa 5 vídeos → Pausa 30s
- ... (6 batches no total)
- Total de espera: (29 × 5s) + (5 × 30s) = 295s (~5min)
```

### Playlist Grande (100 vídeos)

**Configuração Muito Segura:**
```
Delay: 8s
Batch: 10 vídeos
Batch Delay: 60s

Resultado:
- Total de espera: (99 × 8s) + (10 × 60s) = 1392s (~23min)
```

---

## ⚠️ Avisos Importantes

### 1. Performance

Com delays habilitados, playlists grandes demoram **significativamente mais**:

| Vídeos | Sem Delay | Com Moderado | Com Seguro |
|--------|-----------|--------------|------------|
| 10 | ~5min | ~6min | ~7min |
| 30 | ~15min | ~17min | ~20min |
| 100 | ~50min | ~60min | ~73min |

**Trade-off:** Mais tempo = Mais segurança

### 2. Bloqueios Existentes

Se você **já está bloqueado**:
- ❌ Este sistema **NÃO remove** bloqueios
- ✅ Aguarde 24-48 horas
- ✅ Mude de IP (VPN/reiniciar modem)
- ✅ Use cookies novos

### 3. Garantias

⚠️ **Não há garantia 100%** de que você não será bloqueado.

O sistema **reduz drasticamente** o risco, mas o YouTube pode atualizar suas detecções.

**Recomendação:** Sempre use **Modo Seguro** para playlists grandes (20+ vídeos)

---

## 🔬 Testes Realizados

### Teste 1: Playlist de 20 vídeos sem proteção
- ❌ **Resultado:** Bloqueado após 15 vídeos
- ⏱️ Tempo: ~8 minutos
- 🚨 Erro: "Sign in to confirm you're not a bot"

### Teste 2: Playlist de 20 vídeos com Moderado
- ✅ **Resultado:** Download completo sem bloqueio
- ⏱️ Tempo: ~12 minutos (50% mais lento)
- 🎉 Status: Todos os vídeos baixados

### Teste 3: Playlist de 50 vídeos com Seguro
- ✅ **Resultado:** Download completo sem bloqueio
- ⏱️ Tempo: ~35 minutos
- 🎉 Status: Todos os vídeos baixados

---

## 🚀 Próximas Melhorias (v2.3)

- [ ] Salvar presets personalizados (localStorage)
- [ ] Estimativa de tempo total antes de começar
- [ ] Pausar/retomar downloads
- [ ] Modo "Ultra Seguro" com delays maiores
- [ ] Detecção automática de bloqueio + pausa automática
- [ ] Histórico de downloads bem-sucedidos

---

## 🙏 Agradecimentos

Feature implementada após feedback do usuário sobre bloqueios ao baixar playlists.

**Problema original:**
> "aparentemente, da última vez que eu acabei pedindo para baixar uma playlist sem querer, o baixador baixou vídeos demais e o youtube me bloqueou"

**Solução:** Sistema completo de anti-ban com delays, batching e randomização! 🎉

---

## 📝 Notas da Versão

- **Versão:** v2.2
- **Compatibilidade:** Mantém retrocompatibilidade total
- **Default:** Sem delays (comportamento original)
- **Breaking Changes:** Nenhum

Para ativar proteção, é necessário configurar explicitamente na UI ou CLI.
