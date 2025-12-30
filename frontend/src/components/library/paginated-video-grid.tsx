"use client";

import { useEffect, useState, useCallback, useRef } from "react";
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
import {
  Loader2,
  VideoOff,
  Trash2,
  X,
  CheckSquare,
  Library,
} from "lucide-react";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";
import {
  deleteLocalVideo,
  deleteLocalVideosBatch,
  renameLocalVideo,
  updateLocalThumbnail,
} from "@/lib/client/api";

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

type PaginatedVideoGridProps = {
  initialData?: {
    videos: Video[];
    total: number;
    page: number;
  };
};

export default function PaginatedVideoGrid({
  initialData,
}: PaginatedVideoGridProps) {
  const apiUrl = useApiUrl();
  const [videos, setVideos] = useState<Video[]>(initialData?.videos || []);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);
  const [page, setPage] = useState(initialData?.page || 1);
  const [total, setTotal] = useState(initialData?.total || 0);
  const skipInitialFetch = useRef(Boolean(initialData));

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
    if (!apiUrl) return;
    if (skipInitialFetch.current && page === (initialData?.page || 1)) {
      skipInitialFetch.current = false;
      return;
    }
    fetchVideos(page);
  }, [fetchVideos, page, apiUrl, initialData?.page]);

  const handleDelete = useCallback(
    async (video: Video) => {
      try {
        await deleteLocalVideo(video.path);

        // Recarregar página atual
        fetchVideos(page);

        setSelectedVideo((prev) => (prev?.id === video.id ? null : prev));
      } catch (err) {
        console.error("Erro ao excluir vídeo:", err);
        setError(err instanceof Error ? err.message : "Erro ao excluir vídeo");
      }
    },
    [page, fetchVideos]
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
    if (deleting || selectedPaths.size === 0) return;

    try {
      setDeleting(true);
      const result = await deleteLocalVideosBatch(Array.from(selectedPaths));

      if (!!result.total_failed && result.total_failed > 0) {
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
  }, [selectedPaths, page, fetchVideos, deleting]);

  const handleBatchDialogChange = useCallback(
    (open: boolean) => {
      if (deleting) return;
      setBatchDeleteDialogOpen(open);
    },
    [deleting]
  );

  const handleEdit = useCallback(
    async (video: Video, newTitle: string, newThumbnail?: File) => {
      try {
        // Rename if title changed
        if (newTitle !== video.title) {
          const renameResult = await renameLocalVideo(video.path, newTitle);
          video.path = renameResult.new_path || video.path;
        }

        // Update thumbnail if provided
        if (newThumbnail) {
          await updateLocalThumbnail(video.path, newThumbnail);
        }

        // Refresh the video list
        await fetchVideos(page);
      } catch (err) {
        console.error("Erro ao editar vídeo:", err);
        setError(err instanceof Error ? err.message : "Erro ao editar vídeo");
        throw err;
      }
    },
    [page, fetchVideos]
  );

  const hasSelection = selectedPaths.size > 0;

  return (
    <>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="icon-glow p-2">
              <Library className="h-5 w-5 text-teal" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Minha Biblioteca</h2>
              <p className="text-sm text-muted-foreground">
                {total} {total === 1 ? "vídeo" : "vídeos"} encontrados
              </p>
            </div>
          </div>

          <PaginationControls
            page={page}
            totalPages={totalPages}
            loading={loading}
            onPageChange={setPage}
            onRefresh={() => fetchVideos(page)}
          />
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-teal/10 flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-teal" />
              </div>
              <p className="text-sm text-muted-foreground">
                Carregando vídeos...
              </p>
            </div>
          </div>
        ) : error ? (
          <Alert className="bg-red-500/10 border-red-500/20">
            <AlertDescription className="text-red-400">
              Erro ao carregar vídeos: {error}
            </AlertDescription>
          </Alert>
        ) : videos.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center glass-card rounded-2xl">
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
              <VideoOff className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium text-white mb-2">
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
                duration={video.duration}
                size={video.size}
                createdAt={video.created_at}
                onPlay={() => setSelectedVideo(video)}
                onDelete={() => handleDelete(video)}
                selectable={true}
                selected={selectedPaths.has(video.path)}
                onSelectionChange={() => toggleSelection(video.path)}
                editable={true}
                onEdit={(newTitle, newThumbnail) =>
                  handleEdit(video, newTitle, newThumbnail)
                }
              />
            ))}
          </div>
        )}
      </div>

      {/* Selection Action Bar */}
      {hasSelection && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[70]">
          <div className="glass-card rounded-xl px-4 py-3 flex items-center gap-4 shadow-lg shadow-black/20">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-teal/10 flex items-center justify-center">
                <CheckSquare className="h-4 w-4 text-teal" />
              </div>
              <span className="font-medium text-white">
                {selectedPaths.size}{" "}
                {selectedPaths.size === 1 ? "selecionado" : "selecionados"}
              </span>
            </div>

            <div className="h-6 w-px bg-white/10" />

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={selectAll}
                disabled={deleting || selectedPaths.size === videos.length}
                className="text-muted-foreground hover:text-white hover:bg-white/10"
              >
                Selecionar todos
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={clearSelection}
                disabled={deleting}
                className="text-muted-foreground hover:text-white hover:bg-white/10"
              >
                <X className="h-4 w-4 mr-1" />
                Limpar
              </Button>

              <Button
                size="sm"
                onClick={() => setBatchDeleteDialogOpen(true)}
                disabled={deleting}
                className="bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30"
              >
                {deleting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Excluindo...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4 mr-1" />
                    Excluir ({selectedPaths.size})
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Batch Delete Confirmation Dialog */}
      <AlertDialog
        open={batchDeleteDialogOpen}
        onOpenChange={handleBatchDialogChange}
      >
        <AlertDialogContent className="glass border-white/10">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white flex items-center gap-2">
              <Trash2 className="h-5 w-5 text-red-400" />
              Excluir {selectedPaths.size} vídeos?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-muted-foreground">
              Tem certeza que deseja excluir {selectedPaths.size}{" "}
              {selectedPaths.size === 1 ? "vídeo" : "vídeos"} da biblioteca?
              Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel
              disabled={deleting}
              className="bg-white/5 border-white/10 text-white hover:bg-white/10 hover:text-white"
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleBatchDeleteConfirm}
              disabled={deleting}
              className="bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30"
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
