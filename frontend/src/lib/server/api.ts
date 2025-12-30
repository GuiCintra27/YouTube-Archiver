import { APIURLS } from "@/lib/api-urls";
import { CACHE_TAGS } from "@/lib/server/tags";

const DEFAULT_API_URL = "http://localhost:8000";

export type LocalVideosResponse = {
  videos: {
    id: string;
    title: string;
    channel: string;
    path: string;
    thumbnail?: string;
    duration?: string;
    size: number;
    created_at: string;
    modified_at: string;
  }[];
  total: number;
  page: number;
  limit: number;
};

export type LocalVideo = LocalVideosResponse["videos"][number];

export type DriveAuthStatus = {
  authenticated: boolean;
  credentials_exists: boolean;
};

export type DriveVideosResponse = {
  videos: {
    id: string;
    name: string;
    path: string;
    size: number;
    created_at: string;
    modified_at: string;
    thumbnail?: string;
    custom_thumbnail_id?: string;
  }[];
  total: number;
  page: number;
  limit: number;
  warning?: string;
};

type FetchOptions = {
  revalidate?: number;
  tags?: string[];
  cache?: RequestCache;
};

export function getServerApiUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL;
}

async function fetchJson<T>(url: string, options: FetchOptions = {}): Promise<T> {
  const next: { revalidate?: number; tags?: string[] } = {};
  if (options.revalidate !== undefined) {
    next.revalidate = options.revalidate;
  }
  if (options.tags && options.tags.length > 0) {
    next.tags = options.tags;
  }

  const response = await fetch(url, {
    cache: options.cache,
    next,
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function fetchLocalVideosPage(
  page: number,
  limit: number
): Promise<LocalVideosResponse> {
  const url = `${getServerApiUrl()}/api/${APIURLS.VIDEOS}?page=${page}&limit=${limit}`;
  return fetchJson<LocalVideosResponse>(url, {
    revalidate: 60,
    tags: [CACHE_TAGS.LOCAL_VIDEOS],
  });
}

export async function fetchDriveAuthStatus(): Promise<DriveAuthStatus> {
  const url = `${getServerApiUrl()}/api/${APIURLS.DRIVE_AUTH_STATUS}`;
  return fetchJson<DriveAuthStatus>(url, {
    cache: "no-store",
  });
}

export async function fetchDriveVideosPage(
  page: number,
  limit: number
): Promise<DriveVideosResponse> {
  const url = `${getServerApiUrl()}/api/${APIURLS.DRIVE_VIDEOS}?page=${page}&limit=${limit}`;
  return fetchJson<DriveVideosResponse>(url, {
    revalidate: 60,
    tags: [CACHE_TAGS.DRIVE_VIDEOS],
  });
}

export async function fetchRecentVideos(
  limit: number
): Promise<LocalVideosResponse> {
  const url = `${getServerApiUrl()}/api/${APIURLS.VIDEOS}?page=1&limit=${limit}`;
  return fetchJson<LocalVideosResponse>(url, {
    revalidate: 20,
    tags: [CACHE_TAGS.RECENT_VIDEOS],
  });
}
