"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Download,
  MonitorPlay,
  RefreshCw,
  Save,
  StopCircle,
  Play,
  Volume2,
  Mic,
  FileVideo,
  AlertCircle,
  CheckCircle2,
  Info,
  Eye,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { APIURLS } from "@/lib/api-urls";

interface ScreenRecorderProps {
  onSaveToLibrary?: () => void;
}

enum RecorderState {
  IDLE = "idle",
  RECORDING = "recording",
  READY = "ready",
}

const getApiUrl = () => {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
  return "http://localhost:8000";
};

const defaultFileName = () => {
  const now = new Date();
  const formatted = now.toISOString().replace(/[:.]/g, "-");
  return `gravacao-${formatted}.webm`;
};

const sanitizeFileName = (name: string) => {
  const trimmed = name.trim() || defaultFileName();
  const safe = trimmed.replace(/[<>:"/\\|?*\x00-\x1F]/g, "").slice(0, 120);
  if (safe.toLowerCase().endsWith(".webm")) {
    return safe;
  }
  return `${safe}.webm`;
};

export default function ScreenRecorder({
  onSaveToLibrary,
}: ScreenRecorderProps) {
  const [state, setState] = useState<RecorderState>(RecorderState.IDLE);
  const [apiUrl, setApiUrl] = useState("");
  const [fileName, setFileName] = useState(defaultFileName);
  const [captureSystemAudio, setCaptureSystemAudio] = useState(false);
  const [captureMicrophone, setCaptureMicrophone] = useState(false);
  const [isLinux, setIsLinux] = useState(false);
  const [saveToLibrary, setSaveToLibrary] = useState(true);
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [blobSize, setBlobSize] = useState<number | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const recordedBlobRef = useRef<Blob | null>(null);

  useEffect(() => {
    setApiUrl(getApiUrl());
    // Detectar se é Linux
    if (typeof navigator !== "undefined") {
      setIsLinux(navigator.platform.toLowerCase().includes("linux"));
    }
  }, []);

  useEffect(() => {
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
      micStreamRef.current?.getTracks().forEach((track) => track.stop());
      audioContextRef.current?.close();
    };
  }, [blobUrl]);

  const startRecording = async () => {
    setError("");
    setStatusMessage("");
    setUploadMessage("");

    if (typeof window === "undefined" || !navigator.mediaDevices) {
      setError("Gravação não suportada neste navegador.");
      return;
    }

    try {
      // Capturar tela (com ou sem áudio do sistema)
      const displayStream = await navigator.mediaDevices.getDisplayMedia({
        video: { frameRate: 30 },
        audio: captureSystemAudio
          ? {
              echoCancellation: false,
              noiseSuppression: false,
              autoGainControl: false,
            }
          : false,
      });

      streamRef.current = displayStream;

      // Capturar microfone se habilitado
      let micStream: MediaStream | null = null;
      if (captureMicrophone) {
        try {
          micStream = await navigator.mediaDevices.getUserMedia({
            audio: {
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
            },
            video: false,
          });
          micStreamRef.current = micStream;
        } catch (micErr) {
          console.warn("Não foi possível capturar microfone:", micErr);
          setStatusMessage(
            "Microfone não disponível, gravando apenas tela/sistema."
          );
        }
      }

      // Montar a stream final para gravação
      let finalStream: MediaStream;
      const videoTracks = displayStream.getVideoTracks();
      const systemAudioTracks = displayStream.getAudioTracks();
      const micAudioTracks = micStream?.getAudioTracks() || [];

      // Se temos múltiplas fontes de áudio, usar AudioContext para mixar
      if (systemAudioTracks.length > 0 && micAudioTracks.length > 0) {
        const audioContext = new AudioContext();
        audioContextRef.current = audioContext;

        const destination = audioContext.createMediaStreamDestination();

        // Conectar áudio do sistema
        const systemSource = audioContext.createMediaStreamSource(
          new MediaStream(systemAudioTracks)
        );
        systemSource.connect(destination);

        // Conectar áudio do microfone
        const micSource = audioContext.createMediaStreamSource(
          new MediaStream(micAudioTracks)
        );
        micSource.connect(destination);

        // Criar stream final com vídeo + áudio mixado
        finalStream = new MediaStream([
          ...videoTracks,
          ...destination.stream.getAudioTracks(),
        ]);
      } else {
        // Apenas uma fonte de áudio (ou nenhuma)
        finalStream = new MediaStream([
          ...videoTracks,
          ...systemAudioTracks,
          ...micAudioTracks,
        ]);
      }

      // Configurar MediaRecorder
      const mimeType = MediaRecorder.isTypeSupported("video/webm;codecs=vp9")
        ? "video/webm;codecs=vp9"
        : "video/webm";

      const recorder = new MediaRecorder(finalStream, { mimeType });

      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
        recordedBlobRef.current = blob;
        setBlobSize(blob.size);
        const url = URL.createObjectURL(blob);
        setBlobUrl(url);
        setState(RecorderState.READY);
        setStatusMessage(
          "Gravação finalizada. Baixe ou envie para a biblioteca."
        );

        // Fechar AudioContext se existir
        audioContextRef.current?.close();
        audioContextRef.current = null;
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setState(RecorderState.RECORDING);

      // Mensagem de status baseada nas fontes de áudio
      const audioSources = [];
      if (systemAudioTracks.length > 0) audioSources.push("sistema");
      if (micAudioTracks.length > 0) audioSources.push("microfone");
      const audioInfo =
        audioSources.length > 0
          ? ` (áudio: ${audioSources.join(" + ")})`
          : " (sem áudio)";
      setStatusMessage(`Gravando${audioInfo}... clique em Parar quando concluir.`);
    } catch (err) {
      console.error("Erro ao iniciar gravação", err);
      setError(
        "Não foi possível iniciar a captura de tela (permissão ou suporte)."
      );
    }
  };

  const stopRecording = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state === "recording"
    ) {
      mediaRecorderRef.current.stop();
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    micStreamRef.current?.getTracks().forEach((track) => track.stop());
  };

  const downloadRecording = () => {
    if (!recordedBlobRef.current || !blobUrl) {
      setError("Nenhuma gravação pronta para download.");
      return;
    }

    const safeName = sanitizeFileName(fileName);
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = safeName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setStatusMessage("Download iniciado no navegador.");
  };

  const saveRecordingToLibrary = async () => {
    if (!recordedBlobRef.current) {
      setError("Grave algo antes de salvar na biblioteca.");
      return;
    }

    if (!apiUrl) {
      setError(
        "API não configurada. Verifique a variável NEXT_PUBLIC_API_URL."
      );
      return;
    }

    setUploading(true);
    setError("");
    setUploadMessage("");

    try {
      const formData = new FormData();
      const safeName = sanitizeFileName(fileName);
      formData.append("file", recordedBlobRef.current, safeName);

      const response = await fetch(
        `${apiUrl}/api/${APIURLS.RECORDINGS_UPLOAD}`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Falha ao salvar gravação");
      }

      const data = await response.json();
      setUploadMessage(`Cópia salva em ${data.path}`);
      onSaveToLibrary?.();
    } catch (err) {
      console.error("Erro ao salvar gravação", err);
      setError("Não foi possível salvar a gravação no servidor.");
    } finally {
      setUploading(false);
    }
  };

  const resetRecorder = () => {
    setState(RecorderState.IDLE);
    setStatusMessage("");
    setError("");
    setUploadMessage("");
    setPreviewOpen(false);
    setBlobUrl(null);
    setBlobSize(null);
    recordedBlobRef.current = null;
    chunksRef.current = [];
    micStreamRef.current = null;
    audioContextRef.current = null;
    setFileName(defaultFileName());
  };

  const actionsDisabled = state === "recording" && uploading;

  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="icon-glow-purple p-2">
            <MonitorPlay className="h-5 w-5 text-purple" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Gravador de Tela</h3>
            <p className="text-sm text-muted-foreground">
              Capture a tela pelo navegador com áudio do sistema e/ou microfone
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-5 space-y-5">
        {/* Status Messages */}
        {(error || uploadMessage || statusMessage) && (
          <Alert
            className={`${
              error
                ? "bg-red-500/10 border-red-500/20 text-red-400"
                : uploadMessage
                ? "bg-teal/10 border-teal/20 text-teal"
                : "bg-purple/10 border-purple/20 text-purple-light"
            }`}
          >
            <div className="flex items-center gap-2">
              {error ? (
                <AlertCircle className="h-4 w-4" />
              ) : uploadMessage ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <Info className="h-4 w-4" />
              )}
              <AlertDescription className="text-sm">
                {error || uploadMessage || statusMessage}
                {blobSize
                  ? ` • Tamanho: ${(blobSize / (1024 * 1024)).toFixed(1)} MB`
                  : ""}
              </AlertDescription>
            </div>
          </Alert>
        )}

        {/* Recording Indicator */}
        {state === "recording" && (
          <div className="flex items-center justify-center gap-2 py-3">
            <div className="relative">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
              <div className="absolute inset-0 w-3 h-3 bg-red-500 rounded-full animate-ping" />
            </div>
            <span className="text-base font-medium text-red-400">Gravando...</span>
          </div>
        )}

        {/* Settings */}
        <div className="space-y-4">
          {/* File Name */}
          <div className="space-y-2">
            <Label htmlFor="fileName" className="text-white flex items-center gap-2">
              <FileVideo className="h-4 w-4 text-muted-foreground" />
              Nome do arquivo
            </Label>
            <Input
              id="fileName"
              value={fileName}
              onChange={(e) => setFileName(e.target.value)}
              placeholder="gravacao.webm"
              disabled={state === "recording"}
              className="glass-input bg-white/5 border-white/10 text-white placeholder:text-muted-foreground"
            />
          </div>

          {/* Audio Toggles */}
          <div className="grid gap-3 sm:grid-cols-2">
            {/* System Audio Toggle */}
            <div className="glass rounded-xl p-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-teal/10 flex items-center justify-center">
                  <Volume2 className="h-4 w-4 text-teal" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">Áudio do sistema</p>
                  <p className="text-xs text-muted-foreground">Som da aba/desktop</p>
                </div>
              </div>
              <Switch
                checked={captureSystemAudio}
                onCheckedChange={setCaptureSystemAudio}
                disabled={state === "recording"}
                className="data-[state=checked]:bg-teal"
              />
            </div>

            {/* Microphone Toggle */}
            <div className="glass rounded-xl p-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-purple/10 flex items-center justify-center">
                  <Mic className="h-4 w-4 text-purple" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">Microfone</p>
                  <p className="text-xs text-muted-foreground">Gravar sua voz</p>
                </div>
              </div>
              <Switch
                checked={captureMicrophone}
                onCheckedChange={setCaptureMicrophone}
                disabled={state === "recording"}
                className="data-[state=checked]:bg-purple"
              />
            </div>
          </div>
        </div>

        {/* Linux Warning */}
        {isLinux && captureSystemAudio && state !== "recording" && (
          <Alert className="bg-yellow/10 border-yellow/20">
            <AlertCircle className="h-4 w-4 text-yellow" />
            <AlertDescription className="text-yellow-light text-sm">
              <strong>Linux:</strong> A captura de áudio do sistema pode não
              funcionar. Ao compartilhar, selecione uma{" "}
              <strong>&quot;Aba do Chrome&quot;</strong> (não janela/tela) e
              marque <strong>&quot;Compartilhar áudio&quot;</strong>.
            </AlertDescription>
          </Alert>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          {state !== "recording" && state !== "ready" && (
            <Button
              onClick={startRecording}
              className="btn-gradient-purple gap-2"
            >
              <Play className="h-4 w-4" />
              Iniciar gravação
            </Button>
          )}

          {state === "recording" && (
            <Button
              onClick={stopRecording}
              className="bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30 gap-2"
            >
              <StopCircle className="h-4 w-4" />
              Parar gravação
            </Button>
          )}

          {state === "ready" && (
            <>
              <Button
                onClick={downloadRecording}
                disabled={actionsDisabled}
                className="btn-gradient-teal gap-1.5"
                size="sm"
              >
                <Download className="h-3.5 w-3.5" />
                Baixar
              </Button>

              <Button
                onClick={() => setPreviewOpen(true)}
                disabled={!blobUrl}
                variant="outline"
                className="bg-white/5 border-white/10 text-white hover:bg-white/10 gap-1.5"
                size="sm"
              >
                <Eye className="h-3.5 w-3.5" />
                Visualizar
              </Button>

              <div className="flex items-center gap-2 px-3 py-1.5 glass rounded-lg">
                <Switch
                  checked={saveToLibrary}
                  onCheckedChange={setSaveToLibrary}
                  id="saveToLibrary"
                  className="data-[state=checked]:bg-yellow scale-90"
                />
                <Label htmlFor="saveToLibrary" className="text-xs text-white cursor-pointer">
                  Salvar na biblioteca
                </Label>
              </div>

              <Button
                onClick={saveRecordingToLibrary}
                disabled={!saveToLibrary || uploading}
                className="btn-gradient-yellow gap-1.5"
                size="sm"
              >
                {uploading ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Save className="h-3.5 w-3.5" />
                )}
                Enviar
              </Button>

              <Button
                onClick={resetRecorder}
                variant="ghost"
                className="text-muted-foreground hover:text-white hover:bg-white/10"
                size="sm"
              >
                Resetar
              </Button>
            </>
          )}
        </div>

        {/* Tips */}
        <div className="glass rounded-lg p-3">
          <p className="text-xs text-muted-foreground">
            <span className="text-teal font-medium">Dica:</span> Para capturar áudio do sistema, marque
            &quot;Compartilhar áudio&quot; no diálogo do navegador ao selecionar a
            aba/janela. Se habilitar ambas as fontes (sistema + microfone), os
            áudios serão mixados automaticamente.
          </p>
        </div>
      </div>

      {/* Preview Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-4xl glass border-white/10">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Eye className="h-5 w-5 text-purple" />
              Pré-visualização
            </DialogTitle>
          </DialogHeader>
          {blobUrl ? (
            <div className="rounded-xl overflow-hidden bg-black">
              <video
                key={blobUrl}
                src={blobUrl}
                controls
                className="w-full h-auto"
              />
            </div>
          ) : (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <p className="text-sm">Nenhuma gravação disponível.</p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
