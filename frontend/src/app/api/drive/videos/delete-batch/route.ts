import { CACHE_TAGS } from "@/lib/server/tags";
import { buildBackendUrl, proxyJsonWithRevalidate } from "@/lib/server/route-utils";

export async function POST(request: Request) {
  const payload = await request.json();
  const url = buildBackendUrl("/api/drive/videos/delete-batch");

  return proxyJsonWithRevalidate(
    url,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    [CACHE_TAGS.DRIVE_VIDEOS]
  );
}
