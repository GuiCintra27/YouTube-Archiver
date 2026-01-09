"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import Link from "next/link";
import { LibraryBig, Play } from "lucide-react";
import VideoCard from "@/components/common/videos/video-card";
import VideoGridHeader from "@/components/common/videos/video-grid-header";
import VideoGridLoadingState from "@/components/common/videos/video-grid-loading-state";
import VideoGridErrorState from "@/components/common/videos/video-grid-error-state";
import VideoGridEmptyState from "@/components/common/videos/video-grid-empty-state";
import VideoPlayerModal from "@/components/common/videos/video-player-modal";
import { PATHS } from "@/lib/paths";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";
import { deleteLocalVideo } from "@/lib/client/api";

interface Video {
  id: string;
  title: string;
  channel: string;
  path: string;
  thumbnail?: string;
  size: number;
  created_at: string;
  modified_at: string;
}

interface RecentVideosProps {
  title?: string;
  limit?: number;
  refreshToken?: number;
  ctaLabel?: string;
  ctaHref?: string;
  initialData?: Video[];
}

export default function RecentVideos({
  title = "Ultimos videos",
  limit = 4,
  refreshToken,
  ctaLabel = "Ver biblioteca completa",
  ctaHref = PATHS.LIBRARY,
  initialData,
}: RecentVideosProps) {
  const apiUrl = useApiUrl();
  const [videos, setVideos] = useState<Video[]>(initialData || []);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const skipInitialFetch = useRef(Boolean(initialData));

  const fetchVideos = useCallback(async () => {
    if (!apiUrl) return;
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `${apiUrl}/api/${APIURLS.VIDEOS}?page=1&limit=${limit}`,
        { cache: "no-store" }
      );
      if (!response.ok) throw new Error("Falha ao carregar vídeos");
      const data = await response.json();
      const list: Video[] = data.videos || [];
      setVideos(list.slice(0, limit));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }, [apiUrl, limit]);

  useEffect(() => {
    if (!apiUrl) return;
    if (skipInitialFetch.current && !refreshToken) {
      skipInitialFetch.current = false;
      return;
    }
    fetchVideos();
  }, [fetchVideos, refreshToken, apiUrl, skipInitialFetch]);

  useEffect(() => {
    if (!initialData) return;
    setVideos(initialData);
    setLoading(false);
  }, [initialData]);

  useEffect(() => {
    const handleRefresh = () => {
      fetchVideos();
    };
    window.addEventListener("yt-archiver:videos-updated", handleRefresh);
    return () => {
      window.removeEventListener("yt-archiver:videos-updated", handleRefresh);
    };
  }, [fetchVideos]);

  const handleDelete = useCallback(
    async (video: Video) => {
      try {
        await deleteLocalVideo(video.path);
        setVideos((prev) => prev.filter((v) => v.id !== video.id));
        setSelectedVideo((prev) => (prev?.id === video.id ? null : prev));
      } catch (err) {
        console.error("Erro ao excluir vídeo:", err);
      }
    },
    []
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <VideoGridHeader
        icon={<LibraryBig className="h-5 w-5 text-teal" />}
        title={title}
        subtitle="Videos baixados recentemente"
        rightSlot={
          <Link
            href={ctaHref}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/10 text-muted-foreground hover:text-white hover:border-teal/30 hover:bg-white/5 transition-all duration-300"
          >
            <Play className="h-4 w-4" />
            <span className="hidden sm:inline">{ctaLabel}</span>
          </Link>
        }
      />

      {/* Content */}
      {loading ? (
        <VideoGridLoadingState
          label="Carregando videos..."
          iconWrapperClassName="bg-teal/10"
          iconClassName="text-teal"
        />
      ) : error ? (
        <VideoGridErrorState message={`Erro ao carregar videos: ${error}`} />
      ) : videos.length === 0 ? (
        <VideoGridEmptyState
          title="Nenhum video encontrado"
          description="Baixe seu primeiro video usando o formulario acima. Seus videos aparecera aqui."
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {videos.map((video, index) => (
              <VideoCard
                key={video.id}
                id={video.id}
                title={video.title}
                channel={video.channel}
                thumbnail={video.thumbnail}
                thumbnailCacheKey={video.modified_at}
                path={video.path}
                onPlay={() => setSelectedVideo(video)}
                onDelete={() => handleDelete(video)}
                priority={index === 0}
              />
          ))}
        </div>
      )}

      {selectedVideo && (
        <VideoPlayerModal
          video={selectedVideo}
          source="local"
          onClose={() => setSelectedVideo(null)}
          onDelete={() => handleDelete(selectedVideo)}
        />
      )}
    </div>
  );
}
