import { CACHE_TAG_SETS } from "@/lib/server/tags";
import { buildBackendUrl, encodePathParam, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

type Params = {
  path: string[];
};

export async function DELETE(
  _request: Request,
  { params }: { params: Params }
) {
  const encodedPath = encodePathParam(params.path);
  const url = buildBackendUrl(`/api/videos/${encodedPath}`);

  return proxyJsonWithRevalidate(url, { method: "DELETE" }, CACHE_TAG_SETS.LOCAL_MUTATION);
}
