"use client";

import { useRef, useState, useEffect } from "react";
import { X, Play, Pause, PictureInPicture2, Loader2, Volume2, VolumeX } from "lucide-react";
import type { MediaPlayerInstance } from "@vidstack/react";
import { MediaPlayer, MediaProvider } from "@vidstack/react";
import { Button } from "@/components/ui/button";
import { useGlobalPlayer } from "@/contexts/global-player-context";
import { useApiUrl } from "@/hooks/use-api-url";
import { APIURLS } from "@/lib/api-urls";

export default function GlobalPlayer() {
  const apiUrl = useApiUrl();
  const { video, source, isActive, startTime, stopVideo } = useGlobalPlayer();
  const playerRef = useRef<MediaPlayerInstance>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [canPip, setCanPip] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);

  // Construir URL do stream
  const videoUrl =
    apiUrl && video
      ? source === "drive"
        ? `${apiUrl}/api/${APIURLS.DRIVE_STREAM}/${video.id}`
        : `${apiUrl}/api/videos/stream/${encodeURIComponent(video.path)}`
      : "";

  // Construir URL da thumbnail
  const thumbnailUrl =
    apiUrl && video?.thumbnail
      ? `${apiUrl}/api/videos/thumbnail/${encodeURIComponent(video.thumbnail)}`
      : null;

  // Verificar suporte a PiP
  useEffect(() => {
    setCanPip("pictureInPictureEnabled" in document);
  }, []);

  // Reset ready state quando trocar de vídeo
  useEffect(() => {
    setIsReady(false);
  }, [videoUrl]);

  // Iniciar reprodução e seek quando o player estiver pronto
  useEffect(() => {
    if (!playerRef.current || !videoUrl) return;

    const player = playerRef.current;

    const handleCanPlay = () => {
      setIsReady(true);
      // Seek para o tempo inicial
      if (startTime > 0) {
        player.currentTime = startTime;
      }
      // Forçar play (autoPlay pode falhar em alguns navegadores)
      player.play().catch((err) => {
        console.warn("AutoPlay blocked:", err);
      });
    };

    player.addEventListener("can-play", handleCanPlay, { once: true });

    return () => {
      player.removeEventListener("can-play", handleCanPlay);
    };
  }, [startTime, videoUrl]);

  const handlePlayPause = () => {
    if (!playerRef.current || !isReady) return;

    if (isPlaying) {
      playerRef.current.pause();
    } else {
      playerRef.current.play().catch((err) => {
        console.warn("Play failed:", err);
      });
    }
  };

  const handlePip = async () => {
    if (!playerRef.current || !isReady) return;

    try {
      await playerRef.current.enterPictureInPicture();
    } catch (error) {
      console.error("Failed to enter PiP:", error);
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (playerRef.current) {
      playerRef.current.volume = newVolume;
      if (newVolume > 0 && isMuted) {
        setIsMuted(false);
        playerRef.current.muted = false;
      }
    }
  };

  const handleMuteToggle = () => {
    if (!playerRef.current) return;
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    playerRef.current.muted = newMuted;
  };

  const handleClose = () => {
    if (playerRef.current) {
      playerRef.current.pause();
    }
    stopVideo();
  };

  // Não renderizar se não estiver ativo
  if (!isActive || !video) {
    return null;
  }

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 border-t">
      <div className="container mx-auto px-4">
        <div className="flex items-center gap-4 h-16">
          {/* Thumbnail */}
          <div className="relative h-12 w-12 flex-shrink-0 rounded overflow-hidden bg-muted">
            {thumbnailUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={thumbnailUrl}
                alt={video.title}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="h-full w-full flex items-center justify-center text-muted-foreground">
                <Play className="h-4 w-4" />
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{video.title}</p>
            <p className="text-xs text-muted-foreground truncate">
              {video.subtitle}
            </p>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-1">
            {/* Volume Control */}
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleMuteToggle}
                title={isMuted ? "Ativar som" : "Silenciar"}
                className="h-9 w-9"
              >
                {isMuted || volume === 0 ? (
                  <VolumeX className="h-4 w-4" />
                ) : (
                  <Volume2 className="h-4 w-4" />
                )}
              </Button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={isMuted ? 0 : volume}
                onChange={handleVolumeChange}
                className="w-20 h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                title={`Volume: ${Math.round((isMuted ? 0 : volume) * 100)}%`}
              />
            </div>

            {/* PiP Button */}
            {canPip && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handlePip}
                disabled={!isReady}
                title="Picture-in-Picture"
                className="h-9 w-9"
              >
                <PictureInPicture2 className="h-4 w-4" />
              </Button>
            )}

            {/* Play/Pause */}
            <Button
              variant="ghost"
              size="icon"
              onClick={handlePlayPause}
              disabled={!isReady}
              title={!isReady ? "Carregando..." : isPlaying ? "Pausar" : "Reproduzir"}
              className="h-9 w-9"
            >
              {!isReady ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : isPlaying ? (
                <Pause className="h-4 w-4" />
              ) : (
                <Play className="h-4 w-4" />
              )}
            </Button>

            {/* Close */}
            <Button
              variant="ghost"
              size="icon"
              onClick={handleClose}
              title="Fechar"
              className="h-9 w-9 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Hidden Video Player - controls the actual playback */}
      <div className="fixed -left-[9999px] w-[1px] h-[1px] overflow-hidden">
        {videoUrl && (
          <MediaPlayer
            ref={playerRef}
            title={video.title}
            src={{ src: videoUrl, type: "video/mp4" }}
            autoPlay
            load="eager"
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onEnded={handleClose}
          >
            <MediaProvider />
          </MediaPlayer>
        )}
      </div>
    </div>
  );
}
