"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import { PaginationControls } from "@/components/common/pagination";
import VideoCard from "@/components/common/videos/video-card";
import VideoGridHeader from "@/components/common/videos/video-grid-header";
import VideoGridLoadingState from "@/components/common/videos/video-grid-loading-state";
import VideoGridErrorState from "@/components/common/videos/video-grid-error-state";
import VideoGridEmptyState from "@/components/common/videos/video-grid-empty-state";
import SelectionActionBar from "@/components/common/videos/selection-action-bar";
import BatchDeleteDialog from "@/components/common/videos/batch-delete-dialog";
import VideoPlayerModal from "@/components/common/videos/video-player-modal";
import { Cloud } from "lucide-react";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";
import {
  deleteDriveVideo,
  deleteDriveVideosBatch,
  renameDriveVideo,
  updateDriveThumbnail,
} from "@/lib/client/api";

export type DriveVideo = {
  id: string;
  name: string;
  path: string;
  size: number;
  created_at: string;
  modified_at: string;
  thumbnail?: string;
  custom_thumbnail_id?: string;
};

const PAGE_SIZE = 12;

type DriveVideoGridProps = {
  initialData?: {
    videos: DriveVideo[];
    total: number;
    page: number;
  };
};

export default function DriveVideoGrid({ initialData }: DriveVideoGridProps) {
  const apiUrl = useApiUrl();
  const [videos, setVideos] = useState<DriveVideo[]>(initialData?.videos || []);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<DriveVideo | null>(null);
  const [page, setPage] = useState(initialData?.page || 1);
  const [total, setTotal] = useState(initialData?.total || 0);
  const skipInitialFetch = useRef(Boolean(initialData));
  const [thumbnailBusters, setThumbnailBusters] = useState<Record<string, string>>({});
  const router = useRouter();

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [batchDeleteDialogOpen, setBatchDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const fetchVideos = useCallback(
    async (pageNumber = 1) => {
      if (!apiUrl) return;
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(
          `${apiUrl}/api/${APIURLS.DRIVE_VIDEOS}?page=${pageNumber}&limit=${PAGE_SIZE}`,
          { cache: "no-store" }
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
    if (!apiUrl) return;
    if (skipInitialFetch.current && page === (initialData?.page || 1)) {
      skipInitialFetch.current = false;
      return;
    }
    fetchVideos(page);
  }, [page, fetchVideos, apiUrl, initialData?.page, skipInitialFetch]);

  useEffect(() => {
    if (!initialData) return;
    const initialPage = initialData.page || 1;
    if (page !== initialPage) return;
    setVideos(initialData.videos || []);
    setTotal(initialData.total || 0);
    setLoading(false);
  }, [initialData, page]);

  const handleDelete = useCallback(
    async (video: DriveVideo) => {
      if (deletingId) return;

      setDeletingId(video.id);

      try {
        await deleteDriveVideo(video.id);
        await fetchVideos(page);
        setSelectedIds(new Set());
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao excluir vídeo");
        throw err;
      } finally {
        setDeletingId(null);
        setSelectedVideo(null);
      }
    },
    [deletingId, page, fetchVideos]
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

  const selectedIdsArray = useMemo(
    () => Array.from(selectedIds),
    [selectedIds]
  );
  const selectedCount = selectedIdsArray.length;

  const handleBatchDeleteConfirm = useCallback(async () => {
    if (deleting || selectedCount === 0) return;

    try {
      setDeleting(true);
      const result = await deleteDriveVideosBatch(selectedIdsArray);

      if (!!result.total_failed && result.total_failed > 0) {
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
  }, [selectedCount, selectedIdsArray, page, fetchVideos, deleting]);

  const handleBatchDialogChange = useCallback(
    (open: boolean) => {
      if (deleting) return;
      setBatchDeleteDialogOpen(open);
    },
    [deleting]
  );

  const handleEdit = useCallback(
    async (video: DriveVideo, newTitle: string, newThumbnail?: File) => {
      try {
        // Get current name without extension for comparison
        const currentBaseName = video.name.replace(/\.[^/.]+$/, "");

        // Rename if title changed
        if (newTitle !== currentBaseName) {
          await renameDriveVideo(video.id, newTitle);
        }

        // Update thumbnail if provided
        if (newThumbnail) {
          await updateDriveThumbnail(video.id, newThumbnail);
          setThumbnailBusters((prev) => ({
            ...prev,
            [video.id]: Date.now().toString(),
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
    [page, fetchVideos, router]
  );

  // Helper to get thumbnail URL for Drive videos
  const getThumbnailUrl = (video: DriveVideo): string | undefined => {
    if (video.custom_thumbnail_id && apiUrl) {
      return `${apiUrl}/api/drive/custom-thumbnail/${video.custom_thumbnail_id}`;
    }
    if (video.thumbnail) {
      return video.thumbnail;
    }
    return undefined;
  };

  return (
    <>
      <div className="space-y-6">
        {/* Header */}
        <VideoGridHeader
          icon={<Cloud className="h-5 w-5 text-cyan" />}
          title="Vídeos no Drive"
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
            label="Carregando vídeos do Drive..."
            iconWrapperClassName="bg-cyan/10"
            iconClassName="text-cyan"
          />
        ) : error ? (
          <VideoGridErrorState message={`Erro ao carregar vídeos: ${error}`} />
        ) : videos.length === 0 ? (
          <VideoGridEmptyState
            title="Nenhum vídeo no Drive"
            description="Faça upload de vídeos locais para o Drive usando o painel de sincronização acima."
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {videos.map((video, index) => (
              <VideoCard
                key={video.id}
                id={video.id}
                title={video.name.replace(/\.[^/.]+$/, "")}
                channel={video.path}
                path={video.path}
                thumbnailUrl={getThumbnailUrl(video)}
                thumbnailCacheKey={thumbnailBusters[video.id]}
                size={video.size}
                createdAt={video.created_at}
                onPlay={() => setSelectedVideo(video)}
                onDelete={() => handleDelete(video)}
                deleteScope="drive"
                selectable={true}
                selected={selectedIds.has(video.id)}
                onSelectionChange={() => toggleSelection(video.id)}
                editable={true}
                onEdit={(newTitle, newThumbnail) =>
                  handleEdit(video, newTitle, newThumbnail)
                }
                shareScope="drive"
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
        iconWrapperClassName="bg-cyan/10"
        iconClassName="text-cyan"
      />

      {/* Batch Delete Confirmation Dialog */}
      <BatchDeleteDialog
        open={batchDeleteDialogOpen}
        onOpenChange={handleBatchDialogChange}
        deleting={deleting}
        selectedCount={selectedCount}
        scopeLabel="do Google Drive"
        onConfirm={handleBatchDeleteConfirm}
      />

      {/* Video Player Modal */}
      {selectedVideo && (
        <VideoPlayerModal
          video={selectedVideo}
          source="drive"
          onClose={() => setSelectedVideo(null)}
          onDelete={() => handleDelete(selectedVideo)}
        />
      )}
    </>
  );
}
