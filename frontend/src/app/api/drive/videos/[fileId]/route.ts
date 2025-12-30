import { CACHE_TAG_SETS } from "@/lib/server/tags";
import { buildBackendUrl, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

type Params = {
  fileId: string;
};

export async function DELETE(
  _request: Request,
  { params }: { params: Params }
) {
  const url = buildBackendUrl(`/api/drive/videos/${params.fileId}`);
  return proxyJsonWithRevalidate(url, { method: "DELETE" }, CACHE_TAG_SETS.DRIVE_MUTATION);
}
