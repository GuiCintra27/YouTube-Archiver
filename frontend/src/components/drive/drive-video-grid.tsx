"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PaginationControls } from "@/components/common/pagination";
import VideoCard from "@/components/common/videos/video-card";
import VideoPlayer from "@/components/common/videos/video-player";
import {
  Loader2,
  VideoOff,
  Cloud,
  Trash2,
  X,
  CheckSquare,
} from "lucide-react";
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
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";

interface DriveVideo {
  id: string;
  name: string;
  path: string;
  size: number;
  created_at: string;
  modified_at: string;
  thumbnail?: string;
  custom_thumbnail_id?: string;
}

const PAGE_SIZE = 12;

export default function DriveVideoGrid() {
  const apiUrl = useApiUrl();
  const [videos, setVideos] = useState<DriveVideo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<DriveVideo | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [batchDeleteDialogOpen, setBatchDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const fetchVideos = useCallback(
    async (pageNumber = 1) => {
      if (!apiUrl) return;
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(
          `${apiUrl}/api/${APIURLS.DRIVE_VIDEOS}?page=${pageNumber}&limit=${PAGE_SIZE}`
        );

        if (!response.ok) {
          throw new Error("Falha ao carregar vídeos do Drive");
        }

        const data = await response.json();
        const list = data.videos || [];
        const totalCount = data.total || list.length;
        const maxPage = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

        if (pageNumber > maxPage) {
          setPage(maxPage);
          return;
        }

        setVideos(list);
        setTotal(totalCount);
        setPage(pageNumber);
        // Clear selection when changing pages
        setSelectedIds(new Set());
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
  }, [page, fetchVideos]);

  const handleDelete = useCallback(
    async (video: DriveVideo) => {
      if (!apiUrl) return;

      const response = await fetch(
        `${apiUrl}/api/${APIURLS.DRIVE_VIDEOS}/${video.id}`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        throw new Error("Falha ao excluir vídeo");
      }

      await fetchVideos(page);
      setSelectedVideo(null);
    },
    [apiUrl, page, fetchVideos]
  );

  // Selection handlers
  const toggleSelection = useCallback((videoId: string) => {
    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(videoId)) {
        newSet.delete(videoId);
      } else {
        newSet.add(videoId);
      }
      return newSet;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelectedIds(new Set(videos.map((v) => v.id)));
  }, [videos]);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const handleBatchDeleteConfirm = useCallback(async () => {
    if (deleting || selectedIds.size === 0 || !apiUrl) return;

    try {
      setDeleting(true);
      const response = await fetch(
        `${apiUrl}/api/${APIURLS.DRIVE_DELETE_BATCH}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(Array.from(selectedIds)),
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
      setSelectedIds(new Set());
    } catch (err) {
      console.error("Erro ao excluir vídeos:", err);
      setError(err instanceof Error ? err.message : "Erro ao excluir vídeos");
    } finally {
      setDeleting(false);
    }
  }, [selectedIds, apiUrl, page, fetchVideos, deleting]);

  const handleBatchDialogChange = useCallback(
    (open: boolean) => {
      if (deleting) return;
      setBatchDeleteDialogOpen(open);
    },
    [deleting]
  );

  const handleEdit = useCallback(
    async (video: DriveVideo, newTitle: string, newThumbnail?: File) => {
      if (!apiUrl) return;

      try {
        // Get current name without extension for comparison
        const currentBaseName = video.name.replace(/\.[^/.]+$/, "");

        // Rename if title changed
        if (newTitle !== currentBaseName) {
          const renameResponse = await fetch(
            `${apiUrl}/api/${APIURLS.DRIVE_VIDEOS}/${video.id}/rename`,
            {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ new_name: newTitle }),
            }
          );

          if (!renameResponse.ok) {
            throw new Error("Falha ao renomear vídeo");
          }
        }

        // Update thumbnail if provided
        if (newThumbnail) {
          const formData = new FormData();
          formData.append("thumbnail", newThumbnail);

          const thumbnailResponse = await fetch(
            `${apiUrl}/api/${APIURLS.DRIVE_VIDEOS}/${video.id}/thumbnail`,
            {
              method: "POST",
              body: formData,
            }
          );

          if (!thumbnailResponse.ok) {
            throw new Error("Falha ao atualizar thumbnail");
          }
        }

        // Refresh the video list
        await fetchVideos(page);
      } catch (err) {
        console.error("Erro ao editar vídeo:", err);
        setError(err instanceof Error ? err.message : "Erro ao editar vídeo");
        throw err;
      }
    },
    [apiUrl, page, fetchVideos]
  );

  // Helper to get thumbnail URL for Drive videos
  const getThumbnailUrl = (video: DriveVideo): string | undefined => {
    if (video.thumbnail) {
      return video.thumbnail;
    }
    if (video.custom_thumbnail_id && apiUrl) {
      return `${apiUrl}/api/drive/custom-thumbnail/${video.custom_thumbnail_id}`;
    }
    return undefined;
  };

  const hasSelection = selectedIds.size > 0;

  return (
    <>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="icon-glow p-2">
              <Cloud className="h-5 w-5 text-cyan" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Vídeos no Drive</h2>
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
              <div className="w-12 h-12 rounded-full bg-cyan/10 flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-cyan" />
              </div>
              <p className="text-sm text-muted-foreground">Carregando vídeos do Drive...</p>
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
              Nenhum vídeo no Drive
            </h3>
            <p className="text-sm text-muted-foreground max-w-md">
              Faça upload de vídeos locais para o Drive usando o painel de
              sincronização acima.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {videos.map((video) => (
              <VideoCard
                key={video.id}
                id={video.id}
                title={video.name.replace(/\.[^/.]+$/, "")}
                channel={video.path}
                path={video.path}
                thumbnailUrl={getThumbnailUrl(video)}
                size={video.size}
                createdAt={video.created_at}
                onPlay={() => setSelectedVideo(video)}
                onDelete={() => handleDelete(video)}
                deleteScope="drive"
                selectable={true}
                selected={selectedIds.has(video.id)}
                onSelectionChange={() => toggleSelection(video.id)}
                editable={true}
                onEdit={(newTitle, newThumbnail) => handleEdit(video, newTitle, newThumbnail)}
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
              <div className="w-8 h-8 rounded-lg bg-cyan/10 flex items-center justify-center">
                <CheckSquare className="h-4 w-4 text-cyan" />
              </div>
              <span className="font-medium text-white">
                {selectedIds.size}{" "}
                {selectedIds.size === 1 ? "selecionado" : "selecionados"}
              </span>
            </div>

            <div className="h-6 w-px bg-white/10" />

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={selectAll}
                disabled={deleting || selectedIds.size === videos.length}
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
                    Excluir ({selectedIds.size})
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
              Excluir {selectedIds.size} vídeos?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-muted-foreground">
              Tem certeza que deseja excluir {selectedIds.size}{" "}
              {selectedIds.size === 1 ? "vídeo" : "vídeos"} do Google Drive?
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
                `Excluir ${selectedIds.size} ${
                  selectedIds.size === 1 ? "vídeo" : "vídeos"
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
          source="drive"
          onClose={() => setSelectedVideo(null)}
          onDelete={() => handleDelete(selectedVideo)}
        />
      )}
    </>
  );
}
