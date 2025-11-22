"use client";

import { useState, useEffect } from "react";
import DriveAuth from "@/components/drive-auth";
import DriveVideoGrid from "@/components/drive-video-grid";
import SyncPanel from "@/components/sync-panel";

export default function DrivePage() {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  const apiUrl =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      : "http://localhost:8000";

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/drive/auth-status`);
      const data = await response.json();
      setAuthenticated(data.authenticated);
    } catch (error) {
      console.error("Erro ao verificar autenticação:", error);
    } finally {
      setLoading(false);
    }
  };

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
