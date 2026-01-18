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
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Upload,
  X,
  FileVideo,
  Loader2,
  CheckCircle2,
  XCircle,
  Cloud,
  Image,
  Subtitles,
  FileText,
} from "lucide-react";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";
import { formatBytes } from "@/lib/utils";

interface UploadProgress {
  status: string;
  total: number;
  uploaded: number;
  failed: number;
  percent: number;
  current_file: string | null;
  folder_name?: string;
}

interface JobResponse {
  status: string;
  progress: UploadProgress;
  result?: {
    uploaded: number;
    total: number;
    failed: Array<{ file: string; error: string }>;
  };
  error?: string;
}

interface ExternalUploadModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUploadComplete?: () => void;
}

export default function ExternalUploadModal({
  open,
  onOpenChange,
  onUploadComplete,
}: ExternalUploadModalProps) {
  const apiUrl = useApiUrl();
  const [folderName, setFolderName] = useState("");
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [thumbnail, setThumbnail] = useState<File | null>(null);
  const [subtitles, setSubtitles] = useState<File[]>([]);
  const [transcription, setTranscription] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const videoInputRef = useRef<HTMLInputElement>(null);
  const thumbnailInputRef = useRef<HTMLInputElement>(null);
  const subtitlesInputRef = useRef<HTMLInputElement>(null);
  const transcriptionInputRef = useRef<HTMLInputElement>(null);
  const pollingCleanupRef = useRef<(() => void) | null>(null);
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

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingCleanupRef.current) {
        pollingCleanupRef.current();
      }
    };
  }, []);

  // Reset state when modal closes
  useEffect(() => {
    if (!open) {
      // Delay reset to allow modal animation
      setTimeout(() => {
        if (!uploading) {
          setFolderName("");
          setVideoFile(null);
          setThumbnail(null);
          setSubtitles([]);
          setTranscription(null);
          setError(null);
          setSuccess(false);
          setUploadProgress(null);
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
      // Auto-fill folder name from video name if empty
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
    // Reset input to allow selecting same file again
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

  const pollJobProgress = useCallback(
    async (jobId: string, onComplete: (result: JobResponse) => void) => {
      if (!apiUrl) return;

      let cancelled = false;
      let timeoutId: NodeJS.Timeout | null = null;

      const poll = async () => {
        if (cancelled) return;

        try {
          const res = await fetch(`${apiUrl}/api/${APIURLS.JOBS}/${jobId}`);
          if (!res.ok) {
            throw new Error("Falha ao obter progresso do job");
          }

          const job: JobResponse = await res.json();

          // Update progress
          if (job.progress) {
            setUploadProgress(job.progress);
          }

          // Check if finished
          if (["completed", "error", "cancelled"].includes(job.status)) {
            onComplete(job);
            return;
          }

          // Continue polling
          if (!cancelled) {
            timeoutId = setTimeout(poll, 1000);
          }
        } catch (err) {
          if (!cancelled) {
            setError(err instanceof Error ? err.message : "Erro no polling");
            onComplete({ status: "error", progress: uploadProgress! });
          }
        }
      };

      poll();

      return () => {
        cancelled = true;
        if (timeoutId) clearTimeout(timeoutId);
      };
    },
    [apiUrl, uploadProgress]
  );

  const handleUpload = async () => {
    if (!videoFile || !folderName.trim() || !apiUrl) return;

    // Calculate total files
    const totalFiles = 1 + (thumbnail ? 1 : 0) + subtitles.length + (transcription ? 1 : 0);

    try {
      setUploading(true);
      setError(null);
      setSuccess(false);
      setUploadProgress({
        status: "uploading",
        total: totalFiles,
        uploaded: 0,
        failed: 0,
        percent: 0,
        current_file: "Enviando arquivos...",
      });

      // Build FormData
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

      // Send upload request
      const response = await fetch(
        `${apiUrl}/api/${APIURLS.DRIVE_UPLOAD_EXTERNAL}`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Falha ao iniciar upload");
      }

      const data = await response.json();
      const jobId = data.job_id;

      if (!jobId) {
        throw new Error("Job ID não retornado pelo servidor");
      }

      // Start polling
      const cleanup = await pollJobProgress(jobId, async (job) => {
        setUploading(false);
        setUploadProgress(null);

        if (job.status === "completed") {
          await fetch("/api/revalidate/drive-videos", { method: "POST" });
          setSuccess(true);
          setVideoFile(null);
          setThumbnail(null);
          setSubtitles([]);
          setTranscription(null);
          setFolderName("");
          resetFileInputs();
          onUploadComplete?.();
        } else if (job.status === "error") {
          setError(job.error || "Erro durante upload");
        } else if (job.status === "cancelled") {
          setError("Upload cancelado");
        }
      });

      pollingCleanupRef.current = cleanup || null;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao fazer upload");
      setUploading(false);
      setUploadProgress(null);
    }
  };

  const canUpload = videoFile && folderName.trim() && !uploading;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] glass border-white/10">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-white">
            <div className="w-8 h-8 rounded-lg bg-cyan/10 flex items-center justify-center">
              <Cloud className="h-4 w-4 text-cyan" />
            </div>
            Upload para o Google Drive
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Envie qualquer vídeo do seu computador para o Google Drive
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-4">
          {/* Error Alert */}
          {error && (
            <Alert className="bg-red-500/10 border-red-500/20">
              <XCircle className="h-4 w-4 text-red-400" />
              <AlertDescription className="text-red-400">{error}</AlertDescription>
            </Alert>
          )}

          {/* Success Alert */}
          {success && (
            <Alert className="bg-teal/10 border-teal/20">
              <CheckCircle2 className="h-4 w-4 text-teal" />
              <AlertDescription className="text-teal">
                Upload concluído com sucesso!
              </AlertDescription>
            </Alert>
          )}

          {/* Folder Name Input */}
          <div className="space-y-2">
            <Label htmlFor="folder-name" className="text-white">Nome da pasta no Drive *</Label>
            <Input
              id="folder-name"
              placeholder="Ex: Meus Vídeos"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              disabled={uploading}
              className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
            />
            <p className="text-xs text-muted-foreground">
              A pasta será criada automaticamente dentro de &quot;YouTube Archiver&quot;
            </p>
          </div>

          {/* Video File Input */}
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
              <div className="flex items-center gap-2 p-2 rounded-lg bg-cyan/10 border border-cyan/20">
                <FileVideo className="h-4 w-4 text-cyan" />
                <span className="text-sm truncate flex-1 text-white">{videoFile.name}</span>
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

          {/* Arquivos Opcionais */}
          <div className="space-y-4">
            <Label className="text-muted-foreground text-xs uppercase tracking-wider">Arquivos opcionais</Label>

            {/* Thumbnail */}
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
                  <span className="text-sm truncate flex-1 text-white">{thumbnail.name}</span>
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

            {/* Legendas */}
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
                      <span className="text-sm truncate flex-1 text-white">{file.name}</span>
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

            {/* Transcrição */}
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
                  <span className="text-sm truncate flex-1 text-white">{transcription.name}</span>
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

          {/* Upload Progress */}
          {uploadProgress && uploading && (
            <div className="space-y-3 p-4 rounded-xl bg-cyan/10 border border-cyan/20">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-cyan">
                  Enviando para o Drive...
                </span>
                <span className="text-cyan/80">
                  {uploadProgress.uploaded}/{uploadProgress.total} (
                  {Math.round(uploadProgress.percent)}%)
                </span>
              </div>
              <Progress value={uploadProgress.percent} className="h-2" />
              {uploadProgress.current_file && (
                <p className="text-xs text-cyan/70 truncate">
                  {uploadProgress.current_file}
                </p>
              )}
            </div>
          )}

          {/* Actions */}
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
                  Enviar para Drive
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
