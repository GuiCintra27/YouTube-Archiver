import { CACHE_TAG_SETS } from "@/lib/server/tags";
import { buildBackendUrl, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

type Params = {
  fileId?: string | string[];
};

export async function PATCH(
  request: Request,
  { params }: { params: Promise<Params> }
) {
  const payload = await request.json();
  const { fileId } = await params;
  const resolvedFileId = Array.isArray(fileId) ? fileId[0] : fileId;
  const url = buildBackendUrl(`/api/drive/videos/${resolvedFileId ?? ""}/rename`);

  return proxyJsonWithRevalidate(
    url,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    CACHE_TAG_SETS.DRIVE_MUTATION
  );
}
