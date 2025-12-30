import { CACHE_TAG_SETS } from "@/lib/server/tags";
import { buildBackendUrl, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

type Params = {
  fileId: string;
};

export async function POST(
  request: Request,
  { params }: { params: Params }
) {
  const formData = await request.formData();
  const url = buildBackendUrl(`/api/drive/videos/${params.fileId}/thumbnail`);

  return proxyJsonWithRevalidate(
    url,
    {
      method: "POST",
      body: formData,
    },
    CACHE_TAG_SETS.DRIVE_MUTATION
  );
}
