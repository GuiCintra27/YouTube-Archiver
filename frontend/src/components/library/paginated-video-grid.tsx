"use client";

import { useEffect, useState, useCallback } from "react";
import VideoCard from "@/components/common/videos/video-card";
import VideoPlayer from "@/components/common/videos/video-player";
import { PaginationControls } from "@/components/common/pagination";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Loader2, VideoOff, Trash2, X, CheckSquare } from "lucide-react";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";

interface Video {
  id: string;
  title: string;
  channel: string;
  path: string;
  thumbnail?: string;
  duration?: string;
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

  // Selection state
  const [selectedPaths, setSelectedPaths] = useState<Set<string>>(new Set());
  const [batchDeleteDialogOpen, setBatchDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

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
        // Clear selection when changing pages
        setSelectedPaths(new Set());
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

  // Selection handlers
  const toggleSelection = useCallback((path: string) => {
    setSelectedPaths((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelectedPaths(new Set(videos.map((v) => v.path)));
  }, [videos]);

  const clearSelection = useCallback(() => {
    setSelectedPaths(new Set());
  }, []);

  const handleBatchDeleteConfirm = useCallback(async () => {
    if (selectedPaths.size === 0 || !apiUrl) return;

    try {
      setDeleting(true);
      const response = await fetch(
        `${apiUrl}/api/${APIURLS.VIDEOS_DELETE_BATCH}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(Array.from(selectedPaths)),
        }
      );

      if (!response.ok) {
        throw new Error("Falha ao excluir vídeos");
      }

      const result = await response.json();

      if (result.total_failed > 0) {
        setError(
          `${result.total_deleted} excluídos, ${result.total_failed} falhas`
        );
      }

      await fetchVideos(page);
      setBatchDeleteDialogOpen(false);
      setSelectedPaths(new Set());
    } catch (err) {
      console.error("Erro ao excluir vídeos:", err);
      setError(err instanceof Error ? err.message : "Erro ao excluir vídeos");
    } finally {
      setDeleting(false);
    }
  }, [selectedPaths, apiUrl, page, fetchVideos]);

  const hasSelection = selectedPaths.size > 0;

  return (
    <>
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
            <AlertDescription>
              Erro ao carregar vídeos: {error}
            </AlertDescription>
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
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {videos.map((video) => (
              <VideoCard
                key={video.id}
                id={video.id}
                title={video.title}
                channel={video.channel}
                thumbnail={video.thumbnail}
                path={video.path}
                duration={video.duration}
                size={video.size}
                createdAt={video.created_at}
                onPlay={() => setSelectedVideo(video)}
                onDelete={() => handleDelete(video)}
                selectable={true}
                selected={selectedPaths.has(video.path)}
                onSelectionChange={() => toggleSelection(video.path)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Selection Action Bar */}
      {hasSelection && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
          <div className="bg-background border shadow-lg rounded-lg px-4 py-3 flex items-center gap-4">
            <div className="flex items-center gap-2">
              <CheckSquare className="h-5 w-5 text-primary" />
              <span className="font-medium">
                {selectedPaths.size}{" "}
                {selectedPaths.size === 1 ? "selecionado" : "selecionados"}
              </span>
            </div>

            <div className="h-6 w-px bg-border" />

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={selectAll}
                disabled={selectedPaths.size === videos.length}
              >
                Selecionar todos
              </Button>

              <Button variant="ghost" size="sm" onClick={clearSelection}>
                <X className="h-4 w-4 mr-1" />
                Limpar
              </Button>

              <Button
                variant="destructive"
                size="sm"
                onClick={() => setBatchDeleteDialogOpen(true)}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Excluir ({selectedPaths.size})
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Batch Delete Confirmation Dialog */}
      <AlertDialog
        open={batchDeleteDialogOpen}
        onOpenChange={setBatchDeleteDialogOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Excluir {selectedPaths.size} vídeos?
            </AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir {selectedPaths.size}{" "}
              {selectedPaths.size === 1 ? "vídeo" : "vídeos"} da biblioteca?
              Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBatchDeleteConfirm}
              disabled={deleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Excluindo...
                </>
              ) : (
                `Excluir ${selectedPaths.size} ${
                  selectedPaths.size === 1 ? "vídeo" : "vídeos"
                }`
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Video Player Modal */}
      {selectedVideo && (
        <VideoPlayer
          video={selectedVideo}
          source="local"
          onClose={() => setSelectedVideo(null)}
          onDelete={() => handleDelete(selectedVideo)}
        />
      )}
    </>
  );
}
