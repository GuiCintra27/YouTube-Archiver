import { CACHE_TAG_SETS } from "@/lib/server/tags";
import { buildBackendUrl, encodePathParam, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

type Params = {
  path?: string | string[];
};

export async function PATCH(
  request: Request,
  { params }: { params: Promise<Params> }
) {
  const payload = await request.json();
  const { path } = await params;
  const encodedPath = encodePathParam(path);
  const url = buildBackendUrl(`/api/videos/rename/${encodedPath}`);

  return proxyJsonWithRevalidate(
    url,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    CACHE_TAG_SETS.LOCAL_MUTATION
  );
}
