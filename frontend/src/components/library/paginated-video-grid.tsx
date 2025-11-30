"use client";

import { useEffect, useState, useCallback } from "react";
import VideoCard from "@/components/common/videos/video-card";
import VideoPlayer from "@/components/common/videos/video-player";
import { PaginationControls } from "@/components/common/pagination";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, VideoOff } from "lucide-react";
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

const PAGE_SIZE = 12;

export default function PaginatedVideoGrid() {
  const apiUrl = useApiUrl();
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const fetchVideos = useCallback(
    async (pageNumber: number) => {
      if (!apiUrl) return;
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(
          `${apiUrl}/api/${APIURLS.VIDEOS}?page=${pageNumber}&limit=${PAGE_SIZE}`
        );

        if (!response.ok) {
          throw new Error("Falha ao carregar vídeos");
        }

        const data = await response.json();
        setVideos(data.videos || []);
        setTotal(data.total || 0);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro desconhecido");
      } finally {
        setLoading(false);
      }
    },
    [apiUrl]
  );

  useEffect(() => {
    fetchVideos(page);
  }, [fetchVideos, page]);

  const handleDelete = useCallback(
    async (video: Video) => {
      if (!apiUrl) return;
      try {
        const response = await fetch(
          `${apiUrl}/api/${APIURLS.VIDEOS}/${encodeURIComponent(video.path)}`,
          { method: "DELETE" }
        );

        if (!response.ok) {
          throw new Error("Falha ao excluir vídeo");
        }

        // Recarregar página atual
        fetchVideos(page);

        setSelectedVideo((prev) => (prev?.id === video.id ? null : prev));
      } catch (err) {
        console.error("Erro ao excluir vídeo:", err);
        setError(err instanceof Error ? err.message : "Erro ao excluir vídeo");
      }
    },
    [apiUrl, page, fetchVideos]
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Minha Biblioteca</h2>
          <p className="text-sm text-muted-foreground">
            {total} {total === 1 ? "vídeo" : "vídeos"}
          </p>
        </div>

        <PaginationControls
          page={page}
          totalPages={totalPages}
          loading={loading}
          onPageChange={setPage}
          onRefresh={() => fetchVideos(page)}
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <Alert variant="destructive">
          <AlertDescription>Erro ao carregar vídeos: {error}</AlertDescription>
        </Alert>
      ) : videos.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <VideoOff className="h-16 w-16 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">
            Nenhum vídeo encontrado
          </h3>
          <p className="text-sm text-muted-foreground max-w-md">
            Faça o download de alguns vídeos para vê-los aparecer aqui.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
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

      {/* Video Player Modal */}
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
