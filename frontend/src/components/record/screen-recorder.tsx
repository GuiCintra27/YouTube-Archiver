"use client";

import { useEffect, useRef, useState } from "react";
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
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Download,
  MonitorDown,
  RefreshCw,
  Save,
  StopCircle,
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
  const safe = trimmed.replace(/[<>:\"/\\|?*\x00-\x1F]/g, "").slice(0, 120);
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
    <Card className="border-primary/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MonitorDown className="h-5 w-5 text-primary" />
          Gravar tela
        </CardTitle>
        <CardDescription>
          Capture a tela pelo navegador com áudio do sistema e/ou microfone.
          Baixe o arquivo e, opcionalmente, salve uma cópia na pasta de vídeos.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {(error || uploadMessage || statusMessage) && (
          <Alert variant={error ? "destructive" : "default"}>
            <AlertDescription>
              {error || uploadMessage || statusMessage}
              {blobSize
                ? ` • Tamanho: ${(blobSize / (1024 * 1024)).toFixed(1)} MB`
                : ""}
            </AlertDescription>
          </Alert>
        )}

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-2">
            <Label htmlFor="fileName">Nome do arquivo</Label>
            <Input
              id="fileName"
              value={fileName}
              onChange={(e) => setFileName(e.target.value)}
              placeholder="gravacao.webm"
              disabled={state === "recording"}
            />
          </div>

          <div className="flex items-center justify-between rounded-md border px-4 py-3">
            <div>
              <p className="text-sm font-medium">Áudio do sistema</p>
              <p className="text-xs text-muted-foreground">
                Som da aba/desktop
              </p>
            </div>
            <Switch
              checked={captureSystemAudio}
              onCheckedChange={setCaptureSystemAudio}
              disabled={state === "recording"}
            />
          </div>

          <div className="flex items-center justify-between rounded-md border px-4 py-3">
            <div>
              <p className="text-sm font-medium">Microfone</p>
              <p className="text-xs text-muted-foreground">
                Gravar sua voz
              </p>
            </div>
            <Switch
              checked={captureMicrophone}
              onCheckedChange={setCaptureMicrophone}
              disabled={state === "recording"}
            />
          </div>
        </div>

        {isLinux && captureSystemAudio && state !== "recording" && (
          <Alert>
            <AlertDescription>
              <strong>Linux:</strong> A captura de áudio do sistema pode não
              funcionar. Ao compartilhar, selecione uma{" "}
              <strong>&quot;Aba do Chrome&quot;</strong> (não janela/tela) e
              marque <strong>&quot;Compartilhar áudio&quot;</strong>.
            </AlertDescription>
          </Alert>
        )}

        <div className="flex flex-wrap gap-3">
          {state !== "recording" && (
            <Button
              onClick={startRecording}
              disabled={state.toString() === RecorderState.RECORDING}
            >
              <MonitorDown className="mr-2 h-4 w-4" />
              Iniciar gravação
            </Button>
          )}

          {state === "recording" && (
            <Button variant="destructive" onClick={stopRecording}>
              <StopCircle className="mr-2 h-4 w-4" />
              Parar gravação
            </Button>
          )}

          {state === "ready" && (
            <>
              <Button
                variant="secondary"
                onClick={downloadRecording}
                disabled={actionsDisabled}
              >
                <Download className="mr-2 h-4 w-4" />
                Baixar
              </Button>
              <Button
                variant="outline"
                onClick={() => setPreviewOpen(true)}
                disabled={!blobUrl}
              >
                Visualizar vídeo
              </Button>
              <div className="flex items-center gap-2">
                <Switch
                  checked={saveToLibrary}
                  onCheckedChange={setSaveToLibrary}
                  id="saveToLibrary"
                />
                <Label htmlFor="saveToLibrary" className="text-sm">
                  Salvar cópia na pasta de downloads
                </Label>
              </div>
              <Button
                onClick={saveRecordingToLibrary}
                disabled={!saveToLibrary || uploading}
                variant="default"
              >
                {uploading ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                Enviar para a biblioteca
              </Button>
              <Button variant="ghost" onClick={resetRecorder}>
                Resetar
              </Button>
            </>
          )}
        </div>

        <p className="text-sm text-muted-foreground">
          <strong>Dica:</strong> Para capturar áudio do sistema, marque
          &quot;Compartilhar áudio&quot; no diálogo do navegador ao selecionar a
          aba/janela. Se habilitar ambas as fontes (sistema + microfone), os
          áudios serão mixados automaticamente.
        </p>
      </CardContent>

      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Pré-visualização</DialogTitle>
          </DialogHeader>
          {blobUrl ? (
            <video
              key={blobUrl}
              src={blobUrl}
              controls
              className="w-full h-auto rounded-lg"
            />
          ) : (
            <p className="text-sm text-muted-foreground">
              Nenhuma gravação disponível.
            </p>
          )}
        </DialogContent>
      </Dialog>
    </Card>
  );
}
