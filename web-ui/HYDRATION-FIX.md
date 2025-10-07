# 🔧 Correções de Hidratação - Next.js

## ✅ Correções Aplicadas

### 1. Layout (app/layout.tsx)

Adicionado `suppressHydrationWarning` para evitar warnings de fontes dinâmicas:

```tsx
<html lang="pt-BR" suppressHydrationWarning>
  <body className={inter.className} suppressHydrationWarning>
```

**Por quê?** Fontes do Google (Inter) são carregadas dinamicamente e podem causar diferenças mínimas entre servidor e cliente.

### 2. Next Config (next.config.ts)

Removido `output: "standalone"` e adicionado `reactStrictMode`:

```tsx
const nextConfig: NextConfig = {
  reactStrictMode: true,
};
```

**Por quê?** O modo standalone não é necessário para desenvolvimento e o strict mode ajuda a identificar problemas.

### 3. Download Form (components/download-form.tsx)

**Antes:**
```tsx
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

**Depois:**
```tsx
const getApiUrl = () => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  return "http://localhost:8000";
};

// No componente
const [apiUrl, setApiUrl] = useState("");

useEffect(() => {
  setApiUrl(getApiUrl());
}, []);
```

**Por quê?** Variáveis de ambiente podem ter valores diferentes entre servidor e cliente. Usar `useEffect` garante que seja inicializado apenas no cliente.

---

## 🐛 Outros Erros Comuns de Hidratação

### Erro: Text content does not match

**Causa:** Conteúdo diferente entre servidor e cliente.

**Solução:**
```tsx
const [mounted, setMounted] = useState(false);

useEffect(() => {
  setMounted(true);
}, []);

if (!mounted) return null;
```

### Erro: Extra attributes from server

**Causa:** HTML gerado no servidor tem atributos que o cliente não espera.

**Solução:** Adicionar `suppressHydrationWarning` no elemento específico.

### Erro: useEffect called during render

**Causa:** Tentativa de usar hooks em componentes server.

**Solução:** Adicionar `'use client'` no topo do arquivo.

---

## 📋 Checklist de Hidratação

Ao adicionar novos componentes, verifique:

- [ ] Componente que usa `useState`/`useEffect` tem `'use client'`?
- [ ] Componentes com conteúdo dinâmico (data, hora) têm `suppressHydrationWarning`?
- [ ] Variáveis de ambiente são acessadas apenas no cliente?
- [ ] Fontes customizadas estão no layout com `suppressHydrationWarning`?
- [ ] Componentes de terceiros (Radix UI) estão em componentes client?

---

## 🧪 Como Testar

### 1. Build de Produção
```bash
npm run build
npm start
```

Erros de hidratação aparecem mais no build de produção.

### 2. Console do Navegador

Abra DevTools (F12) e procure por:
- ❌ "Hydration failed"
- ❌ "Text content does not match"
- ❌ "Extra attributes from server"

### 3. React DevTools

Instale a extensão React DevTools e ative "Highlight updates".

---

## 🔍 Debug Avançado

### Modo Verbose

No `next.config.ts`:
```tsx
const nextConfig: NextConfig = {
  reactStrictMode: true,
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
};
```

### Componente de Debug

```tsx
'use client';

import { useEffect, useState } from 'react';

export function HydrationDebug() {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  return (
    <div className="fixed bottom-4 right-4 bg-black text-white p-2 text-xs">
      {isClient ? '✅ Client' : '⏳ Server'}
    </div>
  );
}
```

Adicione no layout para ver quando a hidratação completa.

---

## 📚 Recursos

- [Next.js Hydration Docs](https://nextjs.org/docs/messages/react-hydration-error)
- [React Hydration](https://react.dev/reference/react-dom/client/hydrateRoot)
- [suppressHydrationWarning](https://react.dev/reference/react-dom/components/common#common-props)

---

**Todas as correções foram aplicadas! ✨**
