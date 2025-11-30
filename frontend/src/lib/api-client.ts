/**
 * Centralized API client for making HTTP requests.
 *
 * Provides:
 * - Type-safe request/response handling
 * - Automatic error handling
 * - Consistent API URL resolution
 * - AbortController support for request cancellation
 */

import { getApiUrl } from "./api-config";

/**
 * API error structure
 */
export interface ApiError {
  status: number;
  message: string;
  detail?: unknown;
  code?: string;
}

/**
 * Custom error class for API errors
 */
export class ApiClientError extends Error {
  status: number;
  detail?: unknown;
  code?: string;

  constructor(error: ApiError) {
    super(error.message);
    this.name = "ApiClientError";
    this.status = error.status;
    this.detail = error.detail;
    this.code = error.code;
  }

  /**
   * Check if error is a network error
   */
  isNetworkError(): boolean {
    return this.status === 0;
  }

  /**
   * Check if error is a client error (4xx)
   */
  isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  /**
   * Check if error is a server error (5xx)
   */
  isServerError(): boolean {
    return this.status >= 500;
  }
}

/**
 * Request options with abort signal support
 */
interface RequestOptions extends Omit<RequestInit, "method" | "body"> {
  signal?: AbortSignal;
}

/**
 * Centralized API client class
 */
class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = getApiUrl();
  }

  /**
   * Refresh base URL (useful for dynamic configuration)
   */
  refreshBaseUrl(): void {
    this.baseUrl = getApiUrl();
  }

  /**
   * Handle API response and extract JSON or throw error
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorDetail: unknown;
      let errorMessage = `HTTP ${response.status}`;
      let errorCode: string | undefined;

      try {
        const errorData = await response.json();
        errorDetail = errorData;
        errorMessage = errorData.detail || errorData.message || errorMessage;
        errorCode = errorData.error_code || errorData.code;
      } catch {
        // Response body is not JSON
      }

      throw new ApiClientError({
        status: response.status,
        message: errorMessage,
        detail: errorDetail,
        code: errorCode,
      });
    }

    // Handle empty responses
    const contentType = response.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      return {} as T;
    }

    return response.json() as Promise<T>;
  }

  /**
   * Build full URL from endpoint
   */
  private buildUrl(endpoint: string): string {
    const cleanEndpoint = endpoint.startsWith("/")
      ? endpoint.slice(1)
      : endpoint;
    return `${this.baseUrl}/${cleanEndpoint}`;
  }

  /**
   * Make a GET request
   */
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const response = await fetch(this.buildUrl(endpoint), {
      ...options,
      method: "GET",
    });
    return this.handleResponse<T>(response);
  }

  /**
   * Make a POST request
   */
  async post<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    const response = await fetch(this.buildUrl(endpoint), {
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

  /**
   * Make a PUT request
   */
  async put<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    const response = await fetch(this.buildUrl(endpoint), {
      ...options,
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    return this.handleResponse<T>(response);
  }

  /**
   * Make a DELETE request
   */
  async delete<T = void>(endpoint: string, options?: RequestOptions): Promise<T> {
    const response = await fetch(this.buildUrl(endpoint), {
      ...options,
      method: "DELETE",
    });
    return this.handleResponse<T>(response);
  }

  /**
   * Get a URL for streaming content (video, audio, etc.)
   * Does not make a request, just builds the URL
   */
  getStreamUrl(endpoint: string): string {
    return this.buildUrl(endpoint);
  }

  /**
   * Get the base URL
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export class for testing or custom instances
export { ApiClient };
