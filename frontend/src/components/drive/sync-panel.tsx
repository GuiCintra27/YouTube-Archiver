"use client";

import { useState, useEffect, useCallback } from "react";
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
} from "lucide-react";
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

export default function SyncPanel() {
  const apiUrl = useApiUrl();
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [uploadingVideo, setUploadingVideo] = useState<string | null>(null);

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

  const handleSyncAll = useCallback(async () => {
    if (!syncStatus || syncStatus.local_only.length === 0 || !apiUrl) return;

    try {
      setSyncing(true);
      setError(null);
      setSuccessMessage(null);

      const response = await fetch(`${apiUrl}/api/${APIURLS.DRIVE_SYNC_ALL}`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Falha ao sincronizar vídeos");
      }

      const data = await response.json();

      // Atualizar status
      await fetchSyncStatus();

      setSuccessMessage(`Sincronização concluída! ${data.total} vídeos processados.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao sincronizar");
    } finally {
      setSyncing(false);
    }
  }, [syncStatus, apiUrl, fetchSyncStatus]);

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
          throw new Error("Falha ao fazer upload");
        }

        // Atualizar status
        await fetchSyncStatus();

        setSuccessMessage("Upload concluído com sucesso!");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao fazer upload");
      } finally {
        setUploadingVideo(null);
      }
    },
    [apiUrl, fetchSyncStatus]
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
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={fetchSyncStatus}
                disabled={loading || syncing}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Atualizar
              </Button>

              {syncStatus.local_only.length > 0 && (
                <Button
                  onClick={handleSyncAll}
                  disabled={syncing || uploadingVideo !== null}
                >
                  {syncing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Sincronizando...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Sincronizar Todos ({syncStatus.local_only.length})
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
                          className="flex items-center p-2 rounded bg-muted"
                        >
                          <span className="text-sm truncate">{video}</span>
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
      </CardContent>
    </Card>
  );
}
