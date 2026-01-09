import { VideoOff } from "lucide-react";

type VideoGridEmptyStateProps = {
  title: string;
  description: string;
};

export default function VideoGridEmptyState({
  title,
  description,
}: VideoGridEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center glass-card rounded-2xl">
      <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
        <VideoOff className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground max-w-md">{description}</p>
    </div>
  );
}
