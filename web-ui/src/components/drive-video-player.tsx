"use client";

import { useEffect, useRef, useState } from "react";
import { X, Trash2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import dynamic from "next/dynamic";

// Importar Plyr dinamicamente para evitar SSR
const Plyr = dynamic(() => import("plyr-react"), {
  ssr: false,
  loading: () => (
    <div className="w-full aspect-video bg-black flex items-center justify-center">
      <Loader2 className="h-12 w-12 animate-spin text-white" />
    </div>
  ),
});

interface DriveVideo {
  id: string;
  name: string;
  path: string;
  size: number;
  created_at: string;
  modified_at: string;
  thumbnail?: string;
}

interface DriveVideoPlayerProps {
  video: DriveVideo;
  onClose: () => void;
  onDelete: () => void;
}

export default function DriveVideoPlayer({
  video,
  onClose,
  onDelete,
}: DriveVideoPlayerProps) {
  const plyrRef = useRef<any>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const apiUrl =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      : "http://localhost:8000";

  const videoUrl = `${apiUrl}/api/drive/stream/${video.id}`;

  // Configuração do Plyr
  const plyrOptions = {
    controls: [
      'play-large',
      'play',
      'progress',
      'current-time',
      'duration',
      'mute',
      'volume',
      'captions',
      'settings',
      'pip',
      'airplay',
      'fullscreen',
    ],
    settings: ['captions', 'speed'],
    speed: { selected: 1, options: [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2] },
    autoplay: false,
    hideControls: true,
    resetOnEnd: false,
    keyboard: { focused: true, global: true },
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await onDelete();
      setDeleteDialogOpen(false);
      onClose();
    } catch (error) {
      console.error("Error deleting video:", error);
      alert("Erro ao excluir vídeo");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="max-w-5xl max-h-[90vh] p-0">
          <DialogHeader className="p-6 pb-0">
            <div className="flex items-start justify-between">
              <div className="flex-1 pr-8">
                <DialogTitle className="text-xl">{video.name}</DialogTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {video.path}
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setDeleteDialogOpen(true)}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" onClick={onClose}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </DialogHeader>

          <div className="p-6 pt-4">
            <div className="bg-black rounded-lg overflow-hidden w-full" style={{ aspectRatio: '16/9' }}>
              <Plyr
                ref={plyrRef}
                source={{
                  type: 'video',
                  sources: [
                    {
                      src: videoUrl,
                      type: 'video/mp4',
                    },
                  ],
                }}
                options={plyrOptions}
              />
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Tamanho:</span>{" "}
                <span className="font-medium">
                  {(video.size / (1024 * 1024)).toFixed(2)} MB
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Criado em:</span>{" "}
                <span className="font-medium">
                  {new Date(video.created_at).toLocaleDateString("pt-BR")}
                </span>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir vídeo do Drive?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir &quot;{video.name}&quot; do Google Drive?
              Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
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
    </>
  );
}
