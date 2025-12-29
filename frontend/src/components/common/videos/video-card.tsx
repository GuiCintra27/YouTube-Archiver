"use client";

import { useState, useCallback, useRef } from "react";
import { Trash2, Play, MoreVertical, Info, Clock, HardDrive, Calendar, FileVideo, Pencil, Loader2, ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  DialogFooter,
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
  deleteScope?: "local" | "drive";
  // Optional selection props
  selectable?: boolean;
  selected?: boolean;
  onSelectionChange?: (selected: boolean) => void;
  // Optional edit props
  editable?: boolean;
  onEdit?: (newTitle: string, newThumbnail?: File) => Promise<void>;
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
  deleteScope = "local",
  selectable = false,
  selected = false,
  onSelectionChange,
  editable = false,
  onEdit,
}: VideoCardProps) {
  const apiUrl = useApiUrl();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showInfoDialog, setShowInfoDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [imageError, setImageError] = useState(false);

  // Edit form state
  const [editTitle, setEditTitle] = useState(title);
  const [editThumbnail, setEditThumbnail] = useState<File | null>(null);
  const [thumbnailPreview, setThumbnailPreview] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleOpenEditDialog = useCallback(() => {
    setEditTitle(title);
    setEditThumbnail(null);
    setThumbnailPreview(null);
    setShowEditDialog(true);
  }, [title]);

  const handleThumbnailChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setEditThumbnail(file);
      // Create preview URL
      const previewUrl = URL.createObjectURL(file);
      setThumbnailPreview(previewUrl);
    }
  }, []);

  const handleSaveEdit = useCallback(async () => {
    if (!onEdit) return;

    try {
      setIsSaving(true);
      await onEdit(editTitle, editThumbnail || undefined);
      setShowEditDialog(false);
    } catch (error) {
      console.error("Error saving edit:", error);
    } finally {
      setIsSaving(false);
    }
  }, [onEdit, editTitle, editThumbnail]);

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
        className={`group relative flex flex-col cursor-pointer glass-card rounded-xl overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:border-white/20 ${
          selected
            ? "ring-2 ring-teal/50 border-teal/30"
            : ""
        }`}
        onClick={handleCardClick}
      >
        {/* Checkbox for selection mode */}
        {selectable && (
          <div
            className={`flex absolute top-3 left-3 z-10 transition-opacity duration-200 ${
              selected ? "opacity-100" : "opacity-0 group-hover:opacity-100"
            }`}
            data-no-play
            onClick={(e) => e.stopPropagation()}
          >
            <Checkbox
              checked={selected}
              onCheckedChange={(checked) => onSelectionChange?.(!!checked)}
              className="h-5 w-5 bg-black/50 backdrop-blur-sm border-2 border-white/50 data-[state=checked]:bg-teal data-[state=checked]:text-navy-dark data-[state=checked]:border-teal"
            />
          </div>
        )}

        {/* Thumbnail Container */}
        <div className="relative aspect-video bg-navy overflow-hidden">
          {thumbnailUrl && !imageError ? (
            <img
              src={thumbnailUrl}
              alt={title}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-navy-light">
              <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center">
                <Play className="h-8 w-8 text-muted-foreground" />
              </div>
            </div>
          )}

          {/* Duration badge */}
          {duration && (
            <div className="absolute bottom-2 right-2 bg-black/80 backdrop-blur-sm text-white text-xs font-medium px-2 py-1 rounded-md">
              {duration}
            </div>
          )}

          {/* Hover overlay with play button */}
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all duration-300 flex items-center justify-center opacity-0 group-hover:opacity-100">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-teal to-cyan flex items-center justify-center transform scale-75 group-hover:scale-100 transition-transform duration-300">
              <Play className="h-6 w-6 text-navy-dark ml-1" />
            </div>
          </div>
        </div>

        {/* Info */}
        <div className="flex gap-3 p-4">
          <div className="flex-1 min-w-0">
            <h3
              className="font-medium line-clamp-2 text-sm leading-snug mb-1 text-white"
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
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 -mt-1 text-muted-foreground hover:text-white hover:bg-white/10"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="glass border-white/10">
                {editable && (
                  <DropdownMenuItem
                    onClick={handleOpenEditDialog}
                    className="cursor-pointer text-white focus:bg-white/10 focus:text-white"
                  >
                    <Pencil className="mr-2 h-4 w-4 text-purple" />
                    Editar
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem
                  onClick={() => setShowInfoDialog(true)}
                  className="cursor-pointer text-white focus:bg-white/10 focus:text-white"
                >
                  <Info className="mr-2 h-4 w-4 text-teal" />
                  Informacoes
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-white/10" />
                <DropdownMenuItem
                  onClick={() => setShowDeleteDialog(true)}
                  className="cursor-pointer text-red-400 focus:bg-red-500/10 focus:text-red-400"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Excluir
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Dialog de informações */}
      <Dialog open={showInfoDialog} onOpenChange={setShowInfoDialog}>
        <DialogContent className="sm:max-w-md glass border-white/10">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-white">
              <FileVideo className="h-5 w-5 text-teal" />
              Informacoes do Video
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 pt-2">
            {/* Título completo */}
            <div className="space-y-1.5">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Titulo
              </p>
              <p className="text-sm font-medium leading-relaxed break-words text-white">
                {title}
              </p>
            </div>

            {/* Grid de informações */}
            <div className="grid grid-cols-2 gap-4">
              {/* Duração */}
              {duration && (
                <div className="flex items-start gap-3 p-3 rounded-lg bg-white/5">
                  <Clock className="h-4 w-4 text-teal mt-0.5" />
                  <div>
                    <p className="text-xs text-muted-foreground">Duracao</p>
                    <p className="text-sm font-medium text-white">{duration}</p>
                  </div>
                </div>
              )}

              {/* Tamanho */}
              {size !== undefined && (
                <div className="flex items-start gap-3 p-3 rounded-lg bg-white/5">
                  <HardDrive className="h-4 w-4 text-purple mt-0.5" />
                  <div>
                    <p className="text-xs text-muted-foreground">Tamanho</p>
                    <p className="text-sm font-medium text-white">{formatBytes(size)}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Data de download */}
            {createdAt && formatDate(createdAt) && (
              <div className="flex items-start gap-3 p-3 rounded-lg bg-white/5">
                <Calendar className="h-4 w-4 text-yellow mt-0.5" />
                <div>
                  <p className="text-xs text-muted-foreground">Data de download</p>
                  <p className="text-sm font-medium text-white">{formatDate(createdAt)}</p>
                </div>
              </div>
            )}

            {/* Canal */}
            <div className="space-y-1.5 pt-2 border-t border-white/10">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Canal
              </p>
              <p className="text-sm text-white">{channel}</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog de confirmação de exclusão */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="glass border-white/10">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white">Excluir vídeo?</AlertDialogTitle>
            <AlertDialogDescription className="text-muted-foreground">
              {deleteScope === "drive"
                ? `Esta ação não poderá ser desfeita. O vídeo "${title}" será permanentemente excluído do Google Drive.`
                : `Esta ação não poderá ser desfeita. O vídeo "${title}" será permanentemente excluído do seu dispositivo.`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-white/5 border-white/10 text-white hover:bg-white/10 hover:text-white">
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30"
            >
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Dialog de edição */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-md glass border-white/10">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-white">
              <Pencil className="h-5 w-5 text-purple" />
              Editar Video
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6 pt-2">
            {/* Nome do vídeo */}
            <div className="space-y-2">
              <Label htmlFor="video-title" className="text-white">Nome do video</Label>
              <Input
                id="video-title"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                placeholder="Digite o novo nome"
                className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
              />
            </div>

            {/* Upload de thumbnail */}
            <div className="space-y-2">
              <Label className="text-white">Thumbnail</Label>
              <div
                className="relative border-2 border-dashed border-white/10 rounded-lg p-4 hover:border-teal/50 transition-colors cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={handleThumbnailChange}
                />

                {thumbnailPreview ? (
                  <div className="relative aspect-video rounded-lg overflow-hidden">
                    <img
                      src={thumbnailPreview}
                      alt="Preview"
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                      <p className="text-white text-sm font-medium">Clique para alterar</p>
                    </div>
                  </div>
                ) : thumbnailUrl ? (
                  <div className="relative aspect-video rounded-lg overflow-hidden">
                    <img
                      src={thumbnailUrl}
                      alt="Thumbnail atual"
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity">
                      <p className="text-white text-sm font-medium">Clique para alterar</p>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-6 text-muted-foreground">
                    <ImageIcon className="h-10 w-10 mb-2" />
                    <p className="text-sm font-medium">Clique para selecionar uma imagem</p>
                    <p className="text-xs">JPG, PNG ou WebP</p>
                  </div>
                )}
              </div>
              {editThumbnail && (
                <p className="text-xs text-muted-foreground">
                  Arquivo selecionado: {editThumbnail.name}
                </p>
              )}
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setShowEditDialog(false)}
              disabled={isSaving}
              className="bg-white/5 border-white/10 text-white hover:bg-white/10 hover:text-white"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleSaveEdit}
              disabled={isSaving || !editTitle.trim()}
              className="btn-gradient-teal"
            >
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Salvando...
                </>
              ) : (
                "Salvar"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
