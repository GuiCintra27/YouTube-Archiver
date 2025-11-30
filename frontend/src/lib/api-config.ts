/**
 * Centralized API configuration
 *
 * This module provides a single source of truth for API URL configuration,
 * eliminating duplicate code across components.
 */

const DEFAULT_API_URL = "http://localhost:8000";

/**
 * Get the API URL for making requests.
 * Uses NEXT_PUBLIC_API_URL environment variable if available.
 */
export function getApiUrl(): string {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL;
  }
  return DEFAULT_API_URL;
}

/**
 * Build a full API endpoint URL
 */
export function buildApiUrl(endpoint: string): string {
  const baseUrl = getApiUrl();
  // Remove leading slash from endpoint if present
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint.slice(1) : endpoint;
  return `${baseUrl}/${cleanEndpoint}`;
}

/**
 * Build a streaming URL for video/media content
 */
export function buildStreamUrl(endpoint: string): string {
  return buildApiUrl(endpoint);
}
