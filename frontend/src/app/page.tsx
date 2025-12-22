import DownloadForm from "@/components/home/download-form";
import RecentVideos from "@/components/common/videos/recent-videos";
import {
  Zap,
  Shield,
  Settings2,
  Cloud,
  Subtitles,
  ListVideo,
  Download,
  Play,
  HardDrive,
  Clock,
} from "lucide-react";
import Link from "next/link";
import { PATHS } from "@/lib/paths";

// Feature cards data
const features = [
  {
    icon: Zap,
    title: "Ultra Rapido",
    description: "Downloads paralelos com fragmentos otimizados",
    color: "teal",
  },
  {
    icon: Shield,
    title: "100% Local",
    description: "Processamento seguro no seu servidor",
    color: "purple",
  },
  {
    icon: Settings2,
    title: "Controle Total",
    description: "Qualidade, formato, legendas e mais",
    color: "yellow",
  },
  {
    icon: Cloud,
    title: "Google Drive",
    description: "Sincronize sua biblioteca na nuvem",
    color: "teal",
  },
  {
    icon: Subtitles,
    title: "Legendas",
    description: "Download automatico de legendas",
    color: "purple",
  },
  {
    icon: ListVideo,
    title: "Playlists",
    description: "Baixe playlists completas de uma vez",
    color: "yellow",
  },
];

// Stats data
const stats = [
  { icon: Download, value: "1000+", label: "Sites suportados" },
  { icon: Play, value: "HLS", label: "Streams suportados" },
  { icon: HardDrive, value: "Local", label: "Armazenamento" },
  { icon: Clock, value: "Real-time", label: "Progresso" },
];

// Badge data
const badges = [
  "YouTube",
  "Playlists",
  "HLS/M3U8",
  "Legendas",
  "Thumbnails",
  "Anti-ban",
];

export default function Home() {
  return (
    <div className="relative">
      {/* ============================================
          HERO SECTION
          ============================================ */}
      <section className="relative min-h-[80vh] flex items-center overflow-hidden">
        {/* Watermark */}
        <div className="watermark top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-50">
          YT-ARCHIVER
        </div>

        <div className="container mx-auto px-4 lg:px-8 py-12 lg:py-20">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left Column - Text */}
            <div className="space-y-8 fade-in-up">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-teal/20">
                <span className="w-2 h-2 rounded-full bg-teal animate-pulse" />
                <span className="text-sm text-muted-foreground">
                  Versao 2.4 disponivel
                </span>
              </div>

              {/* Main Headline */}
              <div className="space-y-4">
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight">
                  <span className="text-white">Baixe videos do </span>
                  <span className="gradient-teal-text">YouTube</span>
                  <span className="text-white"> de forma simples</span>
                </h1>
                <p className="text-lg md:text-xl text-muted-foreground max-w-xl">
                  Interface moderna, downloads rapidos e sincronizacao com
                  Google Drive. Tudo local e seguro.
                </p>
              </div>

              {/* CTAs */}
              <div className="flex flex-wrap gap-4">
                <a
                  href="#download-form"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full btn-gradient-yellow text-base"
                >
                  <Download className="h-5 w-5" />
                  Iniciar Download
                </a>
                <Link
                  href={PATHS.LIBRARY}
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-full border border-white/20 text-white hover:bg-white/5 hover:border-teal/30 transition-all duration-300"
                >
                  <Play className="h-5 w-5" />
                  Ver Biblioteca
                </Link>
              </div>

              {/* Trust Badge */}
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <Shield className="h-5 w-5 text-teal" />
                <span>Processamento 100% local e seguro</span>
              </div>

              {/* Feature Badges */}
              <div className="flex flex-wrap gap-2">
                {badges.map((badge) => (
                  <span
                    key={badge}
                    className="px-3 py-1 rounded-full text-xs font-medium bg-white/5 border border-white/10 text-muted-foreground"
                  >
                    {badge}
                  </span>
                ))}
              </div>
            </div>

            {/* Right Column - Mockup/Visual */}
            <div className="relative hidden lg:block">
              {/* Floating elements */}
              <div className="absolute -top-8 -right-8 w-24 h-24 rounded-full bg-teal/10 blur-3xl" />
              <div className="absolute -bottom-8 -left-8 w-32 h-32 rounded-full bg-purple/10 blur-3xl" />

              {/* Main Card */}
              <div className="relative glass-card p-6 rounded-2xl animate-float">
                {/* Preview mockup */}
                <div className="aspect-video rounded-xl bg-gradient-to-br from-navy-light to-navy overflow-hidden border border-white/10">
                  <div className="h-full flex flex-col">
                    {/* Fake toolbar */}
                    <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
                      <div className="flex gap-1.5">
                        <div className="w-3 h-3 rounded-full bg-red-500/50" />
                        <div className="w-3 h-3 rounded-full bg-yellow/50" />
                        <div className="w-3 h-3 rounded-full bg-teal/50" />
                      </div>
                      <div className="flex-1 mx-4">
                        <div className="h-6 rounded-full bg-white/5 flex items-center px-3">
                          <span className="text-xs text-muted-foreground truncate">
                            youtube.com/watch?v=example
                          </span>
                        </div>
                      </div>
                    </div>
                    {/* Fake content */}
                    <div className="flex-1 p-4 flex items-center justify-center">
                      <div className="text-center space-y-3">
                        <div className="w-16 h-16 mx-auto rounded-full bg-gradient-to-br from-teal to-cyan flex items-center justify-center">
                          <Play className="h-8 w-8 text-navy-dark ml-1" />
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Clique para baixar
                        </p>
                      </div>
                    </div>
                    {/* Fake progress bar */}
                    <div className="px-4 pb-4">
                      <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                        <div className="h-full w-3/4 rounded-full bg-gradient-to-r from-teal to-cyan animate-pulse" />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Floating badges */}
                <div className="absolute -right-4 top-1/4 glass-card px-3 py-2 rounded-lg animate-float">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-yellow" />
                    <span className="text-xs text-white">1080p</span>
                  </div>
                </div>

                <div className="absolute -left-4 bottom-1/3 glass-card px-3 py-2 rounded-lg animate-float" style={{ animationDelay: "0.5s" }}>
                  <div className="flex items-center gap-2">
                    <Cloud className="h-4 w-4 text-teal" />
                    <span className="text-xs text-white">Sync</span>
                  </div>
                </div>
              </div>

              {/* Circular text badge */}
              <div className="absolute -bottom-4 right-8 w-24 h-24">
                <div className="w-full h-full rounded-full border border-white/10 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-2xl font-bold gradient-teal-text">
                      yt
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================
          STATS SECTION
          ============================================ */}
      <section className="relative py-12 border-y border-white/5">
        <div className="container mx-auto px-4 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8">
            {stats.map((stat, index) => (
              <div
                key={index}
                className="flex items-center gap-4 p-4 rounded-xl glass-dark"
              >
                <div className="icon-glow">
                  <stat.icon className="h-5 w-5 text-teal" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">
                    {stat.value}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {stat.label}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================
          FEATURES SECTION
          ============================================ */}
      <section className="relative py-20">
        {/* Watermark */}
        <div className="watermark top-0 left-0 -translate-y-1/2">
          FEATURES
        </div>

        <div className="container mx-auto px-4 lg:px-8">
          {/* Section Header */}
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass border border-purple/20 text-sm text-muted-foreground mb-4">
              <Settings2 className="h-4 w-4 text-purple" />
              Recursos
            </span>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Tudo que voce precisa
            </h2>
            <p className="text-muted-foreground">
              Ferramentas poderosas para download e gerenciamento de videos
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group p-6 rounded-2xl glass-card hover:scale-[1.02] hover:border-white/20 transition-all duration-300"
              >
                <div
                  className={`w-14 h-14 rounded-xl flex items-center justify-center mb-4 ${
                    feature.color === "teal"
                      ? "bg-teal/10 text-teal"
                      : feature.color === "purple"
                      ? "bg-purple/10 text-purple"
                      : "bg-yellow/10 text-yellow"
                  }`}
                >
                  <feature.icon className="h-7 w-7" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================
          DOWNLOAD FORM SECTION
          ============================================ */}
      <section id="download-form" className="relative py-20">
        <div className="container mx-auto px-4 lg:px-8">
          <DownloadForm />
        </div>
      </section>

      {/* ============================================
          RECENT VIDEOS SECTION
          ============================================ */}
      <section className="relative py-20 border-t border-white/5">
        {/* Watermark */}
        <div className="watermark bottom-0 right-0 translate-y-1/2">
          LIBRARY
        </div>

        <div className="container mx-auto px-4 lg:px-8">
          <RecentVideos />
        </div>
      </section>
    </div>
  );
}
