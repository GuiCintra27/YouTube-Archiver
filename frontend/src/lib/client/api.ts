import { APIURLS } from "@/lib/api-urls";

type JsonValue = Record<string, unknown>;

type BatchDeleteResult = {
  total_deleted?: number;
  total_failed?: number;
  failed?: JsonValue[];
  deleted?: JsonValue[];
};

type RenameResult = {
  new_path?: string;
};

type ShareStatus = {
  shared: boolean;
  link?: string | null;
};

async function requestJson<T>(url: string, init: RequestInit): Promise<T> {
  const response = await fetch(url, { ...init, cache: "no-store" });
  const text = await response.text();
  let data: unknown = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const message =
      (data as JsonValue)?.detail ||
      (data as JsonValue)?.message ||
      `Request failed: ${response.status}`;
    throw new Error(String(message));
  }

  return data as T;
}

export async function deleteLocalVideo(path: string) {
  const url = `/api/videos/${encodeURIComponent(path)}`;
  await requestJson<JsonValue>(url, { method: "DELETE" });
}

export async function deleteLocalVideosBatch(paths: string[]) {
  const url = `/api/${APIURLS.VIDEOS_DELETE_BATCH}`;
  return requestJson<BatchDeleteResult>(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(paths),
  });
}

export async function renameLocalVideo(path: string, newName: string) {
  const url = `/api/${APIURLS.VIDEOS_RENAME}/${encodeURIComponent(path)}`;
  return requestJson<RenameResult>(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ new_name: newName }),
  });
}

export async function updateLocalThumbnail(path: string, thumbnail: File) {
  const url = `/api/${APIURLS.VIDEOS_UPDATE_THUMBNAIL}/${encodeURIComponent(path)}`;
  const formData = new FormData();
  formData.append("thumbnail", thumbnail);
  await requestJson<JsonValue>(url, {
    method: "POST",
    body: formData,
  });
}

export async function deleteDriveVideo(fileId: string) {
  const url = `/api/${APIURLS.DRIVE_VIDEOS}/${encodeURIComponent(fileId)}`;
  await requestJson<JsonValue>(url, { method: "DELETE" });
}

export async function deleteDriveVideosBatch(fileIds: string[]) {
  const url = `/api/${APIURLS.DRIVE_DELETE_BATCH}`;
  return requestJson<BatchDeleteResult>(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fileIds),
  });
}

export async function renameDriveVideo(fileId: string, newName: string) {
  const url = `/api/${APIURLS.DRIVE_VIDEOS}/${encodeURIComponent(fileId)}/rename`;
  return requestJson<JsonValue>(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ new_name: newName }),
  });
}

export async function updateDriveThumbnail(fileId: string, thumbnail: File) {
  const url = `/api/${APIURLS.DRIVE_VIDEOS}/${encodeURIComponent(fileId)}/thumbnail`;
  const formData = new FormData();
  formData.append("thumbnail", thumbnail);
  await requestJson<JsonValue>(url, {
    method: "POST",
    body: formData,
  });
}

export async function getDriveShareStatus(fileId: string) {
  const url = `/api/${APIURLS.DRIVE_VIDEOS}/${encodeURIComponent(fileId)}/${APIURLS.DRIVE_SHARE}`;
  return requestJson<ShareStatus>(url, { method: "GET" });
}

export async function shareDriveVideo(fileId: string) {
  const url = `/api/${APIURLS.DRIVE_VIDEOS}/${encodeURIComponent(fileId)}/${APIURLS.DRIVE_SHARE}`;
  return requestJson<ShareStatus>(url, { method: "POST" });
}

export async function unshareDriveVideo(fileId: string) {
  const url = `/api/${APIURLS.DRIVE_VIDEOS}/${encodeURIComponent(fileId)}/${APIURLS.DRIVE_SHARE}`;
  return requestJson<ShareStatus>(url, { method: "DELETE" });
}
