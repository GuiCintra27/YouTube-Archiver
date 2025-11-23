"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Loader2,
  VideoOff,
  Cloud,
  Trash2,
  RefreshCw,
  Play,
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
import DriveVideoPlayer from "./drive-video-player";
import { APIURLS } from "@/lib/api-urls";

interface DriveVideo {
  id: string;
  name: string;
  path: string;
  size: number;
  created_at: string;
  modified_at: string;
  thumbnail?: string;
}

export default function DriveVideoGrid() {
  const [videos, setVideos] = useState<DriveVideo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [videoToDelete, setVideoToDelete] = useState<DriveVideo | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<DriveVideo | null>(null);
  const [thumbnailErrors, setThumbnailErrors] = useState<Set<string>>(
    new Set()
  );

  const apiUrl =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      : "http://localhost:8000";

  const fetchVideos = async () => {
    try {
      setLoading(true);
      setError(null);
      setThumbnailErrors(new Set()); // Resetar erros ao recarregar
      const response = await fetch(`${apiUrl}/api/${APIURLS.DRIVE_VIDEOS}`);

      if (!response.ok) {
        throw new Error("Falha ao carregar vídeos do Drive");
      }

      const data = await response.json();
      setVideos(data.videos || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  const handleDeleteClick = (video: DriveVideo) => {
    setVideoToDelete(video);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!videoToDelete) return;

    try {
      setDeleting(true);
      const response = await fetch(
        `${apiUrl}/api/${APIURLS.DRIVE_VIDEOS}/${videoToDelete.id}`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        throw new Error("Falha ao excluir vídeo");
      }

      // Remover da lista
      setVideos((prev) => prev.filter((v) => v.id !== videoToDelete.id));
      setDeleteDialogOpen(false);
    } catch (err) {
      alert(
        `Erro ao excluir vídeo: ${
          err instanceof Error ? err.message : "Erro desconhecido"
        }`
      );
    } finally {
      setDeleting(false);
      setVideoToDelete(null);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const handleThumbnailError = (videoId: string) => {
    setThumbnailErrors((prev) => new Set(prev).add(videoId));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>Erro ao carregar vídeos: {error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Cloud className="h-6 w-6" />
            Vídeos no Drive
          </h2>
          <div className="flex items-center gap-4">
            <p className="text-sm text-muted-foreground">
              {videos.length} {videos.length === 1 ? "vídeo" : "vídeos"}
            </p>
            <Button variant="outline" size="sm" onClick={fetchVideos}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Atualizar
            </Button>
          </div>
        </div>

        {videos.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <VideoOff className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">
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
              <Card
                key={video.id}
                className="overflow-hidden hover:shadow-lg transition-shadow group"
              >
                <CardContent className="p-0">
                  {/* Thumbnail or Placeholder */}
                  <div
                    className="aspect-video bg-muted flex items-center justify-center relative cursor-pointer overflow-hidden"
                    onClick={() => setSelectedVideo(video)}
                  >
                    {!thumbnailErrors.has(video.id) ? (
                      <img
                        src={`${apiUrl}/api/${APIURLS.DRIVE_THUMBNAIL}/${video.id}`}
                        alt={video.name}
                        className="w-full h-full object-cover"
                        onError={() => handleThumbnailError(video.id)}
                      />
                    ) : (
                      <VideoOff className="h-12 w-12 text-muted-foreground" />
                    )}

                    {/* Play Button Overlay */}
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <div className="bg-primary rounded-full p-4">
                        <Play
                          className="h-8 w-8 text-primary-foreground"
                          fill="currentColor"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Info */}
                  <div className="p-4 space-y-2">
                    <h3 className="font-semibold text-sm line-clamp-2">
                      {video.name}
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      {video.path}
                    </p>
                    <div className="flex items-center justify-between pt-2">
                      <span className="text-xs text-muted-foreground">
                        {formatSize(video.size)}
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteClick(video);
                        }}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir vídeo do Drive?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir &quot;{videoToDelete?.name}&quot;
              do Google Drive? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={deleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Excluindo...
                </>
              ) : (
                "Excluir"
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Video Player Modal */}
      {selectedVideo && (
        <DriveVideoPlayer
          video={selectedVideo}
          onClose={() => setSelectedVideo(null)}
          onDelete={() => handleDeleteClick(selectedVideo)}
        />
      )}
    </>
  );
}
