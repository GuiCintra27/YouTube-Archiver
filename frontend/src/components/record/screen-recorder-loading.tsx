"use client";

import { Loader2 } from "lucide-react";

export default function ScreenRecorderLoading() {
  return (
    <div className="glass-card rounded-2xl p-10 flex items-center justify-center">
      <div className="flex items-center gap-3">
        <Loader2 className="h-5 w-5 animate-spin text-purple" />
        <span className="text-sm text-muted-foreground">Carregando gravador...</span>
      </div>
    </div>
  );
}
