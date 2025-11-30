/**
 * Custom hook for making fetch requests with automatic cleanup.
 *
 * Features:
 * - Automatic AbortController management
 * - Type-safe responses
 * - Loading and error states
 * - Refetch capability
 * - Prevents memory leaks on unmount
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { useApiUrl } from "./use-api-url";

interface UseFetchOptions<T> {
  /** Initial data value */
  initialData?: T;
  /** Callback when request succeeds */
  onSuccess?: (data: T) => void;
  /** Callback when request fails */
  onError?: (error: Error) => void;
  /** Skip initial fetch */
  skip?: boolean;
  /** Dependencies that trigger refetch */
  deps?: unknown[];
}

interface UseFetchResult<T> {
  /** Response data */
  data: T | undefined;
  /** Loading state */
  loading: boolean;
  /** Error object if request failed */
  error: Error | null;
  /** Function to manually refetch data */
  refetch: () => void;
}

/**
 * Hook for fetching data with automatic cleanup.
 *
 * @param endpoint - API endpoint (without base URL)
 * @param options - Configuration options
 *
 * @example
 * ```tsx
 * const { data, loading, error, refetch } = useFetch<Video[]>(
 *   "api/videos?page=1&limit=10"
 * );
 *
 * if (loading) return <Spinner />;
 * if (error) return <Error message={error.message} />;
 * return <VideoList videos={data} />;
 * ```
 */
export function useFetch<T>(
  endpoint: string | null,
  options: UseFetchOptions<T> = {}
): UseFetchResult<T> {
  const { initialData, onSuccess, onError, skip = false, deps = [] } = options;
  const apiUrl = useApiUrl();

  const [data, setData] = useState<T | undefined>(initialData);
  const [loading, setLoading] = useState(!skip);
  const [error, setError] = useState<Error | null>(null);

  // Use ref to track if component is mounted
  const isMounted = useRef(true);
  // Use ref for abort controller
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(async () => {
    if (!endpoint || !apiUrl || skip) return;

    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController();
    const { signal } = abortControllerRef.current;

    setLoading(true);
    setError(null);

    try {
      const url = endpoint.startsWith("http")
        ? endpoint
        : `${apiUrl}/${endpoint}`;

      const response = await fetch(url, { signal });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = (await response.json()) as T;

      // Only update state if still mounted
      if (isMounted.current) {
        setData(result);
        onSuccess?.(result);
      }
    } catch (err) {
      // Ignore abort errors
      if (err instanceof Error && err.name === "AbortError") {
        return;
      }

      // Only update state if still mounted
      if (isMounted.current) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        onError?.(error);
      }
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [endpoint, apiUrl, skip, onSuccess, onError]);

  // Fetch on mount and when dependencies change
  useEffect(() => {
    isMounted.current = true;
    fetchData();

    return () => {
      isMounted.current = false;
      // Cleanup: abort any pending request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchData, ...deps]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
}

/**
 * Hook for making mutations (POST, PUT, DELETE) with automatic cleanup.
 *
 * @example
 * ```tsx
 * const { mutate, loading, error } = useMutation<Video>("api/videos");
 *
 * const handleSubmit = async (data: VideoInput) => {
 *   const result = await mutate(data);
 *   if (result) {
 *     toast.success("Video created!");
 *   }
 * };
 * ```
 */
export function useMutation<T, TBody = unknown>(endpoint: string) {
  const apiUrl = useApiUrl();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const mutate = useCallback(
    async (
      body?: TBody,
      options: { method?: "POST" | "PUT" | "DELETE" } = {}
    ): Promise<T | null> => {
      if (!apiUrl) return null;

      // Cancel any existing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();
      const { signal } = abortControllerRef.current;
      const method = options.method || "POST";

      setLoading(true);
      setError(null);

      try {
        const url = endpoint.startsWith("http")
          ? endpoint
          : `${apiUrl}/${endpoint}`;

        const response = await fetch(url, {
          method,
          headers: {
            "Content-Type": "application/json",
          },
          body: body ? JSON.stringify(body) : undefined,
          signal,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        // Handle empty responses
        const contentType = response.headers.get("content-type");
        if (!contentType?.includes("application/json")) {
          return {} as T;
        }

        return (await response.json()) as T;
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") {
          return null;
        }

        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [endpoint, apiUrl]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return { mutate, loading, error };
}
