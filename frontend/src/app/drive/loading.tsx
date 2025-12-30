import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="flex flex-col items-center gap-3">
        <div className="w-12 h-12 rounded-full bg-cyan/10 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-cyan" />
        </div>
        <p className="text-sm text-muted-foreground">Carregando Drive...</p>
      </div>
    </div>
  );
}
