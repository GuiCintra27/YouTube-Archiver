"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

// Interface para vídeo no player global
export interface GlobalPlayerVideo {
  id: string;
  title: string;
  subtitle: string; // channel ou path
  path: string;
  thumbnail?: string;
  size: number;
}

// Interface do contexto
interface GlobalPlayerContextType {
  video: GlobalPlayerVideo | null;
  source: "local" | "drive";
  isActive: boolean;
  startTime: number;
  playVideo: (
    video: GlobalPlayerVideo,
    source: "local" | "drive",
    startTime?: number
  ) => void;
  stopVideo: () => void;
}

// Criar contexto com valor padrão
const GlobalPlayerContext = createContext<GlobalPlayerContextType | null>(null);

// Provider
export function GlobalPlayerProvider({ children }: { children: ReactNode }) {
  const [video, setVideo] = useState<GlobalPlayerVideo | null>(null);
  const [source, setSource] = useState<"local" | "drive">("local");
  const [isActive, setIsActive] = useState(false);
  const [startTime, setStartTime] = useState(0);

  const playVideo = useCallback(
    (
      newVideo: GlobalPlayerVideo,
      newSource: "local" | "drive",
      time: number = 0
    ) => {
      setVideo(newVideo);
      setSource(newSource);
      setStartTime(time);
      setIsActive(true);
    },
    []
  );

  const stopVideo = useCallback(() => {
    setIsActive(false);
    setVideo(null);
    setStartTime(0);
  }, []);

  return (
    <GlobalPlayerContext.Provider
      value={{
        video,
        source,
        isActive,
        startTime,
        playVideo,
        stopVideo,
      }}
    >
      {children}
    </GlobalPlayerContext.Provider>
  );
}

// Hook para usar o contexto
export function useGlobalPlayer() {
  const context = useContext(GlobalPlayerContext);
  if (!context) {
    throw new Error("useGlobalPlayer must be used within a GlobalPlayerProvider");
  }
  return context;
}
