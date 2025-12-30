"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  RefreshCw,
  Search,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface PaginationControlsProps {
  page: number;
  totalPages: number;
  loading?: boolean;
  onPageChange: (page: number) => void;
  onRefresh?: () => void;
  showRefreshButton?: boolean;
}

export default function PaginationControls({
  page,
  totalPages,
  loading = false,
  onPageChange,
  onRefresh,
  showRefreshButton = true,
}: PaginationControlsProps) {
  const [pageInput, setPageInput] = useState(String(page));

  // Sincronizar input com página atual
  useEffect(() => {
    setPageInput(String(page));
  }, [page]);

  const canPrev = page > 1;
  const canNext = page < totalPages;

  const handlePageJump = () => {
    const parsed = parseInt(pageInput, 10);
    if (Number.isNaN(parsed)) {
      setPageInput(String(page));
      return;
    }
    const target = Math.min(Math.max(parsed, 1), totalPages);
    setPageInput(String(target));
    onPageChange(target);
  };

  const handlePrevious = () => {
    if (canPrev) {
      onPageChange(page - 1);
    }
  };

  const handleNext = () => {
    if (canNext) {
      onPageChange(page + 1);
    }
  };

  return (
    <div className="flex w-full flex-wrap items-center gap-2 glass rounded-xl px-3 py-2 sm:w-auto">
      {/* Botão Atualizar */}
      {showRefreshButton && onRefresh && (
        <>
          <Button
            variant="ghost"
            size="sm"
            className="flex items-center gap-1.5 text-muted-foreground hover:text-teal hover:bg-teal/10"
            onClick={onRefresh}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Atualizar</span>
          </Button>

          <span className="hidden sm:block h-5 w-px bg-white/10" aria-hidden />
        </>
      )}

      {/* Input de navegação direta */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground hidden sm:inline">Ir para:</span>

        <div className="relative flex items-center">
          <Input
            type="number"
            inputMode="numeric"
            min={1}
            max={totalPages}
            value={pageInput}
            onChange={(e) => setPageInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handlePageJump();
              }
            }}
            className="h-8 w-16 pr-7 text-center no-spinner glass-input bg-white/5 border-white/10 text-white text-sm"
            aria-label="Ir para página"
            placeholder="Pág"
            disabled={loading || totalPages === 0}
          />
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-0.5 top-1/2 -translate-y-1/2 h-6 w-6 text-muted-foreground hover:text-teal"
          onClick={handlePageJump}
          disabled={loading || totalPages === 0}
          aria-label="Confirmar página"
        >
          <Search className="h-3 w-3" />
        </Button>
        </div>
      </div>

      <span className="hidden sm:block h-5 w-px bg-white/10" aria-hidden />

      {/* Botões de navegação */}
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-white hover:bg-white/10"
          onClick={handlePrevious}
          disabled={!canPrev || loading}
          aria-label="Página anterior"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        <span className="text-xs text-muted-foreground px-2 min-w-[4rem] text-center">
          <span className="text-white font-medium">{page}</span>
          <span className="mx-1">/</span>
          <span>{totalPages}</span>
        </span>

        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-white hover:bg-white/10"
          onClick={handleNext}
          disabled={!canNext || loading}
          aria-label="Próxima página"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
