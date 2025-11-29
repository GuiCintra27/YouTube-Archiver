"use client";

import { useEffect, useState } from "react";
import VideoCard from "@/components/common/videos/video-card";
import VideoPlayer from "@/components/common/videos/video-player";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, VideoOff, Search, RefreshCw } from "lucide-react";
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

const PAGE_SIZE = 12;

export default function PaginatedVideoGrid() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pageInput, setPageInput] = useState("1");
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const apiUrl =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      : "http://localhost:8000";

  const fetchVideos = async (pageNumber: number) => {
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
  };

  useEffect(() => {
    fetchVideos(page);
  }, [apiUrl, page]);

  useEffect(() => {
    setPageInput(String(page));
  }, [page]);

  const handleDelete = async (video: Video) => {
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

      if (selectedVideo?.id === video.id) {
        setSelectedVideo(null);
      }
    } catch (err) {
      alert(
        `Erro ao excluir vídeo: ${
          err instanceof Error ? err.message : "Erro desconhecido"
        }`
      );
    }
  };

  const canPrev = page > 1;
  const canNext = page < totalPages;

  const handlePageJump = () => {
    const parsed = parseInt(pageInput, 10);
    if (Number.isNaN(parsed)) {
      setPageInput(String(page));
      return;
    }

    const target = Math.min(Math.max(parsed, 1), totalPages);
    setPageInput(String(target));
    setPage(target);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Minha Biblioteca</h2>
          <p className="text-sm text-muted-foreground">
            {total} {total === 1 ? "vídeo" : "vídeos"}
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
          <div className="flex w-full flex-wrap items-center gap-3 rounded-lg border bg-card/60 px-3 py-2 shadow-sm sm:w-auto">
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
              onClick={() => fetchVideos(page)}
              disabled={loading}
            >
              <RefreshCw className="h-4 w-4" />
              <span className="hidden sm:inline">Atualizar</span>
            </Button>

            <span className="hidden sm:block h-6 w-px bg-border" aria-hidden />

            <div className="flex items-center gap-2">
              <span>Navegar Para:</span>

              <div className="relative flex items-center">
                <Input
                  type="number"
                  inputMode="numeric"
                  min={1}
                  max={totalPages}
                  value={pageInput}
                  onChange={(e) => setPageInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handlePageJump();
                    }
                  }}
                  className="h-10 w-24 pr-10 text-center"
                  aria-label="Ir para página"
                  placeholder="Página"
                  disabled={loading || totalPages === 0}
                />
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2"
                  onClick={handlePageJump}
                  disabled={loading || totalPages === 0}
                  aria-label="Confirmar página"
                >
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <span className="hidden sm:block h-6 w-px bg-border" aria-hidden />

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={!canPrev || loading}
              >
                Anterior
              </Button>
              <span className="text-sm text-muted-foreground">
                Página {page} de {totalPages}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPage((p) => p + 1)}
                disabled={!canNext || loading}
              >
                Próxima
              </Button>
            </div>
          </div>
        </div>
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
