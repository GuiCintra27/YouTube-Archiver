"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RefreshCw, Search } from "lucide-react";

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
    <div className="flex w-full flex-wrap items-center gap-3 rounded-lg border bg-card/60 px-3 py-2 shadow-sm sm:w-auto">
      {/* Botão Atualizar */}
      {showRefreshButton && onRefresh && (
        <>
          <Button
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
            onClick={onRefresh}
            disabled={loading}
          >
            <RefreshCw className="h-4 w-4" />
            <span className="hidden sm:inline">Atualizar</span>
          </Button>

          <span className="hidden sm:block h-6 w-px bg-border" aria-hidden />
        </>
      )}

      {/* Input de navegação direta */}
      <div className="flex items-center gap-2">
        <span>Navegar Para:</span>

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
            className="h-10 w-24 pr-10 text-center no-spinner"
            aria-label="Ir para página"
            placeholder="Página"
            disabled={loading || totalPages === 0}
          />
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-1 top-1/2 -translate-y-1/2"
            onClick={handlePageJump}
            disabled={loading || totalPages === 0}
            aria-label="Confirmar página"
          >
            <Search className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <span className="hidden sm:block h-6 w-px bg-border" aria-hidden />

      {/* Botões de navegação */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={handlePrevious}
          disabled={!canPrev || loading}
        >
          Anterior
        </Button>
        <span className="text-sm text-muted-foreground">
          Página {page} de {totalPages}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleNext}
          disabled={!canNext || loading}
        >
          Próxima
        </Button>
      </div>
    </div>
  );
}
