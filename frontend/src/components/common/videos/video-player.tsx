"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { X, Trash2, Download, Maximize2 } from "lucide-react";
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
import { useApiUrl } from "@/hooks/use-api-url";
import { formatBytes } from "@/lib/utils";

interface Video {
  id: string;
  title: string;
  channel: string;
  path: string;
  thumbnail?: string;
  size: number;
}

interface VideoPlayerProps {
  video: Video;
  onClose: () => void;
  onDelete: () => void;
}

export default function VideoPlayer({ video, onClose, onDelete }: VideoPlayerProps) {
  const apiUrl = useApiUrl();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  const videoUrl = apiUrl
    ? `${apiUrl}/api/videos/stream/${encodeURIComponent(video.path)}`
    : "";

  // Fechar com ESC
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [onClose]);

  const handleDelete = useCallback(() => {
    setShowDeleteDialog(false);
    onDelete();
  }, [onDelete]);

  const handleFullscreen = useCallback(() => {
    if (videoRef.current?.requestFullscreen) {
      videoRef.current.requestFullscreen();
    }
  }, []);

  const handleDownload = useCallback(() => {
    if (videoUrl) {
      window.open(videoUrl, "_blank");
    }
  }, [videoUrl]);

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-50 bg-black/90 animate-in fade-in"
        onClick={onClose}
      >
        {/* Container */}
        <div
          className="absolute inset-0 flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 bg-black/50 backdrop-blur-sm">
            <div className="flex-1 min-w-0 mr-4">
              <h2 className="text-xl font-semibold text-white truncate">
                {video.title}
              </h2>
              <p className="text-sm text-gray-300 truncate">{video.channel}</p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleFullscreen}
                className="text-white hover:bg-white/10"
                title="Tela cheia"
              >
                <Maximize2 className="h-5 w-5" />
              </Button>

              <Button
                variant="ghost"
                size="icon"
                onClick={handleDownload}
                className="text-white hover:bg-white/10"
                title="Baixar"
              >
                <Download className="h-5 w-5" />
              </Button>

              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowDeleteDialog(true)}
                className="text-red-400 hover:bg-red-500/10"
                title="Excluir"
              >
                <Trash2 className="h-5 w-5" />
              </Button>

              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="text-white hover:bg-white/10"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
          </div>

          {/* Video Player */}
          <div className="flex-1 flex items-center justify-center p-6">
            <video
              ref={videoRef}
              src={videoUrl}
              controls
              autoPlay
              className="max-w-full max-h-full rounded-lg shadow-2xl"
              controlsList="nodownload"
            >
              Seu navegador não suporta o elemento de vídeo.
            </video>
          </div>

          {/* Footer - Info */}
          <div className="px-6 py-3 bg-black/50 backdrop-blur-sm text-sm text-gray-300">
            <span>Tamanho: {formatBytes(video.size)}</span>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir vídeo?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. O vídeo &quot;{video.title}&quot; será
              permanentemente excluído do seu dispositivo.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
