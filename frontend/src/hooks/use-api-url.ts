/**
 * Hook for getting API URL in React components.
 *
 * Handles SSR vs client-side rendering automatically.
 */

import { useState, useEffect } from "react";
import { getApiUrl } from "@/lib/api-config";

/**
 * Hook to get the API URL safely in client components.
 *
 * Returns empty string during SSR to prevent hydration mismatches,
 * then updates to the actual URL on the client.
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const apiUrl = useApiUrl();
 *
 *   // apiUrl will be empty on server, populated on client
 *   if (!apiUrl) return null;
 *
 *   return <div>API: {apiUrl}</div>;
 * }
 * ```
 */
export function useApiUrl(): string {
  const [apiUrl, setApiUrl] = useState("");

  useEffect(() => {
    setApiUrl(getApiUrl());
  }, []);

  return apiUrl;
}

/**
 * Hook to check if the API URL is ready.
 *
 * Useful for conditionally rendering components that depend on the API.
 */
export function useApiReady(): boolean {
  const apiUrl = useApiUrl();
  return apiUrl !== "";
}
