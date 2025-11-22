# 🛡️ Sistema Anti-Ban

## 📋 Visão Geral

O YouTube possui sistemas de detecção automática que bloqueiam usuários que baixam muitos vídeos em sequência muito rápida. Este sistema implementa delays e batching inteligente para simular comportamento humano e evitar bloqueios.

## 🚨 Quando Usar

Use proteção anti-ban quando:
- ✅ Baixar playlists com mais de 5-10 vídeos
- ✅ Baixar conteúdo de canais que você não assiste regularmente
- ✅ Usar cookies/conta pessoal (evitar ban na sua conta)
- ✅ Já teve bloqueio anteriormente

**Não é necessário** para:
- ❌ Downloads individuais de 1-2 vídeos
- ❌ Vídeos que você assiste regularmente
- ❌ Quando não está usando cookies de conta

---

## ⚙️ Configurações

### 1. Delay Entre Vídeos

**Descrição:** Pausa (em segundos) entre cada vídeo da playlist.

**Valores Recomendados:**
- `2-3s` - Para playlists pequenas (5-15 vídeos)
- `5-8s` - Para playlists médias (15-50 vídeos)
- `10-15s` - Para playlists grandes (50+ vídeos)

**Exemplo:**
```
Playlist: 10 vídeos, Delay: 5s
Tempo total de espera: 9 × 5s = 45s
```

---

### 2. Vídeos por Batch

**Descrição:** Agrupa downloads em lotes. Após completar um lote, aplica um delay maior.

**Valores Recomendados:**
- `5` - Pausas frequentes (mais seguro)
- `10` - Balanceado
- `20` - Pausas espaçadas (mais rápido)

**Exemplo:**
```
Playlist: 30 vídeos
Batch Size: 10

Baixa vídeos 1-10 → PAUSA LONGA
Baixa vídeos 11-20 → PAUSA LONGA
Baixa vídeos 21-30 → FIM
```

---

### 3. Delay Entre Batches

**Descrição:** Pausa maior (em segundos) entre grupos de vídeos.

**Valores Recomendados:**
- `10-20s` - Para playlists pequenas
- `30-60s` - Para playlists médias
- `60-120s` - Para playlists grandes ou múltiplos downloads no dia

**Combinado com Batches:**
```
Batch Size: 5 vídeos
Batch Delay: 30s

Download 5 vídeos → Pausa 30s → Download 5 vídeos → ...
```

---

### 4. Randomizar Delays

**Descrição:** Varia o tempo de espera em cada pausa para parecer mais humano.

**Como Funciona:**
- Delays individuais: variam entre **80-120%** do valor configurado
- Batch delays: variam entre **90-110%** do valor configurado

**Exemplo:**
```
Delay configurado: 5s
Com randomização:
- Vídeo 1: aguarda 4.2s
- Vídeo 2: aguarda 5.8s
- Vídeo 3: aguarda 5.1s
- Vídeo 4: aguarda 4.7s
```

**Recomendação:** ✅ Sempre habilitar (mais seguro)

---

## 🎯 Presets Recomendados

### 🛡️ Modo Seguro (Recomendado para Playlists Grandes)

```
✓ Delay Entre Vídeos: 5s
✓ Vídeos por Batch: 5
✓ Delay Entre Batches: 30s
✓ Randomizar: SIM
```

**Tempo estimado para 30 vídeos:**
- Delays individuais: 29 × 5s = ~145s (2.4min)
- Delays de batch: 5 × 30s = ~150s (2.5min)
- **Total de espera: ~5 minutos**

**Use quando:**
- Playlist com 20+ vídeos
- Primeira vez baixando deste canal
- Já teve bloqueio anteriormente

---

### ⚖️ Modo Moderado (Balanceado)

```
✓ Delay Entre Vídeos: 3s
✓ Vídeos por Batch: 10
✓ Delay Entre Batches: 15s
✓ Randomizar: SIM
```

**Tempo estimado para 30 vídeos:**
- Delays individuais: 29 × 3s = ~87s (1.4min)
- Delays de batch: 2 × 15s = ~30s
- **Total de espera: ~2 minutos**

**Use quando:**
- Playlist com 10-20 vídeos
- Já baixou vídeos deste canal antes
- Risco moderado de ban

---

### ⚡ Modo Rápido (Sem Proteção)

```
✗ Delay Entre Vídeos: 0s
✗ Vídeos por Batch: Desabilitado
✗ Delay Entre Batches: 0s
✗ Randomizar: NÃO
```

**Tempo estimado:** Sem delays adicionais

**Use quando:**
- Apenas 1-5 vídeos
- Download único do dia
- Não se importa com risco de ban

⚠️ **ATENÇÃO:** Pode causar bloqueio em playlists grandes!

---

## 📊 Cálculo de Tempo Total

**Fórmula:**
```
Tempo Total = Tempo de Download + Tempo de Delays

Tempo de Delays = (N-1) × Delay Individual + (N ÷ Batch Size) × Batch Delay

Onde:
N = número de vídeos
```

**Exemplo Prático:**

```
Playlist: 50 vídeos
Configuração: Modo Seguro
- Delay individual: 5s
- Batch size: 5 vídeos
- Batch delay: 30s

Cálculo:
- Delays individuais: 49 × 5s = 245s (~4min)
- Delays de batch: 10 × 30s = 300s (5min)
- Total de espera: ~9 minutos

Se cada vídeo baixa em ~30s:
- Tempo de download: 50 × 30s = 25min
- Total: 25min + 9min = ~34 minutos
```

---

## 🔬 Detecção do YouTube

**O que o YouTube detecta:**
- ❌ Muitos requests em sequência rápida
- ❌ Downloads sem interação (sem visualização)
- ❌ Padrões robóticos (delays constantes)
- ❌ IPs com muita atividade

**Como este sistema evita:**
- ✅ Delays entre downloads
- ✅ Pausas mais longas entre grupos
- ✅ Randomização (parece humano)
- ✅ Uso de cookies de sessões reais

---

## 💡 Dicas Avançadas

### 1. Combine com Cookies Frescos

```bash
# Exportar cookies do navegador antes de baixar
python main.py download "URL_PLAYLIST" \
  --cookies-from-browser chrome \
  --delay-between-downloads 5 \
  --batch-size 5 \
  --batch-delay 30 \
  --randomize-delay
```

### 2. Divida Playlists Grandes

Ao invés de baixar 100 vídeos de uma vez:
```
Download 1: Vídeos 1-30 (com proteção)
Aguardar 30-60 minutos
Download 2: Vídeos 31-60 (com proteção)
Aguardar 30-60 minutos
Download 3: Vídeos 61-100 (com proteção)
```

### 3. Use VPN/Proxy (Opcional)

Se já foi bloqueado:
- Mude de IP (VPN, proxy, reiniciar modem)
- Use conta diferente
- Aguarde 24-48h antes de tentar novamente

### 4. Monitore Bloqueios

Sinais de que você está sendo detectado:
- ❌ Erro "Sign in to confirm you're not a bot"
- ❌ Captchas frequentes
- ❌ Downloads começam a falhar

**Solução:** Aumentar delays e aguardar algumas horas

---

## 🚀 Uso via Interface Web

1. Acesse a interface: `http://localhost:3000`
2. Cole a URL da playlist
3. Clique em **"Opções Avançadas"**
4. Role até **"Proteção Anti-Ban"**
5. Escolha um preset ou configure manualmente:
   - **🛡️ Seguro** - Para playlists grandes (20+ vídeos)
   - **⚖️ Moderado** - Para playlists médias (10-20 vídeos)
   - **⚡ Rápido** - Sem proteção (1-5 vídeos)
6. Clique em **"Baixar"**

Durante o download, você verá mensagens como:
```
⏳ Aguardando 5s antes do próximo vídeo...
⏳ Pausa entre batches: 30s... (Batch 2 concluído)
```

---

## 📈 Benchmark de Segurança

| Cenário | Risco de Ban | Tempo Extra | Recomendação |
|---------|--------------|-------------|--------------|
| 5 vídeos, sem delay | 🟢 Baixo | 0min | OK sem proteção |
| 10 vídeos, sem delay | 🟡 Médio | 0min | Use Moderado |
| 20 vídeos, sem delay | 🔴 Alto | 0min | Use Seguro |
| 50+ vídeos, sem delay | 🔴 **Muito Alto** | 0min | **Sempre use Seguro** |
| 20 vídeos, Moderado | 🟢 Baixo | ~2min | ✅ Recomendado |
| 50 vídeos, Seguro | 🟢 Muito Baixo | ~10min | ✅ Ideal |

---

## ❓ FAQ

### 1. Por que meu download está "esperando"?

Isso é **normal** e **esperado** quando você ativa proteção anti-ban. O sistema está aplicando delays para evitar bloqueio.

### 2. Posso cancelar durante a espera?

Sim! Clique no botão **"Cancelar"** a qualquer momento.

### 3. As configurações são salvas?

Não, você precisa reconfigurar a cada download. (Feature futura: salvar presets personalizados)

### 4. Qual o delay mínimo seguro?

- **Mínimo recomendado:** 2-3s entre vídeos
- **Ideal:** 5s entre vídeos + batches de 5-10

### 5. Já fui bloqueado, o que fazer?

1. **Aguarde 24-48 horas**
2. Mude de IP (VPN ou reiniciar modem)
3. Use novos cookies (navegador limpo)
4. Configure **Modo Seguro** com delays maiores (10s+)

---

## 🎓 Conclusão

**Recomendação Geral:**

- Para **1-5 vídeos**: Não precisa de proteção
- Para **10-20 vídeos**: Use **Moderado**
- Para **20+ vídeos**: Sempre use **Seguro**
- Se **já foi bloqueado**: Use Seguro + aguarde 24h

**Regra de Ouro:** É melhor esperar alguns minutos extras do que levar ban e não conseguir baixar nada por dias! 🛡️
