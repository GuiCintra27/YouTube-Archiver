import PaginatedVideoGrid from "@/components/library/paginated-video-grid";

export default function LibraryPage() {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Biblioteca completa</h2>
        <p className="text-muted-foreground">
          Visualize e gerencie todos os vídeos armazenados localmente.
        </p>
      </div>

      <PaginatedVideoGrid />
    </div>
  );
}
