import { CACHE_TAG_SETS } from "@/lib/server/tags";
import { buildBackendUrl, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

type Params = {
  fileId: string;
};

export async function PATCH(
  request: Request,
  { params }: { params: Params }
) {
  const payload = await request.json();
  const url = buildBackendUrl(`/api/drive/videos/${params.fileId}/rename`);

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
