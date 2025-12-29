"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
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
  Shield,
  Settings2,
  LibraryBig,
} from "lucide-react";
import { formatBytes, formatSpeed, formatTime } from "@/lib/utils";
import { validateUrl, type UrlType } from "@/lib/url-validator";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";
import Link from "next/link";
import { PATHS } from "@/lib/paths";

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

interface DownloadFormProps {
  onDownloadComplete?: () => void;
}

export default function DownloadForm({ onDownloadComplete }: DownloadFormProps) {
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
            if (status.status === "completed") {
              onDownloadComplete?.();
              window.dispatchEvent(new Event("yt-archiver:videos-updated"));
            }
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
    [apiUrl, onDownloadComplete]
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
      {/* Glass Card Container */}
      <div className="glass-card rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-white/5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-teal to-cyan flex items-center justify-center">
              <Download className="h-6 w-6 text-navy-dark" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Download</h2>
              <p className="text-sm text-muted-foreground">
                Cole a URL e clique em baixar
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-teal/10 text-teal border border-teal/20">
              <Shield className="inline h-3 w-3 mr-1" />
              Anti-ban
            </span>
            <Link
              href={PATHS.LIBRARY}
              className="px-3 py-1.5 rounded-full text-xs font-medium border border-white/10 text-muted-foreground hover:text-white hover:border-white/20 transition-all flex items-center gap-1"
            >
              <LibraryBig className="h-3 w-3" />
              Biblioteca
            </Link>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Seletor de Tipo */}
          <div className="space-y-3">
            <Label className="text-white">Tipo de Download</Label>
            <RadioGroup
              value={urlType}
              onValueChange={(value) => setUrlType(value as UrlType)}
              className="flex gap-4"
              disabled={isDownloading}
            >
              <div
                className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all ${
                  urlType === "video"
                    ? "bg-teal/10 border border-teal/30"
                    : "bg-white/5 border border-white/10 hover:border-white/20"
                }`}
                onClick={() => !isDownloading && setUrlType("video")}
              >
                <RadioGroupItem value="video" id="video" className="sr-only" />
                <Video
                  className={`h-5 w-5 ${
                    urlType === "video" ? "text-teal" : "text-muted-foreground"
                  }`}
                />
                <Label
                  htmlFor="video"
                  className={`cursor-pointer ${
                    urlType === "video" ? "text-white" : "text-muted-foreground"
                  }`}
                >
                  Video Unico
                </Label>
              </div>
              <div
                className={`flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all ${
                  urlType === "playlist"
                    ? "bg-teal/10 border border-teal/30"
                    : "bg-white/5 border border-white/10 hover:border-white/20"
                }`}
                onClick={() => !isDownloading && setUrlType("playlist")}
              >
                <RadioGroupItem
                  value="playlist"
                  id="playlist"
                  className="sr-only"
                />
                <List
                  className={`h-5 w-5 ${
                    urlType === "playlist"
                      ? "text-teal"
                      : "text-muted-foreground"
                  }`}
                />
                <Label
                  htmlFor="playlist"
                  className={`cursor-pointer ${
                    urlType === "playlist"
                      ? "text-white"
                      : "text-muted-foreground"
                  }`}
                >
                  Playlist
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* URL Input */}
          <div className="space-y-3">
            <Label htmlFor="url" className="text-white">
              {urlType === "video" ? "URL do Video" : "URL da Playlist"}
            </Label>
            <div className="flex gap-3">
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
                className={`glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground h-12 ${
                  validationError
                    ? "border-red-500/50 focus:border-red-500"
                    : "focus:border-teal/50"
                }`}
              />
              {!isDownloading ? (
                <Button
                  onClick={startDownload}
                  disabled={isDownloading || !url.trim() || !!validationError}
                  className="h-12 px-6 btn-gradient-teal rounded-xl"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Baixar
                </Button>
              ) : (
                <Button
                  onClick={cancelDownload}
                  variant="destructive"
                  className="h-12 px-6 rounded-xl"
                >
                  <X className="mr-2 h-4 w-4" />
                  Cancelar
                </Button>
              )}
            </div>

            {/* Validação Error */}
            {validationError && (
              <Alert
                variant="destructive"
                className="bg-red-500/10 border-red-500/20"
              >
                <AlertDescription>{validationError}</AlertDescription>
              </Alert>
            )}
          </div>

          {/* Progress Bar */}
          {jobStatus && (
            <div className="space-y-4 p-5 rounded-xl bg-white/5 border border-white/10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {jobStatus.status === "completed" && (
                    <div className="w-10 h-10 rounded-full bg-green-500/10 flex items-center justify-center">
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    </div>
                  )}
                  {jobStatus.status === "error" && (
                    <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center">
                      <XCircle className="h-5 w-5 text-red-500" />
                    </div>
                  )}
                  {jobStatus.status === "cancelled" && (
                    <div className="w-10 h-10 rounded-full bg-orange-500/10 flex items-center justify-center">
                      <XCircle className="h-5 w-5 text-orange-500" />
                    </div>
                  )}
                  {(jobStatus.status === "downloading" ||
                    jobStatus.status === "pending") && (
                    <div className="w-10 h-10 rounded-full bg-teal/10 flex items-center justify-center">
                      <Loader2 className="h-5 w-5 animate-spin text-teal" />
                    </div>
                  )}
                  <div>
                    <span className="font-medium text-white">
                      {jobStatus.status === "completed" &&
                        "Download Concluido!"}
                      {jobStatus.status === "error" && "Erro no Download"}
                      {jobStatus.status === "cancelled" && "Download Cancelado"}
                      {jobStatus.status === "downloading" && "Baixando..."}
                      {jobStatus.status === "pending" && "Aguardando..."}
                    </span>
                    {progress.filename && (
                      <p className="text-sm text-muted-foreground truncate max-w-xs">
                        {progress.filename}
                      </p>
                    )}
                  </div>
                </div>
                <span className="text-2xl font-bold gradient-teal-text">
                  {Math.round(percentage)}%
                </span>
              </div>

              {/* Custom Progress Bar */}
              <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-teal to-cyan transition-all duration-300"
                  style={{ width: `${percentage}%` }}
                />
              </div>

              {/* Download Stats */}
              {progress.status === "downloading" && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {progress.downloaded_bytes !== undefined &&
                    progress.total_bytes && (
                      <div className="p-3 rounded-lg bg-white/5">
                        <div className="text-xs text-muted-foreground mb-1">
                          Tamanho
                        </div>
                        <div className="font-medium text-white">
                          {formatBytes(progress.downloaded_bytes)} /{" "}
                          {formatBytes(progress.total_bytes)}
                        </div>
                      </div>
                    )}
                  {progress.speed && (
                    <div className="p-3 rounded-lg bg-white/5">
                      <div className="text-xs text-muted-foreground mb-1">
                        Velocidade
                      </div>
                      <div className="font-medium text-white">
                        {formatSpeed(progress.speed)}
                      </div>
                    </div>
                  )}
                  {progress.eta && (
                    <div className="p-3 rounded-lg bg-white/5">
                      <div className="text-xs text-muted-foreground mb-1">
                        Tempo Restante
                      </div>
                      <div className="font-medium text-white">
                        {formatTime(progress.eta)}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Waiting Status */}
              {(progress.status === "waiting" ||
                progress.status === "batch_waiting") && (
                <div className="flex items-center gap-3 p-3 rounded-lg bg-teal/5 border border-teal/20">
                  <Loader2 className="h-4 w-4 animate-spin text-teal" />
                  <div>
                    <div className="font-medium text-white">
                      {progress.message}
                    </div>
                    {progress.batch_completed && (
                      <div className="text-sm text-muted-foreground">
                        Batch {progress.batch_completed} concluido
                      </div>
                    )}
                  </div>
                </div>
              )}

              {jobStatus.error && (
                <div className="text-sm text-red-400 bg-red-500/10 p-3 rounded-lg">
                  Erro: {jobStatus.error}
                </div>
              )}
            </div>
          )}

          {/* Advanced Options */}
          <Accordion type="single" collapsible>
            <AccordionItem
              value="advanced"
              className="border-white/10 rounded-xl overflow-hidden"
            >
              <AccordionTrigger className="px-4 py-3 hover:no-underline hover:bg-white/5 text-white">
                <div className="flex items-center gap-2">
                  <Settings2 className="h-4 w-4 text-purple" />
                  Opcoes Avancadas
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-4 pb-4">
                <div className="space-y-6 pt-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Resolução Máxima */}
                    <div className="space-y-2">
                      <Label htmlFor="maxRes" className="text-white text-sm">
                        Resolucao Maxima (altura)
                      </Label>
                      <Input
                        id="maxRes"
                        type="number"
                        value={maxRes}
                        onChange={(e) => setMaxRes(e.target.value)}
                        placeholder="1080"
                        disabled={isDownloading}
                        className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
                      />
                    </div>

                    {/* Caminho Customizado */}
                    <div className="space-y-2">
                      <Label
                        htmlFor="customPath"
                        className="text-white text-sm"
                      >
                        Subpasta Personalizada
                      </Label>
                      <Input
                        id="customPath"
                        value={customPath}
                        onChange={(e) => setCustomPath(e.target.value)}
                        placeholder="Curso/Modulo 01"
                        disabled={isDownloading}
                        className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
                      />
                    </div>

                    {/* Nome do Arquivo */}
                    <div className="space-y-2">
                      <Label htmlFor="fileName" className="text-white text-sm">
                        Nome do Arquivo
                      </Label>
                      <Input
                        id="fileName"
                        value={fileName}
                        onChange={(e) => setFileName(e.target.value)}
                        placeholder="Aula 01 - Introducao"
                        disabled={isDownloading}
                        className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
                      />
                    </div>

                    {/* Referer */}
                    <div className="space-y-2">
                      <Label htmlFor="referer" className="text-white text-sm">
                        Header Referer
                      </Label>
                      <Input
                        id="referer"
                        value={referer}
                        onChange={(e) => setReferer(e.target.value)}
                        placeholder="https://example.com"
                        disabled={isDownloading}
                        className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
                      />
                    </div>

                    {/* Origin */}
                    <div className="space-y-2">
                      <Label htmlFor="origin" className="text-white text-sm">
                        Header Origin
                      </Label>
                      <Input
                        id="origin"
                        value={origin}
                        onChange={(e) => setOrigin(e.target.value)}
                        placeholder="https://example.com"
                        disabled={isDownloading}
                        className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
                      />
                    </div>

                    {/* Cookies File */}
                    <div className="space-y-2">
                      <Label htmlFor="cookies" className="text-white text-sm">
                        Arquivo de Cookies
                      </Label>
                      <Input
                        id="cookies"
                        value={cookiesFile}
                        onChange={(e) => setCookiesFile(e.target.value)}
                        placeholder="./cookies.txt"
                        disabled={isDownloading}
                        className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
                      />
                    </div>
                  </div>

                  {/* Switches */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-white/10">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                      <Label htmlFor="subs" className="text-white">
                        Baixar Legendas
                      </Label>
                      <Switch
                        id="subs"
                        checked={subs}
                        onCheckedChange={setSubs}
                        disabled={isDownloading}
                      />
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                      <Label htmlFor="autoSubs" className="text-white">
                        Legendas Automaticas
                      </Label>
                      <Switch
                        id="autoSubs"
                        checked={autoSubs}
                        onCheckedChange={setAutoSubs}
                        disabled={isDownloading}
                      />
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                      <Label htmlFor="thumbnails" className="text-white">
                        Baixar Miniaturas
                      </Label>
                      <Switch
                        id="thumbnails"
                        checked={thumbnails}
                        onCheckedChange={setThumbnails}
                        disabled={isDownloading}
                      />
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                      <Label htmlFor="audioOnly" className="text-white">
                        Apenas Audio (MP3)
                      </Label>
                      <Switch
                        id="audioOnly"
                        checked={audioOnly}
                        onCheckedChange={setAudioOnly}
                        disabled={isDownloading}
                      />
                    </div>
                  </div>

                  {/* Anti-Ban Settings */}
                  <div className="space-y-4 pt-4 border-t border-white/10">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="icon-glow-yellow p-2">
                        <Shield className="h-4 w-4 text-yellow" />
                      </div>
                      <div>
                        <Label className="text-base font-semibold text-white">
                          Protecao Anti-Ban
                        </Label>
                        <p className="text-sm text-muted-foreground">
                          Evite bloqueios ao baixar playlists grandes
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Delay Between Downloads */}
                      <div className="space-y-2">
                        <Label
                          htmlFor="delayBetweenDownloads"
                          className="text-white text-sm"
                        >
                          Delay Entre Videos (segundos)
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
                          className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
                        />
                        <p className="text-xs text-muted-foreground">
                          Pausa entre cada video (recomendado: 2-5s)
                        </p>
                      </div>

                      {/* Batch Size */}
                      <div className="space-y-2">
                        <Label
                          htmlFor="batchSize"
                          className="text-white text-sm"
                        >
                          Videos por Batch
                        </Label>
                        <Input
                          id="batchSize"
                          type="number"
                          min="1"
                          value={batchSize}
                          onChange={(e) => setBatchSize(e.target.value)}
                          placeholder="Desabilitado"
                          disabled={isDownloading}
                          className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
                        />
                        <p className="text-xs text-muted-foreground">
                          Agrupar downloads em batches (ex: 5)
                        </p>
                      </div>

                      {/* Batch Delay */}
                      <div className="space-y-2">
                        <Label
                          htmlFor="batchDelay"
                          className="text-white text-sm"
                        >
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
                          className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
                        />
                        <p className="text-xs text-muted-foreground">
                          Pausa maior entre grupos (recomendado: 10-30s)
                        </p>
                      </div>

                      {/* Randomize Delay */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between p-3 rounded-lg bg-white/5 h-10">
                          <Label
                            htmlFor="randomizeDelay"
                            className="text-white"
                          >
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
                    <div className="flex gap-2 flex-wrap pt-2">
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
                        className="bg-white/5 border-white/10 hover:bg-white/10 hover:border-teal/30 text-white"
                      >
                        <Shield className="h-3 w-3 mr-1 text-teal" />
                        Seguro
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
                        className="bg-white/5 border-white/10 hover:bg-white/10 hover:border-yellow/30 text-white"
                      >
                        <Settings2 className="h-3 w-3 mr-1 text-yellow" />
                        Moderado
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
                        className="bg-white/5 border-white/10 hover:bg-white/10 hover:border-purple/30 text-white"
                      >
                        <Download className="h-3 w-3 mr-1 text-purple" />
                        Rapido
                      </Button>
                    </div>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </div>
    </div>
  );
}
