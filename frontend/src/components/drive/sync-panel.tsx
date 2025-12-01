"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  ArrowUpCircle,
  Loader2,
  RefreshCw,
  CheckCircle2,
  Upload,
  HardDrive,
  Cloud,
  XCircle,
  FolderUp,
  Download,
} from "lucide-react";
import ExternalUploadModal from "./external-upload-modal";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";

interface SyncStatus {
  local_only: string[];
  drive_only: string[];
  synced: string[];
  total_local: number;
  total_drive: number;
}

interface UploadProgress {
  status: string;
  total: number;
  uploaded: number;
  failed: number;
  percent: number;
  current_file: string | null;
  files_in_progress?: string[];
}

interface DownloadProgress {
  status: string;
  total: number;
  downloaded: number;
  failed: number;
  percent: number;
  current_file: string | null;
  files_in_progress?: string[];
}

interface JobResponse {
  status: string;
  progress: UploadProgress | DownloadProgress;
  result?: {
    uploaded?: number;
    downloaded?: number;
    total: number;
    failed: Array<{ file: string; error: string }>;
  };
  error?: string;
}

export default function SyncPanel() {
  const apiUrl = useApiUrl();
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [uploadingVideo, setUploadingVideo] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const [showExternalUpload, setShowExternalUpload] = useState(false);

  // Download states
  const [downloading, setDownloading] = useState(false);
  const [downloadingVideo, setDownloadingVideo] = useState<string | null>(null);
  const [downloadProgress, setDownloadProgress] = useState<DownloadProgress | null>(null);

  // Ref para cleanup do polling
  const pollingCleanupRef = useRef<(() => void) | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingCleanupRef.current) {
        pollingCleanupRef.current();
      }
    };
  }, []);

  const fetchSyncStatus = useCallback(async () => {
    if (!apiUrl) return;
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(
        `${apiUrl}/api/${APIURLS.DRIVE_SYNC_STATUS}`
      );

      if (!response.ok) {
        throw new Error("Falha ao obter status de sincronização");
      }

      const data = await response.json();
      setSyncStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchSyncStatus();
  }, [fetchSyncStatus]);

  const pollJobProgress = useCallback(
    async (jobId: string, onComplete: (result: JobResponse) => void) => {
      if (!apiUrl) return;

      let cancelled = false;
      let timeoutId: NodeJS.Timeout | null = null;

      const poll = async () => {
        if (cancelled) return;

        try {
          const res = await fetch(`${apiUrl}/api/jobs/${jobId}`);
          if (!res.ok) {
            throw new Error("Falha ao obter progresso do job");
          }

          const job: JobResponse = await res.json();

          // Atualizar progresso
          if (job.progress) {
            setUploadProgress(job.progress);
          }

          // Verificar se terminou
          if (["completed", "error", "cancelled"].includes(job.status)) {
            onComplete(job);
            return;
          }

          // Continuar polling
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

      // Iniciar polling
      poll();

      // Retornar função de cleanup
      return () => {
        cancelled = true;
        if (timeoutId) clearTimeout(timeoutId);
      };
    },
    [apiUrl, uploadProgress]
  );

  const handleSyncAll = useCallback(async () => {
    if (!syncStatus || syncStatus.local_only.length === 0 || !apiUrl) return;

    try {
      setSyncing(true);
      setError(null);
      setSuccessMessage(null);
      setUploadProgress({
        status: "initializing",
        total: syncStatus.local_only.length,
        uploaded: 0,
        failed: 0,
        percent: 0,
        current_file: null,
      });

      const response = await fetch(`${apiUrl}/api/${APIURLS.DRIVE_SYNC_ALL}`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Falha ao iniciar sincronização");
      }

      const data = await response.json();
      const jobId = data.job_id;

      if (!jobId) {
        throw new Error("Job ID não retornado pelo servidor");
      }

      // Iniciar polling do progresso
      const cleanup = await pollJobProgress(jobId, async (job) => {
        setSyncing(false);
        setUploadProgress(null);

        if (job.status === "completed" && job.result) {
          const { uploaded, failed } = job.result;
          await fetchSyncStatus();

          if (failed.length > 0) {
            setSuccessMessage(
              `Sincronização concluída! ${uploaded} vídeos enviados, ${failed.length} falhas.`
            );
          } else {
            setSuccessMessage(
              `Sincronização concluída! ${uploaded} vídeos enviados com sucesso.`
            );
          }
        } else if (job.status === "error") {
          setError(job.error || "Erro durante sincronização");
        } else if (job.status === "cancelled") {
          setError("Sincronização cancelada");
        }
      });

      pollingCleanupRef.current = cleanup || null;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao sincronizar");
      setSyncing(false);
      setUploadProgress(null);
    }
  }, [syncStatus, apiUrl, fetchSyncStatus, pollJobProgress]);

  const handleUploadSingle = useCallback(
    async (videoPath: string) => {
      if (!apiUrl) return;
      try {
        setUploadingVideo(videoPath);
        setError(null);
        setSuccessMessage(null);

        const response = await fetch(
          `${apiUrl}/api/${APIURLS.DRIVE_UPLOAD}/${encodeURIComponent(
            videoPath
          )}`,
          { method: "POST" }
        );

        if (!response.ok) {
          throw new Error("Falha ao iniciar upload");
        }

        const data = await response.json();
        const jobId = data.job_id;

        if (!jobId) {
          throw new Error("Job ID não retornado pelo servidor");
        }

        // Iniciar polling do progresso
        const cleanup = await pollJobProgress(jobId, async (job) => {
          setUploadingVideo(null);

          if (job.status === "completed") {
            await fetchSyncStatus();
            setSuccessMessage("Upload concluído com sucesso!");
          } else if (job.status === "error") {
            setError(job.error || "Erro no upload");
          }
        });

        pollingCleanupRef.current = cleanup || null;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao fazer upload");
        setUploadingVideo(null);
      }
    },
    [apiUrl, fetchSyncStatus, pollJobProgress]
  );

  // Download polling function
  const pollDownloadProgress = useCallback(
    async (jobId: string, onComplete: (result: JobResponse) => void) => {
      if (!apiUrl) return;

      let cancelled = false;
      let timeoutId: NodeJS.Timeout | null = null;

      const poll = async () => {
        if (cancelled) return;

        try {
          const res = await fetch(`${apiUrl}/api/jobs/${jobId}`);
          if (!res.ok) {
            throw new Error("Falha ao obter progresso do download");
          }

          const job: JobResponse = await res.json();

          // Atualizar progresso
          if (job.progress && "downloaded" in job.progress) {
            setDownloadProgress(job.progress as DownloadProgress);
          }

          // Verificar se terminou
          if (["completed", "error", "cancelled"].includes(job.status)) {
            onComplete(job);
            return;
          }

          // Continuar polling
          if (!cancelled) {
            timeoutId = setTimeout(poll, 1000);
          }
        } catch (err) {
          if (!cancelled) {
            setError(err instanceof Error ? err.message : "Erro no polling");
            onComplete({ status: "error", progress: downloadProgress! });
          }
        }
      };

      poll();

      return () => {
        cancelled = true;
        if (timeoutId) clearTimeout(timeoutId);
      };
    },
    [apiUrl, downloadProgress]
  );

  // Download all videos from Drive to local
  const handleDownloadAll = useCallback(async () => {
    if (!syncStatus || syncStatus.drive_only.length === 0 || !apiUrl) return;

    try {
      setDownloading(true);
      setError(null);
      setSuccessMessage(null);
      setDownloadProgress({
        status: "initializing",
        total: syncStatus.drive_only.length,
        downloaded: 0,
        failed: 0,
        percent: 0,
        current_file: null,
      });

      const response = await fetch(`${apiUrl}/api/${APIURLS.DRIVE_DOWNLOAD_ALL}`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Falha ao iniciar download");
      }

      const data = await response.json();
      const jobId = data.job_id;

      if (!jobId) {
        throw new Error("Job ID não retornado pelo servidor");
      }

      const cleanup = await pollDownloadProgress(jobId, async (job) => {
        setDownloading(false);
        setDownloadProgress(null);

        if (job.status === "completed" && job.result) {
          const downloaded = job.result.downloaded || 0;
          const failed = job.result.failed || [];
          await fetchSyncStatus();

          if (failed.length > 0) {
            setSuccessMessage(
              `Download concluído! ${downloaded} vídeos baixados, ${failed.length} falhas.`
            );
          } else {
            setSuccessMessage(
              `Download concluído! ${downloaded} vídeos baixados com sucesso.`
            );
          }
        } else if (job.status === "error") {
          setError(job.error || "Erro durante download");
        } else if (job.status === "cancelled") {
          setError("Download cancelado");
        }
      });

      pollingCleanupRef.current = cleanup || null;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao baixar");
      setDownloading(false);
      setDownloadProgress(null);
    }
  }, [syncStatus, apiUrl, fetchSyncStatus, pollDownloadProgress]);

  // Download single video from Drive to local
  const handleDownloadSingle = useCallback(
    async (videoPath: string) => {
      if (!apiUrl) return;
      try {
        setDownloadingVideo(videoPath);
        setError(null);
        setSuccessMessage(null);
        // Inicializar progresso para download individual
        setDownloadProgress({
          status: "initializing",
          total: 1,
          downloaded: 0,
          failed: 0,
          percent: 0,
          current_file: videoPath,
        });

        const response = await fetch(
          `${apiUrl}/api/${APIURLS.DRIVE_DOWNLOAD}?path=${encodeURIComponent(videoPath)}`,
          { method: "POST" }
        );

        if (!response.ok) {
          throw new Error("Falha ao iniciar download");
        }

        const data = await response.json();
        const jobId = data.job_id;

        if (!jobId) {
          throw new Error("Job ID não retornado pelo servidor");
        }

        const cleanup = await pollDownloadProgress(jobId, async (job) => {
          setDownloadingVideo(null);
          setDownloadProgress(null);

          if (job.status === "completed") {
            await fetchSyncStatus();
            setSuccessMessage("Download concluído com sucesso!");
          } else if (job.status === "error") {
            setError(job.error || "Erro no download");
          }
        });

        pollingCleanupRef.current = cleanup || null;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao fazer download");
        setDownloadingVideo(null);
        setDownloadProgress(null);
      }
    },
    [apiUrl, fetchSyncStatus, pollDownloadProgress]
  );

  if (loading && !syncStatus) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  const syncPercentage = syncStatus
    ? syncStatus.total_local > 0
      ? (syncStatus.synced.length / syncStatus.total_local) * 100
      : 100
    : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ArrowUpCircle className="h-5 w-5" />
          Sincronização Local → Drive
        </CardTitle>
        <CardDescription>
          Gerencie seus vídeos entre armazenamento local e Google Drive
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {successMessage && (
          <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-700 dark:text-green-300">
              {successMessage}
            </AlertDescription>
          </Alert>
        )}

        {/* Upload Progress */}
        {uploadProgress && syncing && (
          <div className="space-y-3 p-4 rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-blue-700 dark:text-blue-300">
                Enviando para o Drive...
              </span>
              <span className="text-blue-600 dark:text-blue-400">
                {uploadProgress.uploaded}/{uploadProgress.total} ({Math.round(uploadProgress.percent)}%)
              </span>
            </div>
            <Progress value={uploadProgress.percent} className="h-2" />
            {uploadProgress.current_file && (
              <p className="text-xs text-blue-600 dark:text-blue-400 truncate">
                Arquivo atual: {uploadProgress.current_file}
              </p>
            )}
            {uploadProgress.failed > 0 && (
              <p className="text-xs text-red-600 dark:text-red-400">
                {uploadProgress.failed} arquivo(s) com falha
              </p>
            )}
          </div>
        )}

        {/* Download Progress */}
        {downloadProgress && (downloading || downloadingVideo !== null) && (
          <div className="space-y-3 p-4 rounded-lg bg-purple-50 dark:bg-purple-950 border border-purple-200 dark:border-purple-800">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-purple-700 dark:text-purple-300">
                {downloading ? "Baixando do Drive..." : "Baixando vídeo..."}
              </span>
              <span className="text-purple-600 dark:text-purple-400">
                {downloadProgress.downloaded}/{downloadProgress.total} ({Math.round(downloadProgress.percent)}%)
              </span>
            </div>
            <Progress value={downloadProgress.percent} className="h-2" />
            {downloadProgress.current_file && (
              <p className="text-xs text-purple-600 dark:text-purple-400 truncate">
                Arquivo atual: {downloadProgress.current_file}
              </p>
            )}
            {downloadProgress.failed > 0 && (
              <p className="text-xs text-red-600 dark:text-red-400">
                {downloadProgress.failed} arquivo(s) com falha
              </p>
            )}
          </div>
        )}

        {syncStatus && (
          <>
            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="flex flex-col items-center gap-2 p-4 rounded-lg bg-muted">
                <HardDrive className="h-5 w-5 text-muted-foreground" />
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {syncStatus.total_local}
                  </div>
                  <div className="text-xs text-muted-foreground">Local</div>
                </div>
              </div>

              <div className="flex flex-col items-center gap-2 p-4 rounded-lg bg-muted">
                <Cloud className="h-5 w-5 text-muted-foreground" />
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {syncStatus.total_drive}
                  </div>
                  <div className="text-xs text-muted-foreground">Drive</div>
                </div>
              </div>

              <div className="flex flex-col items-center gap-2 p-4 rounded-lg bg-primary/10">
                <CheckCircle2 className="h-5 w-5 text-primary" />
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {syncStatus.synced.length}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Sincronizados
                  </div>
                </div>
              </div>
            </div>

            {/* Progress */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  Progresso de sincronização
                </span>
                <span className="font-medium">
                  {Math.round(syncPercentage)}%
                </span>
              </div>
              <Progress value={syncPercentage} />
            </div>

            {/* Actions */}
            <div className="flex gap-2 flex-wrap">
              <Button
                variant="outline"
                onClick={fetchSyncStatus}
                disabled={loading || syncing}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Atualizar
              </Button>

              <Button
                variant="outline"
                onClick={() => setShowExternalUpload(true)}
                disabled={syncing || uploadingVideo !== null}
              >
                <FolderUp className="h-4 w-4 mr-2" />
                Upload Externo
              </Button>

              {syncStatus.local_only.length > 0 && (
                <Button
                  onClick={handleSyncAll}
                  disabled={syncing || uploadingVideo !== null || downloading || downloadingVideo !== null}
                >
                  {syncing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Sincronizando ({uploadProgress?.uploaded || 0}/{uploadProgress?.total || 0})
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Sincronizar Todos ({syncStatus.local_only.length})
                    </>
                  )}
                </Button>
              )}

              {syncStatus.drive_only.length > 0 && (
                <Button
                  variant="secondary"
                  onClick={handleDownloadAll}
                  disabled={downloading || downloadingVideo !== null || syncing || uploadingVideo !== null}
                >
                  {downloading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Baixando ({downloadProgress?.downloaded || 0}/{downloadProgress?.total || 0})
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-2" />
                      Baixar Todos ({syncStatus.drive_only.length})
                    </>
                  )}
                </Button>
              )}
            </div>

            {/* Details Accordion */}
            <Accordion type="single" collapsible className="w-full">
              {/* Local Only */}
              {syncStatus.local_only.length > 0 && (
                <AccordionItem value="local-only">
                  <AccordionTrigger>
                    <div className="flex items-center gap-2">
                      <HardDrive className="h-4 w-4" />
                      Apenas Local ({syncStatus.local_only.length})
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {syncStatus.local_only.map((video) => (
                        <div
                          key={video}
                          className="flex items-center justify-between p-2 rounded bg-muted"
                        >
                          <span className="text-sm truncate flex-1">
                            {video}
                          </span>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleUploadSingle(video)}
                            disabled={uploadingVideo !== null || syncing}
                          >
                            {uploadingVideo === video ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Upload className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              )}

              {/* Drive Only */}
              {syncStatus.drive_only.length > 0 && (
                <AccordionItem value="drive-only">
                  <AccordionTrigger>
                    <div className="flex items-center gap-2">
                      <Cloud className="h-4 w-4" />
                      Apenas Drive ({syncStatus.drive_only.length})
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {syncStatus.drive_only.map((video) => (
                        <div
                          key={video}
                          className="flex items-center justify-between p-2 rounded bg-muted"
                        >
                          <span className="text-sm truncate flex-1">
                            {video}
                          </span>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDownloadSingle(video)}
                            disabled={downloadingVideo !== null || downloading || syncing || uploadingVideo !== null}
                          >
                            {downloadingVideo === video ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Download className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              )}

              {/* Synced */}
              {syncStatus.synced.length > 0 && (
                <AccordionItem value="synced">
                  <AccordionTrigger>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-primary" />
                      Sincronizados ({syncStatus.synced.length})
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {syncStatus.synced.map((video) => (
                        <div
                          key={video}
                          className="flex items-center p-2 rounded bg-muted"
                        >
                          <CheckCircle2 className="h-4 w-4 text-primary mr-2" />
                          <span className="text-sm truncate">{video}</span>
                        </div>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              )}
            </Accordion>
          </>
        )}

        {/* External Upload Modal */}
        <ExternalUploadModal
          open={showExternalUpload}
          onOpenChange={setShowExternalUpload}
          onUploadComplete={fetchSyncStatus}
        />
      </CardContent>
    </Card>
  );
}
