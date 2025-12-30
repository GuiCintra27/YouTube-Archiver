import { CACHE_TAG_SETS } from "@/lib/server/tags";
import { buildBackendUrl, encodePathParam, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

type Params = {
  path?: string | string[];
};

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<Params> }
) {
  const { path } = await params;
  const encodedPath = encodePathParam(path);
  const url = buildBackendUrl(`/api/videos/${encodedPath}`);

  return proxyJsonWithRevalidate(url, { method: "DELETE" }, CACHE_TAG_SETS.LOCAL_MUTATION);
}
