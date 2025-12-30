"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Cloud, Loader2, ShieldAlert, Shield, Link } from "lucide-react";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";

interface DriveAuthProps {
  onAuthenticated: () => void;
}

export default function DriveAuth({ onAuthenticated }: DriveAuthProps) {
  const apiUrl = useApiUrl();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAuth = useCallback(async () => {
    if (!apiUrl) return;
    try {
      setLoading(true);
      setError(null);

      // Obter URL de autenticação
      const response = await fetch(`${apiUrl}/api/${APIURLS.DRIVE_AUTH_URL}`);
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
        throw new Error(
          "Popup bloqueado. Por favor, habilite popups para este site."
        );
      }

      // Monitorar callback
      const checkInterval = setInterval(async () => {
        try {
          // Verificar se o popup foi fechado pelo usuário
          if (popup.closed) {
            clearInterval(checkInterval);
            setLoading(false);
            return;
          }

          // Verificar se autenticação foi concluída
          const statusResponse = await fetch(
            `${apiUrl}/api/${APIURLS.DRIVE_AUTH_STATUS}`
          );
          const statusData = await statusResponse.json();

          if (statusData.authenticated) {
            clearInterval(checkInterval);
            popup.close();
            setLoading(false);
            onAuthenticated();
          }
        } catch {
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
  }, [apiUrl, onAuthenticated]);

  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="glass-card rounded-2xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-white/10 text-center">
          <div className="flex justify-center mb-4">
            <div className="relative">
              <div className="absolute inset-0 bg-cyan/20 blur-xl rounded-full" />
              <div className="relative w-16 h-16 rounded-xl bg-gradient-to-br from-cyan to-teal flex items-center justify-center">
                <Cloud className="h-8 w-8 text-navy-dark" />
              </div>
            </div>
          </div>
          <h2 className="text-xl font-bold text-white">Conectar ao Google Drive</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Autentique-se para visualizar e gerenciar seus vídeos no Google Drive
          </p>
        </div>

        {/* Content */}
        <div className="px-6 py-5 space-y-4">
          {error && (
            <Alert className="bg-red-500/10 border-red-500/20">
              <ShieldAlert className="h-4 w-4 text-red-400" />
              <AlertDescription className="text-red-400">{error}</AlertDescription>
            </Alert>
          )}

          <Button
            onClick={handleAuth}
            disabled={loading}
            className="w-full btn-gradient-cyan"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Autenticando...
              </>
            ) : (
              <>
                <Link className="mr-2 h-4 w-4" />
                Conectar com Google Drive
              </>
            )}
          </Button>

          {/* Info */}
          <div className="space-y-3 pt-2">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-white/5">
              <Shield className="h-4 w-4 text-cyan mt-0.5" />
              <p className="text-xs text-muted-foreground">
                Ao conectar, você será redirecionado para o Google para autorizar
                o acesso ao Drive.
              </p>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-lg bg-yellow/5 border border-yellow/20">
              <ShieldAlert className="h-4 w-4 text-yellow mt-0.5" />
              <p className="text-xs text-yellow/80">
                Certifique-se de que o arquivo <code className="text-yellow">credentials.json</code> está
                configurado no backend.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
