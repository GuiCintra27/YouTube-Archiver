import { Button } from "@/components/ui/button";
import { CheckSquare, Loader2, Trash2, X } from "lucide-react";

type SelectionActionBarProps = {
  selectedCount: number;
  totalCount: number;
  deleting: boolean;
  onSelectAll: () => void;
  onClear: () => void;
  onDelete: () => void;
  iconWrapperClassName: string;
  iconClassName: string;
};

export default function SelectionActionBar({
  selectedCount,
  totalCount,
  deleting,
  onSelectAll,
  onClear,
  onDelete,
  iconWrapperClassName,
  iconClassName,
}: SelectionActionBarProps) {
  if (selectedCount <= 0) {
    return null;
  }

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[70]">
      <div className="glass-card rounded-xl px-4 py-3 flex items-center gap-4 shadow-lg shadow-black/20">
        <div className="flex items-center gap-2">
          <div
            className={`w-8 h-8 rounded-lg flex items-center justify-center ${iconWrapperClassName}`}
          >
            <CheckSquare className={`h-4 w-4 ${iconClassName}`} />
          </div>
          <span className="font-medium text-white">
            {selectedCount} {selectedCount === 1 ? "selecionado" : "selecionados"}
          </span>
        </div>

        <div className="h-6 w-px bg-white/10" />

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onSelectAll}
            disabled={deleting || selectedCount === totalCount}
            className="text-muted-foreground hover:text-white hover:bg-white/10"
          >
            Selecionar todos
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={onClear}
            disabled={deleting}
            className="text-muted-foreground hover:text-white hover:bg-white/10"
          >
            <X className="h-4 w-4 mr-1" />
            Limpar
          </Button>

          <Button
            size="sm"
            onClick={onDelete}
            disabled={deleting}
            className="bg-red-500/20 text-red-400 border border-red-500/30 hover:bg-red-500/30"
          >
            {deleting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Excluindo...
              </>
            ) : (
              <>
                <Trash2 className="h-4 w-4 mr-1" />
                Excluir ({selectedCount})
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
