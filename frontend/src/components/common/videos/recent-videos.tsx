"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Loader2, VideoOff, LibraryBig, Play } from "lucide-react";
import VideoCard from "@/components/common/videos/video-card";
import VideoPlayer from "@/components/common/videos/video-player";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PATHS } from "@/lib/paths";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";

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
}

export default function RecentVideos({
  title = "Ultimos videos",
  limit = 4,
  refreshToken,
  ctaLabel = "Ver biblioteca completa",
  ctaHref = PATHS.LIBRARY,
}: RecentVideosProps) {
  const apiUrl = useApiUrl();
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);

  const fetchVideos = useCallback(async () => {
    if (!apiUrl) return;
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `${apiUrl}/api/${APIURLS.VIDEOS}?page=1&limit=${limit}`
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
    fetchVideos();
  }, [fetchVideos, refreshToken]);

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
      if (!apiUrl) return;
      try {
        const response = await fetch(
          `${apiUrl}/api/${APIURLS.VIDEOS}/${encodeURIComponent(video.path)}`,
          { method: "DELETE" }
        );
        if (!response.ok) throw new Error("Falha ao excluir vídeo");
        setVideos((prev) => prev.filter((v) => v.id !== video.id));
        setSelectedVideo((prev) => (prev?.id === video.id ? null : prev));
      } catch (err) {
        console.error("Erro ao excluir vídeo:", err);
      }
    },
    [apiUrl]
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="icon-glow">
            <LibraryBig className="h-5 w-5 text-teal" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">{title}</h2>
            <p className="text-sm text-muted-foreground">
              Videos baixados recentemente
            </p>
          </div>
        </div>
        <Link
          href={ctaHref}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-white/10 text-muted-foreground hover:text-white hover:border-teal/30 hover:bg-white/5 transition-all duration-300"
        >
          <Play className="h-4 w-4" />
          <span className="hidden sm:inline">{ctaLabel}</span>
        </Link>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-teal/10 flex items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-teal" />
            </div>
            <p className="text-sm text-muted-foreground">Carregando videos...</p>
          </div>
        </div>
      ) : error ? (
        <Alert
          variant="destructive"
          className="bg-red-500/10 border-red-500/20"
        >
          <AlertDescription>Erro ao carregar videos: {error}</AlertDescription>
        </Alert>
      ) : videos.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center glass-card rounded-2xl">
          <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
            <VideoOff className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">
            Nenhum video encontrado
          </h3>
          <p className="text-sm text-muted-foreground max-w-md">
            Baixe seu primeiro video usando o formulario acima. Seus videos aparecera aqui.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {videos.map((video) => (
            <VideoCard
              key={video.id}
              id={video.id}
              title={video.title}
              channel={video.channel}
              thumbnail={video.thumbnail}
              path={video.path}
              onPlay={() => setSelectedVideo(video)}
              onDelete={() => handleDelete(video)}
            />
          ))}
        </div>
      )}

      {selectedVideo && (
        <VideoPlayer
          video={selectedVideo}
          source="local"
          onClose={() => setSelectedVideo(null)}
          onDelete={() => handleDelete(selectedVideo)}
        />
      )}
    </div>
  );
}
