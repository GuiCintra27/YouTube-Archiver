import type { Metadata } from "next";
import "./globals.css";

// Vidstack CSS
import "@vidstack/react/player/styles/default/theme.css";
import "@vidstack/react/player/styles/default/layouts/video.css";

import Navigation from "@/components/common/navigation";
import Providers from "@/components/common/providers";

export const metadata: Metadata = {
  title: "YT-Archiver - Download & Archive Videos",
  description:
    "Download YouTube videos, playlists and HLS streams with a modern interface",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning className="dark">
      <body className="antialiased" suppressHydrationWarning>
        <Providers>
          <div className="min-h-screen relative overflow-hidden">
            {/* Particles/gradient background */}
            <div className="fixed inset-0 particles-bg pointer-events-none" />

            {/* Glassmorphism Header */}
            <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5">
              <div className="container mx-auto px-4 lg:px-8">
                <div className="flex items-center justify-between h-16 md:h-20">
                  {/* Logo */}
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal to-cyan flex items-center justify-center">
                        <svg
                          className="w-6 h-6 text-navy-dark"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
                          />
                        </svg>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xl font-bold text-white">
                        YT-Archiver
                      </span>
                      <span className="hidden sm:inline-flex px-2 py-0.5 text-xs font-semibold rounded-full bg-gradient-to-r from-teal to-cyan text-navy-dark">
                        v2.4
                      </span>
                    </div>
                  </div>

                  {/* Navigation */}
                  <Navigation />
                </div>
              </div>
            </header>

            {/* Main Content */}
            <main className="relative pt-20 md:pt-24">
              {children}
            </main>

            {/* Footer */}
            <footer className="relative border-t border-white/5 mt-auto">
              <div className="container mx-auto px-4 py-8">
                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span className="gradient-teal-text font-semibold">YT-Archiver</span>
                    <span>v2.4</span>
                    <span className="hidden sm:inline">|</span>
                    <span className="hidden sm:inline">Arquivamento local de conteudo publico</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <a
                      href="https://github.com"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-teal transition-colors animated-underline"
                    >
                      GitHub
                    </a>
                    <span className="w-1 h-1 rounded-full bg-white/20" />
                    <span>Made with FastAPI + Next.js</span>
                  </div>
                </div>
              </div>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
