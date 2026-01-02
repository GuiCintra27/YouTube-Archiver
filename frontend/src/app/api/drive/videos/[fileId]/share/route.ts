import { CACHE_TAGS } from "@/lib/server/tags";
import { buildBackendUrl, proxyJson, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

type Params = {
  fileId?: string | string[];
};

export async function GET(
  _request: Request,
  { params }: { params: Promise<Params> }
) {
  const { fileId } = await params;
  const resolvedFileId = Array.isArray(fileId) ? fileId[0] : fileId;
  const url = buildBackendUrl(`/api/drive/videos/${resolvedFileId ?? ""}/share`);
  return proxyJson(url, { method: "GET" });
}

export async function POST(
  _request: Request,
  { params }: { params: Promise<Params> }
) {
  const { fileId } = await params;
  const resolvedFileId = Array.isArray(fileId) ? fileId[0] : fileId;
  const url = buildBackendUrl(`/api/drive/videos/${resolvedFileId ?? ""}/share`);
  return proxyJsonWithRevalidate(url, { method: "POST" }, [CACHE_TAGS.DRIVE_VIDEOS]);
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<Params> }
) {
  const { fileId } = await params;
  const resolvedFileId = Array.isArray(fileId) ? fileId[0] : fileId;
  const url = buildBackendUrl(`/api/drive/videos/${resolvedFileId ?? ""}/share`);
  return proxyJsonWithRevalidate(url, { method: "DELETE" }, [CACHE_TAGS.DRIVE_VIDEOS]);
}
