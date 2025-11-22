"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Cloud, Loader2, ShieldAlert } from "lucide-react";

interface DriveAuthProps {
  onAuthenticated: () => void;
}

export default function DriveAuth({ onAuthenticated }: DriveAuthProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiUrl =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      : "http://localhost:8000";

  const handleAuth = async () => {
    try {
      setLoading(true);
      setError(null);

      // Obter URL de autenticação
      const response = await fetch(`${apiUrl}/api/drive/auth-url`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Erro ao obter URL de autenticação");
      }

      // Abrir popup de autenticação
      const width = 600;
      const height = 700;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;

      const popup = window.open(
        data.auth_url,
        "Google Drive Auth",
        `width=${width},height=${height},left=${left},top=${top}`
      );

      if (!popup) {
        throw new Error("Popup bloqueado. Por favor, habilite popups para este site.");
      }

      // Monitorar callback
      const checkInterval = setInterval(async () => {
        try {
          // Verificar se autenticação foi concluída
          const statusResponse = await fetch(`${apiUrl}/api/drive/auth-status`);
          const statusData = await statusResponse.json();

          if (statusData.authenticated) {
            clearInterval(checkInterval);
            popup.close();
            onAuthenticated();
          }
        } catch (err) {
          // Continuar checando
        }
      }, 1000);

      // Cleanup após 5 minutos
      setTimeout(() => {
        clearInterval(checkInterval);
        if (popup && !popup.closed) {
          popup.close();
          setError("Tempo de autenticação esgotado");
        }
        setLoading(false);
      }, 5 * 60 * 1000);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[500px]">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
            <Cloud className="h-8 w-8 text-primary" />
          </div>
          <CardTitle>Conectar ao Google Drive</CardTitle>
          <CardDescription>
            Autentique-se para visualizar e gerenciar seus vídeos no Google Drive
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <ShieldAlert className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button
            onClick={handleAuth}
            disabled={loading}
            className="w-full"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Autenticando...
              </>
            ) : (
              <>
                <Cloud className="mr-2 h-4 w-4" />
                Conectar com Google Drive
              </>
            )}
          </Button>

          <div className="text-xs text-muted-foreground text-center space-y-2">
            <p>
              Ao conectar, você será redirecionado para o Google para autorizar o acesso ao Drive.
            </p>
            <p className="font-medium">
              ⚠️ Certifique-se de que o arquivo credentials.json está configurado no backend.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
