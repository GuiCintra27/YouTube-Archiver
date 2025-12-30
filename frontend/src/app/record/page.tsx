import RecordPageClient from "@/components/record/record-page-client";
import { fetchRecentVideos } from "@/lib/server/api";

export default async function RecordPage() {
  let initialRecentVideos: {
    id: string;
    title: string;
    channel: string;
    path: string;
    thumbnail?: string;
    size: number;
    created_at: string;
    modified_at: string;
  }[] = [];

  try {
    const data = await fetchRecentVideos(4);
    initialRecentVideos = data.videos || [];
  } catch (error) {
    console.error("Erro ao carregar recentes:", error);
  }

  return <RecordPageClient initialRecentVideos={initialRecentVideos} />;
}
