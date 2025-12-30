import DrivePageClient from "@/components/drive/drive-page-client";
import { fetchDriveAuthStatus, fetchDriveVideosPage } from "@/lib/server/api";

const PAGE_SIZE = 12;

export default async function DrivePageSection() {
  let initialAuthenticated = false;
  let initialVideos: {
    videos: {
      id: string;
      name: string;
      path: string;
      size: number;
      created_at: string;
      modified_at: string;
      thumbnail?: string;
      custom_thumbnail_id?: string;
    }[];
    total: number;
    page: number;
  } | null = null;

  try {
    const auth = await fetchDriveAuthStatus();
    initialAuthenticated = auth.authenticated;
  } catch (error) {
    console.error("Erro ao verificar autenticação do Drive:", error);
  }

  if (initialAuthenticated) {
    try {
      const data = await fetchDriveVideosPage(1, PAGE_SIZE);
      initialVideos = {
        videos: data.videos || [],
        total: data.total || 0,
        page: data.page || 1,
      };
    } catch (error) {
      console.error("Erro ao carregar vídeos do Drive:", error);
    }
  }

  return (
    <DrivePageClient
      initialAuthenticated={initialAuthenticated}
      initialVideos={initialVideos}
    />
  );
}
