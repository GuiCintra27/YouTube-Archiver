# ⚡ Solução Rápida - Bloqueio do YouTube

## 🔴 Problema Identificado

```
❌ Seus cookies NÃO contêm dados do YouTube
❌ YouTube bloqueou: "Sign in to confirm you're not a bot"
```

## ✅ Solução em 3 Passos

### Passo 1: Abrir YouTube Logado

1. Abra Chrome
2. Vá para: https://www.youtube.com
3. **FAÇA LOGIN** na sua conta
4. Assista 1-2 vídeos (para gerar cookies frescos)

### Passo 2: Exportar Cookies com DevTools

1. Pressione `F12` (abre DevTools)
2. Clique na aba **Console**
3. Abra o arquivo: `export-cookies-devtools.js`
4. **Copie TODO o conteúdo** do arquivo
5. **Cole no Console** e pressione `Enter`

**Você verá:**
```
🍪 Exportando cookies do YouTube...
✅ CONSENT (YES+cb.20220419...)
✅ VISITOR_INFO1_LIVE (abc123...)
✅ LOGIN_INFO (AFm...)
...
✅ COOKIES COPIADOS PARA CLIPBOARD!
```

### Passo 3: Salvar Cookies

1. Abra: `python/cookies.txt`
2. **Delete todo o conteúdo**
3. **Cole** (Ctrl+V) os cookies copiados
4. **Salve** o arquivo

## 🧪 Testar

```bash
cd python
source .venv/bin/activate

# Testar download
python main.py download "https://www.youtube.com/watch?v=jNQXAC9IVRw" \
  --cookies-file cookies.txt \
  --skip-download
```

**Esperado:**
```
✅ [youtube] jNQXAC9IVRw: Downloading webpage
✅ [youtube] jNQXAC9IVRw: Downloading player...
```

---

## 🚀 Alternativa: Método Automático

**Use cookies direto do navegador (sem exportar):**

```bash
cd python
source .venv/bin/activate

python main.py download "URL" \
  --cookies-from-browser chrome
```

**Navegadores suportados:**
- `chrome`
- `firefox`
- `edge`
- `brave`
- `safari`

---

## ⏰ Se Ainda Não Funcionar

### Opção 1: Aguardar
- Rate limit do YouTube dura **6-24 horas**
- Tente novamente amanhã

### Opção 2: Mudar IP
- Reinicie seu modem/roteador
- Use VPN/Proxy

### Opção 3: Usar Conta Diferente
- Faça login com outra conta Google
- Exporte cookies dessa conta

---

## 📊 Debug

Se quiser ver o diagnóstico completo:

```bash
./debug-youtube-block.sh
```

Isso mostra:
- ✅/❌ Status dos cookies
- ✅/❌ Teste de download
- 💡 Recomendações personalizadas

---

## 💡 Dica Pro

**Prevenir bloqueios futuros:**

1. **Não baixar playlists muito grandes de uma vez**
   ```bash
   # Limite de 10 vídeos por vez
   python main.py download "URL" --limit 10
   ```

2. **Adicionar delay entre downloads** (vai fazer isso no próximo update)

3. **Usar `--cookies-from-browser` sempre**
   - Cookies sempre frescos
   - Sem exportação manual

---

**Boa sorte! 🍀**
