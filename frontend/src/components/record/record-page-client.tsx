"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { MonitorPlay, Video, Mic, HardDrive, Zap } from "lucide-react";
import RecentVideos from "@/components/common/videos/recent-videos";
import ScreenRecorderLoading from "@/components/record/screen-recorder-loading";

const ScreenRecorder = dynamic(
  () => import("@/components/record/screen-recorder"),
  {
    ssr: false,
    loading: () => <ScreenRecorderLoading />,
  }
);

type RecordPageClientProps = {
  initialRecentVideos?: {
    id: string;
    title: string;
    channel: string;
    path: string;
    thumbnail?: string;
    size: number;
    created_at: string;
    modified_at: string;
  }[];
};

export default function RecordPageClient({
  initialRecentVideos,
}: RecordPageClientProps) {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="space-y-10">
      {/* Hero Section */}
      <section className="relative max-w-3xl mx-auto">
        {/* Watermark */}
        <div className="absolute -top-4 left-0 right-0 flex justify-center pointer-events-none select-none overflow-hidden">
          <span className="watermark text-[6rem] md:text-[8rem] font-bold">
            RECORD
          </span>
        </div>

        <div className="relative z-10 text-center space-y-4 pt-4">
          {/* Icon */}
          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-purple/20 blur-xl rounded-full" />
              <div className="relative w-14 h-14 rounded-xl bg-gradient-to-br from-purple to-purple-light flex items-center justify-center">
                <MonitorPlay className="h-7 w-7 text-white" />
              </div>
            </div>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <h1 className="text-3xl md:text-4xl font-bold text-white">
              Gravar{" "}
              <span className="bg-gradient-to-r from-purple to-purple-light bg-clip-text text-transparent">
                Tela
              </span>
            </h1>
            <p className="text-base text-muted-foreground max-w-xl mx-auto">
              Capture sua tela diretamente no navegador com suporte a áudio do
              sistema e microfone.
            </p>
          </div>

          {/* Feature Pills */}
          <div className="flex flex-wrap justify-center gap-2 pt-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <Video className="h-3.5 w-3.5 text-purple" />
              <span className="text-white">HD Video</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <Mic className="h-3.5 w-3.5 text-teal" />
              <span className="text-white">Sistema + Mic</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <HardDrive className="h-3.5 w-3.5 text-yellow" />
              <span className="text-white">Salvar Local</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <Zap className="h-3.5 w-3.5 text-orange" />
              <span className="text-white">Sem Limite</span>
            </div>
          </div>
        </div>
      </section>

      {/* Recorder Section */}
      <section className="relative max-w-4xl mx-auto">
        <div className="absolute inset-0 bg-gradient-to-b from-purple/5 to-transparent rounded-3xl" />
        <ScreenRecorder onSaveToLibrary={() => setRefreshKey((v) => v + 1)} />
      </section>

      {/* Recent Videos Section */}
      <section className="relative max-w-[90rem] mx-auto">
        {/* Watermark */}
        <div className="absolute -top-2 left-0 right-0 flex justify-center pointer-events-none select-none overflow-hidden">
          <span className="watermark text-[5rem] md:text-[6rem] font-bold">
            LIBRARY
          </span>
        </div>

        <div className="relative z-10 pt-6">
          <RecentVideos
            title="Últimas gravações e downloads"
            refreshToken={refreshKey}
            ctaLabel="Abrir biblioteca"
            initialData={initialRecentVideos}
          />
        </div>
      </section>
    </div>
  );
}
