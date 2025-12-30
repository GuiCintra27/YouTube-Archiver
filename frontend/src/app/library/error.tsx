"use client";

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

type LibraryErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function LibraryError({ error, reset }: LibraryErrorProps) {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="glass-card rounded-2xl p-6 text-center max-w-md">
        <div className="w-12 h-12 mx-auto rounded-full bg-red-500/10 flex items-center justify-center">
          <AlertTriangle className="h-6 w-6 text-red-400" />
        </div>
        <h2 className="mt-4 text-lg font-semibold text-white">
          Falha ao carregar a biblioteca
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          {error.message || "Tente novamente em instantes."}
        </p>
        <Button
          onClick={reset}
          className="mt-4 btn-gradient-teal"
        >
          Tentar novamente
        </Button>
      </div>
    </div>
  );
}
