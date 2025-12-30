import PaginatedVideoGrid from "@/components/library/paginated-video-grid";
import { fetchLocalVideosPage } from "@/lib/server/api";

const PAGE_SIZE = 12;

export default async function LibraryGridSection() {
  let initialData: {
    videos: {
      id: string;
      title: string;
      channel: string;
      path: string;
      thumbnail?: string;
      duration?: string;
      size: number;
      created_at: string;
      modified_at: string;
    }[];
    total: number;
    page: number;
  } | null = null;

  try {
    const data = await fetchLocalVideosPage(1, PAGE_SIZE);
    initialData = {
      videos: data.videos || [],
      total: data.total || 0,
      page: data.page || 1,
    };
  } catch (error) {
    console.error("Erro ao carregar biblioteca:", error);
  }

  return <PaginatedVideoGrid initialData={initialData || undefined} />;
}
