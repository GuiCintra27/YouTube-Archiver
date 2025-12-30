import { CACHE_TAG_SETS } from "@/lib/server/tags";
import { buildBackendUrl, encodePathParam, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

type Params = {
  path: string[];
};

export async function POST(
  request: Request,
  { params }: { params: Params }
) {
  const formData = await request.formData();
  const encodedPath = encodePathParam(params.path);
  const url = buildBackendUrl(`/api/videos/update-thumbnail/${encodedPath}`);

  return proxyJsonWithRevalidate(
    url,
    {
      method: "POST",
      body: formData,
    },
    CACHE_TAG_SETS.LOCAL_MUTATION
  );
}
