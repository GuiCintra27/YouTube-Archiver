"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Upload,
  X,
  FileVideo,
  Loader2,
  CheckCircle2,
  XCircle,
  Image,
  Subtitles,
  FileText,
  FolderPlus,
} from "lucide-react";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";
import { formatBytes } from "@/lib/utils";

interface ExternalLibraryUploadModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUploadComplete?: () => void;
}

export default function ExternalLibraryUploadModal({
  open,
  onOpenChange,
  onUploadComplete,
}: ExternalLibraryUploadModalProps) {
  const apiUrl = useApiUrl();
  const [folderName, setFolderName] = useState("");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [thumbnail, setThumbnail] = useState<File | null>(null);
  const [subtitles, setSubtitles] = useState<File[]>([]);
  const [transcription, setTranscription] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const videoInputRef = useRef<HTMLInputElement>(null);
  const thumbnailInputRef = useRef<HTMLInputElement>(null);
  const subtitlesInputRef = useRef<HTMLInputElement>(null);
  const transcriptionInputRef = useRef<HTMLInputElement>(null);

  const resetFileInputs = useCallback(() => {
    if (videoInputRef.current) {
      videoInputRef.current.value = "";
    }
    if (thumbnailInputRef.current) {
      thumbnailInputRef.current.value = "";
    }
    if (subtitlesInputRef.current) {
      subtitlesInputRef.current.value = "";
    }
    if (transcriptionInputRef.current) {
      transcriptionInputRef.current.value = "";
    }
  }, []);

  useEffect(() => {
    if (!open) {
      setTimeout(() => {
        if (!uploading) {
          setFolderName("");
          setVideoFile(null);
          setThumbnail(null);
          setSubtitles([]);
          setTranscription(null);
          setError(null);
          setSuccess(false);
          resetFileInputs();
        }
      }, 300);
    }
  }, [open, uploading, resetFileInputs]);

  const handleVideoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSuccess(false);
      setError(null);
      setVideoFile(file);
      if (!folderName) {
        const nameWithoutExt = file.name.replace(/\.[^.]+$/, "");
        setFolderName(nameWithoutExt);
      }
    }
    if (videoInputRef.current) {
      videoInputRef.current.value = "";
    }
  };

  const handleThumbnailSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSuccess(false);
      setError(null);
      setThumbnail(file);
    }
    if (thumbnailInputRef.current) {
      thumbnailInputRef.current.value = "";
    }
  };

  const handleSubtitlesSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setSuccess(false);
      setError(null);
      setSubtitles((prev) => [...prev, ...files]);
    }
    if (subtitlesInputRef.current) {
      subtitlesInputRef.current.value = "";
    }
  };

  const removeSubtitle = (index: number) => {
    setSubtitles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleTranscriptionSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSuccess(false);
      setError(null);
      setTranscription(file);
    }
    if (transcriptionInputRef.current) {
      transcriptionInputRef.current.value = "";
    }
  };

  const handleUpload = async () => {
    if (!videoFile || !folderName.trim() || !apiUrl) return;

    try {
      setUploading(true);
      setError(null);
      setSuccess(false);

      const formData = new FormData();
      formData.append("folder_name", folderName.trim());
      formData.append("video", videoFile);

      if (thumbnail) {
        formData.append("thumbnail", thumbnail);
      }

      subtitles.forEach((file) => {
        formData.append("subtitles", file);
      });

      if (transcription) {
        formData.append("transcription", transcription);
      }

      const response = await fetch(
        `${apiUrl}/api/${APIURLS.VIDEOS_UPLOAD_EXTERNAL}`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Falha ao enviar arquivo");
      }

      await response.json();
      await fetch("/api/revalidate/local-videos", { method: "POST" });

      setSuccess(true);
      setVideoFile(null);
      setThumbnail(null);
      setSubtitles([]);
      setTranscription(null);
      setFolderName("");
      resetFileInputs();
      onUploadComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao fazer upload");
    } finally {
      setUploading(false);
    }
  };

  const canUpload = videoFile && folderName.trim() && !uploading;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] glass border-white/10">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-white">
            <div className="w-8 h-8 rounded-lg bg-teal/10 flex items-center justify-center">
              <FolderPlus className="h-4 w-4 text-teal" />
            </div>
            Upload para a Biblioteca
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Envie um vídeo do seu computador para a biblioteca local
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-4">
          {error && (
            <Alert className="bg-red-500/10 border-red-500/20">
              <XCircle className="h-4 w-4 text-red-400" />
              <AlertDescription className="text-red-400">{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert className="bg-teal/10 border-teal/20">
              <CheckCircle2 className="h-4 w-4 text-teal" />
              <AlertDescription className="text-teal">
                Upload concluído com sucesso!
              </AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="folder-name" className="text-white">
              Pasta na biblioteca *
            </Label>
            <Input
              id="folder-name"
              placeholder="Ex: Cursos / React"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              disabled={uploading}
              className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
            />
            <p className="text-xs text-muted-foreground">
              O vídeo será salvo dentro de downloads/&lt;sua pasta&gt;
            </p>
          </div>

          <div className="space-y-2">
            <Label className="text-white">Vídeo principal *</Label>
            <input
              ref={videoInputRef}
              type="file"
              accept="video/*"
              onChange={handleVideoSelect}
              className="hidden"
              disabled={uploading}
            />
            <Button
              variant="outline"
              className="w-full justify-start bg-white/5 border-white/10 text-muted-foreground hover:text-white hover:bg-white/10"
              onClick={() => videoInputRef.current?.click()}
              disabled={uploading}
            >
              <FileVideo className="h-4 w-4 mr-2" />
              {videoFile ? "Alterar vídeo..." : "Selecionar vídeo..."}
            </Button>
            {videoFile && (
              <div className="flex items-center gap-2 p-2 rounded-lg bg-teal/10 border border-teal/20">
                <FileVideo className="h-4 w-4 text-teal" />
                <span className="text-sm truncate flex-1 text-white">
                  {videoFile.name}
                </span>
                <span className="text-xs text-muted-foreground">
                  {formatBytes(videoFile.size)}
                </span>
                {!uploading && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 text-muted-foreground hover:text-white"
                    onClick={() => {
                      setVideoFile(null);
                      resetFileInputs();
                    }}
                    aria-label="Remover vídeo selecionado"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                )}
              </div>
            )}
          </div>

          <div className="space-y-4">
            <Label className="text-muted-foreground text-xs uppercase tracking-wider">
              Arquivos opcionais
            </Label>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Image className="h-4 w-4 text-teal" />
                <span className="text-sm text-white">Thumbnail</span>
              </div>
              <input
                ref={thumbnailInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
                onChange={handleThumbnailSelect}
                className="hidden"
                disabled={uploading}
              />
              {thumbnail ? (
                <div className="flex items-center gap-2 p-2 rounded-lg bg-teal/10 border border-teal/20">
                  <Image className="h-4 w-4 text-teal" />
                  <span className="text-sm truncate flex-1 text-white">
                    {thumbnail.name}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatBytes(thumbnail.size)}
                  </span>
                  {!uploading && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 text-muted-foreground hover:text-white"
                      onClick={() => {
                        setThumbnail(null);
                        resetFileInputs();
                      }}
                      aria-label="Remover thumbnail selecionada"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full justify-start bg-white/5 border-white/10 text-muted-foreground hover:text-white hover:bg-white/10"
                  onClick={() => thumbnailInputRef.current?.click()}
                  disabled={uploading}
                >
                  <Image className="h-4 w-4 mr-2" />
                  Selecionar imagem...
                </Button>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Subtitles className="h-4 w-4 text-yellow" />
                <span className="text-sm text-white">Legendas</span>
                <span className="text-xs text-muted-foreground">(múltiplas)</span>
              </div>
              <input
                ref={subtitlesInputRef}
                type="file"
                accept=".srt,.vtt"
                multiple
                onChange={handleSubtitlesSelect}
                className="hidden"
                disabled={uploading}
              />
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start bg-white/5 border-white/10 text-muted-foreground hover:text-white hover:bg-white/10"
                onClick={() => subtitlesInputRef.current?.click()}
                disabled={uploading}
              >
                <Subtitles className="h-4 w-4 mr-2" />
                Adicionar legendas...
              </Button>
              {subtitles.length > 0 && (
                <div className="space-y-1 max-h-24 overflow-y-auto">
                  {subtitles.map((file, index) => (
                    <div
                      key={`${file.name}-${index}`}
                      className="flex items-center gap-2 p-2 rounded-lg bg-yellow/10 border border-yellow/20"
                    >
                      <Subtitles className="h-4 w-4 text-yellow" />
                      <span className="text-sm truncate flex-1 text-white">
                        {file.name}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatBytes(file.size)}
                      </span>
                      {!uploading && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 text-muted-foreground hover:text-white"
                          onClick={() => removeSubtitle(index)}
                          aria-label={`Remover legenda ${file.name}`}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-purple" />
                <span className="text-sm text-white">Transcrição</span>
              </div>
              <input
                ref={transcriptionInputRef}
                type="file"
                accept=".txt"
                onChange={handleTranscriptionSelect}
                className="hidden"
                disabled={uploading}
              />
              {transcription ? (
                <div className="flex items-center gap-2 p-2 rounded-lg bg-purple/10 border border-purple/20">
                  <FileText className="h-4 w-4 text-purple" />
                  <span className="text-sm truncate flex-1 text-white">
                    {transcription.name}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatBytes(transcription.size)}
                  </span>
                  {!uploading && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 text-muted-foreground hover:text-white"
                      onClick={() => {
                        setTranscription(null);
                        resetFileInputs();
                      }}
                      aria-label="Remover transcrição selecionada"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full justify-start bg-white/5 border-white/10 text-muted-foreground hover:text-white hover:bg-white/10"
                  onClick={() => transcriptionInputRef.current?.click()}
                  disabled={uploading}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Selecionar arquivo...
                </Button>
              )}
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="ghost"
              onClick={() => onOpenChange(false)}
              disabled={uploading}
              className="text-muted-foreground hover:text-white hover:bg-white/10"
            >
              Cancelar
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!canUpload}
              className="btn-gradient-cyan"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Enviando...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Enviar para Biblioteca
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
