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
  const [captureAudio, setCaptureAudio] = useState(true);
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
  const chunksRef = useRef<Blob[]>([]);
  const recordedBlobRef = useRef<Blob | null>(null);

  useEffect(() => {
    setApiUrl(getApiUrl());
  }, []);

  useEffect(() => {
    return () => {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
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
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: { frameRate: 30 },
        audio: captureAudio,
      });

      const recorder = new MediaRecorder(stream, {
        mimeType: "video/webm;codecs=vp9",
      });

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
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      streamRef.current = stream;
      setState(RecorderState.RECORDING);
      setStatusMessage("Gravando... clique em Parar quando concluir.");
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
          Capture a tela pelo navegador. Baixe o arquivo e, opcionalmente, salve
          uma cópia na pasta de vídeos do app.
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

        <div className="grid gap-4 md:grid-cols-3">
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
              <p className="text-sm font-medium">Capturar áudio</p>
              <p className="text-xs text-muted-foreground">
                Inclui áudio compartilhado pela aba/desktop
              </p>
            </div>
            <Switch
              checked={captureAudio}
              onCheckedChange={setCaptureAudio}
              disabled={state === "recording"}
            />
          </div>
        </div>

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
          Observações: o navegador sempre abre o diálogo padrão para salvar
          localmente; a pasta do app recebe cópias via upload (webm). Durante a
          captura, finalize a seleção de janela/aba para que a gravação inicie.
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
