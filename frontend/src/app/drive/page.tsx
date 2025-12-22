"use client";

import { useState, useEffect, useCallback } from "react";
import { Cloud, Loader2, Upload, Download, FolderSync, Shield } from "lucide-react";
import DriveAuth from "@/components/drive/drive-auth";
import DriveVideoGrid from "@/components/drive/drive-video-grid";
import SyncPanel from "@/components/drive/sync-panel";
import { APIURLS } from "@/lib/api-urls";
import { useApiUrl } from "@/hooks/use-api-url";

export default function DrivePage() {
  const apiUrl = useApiUrl();
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  const checkAuthStatus = useCallback(async () => {
    if (!apiUrl) return;
    try {
      const response = await fetch(
        `${apiUrl}/api/${APIURLS.DRIVE_AUTH_STATUS}`
      );
      const data = await response.json();
      setAuthenticated(data.authenticated);
    } catch (error) {
      console.error("Erro ao verificar autenticação:", error);
    } finally {
      setLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-cyan/10 flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-cyan" />
          </div>
          <p className="text-sm text-muted-foreground">Verificando autenticação...</p>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return <DriveAuth onAuthenticated={() => setAuthenticated(true)} />;
  }

  return (
    <div className="space-y-10">
      {/* Hero Section */}
      <section className="relative max-w-3xl mx-auto">
        {/* Watermark */}
        <div className="absolute -top-4 left-0 right-0 flex justify-center pointer-events-none select-none overflow-hidden">
          <span className="watermark text-[6rem] md:text-[8rem] font-bold">
            DRIVE
          </span>
        </div>

        <div className="relative z-10 text-center space-y-4 pt-4">
          {/* Icon */}
          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-cyan/20 blur-xl rounded-full" />
              <div className="relative w-14 h-14 rounded-xl bg-gradient-to-br from-cyan to-teal flex items-center justify-center">
                <Cloud className="h-7 w-7 text-navy-dark" />
              </div>
            </div>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <h1 className="text-3xl md:text-4xl font-bold text-white">
              Google{" "}
              <span className="bg-gradient-to-r from-cyan to-teal bg-clip-text text-transparent">
                Drive
              </span>
            </h1>
            <p className="text-base text-muted-foreground max-w-xl mx-auto">
              Sincronize e gerencie seus vídeos entre armazenamento local e Google Drive.
            </p>
          </div>

          {/* Feature Pills */}
          <div className="flex flex-wrap justify-center gap-2 pt-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <Upload className="h-3.5 w-3.5 text-cyan" />
              <span className="text-white">Upload</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <Download className="h-3.5 w-3.5 text-teal" />
              <span className="text-white">Download</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <FolderSync className="h-3.5 w-3.5 text-purple" />
              <span className="text-white">Sync</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <Shield className="h-3.5 w-3.5 text-yellow" />
              <span className="text-white">OAuth 2.0</span>
            </div>
          </div>
        </div>
      </section>

      {/* Sync Panel */}
      <section className="max-w-5xl mx-auto">
        <SyncPanel />
      </section>

      {/* Drive Videos */}
      <section className="max-w-[90rem] mx-auto">
        <DriveVideoGrid />
      </section>
    </div>
  );
}
