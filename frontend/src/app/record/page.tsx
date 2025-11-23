"use client";

import { useState } from "react";
import ScreenRecorder from "@/components/record/screen-recorder";
import RecentVideos from "@/components/common/videos/recent-videos";

export default function RecordPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Gravar tela</h2>
        <p className="text-muted-foreground max-w-2xl mx-auto">
          Capture a tela diretamente no navegador. Baixe o arquivo e salve uma
          cópia na pasta de downloads para aparecer na biblioteca.
        </p>
      </div>

      <ScreenRecorder onSaveToLibrary={() => setRefreshKey((v) => v + 1)} />

      <div className="mt-4 pt-6 border-t">
        <RecentVideos
          title="Últimas gravações e downloads"
          refreshToken={refreshKey}
          ctaLabel="Abrir biblioteca"
        />
      </div>
    </div>
  );
}
