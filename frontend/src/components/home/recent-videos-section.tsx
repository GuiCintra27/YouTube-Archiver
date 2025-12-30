import RecentVideos from "@/components/common/videos/recent-videos";
import { fetchRecentVideos } from "@/lib/server/api";
import { PATHS } from "@/lib/paths";

type RecentVideosSectionProps = {
  title?: string;
  limit?: number;
  ctaLabel?: string;
  ctaHref?: string;
};

export default async function RecentVideosSection({
  title = "Últimos vídeos",
  limit = 4,
  ctaLabel = "Ver biblioteca completa",
  ctaHref = PATHS.LIBRARY,
}: RecentVideosSectionProps) {
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
    const data = await fetchRecentVideos(limit);
    initialRecentVideos = data.videos || [];
  } catch (error) {
    console.error("Erro ao carregar recentes:", error);
  }

  return (
    <RecentVideos
      title={title}
      limit={limit}
      ctaLabel={ctaLabel}
      ctaHref={ctaHref}
      initialData={initialRecentVideos}
    />
  );
}
