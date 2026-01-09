# Frontend Improvements - Status Final

**Data de Criação:** 2025-11-29
**Última Atualização:** 2025-11-30
**Stack:** Next.js 15 + TypeScript + shadcn/ui + Tailwind CSS

Este documento lista as melhorias implementadas no frontend do YT-Archiver.

---

## Status das Implementações

| # | Melhoria | Status | Arquivos |
|---|----------|--------|----------|
| 1 | Centralizar URL da API | ✅ Implementado | `lib/api-config.ts`, `hooks/use-api-url.ts` |
| 2 | Corrigir Memory Leak no Polling | ✅ Implementado | `components/home/download-form.tsx` |
| 3 | Criar Camada de API Centralizada | ✅ Implementado | `lib/api-client.ts` |
| 4 | Remover Duplicação de formatBytes | ✅ Implementado | `lib/utils.ts` |
| 5 | Criar Error Boundary | ✅ Implementado | `components/common/error-boundary.tsx` |
| 6 | Substituir alert() por mensagens inline | ✅ Implementado | `components/drive/sync-panel.tsx`, `components/drive/drive-video-grid.tsx` |
| 7 | Adicionar useCallback para Event Handlers | ✅ Implementado | 8+ componentes |
| 8 | Adicionar AbortController às Requisições | ✅ Implementado | `hooks/use-fetch.ts` |
| 9 | Migrar ESLint para Flat Config | ✅ Implementado | `eslint.config.mjs` |
| 10 | Migrar Video Player de Plyr para Vidstack | ✅ Implementado | `components/common/videos/video-player.tsx` |
| 11 | Upload Externo para o Drive | ✅ Implementado | `components/drive/external-upload-modal.tsx`, `sync-panel.tsx` |
| 12 | Download do Drive para Local | ✅ Implementado | `components/drive/sync-panel.tsx`, `lib/api-urls.ts` |

---

## Funcionalidades Recentes (v2.2+)

### 10. Migração do Video Player de Plyr para Vidstack

**Status:** ✅ Implementado
**Commit:** `9b9f4a5`
**Impacto:** Alto (UX)

**Implementação:**
- Substituição do player Plyr (deprecado) pelo Vidstack para uma experiência moderna
- Componente `VideoPlayer` unificado para vídeos locais e do Drive
- Remoção do componente `DriveVideoPlayer` duplicado (code deduplication)

**Novas Features:**
- Toggle de loop para repetição de vídeo
- Controle de velocidade de reprodução (0.25x - 2x)
- Seek step de 10 segundos
- Suporte a Picture-in-Picture
- Integração com Google Cast
- Atalhos de teclado (k/Space, m, i, f)
- Tema escuro com esquema de cores automático
- Acessibilidade melhorada (ARIA labels, roles)

**Arquivos Modificados:**
- `components/common/videos/video-player.tsx` - Reescrito com Vidstack
- `app/layout.tsx` - Atualização de CSS imports

**Dependências Adicionadas:**
- `@vidstack/react` (v1.12.13)

---

### 11. Upload Externo para o Drive

**Status:** ✅ Implementado
**Commit:** `6ab1e18`
**Impacto:** Médio (Feature)

**Implementação:**
- Modal para upload de arquivos externos do PC para o Google Drive
- Suporte a arquivos extras (thumbnails, legendas, transcrições)
- Auto-preenchimento do nome da pasta baseado no nome do vídeo
- Barra de progresso durante upload com indicador de arquivo atual

**Arquivos Criados/Modificados:**
- `components/drive/external-upload-modal.tsx` - Novo componente modal
- `components/drive/sync-panel.tsx` - Botão "Upload Externo" adicionado

---

### 12. Download do Drive para Local

**Status:** ✅ Implementado
**Commit:** `dcf5e89`
**Impacto:** Alto (Feature)

**Implementação:**
- Download de vídeos do Google Drive para armazenamento local
- Botão "Baixar Todos" para downloads em lote
- Botões individuais de download na seção "Apenas Drive"
- Barra de progresso de download (tema roxo para diferenciar do upload azul)
- Atualizações de progresso em tempo real via job polling
- Progresso exibido tanto para downloads em lote quanto individuais

**Arquivos Modificados:**
- `components/drive/sync-panel.tsx` - Interface de download completa
- `lib/api-urls.ts` - URLs `DRIVE_DOWNLOAD` e `DRIVE_DOWNLOAD_ALL`

**Estados Adicionados:**
```typescript
const [downloading, setDownloading] = useState(false);
const [downloadingVideo, setDownloadingVideo] = useState<string | null>(null);
const [downloadProgress, setDownloadProgress] = useState<DownloadProgress | null>(null);
```

**Funções Adicionadas:**
- `pollDownloadProgress()` - Polling de progresso de download
- `handleDownloadAll()` - Download de todos os vídeos do Drive
- `handleDownloadSingle()` - Download de vídeo individual

---

### Bug Fixes (v2.2+)

#### Fix: Vídeos do Drive não reproduziam após migração para Vidstack

**Commit:** `e2e2823`
**Problema:** Vidstack enviava requisição HEAD para detectar tipo de mídia, backend retornava 405
**Solução:** Especificar tipo explicitamente: `src={{ src: videoUrl, type: "video/mp4" }}`

#### Fix: Poster aparecia como faixa no meio do player

**Commit:** `e2e2823`
**Problema:** Componente Poster do Vidstack renderizando incorretamente
**Solução:** Remoção do componente Poster do video-player.tsx

---

## Arquivos Criados/Modificados

### Novos Arquivos

```
frontend/src/
├── lib/
│   ├── api-config.ts          # URL da API centralizada
│   └── api-client.ts          # Cliente HTTP tipado
├── hooks/
│   ├── index.ts               # Barrel export
│   ├── use-api-url.ts         # Hook SSR-safe para URL da API
│   └── use-fetch.ts           # Hook com AbortController
└── components/
    └── common/
        └── error-boundary.tsx # Error Boundary com retry
```

### Arquivos Modificados

- `components/home/download-form.tsx` - Memory leak fix (pollingCleanupRef)
- `components/common/theme-provider.tsx` - useCallback para setTheme/toggleTheme
- `components/common/videos/video-card.tsx` - Usa useApiUrl
- `components/drive/sync-panel.tsx` - Mensagens inline (Alert)
- `components/drive/drive-video-grid.tsx` - useApiUrl + useCallback
- `components/drive/drive-auth.tsx` - useApiUrl
- `components/library/paginated-video-grid.tsx` - useApiUrl + useCallback
- `app/drive/page.tsx` - useApiUrl

### ESLint

- **Deletado:** `.eslintrc.json` (formato antigo)
- **Criado:** `eslint.config.mjs` (flat config ESLint 9)
- **Atualizado:** `package.json` - script lint usa ESLint CLI diretamente

---

## Detalhes das Implementações

### 1. Centralização da URL da API

**Problema:** Lógica de resolução de URL duplicada em 9+ arquivos.

**Solução:**

```typescript
// src/lib/api-config.ts
const DEFAULT_API_URL = "http://localhost:8000";

export function getApiUrl(): string {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL;
  }
  return DEFAULT_API_URL;
}

export function buildApiUrl(endpoint: string): string {
  const baseUrl = getApiUrl();
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint.slice(1) : endpoint;
  return `${baseUrl}/${cleanEndpoint}`;
}

// src/hooks/use-api-url.ts - SSR-safe
export function useApiUrl(): string {
  const [apiUrl, setApiUrl] = useState("");
  useEffect(() => {
    setApiUrl(getApiUrl());
  }, []);
  return apiUrl;
}
```

---

### 2. Memory Leak no Polling

**Problema:** setTimeout sem cleanup no polling de jobs.

**Solução:** `pollingCleanupRef` em `download-form.tsx`:

```typescript
const pollingCleanupRef = useRef<(() => void) | null>(null);

// Na função de polling
return () => {
  cancelled = true;
  if (timeoutId) clearTimeout(timeoutId);
};

// No useEffect de cleanup
useEffect(() => {
  return () => {
    if (pollingCleanupRef.current) {
      pollingCleanupRef.current();
    }
  };
}, []);
```

---

### 3. Camada de API Centralizada

**Arquivo:** `src/lib/api-client.ts`

```typescript
class ApiClient {
  async get<T>(endpoint: string, options?: RequestInit): Promise<T>
  async post<T>(endpoint: string, body?: unknown, options?: RequestInit): Promise<T>
  async put<T>(endpoint: string, body?: unknown, options?: RequestInit): Promise<T>
  async delete(endpoint: string, options?: RequestInit): Promise<void>
  getStreamUrl(endpoint: string): string
}

export const api = new ApiClient();
```

---

### 4. Error Boundary

**Arquivo:** `src/components/common/error-boundary.tsx`

```typescript
export class ErrorBoundary extends Component<Props, State> {
  static getDerivedStateFromError(error: Error): State
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void
  handleRetry = () => void
  render(): ReactNode
}

// HOC para facilitar uso
export function withErrorBoundary<P extends object>(
  WrappedComponent: ComponentType<P>,
  fallback?: ReactNode
): ComponentType<P>
```

---

### 5. useFetch Hook

**Arquivo:** `src/hooks/use-fetch.ts`

```typescript
export function useFetch<T>(
  url: string | null,
  options?: UseFetchOptions<T>
): UseFetchResult<T>

export function useMutation<TData, TVariables>(
  mutationFn: MutationFn<TData, TVariables>,
  options?: UseMutationOptions<TData>
): UseMutationResult<TData, TVariables>
```

Features:
- AbortController para cancelamento
- Cleanup automático no unmount
- Estados de loading/error
- Função refetch

---

### 6. ESLint Flat Config

**Arquivo:** `eslint.config.mjs`

```javascript
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";
import nextPlugin from "@next/eslint-plugin-next";

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    plugins: { react, "react-hooks", "@next/next" },
    rules: { /* ... */ }
  }
);
```

**Dependências adicionadas:**
- `@eslint/js`
- `typescript-eslint`
- `eslint-plugin-react`
- `@next/eslint-plugin-next`

---

## Validação

### Comandos de Teste

```bash
# Lint (0 errors, 7 warnings)
npm run lint

# Build (sucesso)
npm run build

# TypeScript check (sem erros)
npx tsc --noEmit
```

### Warnings Restantes

Sem warnings críticos registrados na última revisão.  
Se quiser validar novamente, rode `npm run lint`.

---

## Melhorias Futuras (Não Implementadas)

| # | Melhoria | Prioridade |
|---|----------|------------|
| 1 | Adicionar ARIA Labels | Baixa |
| 2 | Implementar Testes Automatizados (Jest) | Média |
| 3 | Adicionar Skeleton Loaders | Baixa |
| 4 | Remover dependência prop-types | Baixa |
| 5 | Implementar Code Splitting | Baixa |
| 6 | Anunciar Estados de Loading | Baixa |

---

## Estrutura Final do Frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Home (Downloads)
│   │   ├── drive/page.tsx        # Google Drive
│   │   ├── library/page.tsx      # Biblioteca
│   │   ├── record/page.tsx       # Gravação
│   │   ├── layout.tsx            # Layout global
│   │   └── globals.css
│   ├── components/
│   │   ├── common/
│   │   │   ├── error-boundary.tsx   # ⭐ Error Boundary
│   │   │   ├── navigation.tsx
│   │   │   ├── theme-provider.tsx
│   │   │   ├── theme-toggle.tsx
│   │   │   ├── videos/
│   │   │   │   ├── video-card.tsx
│   │   │   │   └── video-player.tsx
│   │   │   └── pagination/
│   │   │       ├── index.ts
│   │   │       └── pagination-controls.tsx
│   │   ├── drive/
│   │   │   ├── drive-auth.tsx
│   │   │   ├── drive-page-client.tsx
│   │   │   ├── drive-video-grid.tsx
│   │   │   ├── external-upload-modal.tsx
│   │   │   └── sync-panel.tsx
│   │   ├── home/
│   │   │   └── download-form.tsx
│   │   ├── library/
│   │   │   └── paginated-video-grid.tsx
│   │   ├── record/
│   │   │   └── screen-recorder.tsx
│   │   └── ui/                   # shadcn/ui components
│   ├── hooks/
│   │   ├── index.ts              # ⭐ Barrel export
│   │   ├── use-api-url.ts        # ⭐ Hook URL da API
│   │   └── use-fetch.ts          # ⭐ Hook com AbortController
│   └── lib/
│       ├── api-config.ts         # ⭐ Configuração da API
│       ├── api-client.ts         # ⭐ Cliente HTTP
│       ├── api-urls.ts           # Constantes de URLs
│       ├── url-validator.ts      # Validação de URLs
│       └── utils.ts              # Utilitários (cn, formatBytes)
├── eslint.config.mjs             # ⭐ ESLint flat config
├── package.json
├── next.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

---

**Última atualização:** 2025-11-30
