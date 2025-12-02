"use client";

import { useState, useCallback } from "react";
import { Trash2, Play, MoreVertical, Info, Clock, HardDrive, Calendar, FileVideo } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useApiUrl } from "@/hooks/use-api-url";
import { formatBytes } from "@/lib/utils";

interface VideoCardProps {
  id: string;
  title: string;
  channel: string;
  thumbnail?: string;
  thumbnailUrl?: string; // Direct URL for thumbnail (used by Drive)
  path: string;
  duration?: string;
  size?: number;
  createdAt?: string;
  onPlay: () => void;
  onDelete: () => void;
  // Optional selection props
  selectable?: boolean;
  selected?: boolean;
  onSelectionChange?: (selected: boolean) => void;
}

export default function VideoCard({
  title,
  channel,
  thumbnail,
  thumbnailUrl: externalThumbnailUrl,
  path: _path,
  duration,
  size,
  createdAt,
  onPlay,
  onDelete,
  selectable = false,
  selected = false,
  onSelectionChange,
}: VideoCardProps) {
  const apiUrl = useApiUrl();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showInfoDialog, setShowInfoDialog] = useState(false);
  const [imageError, setImageError] = useState(false);

  // Use external URL if provided, otherwise construct from thumbnail path
  const thumbnailUrl = externalThumbnailUrl
    ? externalThumbnailUrl
    : thumbnail && apiUrl
      ? `${apiUrl}/api/videos/thumbnail/${encodeURIComponent(thumbnail)}`
      : null;

  const handleDelete = useCallback(() => {
    setShowDeleteDialog(false);
    onDelete();
  }, [onDelete]);

  const handleCardClick = useCallback(
    (e: React.MouseEvent) => {
      // Don't trigger play if clicking on checkbox area or menu
      const target = e.target as HTMLElement;
      if (target.closest("[data-no-play]")) return;
      onPlay();
    },
    [onPlay]
  );

  const formatDate = (dateString?: string) => {
    if (!dateString) return null;
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return null;
    }
  };

  return (
    <>
      <div
        className={`group relative flex flex-col cursor-pointer hover:bg-gray-200/35 dark:hover:bg-white/10 rounded-xl ${
          selected
            ? "ring-2 transition-all duration-300 ring-gray-200/70 dark:ring-white/70 rounded-xl"
            : ""
        }`}
        onClick={handleCardClick}
      >
        {/* Checkbox for selection mode */}
        {selectable && (
          <div
            className={`flex absolute top-9 left-7 z-10 transition-opacity duration-200 ${
              selected ? "opacity-100" : "opacity-0 group-hover:opacity-100"
            }`}
            data-no-play
            onClick={(e) => e.stopPropagation()}
          >
            <Checkbox
              checked={selected}
              onCheckedChange={(checked) => onSelectionChange?.(!!checked)}
              className="h-5 w-5 bg-background/30 backdrop-blur-[2px] border-2 border-gray-300 dark:border-gray-200 data-[state=checked]:bg-gray-500/50 data-[state=checked]:text-white"
            />
          </div>
        )}

        <div className="p-4 py-6">
          {/* Thumbnail Container */}
          <div className="relative aspect-video bg-muted overflow-hidden rounded-xl">
            {thumbnailUrl && !imageError ? (
              <img
                src={thumbnailUrl}
                alt={title}
                className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-muted">
                <Play className="h-16 w-16 text-muted-foreground/50" />
              </div>
            )}

            {/* Duration badge */}
            {duration && (
              <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs font-medium px-1.5 py-0.5 rounded">
                {duration}
              </div>
            )}

            {/* Hover overlay */}
            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
          </div>

          {/* Info */}
          <div className="flex gap-3 pt-3 px-1">
            <div className="flex-1 min-w-0">
              <h3
                className="font-medium line-clamp-2 text-sm leading-snug mb-1"
                title={title}
              >
                {title}
              </h3>
              <p
                className="text-xs text-muted-foreground truncate"
                title={channel}
              >
                {channel}
              </p>
            </div>

            {/* Menu de ações */}
            <div data-no-play onClick={(e) => e.stopPropagation()}>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8 -mt-1">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    onClick={() => setShowInfoDialog(true)}
                    className="cursor-pointer"
                  >
                    <Info className="mr-2 h-4 w-4" />
                    Informações
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => setShowDeleteDialog(true)}
                    className="cursor-pointer text-destructive focus:text-destructive"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Excluir
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </div>

      {/* Dialog de informações */}
      <Dialog open={showInfoDialog} onOpenChange={setShowInfoDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileVideo className="h-5 w-5 text-primary" />
              Informações do Vídeo
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 pt-2">
            {/* Título completo */}
            <div className="space-y-1.5">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Título
              </p>
              <p className="text-sm font-medium leading-relaxed break-words">
                {title}
              </p>
            </div>

            {/* Grid de informações */}
            <div className="grid grid-cols-2 gap-4">
              {/* Duração */}
              {duration && (
                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                  <Clock className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-xs text-muted-foreground">Duração</p>
                    <p className="text-sm font-medium">{duration}</p>
                  </div>
                </div>
              )}

              {/* Tamanho */}
              {size !== undefined && (
                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                  <HardDrive className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-xs text-muted-foreground">Tamanho</p>
                    <p className="text-sm font-medium">{formatBytes(size)}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Data de download */}
            {createdAt && formatDate(createdAt) && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                <Calendar className="h-4 w-4 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-xs text-muted-foreground">Data de download</p>
                  <p className="text-sm font-medium">{formatDate(createdAt)}</p>
                </div>
              </div>
            )}

            {/* Canal */}
            <div className="space-y-1.5 pt-2 border-t">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Canal
              </p>
              <p className="text-sm">{channel}</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog de confirmação de exclusão */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir vídeo?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. O vídeo &quot;{title}&quot; será
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
