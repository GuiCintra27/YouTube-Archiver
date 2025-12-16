"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";

// Chave do localStorage
const VOLUME_STORAGE_KEY = "yt-archiver-volume";
const MUTED_STORAGE_KEY = "yt-archiver-muted";

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
  // Volume persistente
  volume: number;
  isMuted: boolean;
  setVolume: (value: number) => void;
  setMuted: (value: boolean) => void;
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

  // Volume state - inicializa com valor padrão, carrega do localStorage no useEffect
  const [volume, setVolumeState] = useState(1);
  const [isMuted, setMutedState] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  // Carregar volume do localStorage na montagem (client-side only)
  useEffect(() => {
    try {
      const savedVolume = localStorage.getItem(VOLUME_STORAGE_KEY);
      const savedMuted = localStorage.getItem(MUTED_STORAGE_KEY);

      if (savedVolume !== null) {
        const parsed = parseFloat(savedVolume);
        if (!isNaN(parsed) && parsed >= 0 && parsed <= 1) {
          setVolumeState(parsed);
        }
      }

      if (savedMuted !== null) {
        setMutedState(savedMuted === "true");
      }
    } catch (error) {
      console.warn("Failed to load volume from localStorage:", error);
    }
    setIsHydrated(true);
  }, []);

  // Função para atualizar volume (salva no localStorage)
  const setVolume = useCallback((value: number) => {
    const clampedValue = Math.max(0, Math.min(1, value));
    setVolumeState(clampedValue);
    try {
      localStorage.setItem(VOLUME_STORAGE_KEY, clampedValue.toString());
    } catch (error) {
      console.warn("Failed to save volume to localStorage:", error);
    }
  }, []);

  // Função para atualizar muted (salva no localStorage)
  const setMuted = useCallback((value: boolean) => {
    setMutedState(value);
    try {
      localStorage.setItem(MUTED_STORAGE_KEY, value.toString());
    } catch (error) {
      console.warn("Failed to save muted state to localStorage:", error);
    }
  }, []);

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

  // Retorna null até hidratar para evitar mismatch de SSR
  // Na verdade, melhor retornar os filhos com valores padrão
  // O volume será aplicado corretamente após hidratação

  return (
    <GlobalPlayerContext.Provider
      value={{
        video,
        source,
        isActive,
        startTime,
        volume: isHydrated ? volume : 1,
        isMuted: isHydrated ? isMuted : false,
        setVolume,
        setMuted,
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
