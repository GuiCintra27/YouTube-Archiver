import { revalidateTag } from "next/cache";

const DEFAULT_API_URL = "http://localhost:8000";

export function getBackendBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL;
}

export function buildBackendUrl(path: string): string {
  const base = getBackendBaseUrl().replace(/\/+$/, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}

export async function proxyJson(url: string, init: RequestInit): Promise<Response> {
  const response = await fetch(url, {
    ...init,
    cache: "no-store",
  });

  const body = await response.text();
  const headers = new Headers(response.headers);

  if (!headers.has("content-type")) {
    headers.set("content-type", "application/json");
  }

  return new Response(body, {
    status: response.status,
    headers,
  });
}

export function revalidateTags(tags: readonly string[]) {
  tags.forEach((tag) => revalidateTag(tag));
}

export function encodePathParam(segments: string[]): string {
  const joined = segments.join("/");
  let decoded = joined;
  try {
    decoded = decodeURIComponent(joined);
  } catch {
    decoded = joined;
  }
  return encodeURIComponent(decoded);
}

export async function proxyJsonWithRevalidate(
  url: string,
  init: RequestInit,
  tags: readonly string[]
): Promise<Response> {
  const response = await proxyJson(url, init);
  if (response.ok) {
    revalidateTags(tags);
  }
  return response;
}
