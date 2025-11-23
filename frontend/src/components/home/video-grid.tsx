"use client";

import { useState, useEffect } from "react";
import VideoCard from "./video-card";
import VideoPlayer from "./video-player";
import { Loader2, VideoOff } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface Video {
  id: string;
  title: string;
  channel: string;
  path: string;
  thumbnail?: string;
  size: number;
  created_at: string;
  modified_at: string;
}

export default function VideoGrid() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<Video | null>(null);

  const apiUrl =
    typeof window !== "undefined"
      ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      : "http://localhost:8000";

  const fetchVideos = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${apiUrl}/api/videos`);

      if (!response.ok) {
        throw new Error("Falha ao carregar vídeos");
      }

      const data = await response.json();
      setVideos(data.videos || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, [apiUrl]);

  const handleDelete = async (video: Video) => {
    try {
      const response = await fetch(
        `${apiUrl}/api/videos/${encodeURIComponent(video.path)}`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        throw new Error("Falha ao excluir vídeo");
      }

      // Remover da lista localmente
      setVideos((prev) => prev.filter((v) => v.id !== video.id));

      // Fechar player se este vídeo estiver sendo reproduzido
      if (selectedVideo?.id === video.id) {
        setSelectedVideo(null);
      }
    } catch (err) {
      alert(
        `Erro ao excluir vídeo: ${
          err instanceof Error ? err.message : "Erro desconhecido"
        }`
      );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>Erro ao carregar vídeos: {error}</AlertDescription>
      </Alert>
    );
  }

  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <VideoOff className="h-16 w-16 text-muted-foreground mb-4" />
        <h3 className="text-lg font-semibold mb-2">Nenhum vídeo encontrado</h3>
        <p className="text-sm text-muted-foreground max-w-md">
          Faça o download de alguns vídeos para vê-los aparecer aqui.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Minha Biblioteca</h2>
          <p className="text-sm text-muted-foreground">
            {videos.length} {videos.length === 1 ? "vídeo" : "vídeos"}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {videos.map((video) => (
            <VideoCard
              key={video.id}
              id={video.id}
              title={video.title}
              channel={video.channel}
              thumbnail={video.thumbnail}
              path={video.path}
              onPlay={() => setSelectedVideo(video)}
              onDelete={() => handleDelete(video)}
            />
          ))}
        </div>
      </div>

      {/* Video Player Modal */}
      {selectedVideo && (
        <VideoPlayer
          video={selectedVideo}
          onClose={() => setSelectedVideo(null)}
          onDelete={() => {
            handleDelete(selectedVideo);
            setSelectedVideo(null);
          }}
        />
      )}
    </>
  );
}
