"use client";

import { Loader2 } from "lucide-react";

export default function VideoPlayerLoading() {
  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/70">
      <div className="glass-card rounded-xl px-6 py-4 flex items-center gap-3">
        <Loader2 className="h-5 w-5 animate-spin text-teal" />
        <span className="text-sm text-muted-foreground">Carregando player...</span>
      </div>
    </div>
  );
}
