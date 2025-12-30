import { Loader2, Cloud } from "lucide-react";

export default function DrivePageSkeleton() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="glass-card rounded-2xl px-8 py-6 flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-cyan/10 flex items-center justify-center">
          <Cloud className="h-5 w-5 text-cyan" />
        </div>
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-cyan" />
          <span className="text-sm text-muted-foreground">
            Preparando Google Drive...
          </span>
        </div>
      </div>
    </div>
  );
}
