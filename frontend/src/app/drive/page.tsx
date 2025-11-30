"use client";

import { useState, useEffect, useCallback } from "react";
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!authenticated) {
    return <DriveAuth onAuthenticated={() => setAuthenticated(true)} />;
  }

  return (
    <div className="space-y-8">
      {/* Sync Panel */}
      <SyncPanel />

      {/* Drive Videos */}
      <DriveVideoGrid />
    </div>
  );
}
