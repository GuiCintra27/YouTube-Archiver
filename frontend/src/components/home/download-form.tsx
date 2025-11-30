"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Download,
  Loader2,
  CheckCircle2,
  XCircle,
  X,
  Video,
  List,
} from "lucide-react";
import { formatBytes, formatSpeed, formatTime } from "@/lib/utils";
import { validateUrl, type UrlType } from "@/lib/url-validator";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";

interface DownloadProgress {
  status: string;
  filename?: string;
  downloaded_bytes?: number;
  total_bytes?: number;
  speed?: number;
  eta?: number;
  percentage?: number;
  current_file?: number;
  total_files?: number;
  message?: string;
  delay_remaining?: number;
  batch_completed?: number;
}

interface JobStatus {
  job_id: string;
  status: string;
  url: string;
  progress: DownloadProgress;
  result?: any;
  error?: string;
}

export default function DownloadForm() {
  // API URL from centralized hook
  const apiUrl = useApiUrl();

  // URL and validation state
  const [url, setUrl] = useState("");
  const [urlType, setUrlType] = useState<UrlType>("video");
  const [validationError, setValidationError] = useState<string | null>(null);

  // Download job state
  const [isDownloading, setIsDownloading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);

  // Polling cleanup ref - prevents memory leaks
  const pollingCleanupRef = useRef<(() => void) | null>(null);

  // Configurações avançadas
  const [outDir, setOutDir] = useState("./downloads");
  const [maxRes, setMaxRes] = useState("");
  const [subs, setSubs] = useState(true);
  const [autoSubs, setAutoSubs] = useState(true);
  const [thumbnails, setThumbnails] = useState(true);
  const [audioOnly, setAudioOnly] = useState(false);
  const [customPath, setCustomPath] = useState("");
  const [fileName, setFileName] = useState("");
  const [cookiesFile, setCookiesFile] = useState("");
  const [referer, setReferer] = useState("");
  const [origin, setOrigin] = useState("");

  // Configurações anti-ban
  const [delayBetweenDownloads, setDelayBetweenDownloads] = useState("0");
  const [batchSize, setBatchSize] = useState("");
  const [batchDelay, setBatchDelay] = useState("0");
  const [randomizeDelay, setRandomizeDelay] = useState(false);

  // Cleanup polling on unmount to prevent memory leaks
  useEffect(() => {
    return () => {
      if (pollingCleanupRef.current) {
        pollingCleanupRef.current();
      }
    };
  }, []);

  // Validar URL quando mudar
  useEffect(() => {
    if (url.trim()) {
      const validation = validateUrl(url, urlType);
      if (!validation.isValid && validation.message) {
        setValidationError(validation.message);
      } else {
        setValidationError(null);
      }
    } else {
      setValidationError(null);
    }
  }, [url, urlType]);

  const cancelDownload = useCallback(async () => {
    if (!jobId || !apiUrl) return;

    // Stop polling first
    if (pollingCleanupRef.current) {
      pollingCleanupRef.current();
      pollingCleanupRef.current = null;
    }

    try {
      const response = await fetch(
        `${apiUrl}/api/${APIURLS.JOBS}/${jobId}/cancel`,
        {
          method: "POST",
        }
      );

      if (response.ok) {
        setIsDownloading(false);
        setJobStatus((prev) =>
          prev ? { ...prev, status: "cancelled" } : null
        );
      }
    } catch (error) {
      console.error("Erro ao cancelar download:", error);
    }
  }, [jobId, apiUrl]);

  /**
   * Poll job status with automatic cleanup.
   * Returns a cleanup function to stop polling.
   */
  const pollJobStatus = useCallback(
    (id: string): (() => void) => {
      // Polling adaptativo: mais rápido no início, depois desacelera
      let pollInterval = 500; // Começa com 500ms
      let pollCount = 0;
      let timeoutId: NodeJS.Timeout | null = null;
      let cancelled = false;

      const poll = async () => {
        if (cancelled) return;

        try {
          const response = await fetch(`${apiUrl}/api/${APIURLS.JOBS}/${id}`);
          if (!response.ok) throw new Error("Erro ao verificar status");

          const status: JobStatus = await response.json();

          if (cancelled) return;
          setJobStatus(status);

          // Parar polling se completou, falhou ou foi cancelado
          if (["completed", "error", "cancelled"].includes(status.status)) {
            setIsDownloading(false);
            return; // Não agendar próximo poll
          }

          // Polling adaptativo
          pollCount++;
          if (pollCount > 10) {
            pollInterval = 2000; // Após 10 polls, reduzir para 2s
          } else if (pollCount > 5) {
            pollInterval = 1000; // Após 5 polls, 1s
          }

          // Agendar próximo poll
          if (!cancelled) {
            timeoutId = setTimeout(poll, pollInterval);
          }
        } catch (error) {
          if (!cancelled) {
            console.error("Erro ao verificar status:", error);
            setIsDownloading(false);
          }
        }
      };

      // Iniciar primeiro poll
      poll();

      // Return cleanup function
      return () => {
        cancelled = true;
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
      };
    },
    [apiUrl]
  );

  const startDownload = useCallback(async () => {
    if (!url.trim() || !apiUrl) return;

    // Validar URL antes de iniciar
    const validation = validateUrl(url, urlType);
    if (!validation.isValid) {
      setValidationError(validation.message || "URL inválida");
      return;
    }

    setIsDownloading(true);
    setJobStatus(null);
    setValidationError(null);

    try {
      // Iniciar download
      const response = await fetch(`${apiUrl}/api/${APIURLS.DOWLOAD}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url.trim(),
          out_dir: outDir,
          max_res: maxRes ? parseInt(maxRes) : null,
          subs,
          auto_subs: autoSubs,
          thumbnails,
          audio_only: audioOnly,
          path: customPath || null,
          file_name: fileName || null,
          cookies_file: cookiesFile || null,
          referer: referer || null,
          origin: origin || null,
          delay_between_downloads: delayBetweenDownloads
            ? parseInt(delayBetweenDownloads)
            : 0,
          batch_size: batchSize ? parseInt(batchSize) : null,
          batch_delay: batchDelay ? parseInt(batchDelay) : 0,
          randomize_delay: randomizeDelay,
        }),
      });

      const data = await response.json();

      if (data.job_id) {
        setJobId(data.job_id);
        // Monitorar progresso via polling with cleanup
        pollingCleanupRef.current = pollJobStatus(data.job_id);
      }
    } catch (error) {
      console.error("Erro ao iniciar download:", error);
      setIsDownloading(false);
      setValidationError("Erro ao conectar com o servidor");
    }
  }, [
    url,
    urlType,
    apiUrl,
    outDir,
    maxRes,
    subs,
    autoSubs,
    thumbnails,
    audioOnly,
    customPath,
    fileName,
    cookiesFile,
    referer,
    origin,
    delayBetweenDownloads,
    batchSize,
    batchDelay,
    randomizeDelay,
    pollJobStatus,
  ]);

  const progress: any = jobStatus?.progress || {};
  const percentage = progress.percentage || 0;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-3xl">YT-Archiver</CardTitle>
          <CardDescription>
            Baixe vídeos do YouTube, playlists e streams HLS de forma simples
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Seletor de Tipo */}
          <div className="space-y-3">
            <Label>Tipo de Download</Label>
            <RadioGroup
              value={urlType}
              onValueChange={(value) => setUrlType(value as UrlType)}
              className="flex gap-4"
              disabled={isDownloading}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="video" id="video" />
                <Label
                  htmlFor="video"
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <Video className="h-4 w-4" />
                  Vídeo Único
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="playlist" id="playlist" />
                <Label
                  htmlFor="playlist"
                  className="flex items-center gap-2 cursor-pointer"
                >
                  <List className="h-4 w-4" />
                  Playlist
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* URL Input */}
          <div className="space-y-2">
            <Label htmlFor="url">
              {urlType === "video" ? "URL do Vídeo" : "URL da Playlist"}
            </Label>
            <div className="flex gap-2">
              <Input
                id="url"
                placeholder={
                  urlType === "video"
                    ? "https://www.youtube.com/watch?v=..."
                    : "https://www.youtube.com/playlist?list=..."
                }
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={isDownloading}
                onKeyDown={(e) =>
                  e.key === "Enter" && !validationError && startDownload()
                }
                className={validationError ? "border-destructive" : ""}
              />
              {!isDownloading ? (
                <Button
                  onClick={startDownload}
                  disabled={isDownloading || !url.trim() || !!validationError}
                  size="lg"
                  className="min-w-[140px]"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Baixar
                </Button>
              ) : (
                <Button
                  onClick={cancelDownload}
                  variant="destructive"
                  size="lg"
                  className="min-w-[140px]"
                >
                  <X className="mr-2 h-4 w-4" />
                  Cancelar
                </Button>
              )}
            </div>

            {/* Validação Error */}
            {validationError && (
              <Alert variant="destructive">
                <AlertDescription>{validationError}</AlertDescription>
              </Alert>
            )}
          </div>

          {/* Progress Bar */}
          {jobStatus && (
            <div className="space-y-3 p-4 bg-muted/50 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {jobStatus.status === "completed" && (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  )}
                  {jobStatus.status === "error" && (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                  {jobStatus.status === "cancelled" && (
                    <XCircle className="h-5 w-5 text-orange-500" />
                  )}
                  {jobStatus.status === "downloading" && (
                    <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                  )}
                  <span className="font-medium">
                    {jobStatus.status === "completed" && "Download Concluído!"}
                    {jobStatus.status === "error" && "Erro no Download"}
                    {jobStatus.status === "cancelled" && "Download Cancelado"}
                    {jobStatus.status === "downloading" && "Baixando..."}
                    {jobStatus.status === "pending" && "Aguardando..."}
                  </span>
                </div>
                <span className="text-sm text-muted-foreground">
                  {Math.round(percentage)}%
                </span>
              </div>

              <Progress value={percentage} className="h-2" />

              {/* Download Stats */}
              {progress.status === "downloading" && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  {progress.filename && (
                    <div>
                      <div className="text-muted-foreground">Arquivo</div>
                      <div className="font-medium truncate">
                        {progress.filename}
                      </div>
                    </div>
                  )}
                  {progress.downloaded_bytes !== undefined &&
                    progress.total_bytes && (
                      <div>
                        <div className="text-muted-foreground">Tamanho</div>
                        <div className="font-medium">
                          {formatBytes(progress.downloaded_bytes)} /{" "}
                          {formatBytes(progress.total_bytes)}
                        </div>
                      </div>
                    )}
                  {progress.speed && (
                    <div>
                      <div className="text-muted-foreground">Velocidade</div>
                      <div className="font-medium">
                        {formatSpeed(progress.speed)}
                      </div>
                    </div>
                  )}
                  {progress.eta && (
                    <div>
                      <div className="text-muted-foreground">
                        Tempo Restante
                      </div>
                      <div className="font-medium">
                        {formatTime(progress.eta)}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Waiting Status */}
              {(progress.status === "waiting" ||
                progress.status === "batch_waiting") && (
                <Alert className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
                  <AlertDescription className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <div>
                      <div className="font-medium">{progress.message}</div>
                      {progress.batch_completed && (
                        <div className="text-sm text-muted-foreground">
                          Batch {progress.batch_completed} concluído
                        </div>
                      )}
                    </div>
                  </AlertDescription>
                </Alert>
              )}

              {jobStatus.error && (
                <div className="text-sm text-red-600 dark:text-red-400">
                  Erro: {jobStatus.error}
                </div>
              )}
            </div>
          )}

          {/* Advanced Options */}
          <Accordion type="single" collapsible>
            <AccordionItem value="advanced">
              <AccordionTrigger>Opções Avançadas</AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4 pt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Diretório */}
                    <div className="space-y-2">
                      <Label htmlFor="outDir">Diretório de Saída</Label>
                      <Input
                        id="outDir"
                        value={outDir}
                        onChange={(e) => setOutDir(e.target.value)}
                        placeholder="./downloads"
                        disabled={isDownloading}
                      />
                    </div>

                    {/* Resolução Máxima */}
                    <div className="space-y-2">
                      <Label htmlFor="maxRes">Resolução Máxima (altura)</Label>
                      <Input
                        id="maxRes"
                        type="number"
                        value={maxRes}
                        onChange={(e) => setMaxRes(e.target.value)}
                        placeholder="1080"
                        disabled={isDownloading}
                      />
                    </div>

                    {/* Caminho Customizado */}
                    <div className="space-y-2">
                      <Label htmlFor="customPath">Subpasta Personalizada</Label>
                      <Input
                        id="customPath"
                        value={customPath}
                        onChange={(e) => setCustomPath(e.target.value)}
                        placeholder="Curso/Módulo 01"
                        disabled={isDownloading}
                      />
                    </div>

                    {/* Nome do Arquivo */}
                    <div className="space-y-2">
                      <Label htmlFor="fileName">Nome do Arquivo</Label>
                      <Input
                        id="fileName"
                        value={fileName}
                        onChange={(e) => setFileName(e.target.value)}
                        placeholder="Aula 01 - Introdução"
                        disabled={isDownloading}
                      />
                    </div>

                    {/* Referer */}
                    <div className="space-y-2">
                      <Label htmlFor="referer">Header Referer</Label>
                      <Input
                        id="referer"
                        value={referer}
                        onChange={(e) => setReferer(e.target.value)}
                        placeholder="https://example.com"
                        disabled={isDownloading}
                      />
                    </div>

                    {/* Origin */}
                    <div className="space-y-2">
                      <Label htmlFor="origin">Header Origin</Label>
                      <Input
                        id="origin"
                        value={origin}
                        onChange={(e) => setOrigin(e.target.value)}
                        placeholder="https://example.com"
                        disabled={isDownloading}
                      />
                    </div>

                    {/* Cookies File */}
                    <div className="space-y-2 md:col-span-2">
                      <Label htmlFor="cookies">Arquivo de Cookies</Label>
                      <Input
                        id="cookies"
                        value={cookiesFile}
                        onChange={(e) => setCookiesFile(e.target.value)}
                        placeholder="./cookies.txt"
                        disabled={isDownloading}
                      />
                    </div>
                  </div>

                  {/* Switches */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="subs">Baixar Legendas</Label>
                      <Switch
                        id="subs"
                        checked={subs}
                        onCheckedChange={setSubs}
                        disabled={isDownloading}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label htmlFor="autoSubs">Legendas Automáticas</Label>
                      <Switch
                        id="autoSubs"
                        checked={autoSubs}
                        onCheckedChange={setAutoSubs}
                        disabled={isDownloading}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label htmlFor="thumbnails">Baixar Miniaturas</Label>
                      <Switch
                        id="thumbnails"
                        checked={thumbnails}
                        onCheckedChange={setThumbnails}
                        disabled={isDownloading}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label htmlFor="audioOnly">Apenas Áudio (MP3)</Label>
                      <Switch
                        id="audioOnly"
                        checked={audioOnly}
                        onCheckedChange={setAudioOnly}
                        disabled={isDownloading}
                      />
                    </div>
                  </div>

                  {/* Anti-Ban Settings */}
                  <div className="space-y-4 pt-4 border-t">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <Label className="text-base font-semibold">
                          Proteção Anti-Ban
                        </Label>
                        <p className="text-sm text-muted-foreground">
                          Evite bloqueios ao baixar playlists grandes
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Delay Between Downloads */}
                      <div className="space-y-2">
                        <Label htmlFor="delayBetweenDownloads">
                          Delay Entre Vídeos (segundos)
                        </Label>
                        <Input
                          id="delayBetweenDownloads"
                          type="number"
                          min="0"
                          value={delayBetweenDownloads}
                          onChange={(e) =>
                            setDelayBetweenDownloads(e.target.value)
                          }
                          placeholder="0"
                          disabled={isDownloading}
                        />
                        <p className="text-xs text-muted-foreground">
                          Pausa entre cada vídeo (recomendado: 2-5s)
                        </p>
                      </div>

                      {/* Batch Size */}
                      <div className="space-y-2">
                        <Label htmlFor="batchSize">Vídeos por Batch</Label>
                        <Input
                          id="batchSize"
                          type="number"
                          min="1"
                          value={batchSize}
                          onChange={(e) => setBatchSize(e.target.value)}
                          placeholder="Desabilitado"
                          disabled={isDownloading}
                        />
                        <p className="text-xs text-muted-foreground">
                          Agrupar downloads em batches (ex: 5)
                        </p>
                      </div>

                      {/* Batch Delay */}
                      <div className="space-y-2">
                        <Label htmlFor="batchDelay">
                          Delay Entre Batches (segundos)
                        </Label>
                        <Input
                          id="batchDelay"
                          type="number"
                          min="0"
                          value={batchDelay}
                          onChange={(e) => setBatchDelay(e.target.value)}
                          placeholder="0"
                          disabled={isDownloading}
                        />
                        <p className="text-xs text-muted-foreground">
                          Pausa maior entre grupos (recomendado: 10-30s)
                        </p>
                      </div>

                      {/* Randomize Delay */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between h-10">
                          <Label htmlFor="randomizeDelay">
                            Randomizar Delays
                          </Label>
                          <Switch
                            id="randomizeDelay"
                            checked={randomizeDelay}
                            onCheckedChange={setRandomizeDelay}
                            disabled={isDownloading}
                          />
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Varia tempo de espera para parecer humano
                        </p>
                      </div>
                    </div>

                    {/* Presets */}
                    <div className="flex gap-2 flex-wrap">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={isDownloading}
                        onClick={() => {
                          setDelayBetweenDownloads("5");
                          setBatchSize("5");
                          setBatchDelay("30");
                          setRandomizeDelay(true);
                        }}
                      >
                        🛡️ Seguro
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={isDownloading}
                        onClick={() => {
                          setDelayBetweenDownloads("3");
                          setBatchSize("10");
                          setBatchDelay("15");
                          setRandomizeDelay(true);
                        }}
                      >
                        ⚖️ Moderado
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={isDownloading}
                        onClick={() => {
                          setDelayBetweenDownloads("0");
                          setBatchSize("");
                          setBatchDelay("0");
                          setRandomizeDelay(false);
                        }}
                      >
                        ⚡ Rápido (sem proteção)
                      </Button>
                    </div>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>
    </div>
  );
}
