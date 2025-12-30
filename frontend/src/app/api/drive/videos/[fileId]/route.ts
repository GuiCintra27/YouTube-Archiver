import { CACHE_TAG_SETS } from "@/lib/server/tags";
import { buildBackendUrl, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

type Params = {
  fileId?: string | string[];
};

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<Params> }
) {
  const { fileId } = await params;
  const resolvedFileId = Array.isArray(fileId) ? fileId[0] : fileId;
  const url = buildBackendUrl(`/api/drive/videos/${resolvedFileId ?? ""}`);
  return proxyJsonWithRevalidate(url, { method: "DELETE" }, CACHE_TAG_SETS.DRIVE_MUTATION);
}
