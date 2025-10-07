"use client";

import { useState } from "react";
import { Trash2, Play, MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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

interface VideoCardProps {
  id: string;
  title: string;
  channel: string;
  thumbnail?: string;
  path: string;
  onPlay: () => void;
  onDelete: () => void;
}

export default function VideoCard({
  title,
  channel,
  thumbnail,
  path,
  onPlay,
  onDelete,
}: VideoCardProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [imageError, setImageError] = useState(false);

  const apiUrl = typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    : "http://localhost:8000";

  const thumbnailUrl = thumbnail
    ? `${apiUrl}/api/videos/thumbnail/${encodeURIComponent(thumbnail)}`
    : null;

  const handleDelete = () => {
    setShowDeleteDialog(false);
    onDelete();
  };

  return (
    <>
      <div className="group relative flex flex-col bg-card rounded-lg overflow-hidden hover:bg-accent/50 transition-colors">
        {/* Thumbnail */}
        <div
          className="relative aspect-video bg-muted cursor-pointer overflow-hidden"
          onClick={onPlay}
        >
          {thumbnailUrl && !imageError ? (
            <img
              src={thumbnailUrl}
              alt={title}
              className="w-full h-full object-cover"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-muted">
              <Play className="h-12 w-12 text-muted-foreground" />
            </div>
          )}

          {/* Play overlay on hover */}
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <div className="bg-white/90 rounded-full p-3">
              <Play className="h-6 w-6 text-black" fill="black" />
            </div>
          </div>
        </div>

        {/* Info */}
        <div className="flex gap-3 p-3">
          <div className="flex-1 min-w-0">
            <h3
              className="font-medium line-clamp-2 text-sm leading-tight mb-1 cursor-pointer hover:text-primary"
              onClick={onPlay}
              title={title}
            >
              {title}
            </h3>
            <p className="text-xs text-muted-foreground truncate" title={channel}>
              {channel}
            </p>
          </div>

          {/* Menu de ações */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setShowDeleteDialog(true)}>
                <Trash2 className="mr-2 h-4 w-4" />
                Excluir
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Dialog de confirmação */}
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
