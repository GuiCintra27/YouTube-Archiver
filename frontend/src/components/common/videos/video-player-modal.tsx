"use client";

import dynamic from "next/dynamic";
import VideoPlayerLoading from "@/components/common/videos/video-player-loading";
import type { VideoPlayerVideo } from "@/components/common/videos/video-player";

const VideoPlayer = dynamic(
  () => import("@/components/common/videos/video-player"),
  {
    ssr: false,
    loading: () => <VideoPlayerLoading />,
  }
);

type VideoPlayerModalProps = {
  video: VideoPlayerVideo;
  source?: "local" | "drive";
  onClose: () => void;
  onDelete: () => void;
};

export default function VideoPlayerModal({
  video,
  source = "local",
  onClose,
  onDelete,
}: VideoPlayerModalProps) {
  return (
    <VideoPlayer video={video} source={source} onClose={onClose} onDelete={onDelete} />
  );
}
