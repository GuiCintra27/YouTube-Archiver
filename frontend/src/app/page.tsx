import DownloadForm from "@/components/home/download-form";
import RecentVideos from "@/components/common/videos/recent-videos";

export default function Home() {
  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-4xl font-bold tracking-tight">
          Baixe vídeos de forma simples
        </h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Suporte para YouTube, playlists e streams HLS. Configure opções
          avançadas como headers customizados, resolução máxima e muito mais.
        </p>
      </div>

      <DownloadForm />

      <div className="max-w-4xl mx-auto">
        <div className="grid md:grid-cols-3 gap-6 mt-12">
          <div className="space-y-2 text-center">
            <div className="text-3xl">⚡</div>
            <h3 className="font-semibold">Rápido e Eficiente</h3>
            <p className="text-sm text-muted-foreground">
              Downloads paralelos e otimizados para máxima velocidade
            </p>
          </div>

          <div className="space-y-2 text-center">
            <div className="text-3xl">🎯</div>
            <h3 className="font-semibold">Controle Total</h3>
            <p className="text-sm text-muted-foreground">
              Configure qualidade, formato, legendas e muito mais
            </p>
          </div>

          <div className="space-y-2 text-center">
            <div className="text-3xl">🔒</div>
            <h3 className="font-semibold">Privado e Seguro</h3>
            <p className="text-sm text-muted-foreground">
              Seus downloads são processados localmente no seu servidor
            </p>
          </div>
        </div>
      </div>

      <div className="mt-16 pt-8 border-t">
        <RecentVideos />
      </div>
    </div>
  );
}
