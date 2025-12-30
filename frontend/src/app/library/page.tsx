import { Library, Film, FolderOpen, Search, Trash2 } from "lucide-react";
import PaginatedVideoGrid from "@/components/library/paginated-video-grid";
import { fetchLocalVideosPage } from "@/lib/server/api";

const PAGE_SIZE = 12;

export default async function LibraryPage() {
  let initialData: {
    videos: {
      id: string;
      title: string;
      channel: string;
      path: string;
      thumbnail?: string;
      duration?: string;
      size: number;
      created_at: string;
      modified_at: string;
    }[];
    total: number;
    page: number;
  } | null = null;

  try {
    const data = await fetchLocalVideosPage(1, PAGE_SIZE);
    initialData = {
      videos: data.videos || [],
      total: data.total || 0,
      page: data.page || 1,
    };
  } catch (error) {
    console.error("Erro ao carregar biblioteca:", error);
  }

  return (
    <div className="space-y-10">
      {/* Hero Section */}
      <section className="relative max-w-3xl mx-auto">
        {/* Watermark */}
        <div className="absolute -top-4 left-0 right-0 flex justify-center pointer-events-none select-none overflow-hidden">
          <span className="watermark text-[6rem] md:text-[8rem] font-bold">
            LIBRARY
          </span>
        </div>

        <div className="relative z-10 text-center space-y-4 pt-4">
          {/* Icon */}
          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-teal/20 blur-xl rounded-full" />
              <div className="relative w-14 h-14 rounded-xl bg-gradient-to-br from-teal to-cyan flex items-center justify-center">
                <Library className="h-7 w-7 text-navy-dark" />
              </div>
            </div>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <h1 className="text-3xl md:text-4xl font-bold text-white">
              Sua{" "}
              <span className="bg-gradient-to-r from-teal to-cyan bg-clip-text text-transparent">
                Biblioteca
              </span>
            </h1>
            <p className="text-base text-muted-foreground max-w-xl mx-auto">
              Visualize e gerencie todos os vídeos armazenados localmente.
            </p>
          </div>

          {/* Feature Pills */}
          <div className="flex flex-wrap justify-center gap-2 pt-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <Film className="h-3.5 w-3.5 text-teal" />
              <span className="text-white">Streaming Local</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <FolderOpen className="h-3.5 w-3.5 text-purple" />
              <span className="text-white">Organização</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <Search className="h-3.5 w-3.5 text-yellow" />
              <span className="text-white">Busca Rápida</span>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-xs">
              <Trash2 className="h-3.5 w-3.5 text-orange" />
              <span className="text-white">Batch Delete</span>
            </div>
          </div>
        </div>
      </section>

      {/* Video Grid Section */}
      <section className="max-w-[90rem] mx-auto">
        <PaginatedVideoGrid initialData={initialData || undefined} />
      </section>
    </div>
  );
}
