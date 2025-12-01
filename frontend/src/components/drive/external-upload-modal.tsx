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
  File,
  Loader2,
  CheckCircle2,
  XCircle,
  Cloud,
  Trash2,
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
  const [extraFiles, setExtraFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const videoInputRef = useRef<HTMLInputElement>(null);
  const extraInputRef = useRef<HTMLInputElement>(null);
  const pollingCleanupRef = useRef<(() => void) | null>(null);

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
          setExtraFiles([]);
          setError(null);
          setSuccess(false);
          setUploadProgress(null);
        }
      }, 300);
    }
  }, [open, uploading]);

  const handleVideoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setVideoFile(file);
      // Auto-fill folder name from video name if empty
      if (!folderName) {
        const nameWithoutExt = file.name.replace(/\.[^.]+$/, "");
        setFolderName(nameWithoutExt);
      }
    }
  };

  const handleExtraFilesSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setExtraFiles((prev) => [...prev, ...files]);
    }
    // Reset input to allow selecting same file again
    if (extraInputRef.current) {
      extraInputRef.current.value = "";
    }
  };

  const removeExtraFile = (index: number) => {
    setExtraFiles((prev) => prev.filter((_, i) => i !== index));
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

    try {
      setUploading(true);
      setError(null);
      setSuccess(false);
      setUploadProgress({
        status: "uploading",
        total: 1 + extraFiles.length,
        uploaded: 0,
        failed: 0,
        percent: 0,
        current_file: "Enviando arquivos...",
      });

      // Build FormData
      const formData = new FormData();
      formData.append("folder_name", folderName.trim());
      formData.append("video", videoFile);

      extraFiles.forEach((file) => {
        formData.append("extra_files", file);
      });

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
          setSuccess(true);
          setVideoFile(null);
          setExtraFiles([]);
          setFolderName("");
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
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Cloud className="h-5 w-5" />
            Upload para o Google Drive
          </DialogTitle>
          <DialogDescription>
            Envie qualquer vídeo do seu computador para o Google Drive
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Error Alert */}
          {error && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Success Alert */}
          {success && (
            <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-700 dark:text-green-300">
                Upload concluído com sucesso!
              </AlertDescription>
            </Alert>
          )}

          {/* Folder Name Input */}
          <div className="space-y-2">
            <Label htmlFor="folder-name">Nome da pasta no Drive *</Label>
            <Input
              id="folder-name"
              placeholder="Ex: Meus Vídeos"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              disabled={uploading}
            />
            <p className="text-xs text-muted-foreground">
              A pasta será criada automaticamente dentro de &quot;YouTube Archiver&quot;
            </p>
          </div>

          {/* Video File Input */}
          <div className="space-y-2">
            <Label>Vídeo principal *</Label>
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
              className="w-full justify-start"
              onClick={() => videoInputRef.current?.click()}
              disabled={uploading}
            >
              <FileVideo className="h-4 w-4 mr-2" />
              {videoFile ? "Alterar vídeo..." : "Selecionar vídeo..."}
            </Button>
            {videoFile && (
              <div className="flex items-center gap-2 p-2 rounded bg-muted">
                <FileVideo className="h-4 w-4 text-primary" />
                <span className="text-sm truncate flex-1">{videoFile.name}</span>
                <span className="text-xs text-muted-foreground">
                  {formatBytes(videoFile.size)}
                </span>
                {!uploading && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0"
                    onClick={() => setVideoFile(null)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                )}
              </div>
            )}
          </div>

          {/* Extra Files Input */}
          <div className="space-y-2">
            <Label>Arquivos extras (opcional)</Label>
            <input
              ref={extraInputRef}
              type="file"
              multiple
              onChange={handleExtraFilesSelect}
              className="hidden"
              disabled={uploading}
            />
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => extraInputRef.current?.click()}
              disabled={uploading}
            >
              <File className="h-4 w-4 mr-2" />
              Adicionar arquivos...
            </Button>
            <p className="text-xs text-muted-foreground">
              Thumbnail, legendas, transcrição, etc.
            </p>
            {extraFiles.length > 0 && (
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {extraFiles.map((file, index) => (
                  <div
                    key={`${file.name}-${index}`}
                    className="flex items-center gap-2 p-2 rounded bg-muted"
                  >
                    <File className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm truncate flex-1">{file.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {formatBytes(file.size)}
                    </span>
                    {!uploading && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => removeExtraFile(index)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Upload Progress */}
          {uploadProgress && uploading && (
            <div className="space-y-3 p-4 rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-blue-700 dark:text-blue-300">
                  Enviando para o Drive...
                </span>
                <span className="text-blue-600 dark:text-blue-400">
                  {uploadProgress.uploaded}/{uploadProgress.total} (
                  {Math.round(uploadProgress.percent)}%)
                </span>
              </div>
              <Progress value={uploadProgress.percent} className="h-2" />
              {uploadProgress.current_file && (
                <p className="text-xs text-blue-600 dark:text-blue-400 truncate">
                  {uploadProgress.current_file}
                </p>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={uploading}
            >
              Cancelar
            </Button>
            <Button onClick={handleUpload} disabled={!canUpload}>
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
