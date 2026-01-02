import { revalidateTag } from "next/cache";
import { CACHE_TAGS } from "@/lib/server/tags";

export async function POST() {
  revalidateTag(CACHE_TAGS.LOCAL_VIDEOS);
  revalidateTag(CACHE_TAGS.RECENT_VIDEOS);
  return Response.json({ status: "ok" });
}
