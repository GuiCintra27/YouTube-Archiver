"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, VideoOff, LibraryBig } from "lucide-react";
import VideoCard from "@/components/common/videos/video-card";
import VideoPlayer from "@/components/common/videos/video-player";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { PATHS } from "@/lib/paths";
import { APIURLS } from "@/lib/api-urls";

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
  title = "Últimos vídeos",
  limit = 4,
  refreshToken,
  ctaLabel = "Ver biblioteca completa",
  ctaHref = PATHS.LIBRARY,
}: RecentVideosProps) {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);

  const apiUrl =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      : "http://localhost:8000";

  const fetchVideos = async () => {
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
  };

  useEffect(() => {
    fetchVideos();
  }, [apiUrl, limit, refreshToken]);

  const handleDelete = async (video: Video) => {
    try {
      const response = await fetch(
        `${apiUrl}/api/${APIURLS.VIDEOS}/${encodeURIComponent(video.path)}`,
        { method: "DELETE" }
      );
      if (!response.ok) throw new Error("Falha ao excluir vídeo");
      setVideos((prev) => prev.filter((v) => v.id !== video.id));
      if (selectedVideo?.id === video.id) setSelectedVideo(null);
    } catch (err) {
      alert(
        `Erro ao excluir vídeo: ${
          err instanceof Error ? err.message : "Erro desconhecido"
        }`
      );
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <LibraryBig className="h-5 w-5 text-primary" />
          <h2 className="text-2xl font-bold">{title}</h2>
        </div>
        <Button variant="outline" size="sm">
          <Link href={ctaHref}>{ctaLabel}</Link>
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-10">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <Alert variant="destructive">
          <AlertDescription>Erro ao carregar vídeos: {error}</AlertDescription>
        </Alert>
      ) : videos.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <VideoOff className="h-12 w-12 text-muted-foreground mb-3" />
          <p className="text-sm text-muted-foreground">
            Nenhum vídeo encontrado.
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
          onClose={() => setSelectedVideo(null)}
          onDelete={() => {
            handleDelete(selectedVideo);
            setSelectedVideo(null);
          }}
        />
      )}
    </div>
  );
}
