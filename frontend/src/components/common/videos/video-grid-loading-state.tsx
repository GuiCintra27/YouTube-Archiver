import { Loader2 } from "lucide-react";

type VideoGridLoadingStateProps = {
  label: string;
  iconWrapperClassName: string;
  iconClassName: string;
};

export default function VideoGridLoadingState({
  label,
  iconWrapperClassName,
  iconClassName,
}: VideoGridLoadingStateProps) {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="flex flex-col items-center gap-3">
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center ${iconWrapperClassName}`}
        >
          <Loader2 className={`h-6 w-6 animate-spin ${iconClassName}`} />
        </div>
        <p className="text-sm text-muted-foreground">{label}</p>
      </div>
    </div>
  );
}
