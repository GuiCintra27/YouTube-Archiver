"use client";

import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import VideoCard from "@/components/common/videos/video-card";
import { PaginationControls } from "@/components/common/pagination";
import VideoGridHeader from "@/components/common/videos/video-grid-header";
import VideoGridLoadingState from "@/components/common/videos/video-grid-loading-state";
import VideoGridErrorState from "@/components/common/videos/video-grid-error-state";
import VideoGridEmptyState from "@/components/common/videos/video-grid-empty-state";
import SelectionActionBar from "@/components/common/videos/selection-action-bar";
import BatchDeleteDialog from "@/components/common/videos/batch-delete-dialog";
import VideoPlayerModal from "@/components/common/videos/video-player-modal";
import { Library } from "lucide-react";
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
  const [thumbnailBusters, setThumbnailBusters] = useState<Record<string, string>>({});
  const router = useRouter();

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
          `${apiUrl}/api/${APIURLS.VIDEOS}?page=${pageNumber}&limit=${PAGE_SIZE}`,
          { cache: "no-store" }
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

  useEffect(() => {
    if (!initialData) return;
    const initialPage = initialData.page || 1;
    if (page !== initialPage) return;
    setVideos(initialData.videos || []);
    setTotal(initialData.total || 0);
    setLoading(false);
  }, [initialData, page]);

  const handleDelete = useCallback(
    async (video: Video) => {
      try {
        await deleteLocalVideo(video.path);

        setVideos((prev) => prev.filter((item) => item.id !== video.id));
        setTotal((prev) => Math.max(0, prev - 1));

        // Recarregar página atual
        await fetchVideos(page);

        setSelectedVideo((prev) => (prev?.id === video.id ? null : prev));
      } catch (err) {
        console.error("Erro ao excluir vídeo:", err);
        setError(err instanceof Error ? err.message : "Erro ao excluir vídeo");
      }
    },
    [page, fetchVideos, router]
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

  const selectedPathsArray = useMemo(
    () => Array.from(selectedPaths),
    [selectedPaths]
  );
  const selectedCount = selectedPathsArray.length;

  const handleBatchDeleteConfirm = useCallback(async () => {
    if (deleting || selectedCount === 0) return;

    try {
      setDeleting(true);
      const result = await deleteLocalVideosBatch(selectedPathsArray);

      if (!!result.total_failed && result.total_failed > 0) {
        setError(
          `${result.total_deleted} excluídos, ${result.total_failed} falhas`
        );
      }

      const selectedSet = new Set(selectedPathsArray);
      setVideos((prev) => prev.filter((item) => !selectedSet.has(item.path)));
      setTotal((prev) => Math.max(0, prev - selectedPathsArray.length));
      await fetchVideos(page);
      setBatchDeleteDialogOpen(false);
      setSelectedPaths(new Set());
    } catch (err) {
      console.error("Erro ao excluir vídeos:", err);
      setError(err instanceof Error ? err.message : "Erro ao excluir vídeos");
    } finally {
      setDeleting(false);
    }
  }, [selectedCount, selectedPathsArray, page, fetchVideos, deleting]);

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
        let updatedPath = video.path;
        if (newTitle !== video.title) {
          const renameResult = await renameLocalVideo(video.path, newTitle);
          updatedPath = renameResult.new_path || video.path;
          video.path = updatedPath;
        }

        // Update thumbnail if provided
        if (newThumbnail) {
          await updateLocalThumbnail(updatedPath, newThumbnail);
          setThumbnailBusters((prev) => ({
            ...prev,
            [updatedPath]: Date.now().toString(),
          }));
        }

        // Refresh the video list + SSR data
        await fetchVideos(page);
        router.refresh();
      } catch (err) {
        console.error("Erro ao editar vídeo:", err);
        setError(err instanceof Error ? err.message : "Erro ao editar vídeo");
        throw err;
      }
    },
    [page, fetchVideos]
  );

  return (
    <>
      <div className="space-y-6">
        {/* Header */}
        <VideoGridHeader
          icon={<Library className="h-5 w-5 text-teal" />}
          title="Minha Biblioteca"
          subtitle={`${total} ${total === 1 ? "vídeo" : "vídeos"} encontrados`}
          rightSlot={
            <PaginationControls
              page={page}
              totalPages={totalPages}
              loading={loading}
              onPageChange={setPage}
              onRefresh={() => fetchVideos(page)}
            />
          }
        />

        {/* Content */}
        {loading ? (
          <VideoGridLoadingState
            label="Carregando vídeos..."
            iconWrapperClassName="bg-teal/10"
            iconClassName="text-teal"
          />
        ) : error ? (
          <VideoGridErrorState message={`Erro ao carregar vídeos: ${error}`} />
        ) : videos.length === 0 ? (
          <VideoGridEmptyState
            title="Nenhum vídeo encontrado"
            description="Faça o download de alguns vídeos para vê-los aparecer aqui."
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {videos.map((video, index) => (
              <VideoCard
                key={video.id}
                id={video.id}
                title={video.title}
                channel={video.channel}
                thumbnail={video.thumbnail}
                thumbnailCacheKey={thumbnailBusters[video.path] ?? video.modified_at}
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
                priority={index === 0}
              />
            ))}
          </div>
        )}
      </div>

      {/* Selection Action Bar */}
      <SelectionActionBar
        selectedCount={selectedCount}
        totalCount={videos.length}
        deleting={deleting}
        onSelectAll={selectAll}
        onClear={clearSelection}
        onDelete={() => setBatchDeleteDialogOpen(true)}
        iconWrapperClassName="bg-teal/10"
        iconClassName="text-teal"
      />

      {/* Batch Delete Confirmation Dialog */}
      <BatchDeleteDialog
        open={batchDeleteDialogOpen}
        onOpenChange={handleBatchDialogChange}
        deleting={deleting}
        selectedCount={selectedCount}
        scopeLabel="da biblioteca"
        onConfirm={handleBatchDeleteConfirm}
      />

      {/* Video Player Modal */}
      {selectedVideo && (
        <VideoPlayerModal
          video={selectedVideo}
          source="local"
          onClose={() => setSelectedVideo(null)}
          onDelete={() => handleDelete(selectedVideo)}
        />
      )}
    </>
  );
}
