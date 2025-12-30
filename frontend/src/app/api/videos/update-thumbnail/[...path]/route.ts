import { CACHE_TAG_SETS } from "@/lib/server/tags";
import { buildBackendUrl, encodePathParam, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

type Params = {
  path?: string | string[];
};

export async function POST(
  request: Request,
  { params }: { params: Promise<Params> }
) {
  const formData = await request.formData();
  const { path } = await params;
  const encodedPath = encodePathParam(path);
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
