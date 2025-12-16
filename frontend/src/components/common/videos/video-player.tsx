"use client";

import { useState, useRef, useCallback } from "react";
import { Trash2, Loader2, AlertCircle, Minimize2 } from "lucide-react";
import type { MediaPlayerInstance } from "@vidstack/react";
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
import { Alert, AlertDescription } from "@/components/ui/alert";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";
import { formatBytes } from "@/lib/utils";
import { useGlobalPlayer } from "@/contexts/global-player-context";

// Vidstack imports
import { MediaPlayer, MediaProvider } from "@vidstack/react";
import {
  DefaultVideoLayout,
  defaultLayoutIcons,
} from "@vidstack/react/player/layouts/default";

// Interface para vídeo local
interface LocalVideo {
  id: string;
  title: string;
  channel: string;
  path: string;
  thumbnail?: string;
  size: number;
  created_at?: string;
  modified_at?: string;
}

// Interface para vídeo do Drive
interface DriveVideo {
  id: string;
  name: string;
  path: string;
  size: number;
  created_at: string;
  modified_at: string;
  thumbnail?: string;
}

// Tipo unificado
type Video = LocalVideo | DriveVideo;

// Type guard para verificar se é vídeo local
function isLocalVideo(video: Video): video is LocalVideo {
  return "title" in video;
}

interface VideoPlayerProps {
  video: Video;
  source?: "local" | "drive";
  onClose: () => void;
  onDelete: () => void;
}

export default function VideoPlayer({
  video,
  source = "local",
  onClose,
  onDelete,
}: VideoPlayerProps) {
  const apiUrl = useApiUrl();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Global player context (volume é sincronizado via props do MediaPlayer)
  const { playVideo, volume, isMuted, setVolume, setMuted } = useGlobalPlayer();
  const playerRef = useRef<MediaPlayerInstance>(null);

  // Determinar título e subtítulo baseado no tipo de vídeo
  const videoTitle = isLocalVideo(video) ? video.title : video.name;
  const videoSubtitle = isLocalVideo(video) ? video.channel : video.path;

  // Handle minimize - transfer to global player
  const handleMinimize = useCallback(() => {
    const currentTime = playerRef.current?.currentTime || 0;
    playVideo(
      {
        id: video.id,
        title: videoTitle,
        subtitle: videoSubtitle,
        path: video.path,
        thumbnail: isLocalVideo(video) ? video.thumbnail : undefined,
        size: video.size,
      },
      source,
      currentTime
    );
    onClose();
  }, [video, videoTitle, videoSubtitle, source, playVideo, onClose]);

  // Construir URL do stream baseado na fonte
  const videoUrl = apiUrl
    ? source === "drive"
      ? `${apiUrl}/api/${APIURLS.DRIVE_STREAM}/${video.id}`
      : `${apiUrl}/api/videos/stream/${encodeURIComponent(video.path)}`
    : "";

  const handleDelete = async () => {
    setDeleting(true);
    setError(null);
    try {
      await onDelete();
      setDeleteDialogOpen(false);
      onClose();
    } catch (err) {
      console.error("Error deleting video:", err);
      setError("Erro ao excluir vídeo. Tente novamente.");
      setDeleteDialogOpen(false);
    } finally {
      setDeleting(false);
    }
  };

  const deleteDialogDescription =
    source === "drive"
      ? `Tem certeza que deseja excluir "${videoTitle}" do Google Drive? Esta ação não pode ser desfeita.`
      : `Esta ação não pode ser desfeita. O vídeo "${videoTitle}" será permanentemente excluído do seu dispositivo.`;

  return (
    <>
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="max-w-5xl w-[95vw] p-0 gap-0 overflow-hidden rounded-lg">
          <div className="flex flex-col bg-background">
            <div className="p-6 pb-4">
              <DialogHeader className="pr-8">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <DialogTitle className="text-xl">{videoTitle}</DialogTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                      {videoSubtitle}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    {/* Minimize button */}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={handleMinimize}
                      className="text-muted-foreground hover:text-foreground -mt-1"
                      title="Minimizar (PiP)"
                    >
                      <Minimize2 className="h-4 w-4" />
                    </Button>
                    {/* Delete button */}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setDeleteDialogOpen(true)}
                      className="text-destructive hover:text-destructive -mt-1"
                      title="Excluir"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </DialogHeader>

              {error && (
                <Alert variant="destructive" className="mt-4">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </div>

            <div className="mx-6 rounded-lg overflow-hidden">
              {videoUrl && (
                <MediaPlayer
                  ref={playerRef}
                  title={videoTitle}
                  src={{ src: videoUrl, type: "video/mp4" }}
                  aspectRatio="16/9"
                  crossOrigin
                  playsInline
                  className="w-full"
                  volume={volume}
                  muted={isMuted}
                  onVolumeChange={(detail) => {
                    setVolume(detail.volume);
                    setMuted(detail.muted);
                  }}
                >
                  <MediaProvider />
                  <DefaultVideoLayout
                    icons={defaultLayoutIcons}
                    // Configurações de velocidade de reprodução
                    playbackRates={[0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]}
                    // Pular 10 segundos
                    seekStep={10}
                    // Tema escuro automático
                    colorScheme="dark"
                    // Remover botão PiP (usamos o minimizar)
                    slots={{ pipButton: null }}
                  />
                </MediaPlayer>
              )}
            </div>

            <div className="flex justify-between text-sm text-muted-foreground px-6 py-4">
              <span>
                Tamanho:{" "}
                <span className="text-foreground font-medium">
                  {formatBytes(video.size)}
                </span>
              </span>
              <span>
                {source === "drive" ? "Criado em:" : "Adicionado em:"}{" "}
                <span className="text-foreground font-medium">
                  {video.created_at
                    ? new Date(video.created_at).toLocaleDateString("pt-BR")
                    : "-"}
                </span>
              </span>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {source === "drive" ? "Excluir vídeo do Drive?" : "Excluir vídeo?"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {deleteDialogDescription}
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
