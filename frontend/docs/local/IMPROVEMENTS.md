# Frontend Improvements Roadmap

**Data de Criação:** 2025-11-29
**Última Atualização:** 2025-11-29
**Stack:** Next.js 15 + TypeScript + shadcn/ui + Tailwind CSS

Este documento lista melhorias identificadas para o frontend do YT-Archiver, organizadas por prioridade e categoria.

---

## Resumo Executivo

| Categoria | Quantidade | Severidade |
|-----------|------------|------------|
| Qualidade de Código | 3 | Média |
| Performance | 4 | Média-Alta |
| Gerenciamento de Estado | 3 | Média |
| Tratamento de Erros | 2 | Média |
| Acessibilidade | 5 | Baixa-Média |
| Testes | 1 | Média |
| Arquitetura | 2 | Média |
| Segurança | 3 | Baixa-Média |
| UI/UX | 3 | Baixa |
| Dependências | 3 | Baixa-Média |
| **TOTAL** | **29** | - |

---

## Prioridade Alta

### 1. Centralizar URL da API

**Status:** Pendente
**Impacto:** Alto
**Esforço:** Baixo

**Problema Atual:**
Lógica de resolução de URL da API duplicada em 8+ arquivos:
- `src/components/home/download-form.tsx` (linhas 37-42)
- `src/components/common/videos/recent-videos.tsx` (linhas 44-47)
- `src/components/common/videos/video-card.tsx` (linhas 44-46)
- `src/components/common/videos/video-player.tsx` (linhas 36-38)
- `src/components/drive/drive-video-grid.tsx` (linhas 48-51)
- `src/components/drive/drive-auth.tsx` (linhas 24-27)
- `src/app/drive/page.tsx` (linhas 13-16)

**Código Atual (repetido):**
```typescript
const apiUrl = typeof window !== "undefined"
  ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  : "http://localhost:8000";
```

**Solução Proposta:**

```typescript
// src/lib/api-config.ts
export function getApiUrl(): string {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  return "http://localhost:8000";
}

// Hook para componentes React
export function useApiUrl(): string {
  const [apiUrl, setApiUrl] = useState("http://localhost:8000");

  useEffect(() => {
    setApiUrl(getApiUrl());
  }, []);

  return apiUrl;
}
```

**Uso:**
```typescript
import { useApiUrl } from "@/lib/api-config";

export function MyComponent() {
  const apiUrl = useApiUrl();
  // ...
}
```

---

### 2. Corrigir Memory Leak no Polling

**Status:** Pendente
**Impacto:** Alto (Estabilidade)
**Esforço:** Médio

**Problema Atual:**
- **Arquivo:** `src/components/home/download-form.tsx`
- **Linhas:** 196-232

O polling usa `setTimeout` em loop mas não retorna função de cleanup. Se o componente desmontar durante o polling, os timers continuam executando.

**Código Atual:**
```typescript
const pollJobStatus = async (id: string) => {
  let pollInterval = 500;
  let pollCount = 0;

  const poll = async () => {
    try {
      // ... polling logic
      setTimeout(poll, pollInterval); // ❌ Sem cleanup
    } catch (error) {
      // ...
    }
  };

  poll();
};
```

**Solução Proposta:**

```typescript
const pollJobStatus = useCallback((id: string) => {
  let pollInterval = 500;
  let pollCount = 0;
  let timeoutId: NodeJS.Timeout | null = null;
  let cancelled = false;

  const poll = async () => {
    if (cancelled) return;

    try {
      const response = await fetch(`${apiUrl}/api/jobs/${id}`);
      if (!response.ok) throw new Error("Erro ao verificar status");

      const status: JobStatus = await response.json();
      setJobStatus(status);

      if (["completed", "error", "cancelled"].includes(status.status)) {
        setIsDownloading(false);
        return; // Para o polling
      }

      // Ajustar intervalo progressivamente
      pollCount++;
      if (pollCount > 10) {
        pollInterval = 2000;
      } else if (pollCount > 5) {
        pollInterval = 1000;
      }

      timeoutId = setTimeout(poll, pollInterval);
    } catch (error) {
      console.error("Erro ao verificar status:", error);
      setIsDownloading(false);
    }
  };

  poll();

  // Retornar função de cleanup
  return () => {
    cancelled = true;
    if (timeoutId) clearTimeout(timeoutId);
  };
}, [apiUrl]);

// Uso no componente:
useEffect(() => {
  if (jobId) {
    const cleanup = pollJobStatus(jobId);
    return cleanup;
  }
}, [jobId, pollJobStatus]);
```

---

### 3. Criar Camada de API Centralizada

**Status:** Pendente
**Impacto:** Alto
**Esforço:** Médio

**Problema Atual:**
- Chamadas fetch espalhadas por todos os componentes
- Lógica de erro duplicada
- Difícil adicionar headers de autenticação, interceptors, etc.

**Solução Proposta:**

```typescript
// src/lib/api-client.ts
import { getApiUrl } from "./api-config";

interface ApiError {
  status: number;
  message: string;
  detail?: unknown;
}

class ApiClientError extends Error {
  status: number;
  detail?: unknown;

  constructor(error: ApiError) {
    super(error.message);
    this.status = error.status;
    this.detail = error.detail;
  }
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = getApiUrl();
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiClientError({
        status: response.status,
        message: error.detail || `HTTP ${response.status}`,
        detail: error,
      });
    }
    return response.json() as Promise<T>;
  }

  async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}/${endpoint}`, {
      ...options,
      method: "GET",
    });
    return this.handleResponse<T>(response);
  }

  async post<T>(endpoint: string, body?: unknown, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}/${endpoint}`, {
      ...options,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    return this.handleResponse<T>(response);
  }

  async delete(endpoint: string, options?: RequestInit): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${endpoint}`, {
      ...options,
      method: "DELETE",
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new ApiClientError({
        status: response.status,
        message: error.detail || `HTTP ${response.status}`,
      });
    }
  }

  // Para streaming de vídeos
  getStreamUrl(endpoint: string): string {
    return `${this.baseUrl}/${endpoint}`;
  }
}

export const api = new ApiClient();
```

**Uso nos Componentes:**
```typescript
import { api } from "@/lib/api-client";
import { APIURLS } from "@/lib/api-urls";

// GET
const videos = await api.get<Video[]>(`api/${APIURLS.VIDEOS}`);

// POST
const job = await api.post<JobResponse>(`api/${APIURLS.DOWNLOAD}`, {
  url: videoUrl,
  max_res: maxRes,
});

// DELETE
await api.delete(`api/videos/${encodeURIComponent(path)}`);

// Stream URL
const streamUrl = api.getStreamUrl(`api/videos/stream/${path}`);
```

---

### 4. Remover Duplicação de formatBytes

**Status:** Pendente
**Impacto:** Médio
**Esforço:** Baixo

**Problema Atual:**
Função `formatBytes` implementada em 3 lugares diferentes:
- `src/lib/utils.ts` (linhas 8-18)
- `src/components/common/videos/video-player.tsx` (linhas 71-77)
- `src/components/drive/drive-video-grid.tsx` (linhas 125-131)

**Solução:**
Usar a versão centralizada de `utils.ts` em todos os componentes:

```typescript
// Já existe em src/lib/utils.ts
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}

// Uso nos componentes:
import { formatBytes } from "@/lib/utils";

// Remover implementações locais de formatBytes
```

---

### 5. Criar Error Boundary

**Status:** Pendente
**Impacto:** Alto (Estabilidade)
**Esforço:** Baixo

**Problema Atual:**
Sem Error Boundaries implementados. Se qualquer componente filho lançar erro, a página inteira crasha.

**Solução Proposta:**

```typescript
// src/components/common/error-boundary.tsx
"use client";

import { Component, ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
          <h2 className="text-xl font-semibold mb-2">Algo deu errado</h2>
          <p className="text-muted-foreground mb-4">
            {this.state.error?.message || "Erro desconhecido"}
          </p>
          <Button onClick={this.handleRetry}>Tentar Novamente</Button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Uso nas Páginas:**
```typescript
// src/app/library/page.tsx
import { ErrorBoundary } from "@/components/common/error-boundary";

export default function LibraryPage() {
  return (
    <ErrorBoundary>
      <PaginatedVideoGrid />
    </ErrorBoundary>
  );
}
```

---

## Prioridade Média

### 6. Substituir alert() por Toast Notifications

**Status:** Pendente
**Impacto:** Médio (UX)
**Esforço:** Baixo

**Problema Atual:**
Uso de `alert()` do browser em vários componentes:
- `src/components/common/videos/recent-videos.tsx` (linha 81)
- `src/components/library/paginated-video-grid.tsx` (linha 83)
- `src/components/drive/drive-video-grid.tsx` (linha 114)
- `src/components/drive/sync-panel.tsx` (linhas 96, 123)

**Solução Proposta:**

```bash
# Instalar toast do shadcn
npx shadcn@latest add toast
```

```typescript
// src/components/common/videos/recent-videos.tsx
import { useToast } from "@/hooks/use-toast";

export function RecentVideos() {
  const { toast } = useToast();

  const handleDelete = async (path: string) => {
    try {
      await api.delete(`api/videos/${encodeURIComponent(path)}`);
      toast({
        title: "Sucesso",
        description: "Vídeo excluído com sucesso!",
      });
      refreshVideos();
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Erro",
        description: err instanceof Error ? err.message : "Erro ao excluir vídeo",
      });
    }
  };
}
```

**Adicionar Toaster ao Layout:**
```typescript
// src/app/layout.tsx
import { Toaster } from "@/components/ui/toaster";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
```

---

### 7. Adicionar useCallback para Event Handlers

**Status:** Pendente
**Impacto:** Médio (Performance)
**Esforço:** Médio

**Problema Atual:**
Event handlers não memoizados em componentes grandes, causando re-renders desnecessários.

**Arquivos Afetados:**
- `src/components/home/download-form.tsx`
- `src/components/drive/drive-video-grid.tsx`
- `src/components/common/videos/recent-videos.tsx`

**Exemplo - download-form.tsx:**
```typescript
// ❌ Atual - recriado a cada render
const startDownload = async () => {
  // ... large function body
};

// ✅ Proposto - memoizado
const startDownload = useCallback(async () => {
  if (!url.trim() || !apiUrl) return;
  // ... rest of logic
}, [url, apiUrl, outDir, maxRes, /* ... outras dependências */]);
```

---

### 8. Agrupar Estado do DownloadForm

**Status:** Pendente
**Impacto:** Médio (Manutenibilidade)
**Esforço:** Médio

**Problema Atual:**
16+ variáveis de estado individuais em `download-form.tsx` (linhas 69-95).

**Solução com useReducer:**

```typescript
// src/components/home/download-form/types.ts
interface DownloadFormState {
  // URL e validação
  url: string;
  urlType: UrlType;
  validationError: string | null;

  // Status do job
  jobId: string | null;
  jobStatus: JobStatus | null;
  isDownloading: boolean;

  // Opções básicas
  outDir: string;
  maxRes: string;
  subs: boolean;
  autoSubs: boolean;
  thumbnails: boolean;
  audioOnly: boolean;

  // Opções avançadas
  customPath: string;
  fileName: string;
  cookiesFile: string;
  referer: string;
  origin: string;

  // Anti-ban
  delayBetweenDownloads: string;
  batchSize: string;
  batchDelay: string;
  randomizeDelay: boolean;
}

type DownloadFormAction =
  | { type: "SET_URL"; payload: string }
  | { type: "SET_JOB_STATUS"; payload: JobStatus }
  | { type: "START_DOWNLOAD"; payload: string }
  | { type: "FINISH_DOWNLOAD" }
  | { type: "UPDATE_OPTIONS"; payload: Partial<DownloadFormState> }
  | { type: "RESET" };

function downloadFormReducer(
  state: DownloadFormState,
  action: DownloadFormAction
): DownloadFormState {
  switch (action.type) {
    case "SET_URL":
      return { ...state, url: action.payload };
    case "SET_JOB_STATUS":
      return { ...state, jobStatus: action.payload };
    case "START_DOWNLOAD":
      return { ...state, jobId: action.payload, isDownloading: true };
    case "FINISH_DOWNLOAD":
      return { ...state, isDownloading: false };
    case "UPDATE_OPTIONS":
      return { ...state, ...action.payload };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}
```

---

### 9. Adicionar AbortController às Requisições Fetch

**Status:** Pendente
**Impacto:** Médio (Estabilidade)
**Esforço:** Médio

**Problema Atual:**
Requisições fetch não são canceláveis. Se o componente desmontar durante uma requisição, o state update ainda ocorre (warning de memory leak).

**Arquivos Afetados:**
- `src/components/home/download-form.tsx`
- `src/components/common/videos/recent-videos.tsx`
- `src/components/library/paginated-video-grid.tsx`

**Solução Proposta:**

```typescript
// src/hooks/use-fetch.ts
import { useState, useEffect, useCallback } from "react";

interface UseFetchOptions<T> {
  initialData?: T;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export function useFetch<T>(
  url: string | null,
  options?: UseFetchOptions<T>
) {
  const [data, setData] = useState<T | undefined>(options?.initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async (signal: AbortSignal) => {
    if (!url) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(url, { signal });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const result = await response.json() as T;
      setData(result);
      options?.onSuccess?.(result);
    } catch (err) {
      if (err instanceof Error && err.name !== "AbortError") {
        setError(err);
        options?.onError?.(err);
      }
    } finally {
      setLoading(false);
    }
  }, [url, options?.onSuccess, options?.onError]);

  useEffect(() => {
    const controller = new AbortController();
    fetchData(controller.signal);
    return () => controller.abort();
  }, [fetchData]);

  const refetch = useCallback(() => {
    const controller = new AbortController();
    fetchData(controller.signal);
    return () => controller.abort();
  }, [fetchData]);

  return { data, loading, error, refetch };
}
```

**Uso:**
```typescript
const { data: videos, loading, error, refetch } = useFetch<Video[]>(
  `${apiUrl}/api/videos?page=${page}&limit=${PAGE_SIZE}`
);
```

---

### 10. Implementar Testes Automatizados

**Status:** Não Implementado
**Impacto:** Alto
**Esforço:** Alto

**Estrutura Sugerida:**

```
frontend/
├── __tests__/
│   ├── setup.ts
│   ├── lib/
│   │   ├── url-validator.test.ts
│   │   └── utils.test.ts
│   ├── components/
│   │   ├── download-form.test.tsx
│   │   └── video-card.test.tsx
│   └── hooks/
│       └── use-fetch.test.ts
├── jest.config.js
└── jest.setup.js
```

**Setup:**

```bash
npm install --save-dev jest @testing-library/react @testing-library/jest-dom @types/jest jest-environment-jsdom
```

**jest.config.js:**
```javascript
const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jest-environment-jsdom",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
};

module.exports = createJestConfig(customJestConfig);
```

**jest.setup.js:**
```javascript
import "@testing-library/jest-dom";
```

**Exemplo de Teste:**

```typescript
// __tests__/lib/url-validator.test.ts
import { validateUrl, detectUrlType } from "@/lib/url-validator";

describe("URL Validator", () => {
  describe("validateUrl", () => {
    it("should reject empty URLs", () => {
      const result = validateUrl("", "video");
      expect(result.isValid).toBe(false);
      expect(result.message).toContain("URL");
    });

    it("should validate YouTube video URLs", () => {
      const result = validateUrl(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "video"
      );
      expect(result.isValid).toBe(true);
    });

    it("should validate YouTube short URLs", () => {
      const result = validateUrl("https://youtu.be/dQw4w9WgXcQ", "video");
      expect(result.isValid).toBe(true);
    });

    it("should detect playlist mismatch", () => {
      const result = validateUrl(
        "https://www.youtube.com/playlist?list=PLtest",
        "video"
      );
      expect(result.isValid).toBe(false);
      expect(result.message).toContain("playlist");
    });
  });

  describe("detectUrlType", () => {
    it("should detect video type", () => {
      const type = detectUrlType("https://www.youtube.com/watch?v=abc123");
      expect(type).toBe("video");
    });

    it("should detect playlist type", () => {
      const type = detectUrlType(
        "https://www.youtube.com/playlist?list=PLtest"
      );
      expect(type).toBe("playlist");
    });
  });
});
```

**Comandos:**
```bash
# Rodar testes
npm test

# Rodar com coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

---

## Prioridade Baixa

### 11. Adicionar ARIA Labels

**Status:** Pendente
**Impacto:** Baixo-Médio (Acessibilidade)
**Esforço:** Baixo

**Exemplo - video-card.tsx:**

```typescript
// ❌ Atual (linhas 59-84)
<Button
  variant="ghost"
  size="icon"
  className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
>
  <MoreVertical className="h-4 w-4" />
</Button>

// ✅ Proposto
<Button
  variant="ghost"
  size="icon"
  aria-label={`Opções para ${title}`}
  className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
>
  <MoreVertical className="h-4 w-4" />
</Button>
```

---

### 12. Adicionar Skeleton Loaders

**Status:** Pendente
**Impacto:** Baixo (UX)
**Esforço:** Baixo

**Solução Proposta:**

```typescript
// src/components/common/videos/video-card-skeleton.tsx
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function VideoCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <Skeleton className="aspect-video w-full" />
      <div className="p-4 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </Card>
  );
}

// Uso em grids de vídeo
if (loading) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <VideoCardSkeleton key={i} />
      ))}
    </div>
  );
}
```

---

### 13. Remover Dependência prop-types

**Status:** Pendente
**Impacto:** Baixo (Bundle Size)
**Esforço:** Baixo

**Problema:** `prop-types` está no `package.json` mas não é usado (TypeScript já faz validação de tipos).

```bash
npm uninstall prop-types
```

---

### 14. Implementar Code Splitting

**Status:** Pendente
**Impacto:** Baixo-Médio (Performance)
**Esforço:** Baixo

**Solução:**

```typescript
// src/app/drive/page.tsx
import dynamic from "next/dynamic";

const DriveAuth = dynamic(
  () => import("@/components/drive/drive-auth"),
  {
    loading: () => <div className="animate-pulse h-32 bg-muted rounded" />,
  }
);

const SyncPanel = dynamic(
  () => import("@/components/drive/sync-panel"),
  {
    loading: () => <div className="animate-pulse h-48 bg-muted rounded" />,
  }
);

const DriveVideoGrid = dynamic(
  () => import("@/components/drive/drive-video-grid"),
  {
    loading: () => <div className="animate-pulse h-64 bg-muted rounded" />,
  }
);
```

---

### 15. Anunciar Estados de Loading para Screen Readers

**Status:** Pendente
**Impacto:** Baixo (Acessibilidade)
**Esforço:** Baixo

**Exemplo:**

```typescript
// ❌ Atual
<div className="flex items-center justify-center py-12">
  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
</div>

// ✅ Proposto
<div
  className="flex items-center justify-center py-12"
  role="status"
  aria-live="polite"
  aria-busy="true"
>
  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
  <span className="sr-only">Carregando vídeos...</span>
</div>
```

---

## Checklist de Implementação

### Fase 1 - Fundação (Semana 1-2)
- [ ] Criar `src/lib/api-config.ts` (centralizar URL)
- [ ] Criar `src/lib/api-client.ts` (camada de API)
- [ ] Criar `src/components/common/error-boundary.tsx`
- [ ] Remover duplicações de `formatBytes`
- [ ] Corrigir cleanup do polling

### Fase 2 - Qualidade (Semana 3-4)
- [ ] Instalar e configurar toast notifications
- [ ] Substituir todos os `alert()` por toast
- [ ] Adicionar `useCallback` em event handlers críticos
- [ ] Refatorar estado do DownloadForm

### Fase 3 - Estabilidade (Semana 5-6)
- [ ] Implementar hook `useFetch` com AbortController
- [ ] Atualizar componentes para usar `useFetch`
- [ ] Configurar Jest e testing-library
- [ ] Escrever testes para `url-validator`
- [ ] Escrever testes para `utils`

### Fase 4 - Polimento (Contínuo)
- [ ] Adicionar ARIA labels em componentes interativos
- [ ] Implementar skeleton loaders
- [ ] Remover dependências não utilizadas
- [ ] Implementar code splitting
- [ ] Adicionar anúncios de loading para screen readers

---

## Dependências a Adicionar

```bash
# Toast notifications (shadcn)
npx shadcn@latest add toast

# Skeleton (se não instalado)
npx shadcn@latest add skeleton

# Testing
npm install --save-dev jest @testing-library/react @testing-library/jest-dom @types/jest jest-environment-jsdom
```

## Dependências a Remover

```bash
npm uninstall prop-types
```

---

## Arquivos a Criar

```
frontend/src/
├── lib/
│   ├── api-config.ts      # URL da API centralizada
│   └── api-client.ts      # Cliente de API tipado
├── hooks/
│   ├── use-fetch.ts       # Hook de fetch com abort
│   └── use-toast.ts       # (gerado pelo shadcn)
├── components/
│   └── common/
│       ├── error-boundary.tsx
│       └── videos/
│           └── video-card-skeleton.tsx
└── __tests__/
    ├── setup.ts
    ├── lib/
    │   ├── url-validator.test.ts
    │   └── utils.test.ts
    └── components/
        └── video-card.test.tsx
```

---

## Notas Importantes

### Compatibilidade
- Todas as melhorias devem manter compatibilidade com a API do backend
- Testar em diferentes browsers (Chrome, Firefox, Safari)
- Verificar responsividade em dispositivos móveis

### Performance
- Usar React DevTools Profiler para medir impacto de mudanças
- Lighthouse para métricas de performance
- Bundle Analyzer para tamanho do pacote

### Acessibilidade
- Testar com screen readers (NVDA, VoiceOver)
- Verificar navegação por teclado
- Usar axe DevTools para auditorias

---

**Última atualização:** 2025-11-29
