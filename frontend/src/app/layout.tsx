import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

// Vidstack CSS
import "@vidstack/react/player/styles/default/theme.css";
import "@vidstack/react/player/styles/default/layouts/video.css";

import Navigation from "@/components/common/navigation";
import ThemeToggle from "@/components/common/theme-toggle";
import { ThemeProvider } from "@/components/common/theme-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "YT-Archiver - Download de Vídeos",
  description:
    "Baixe vídeos do YouTube, playlists e streams HLS de forma simples",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        <ThemeProvider>
          <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
            <header className="border-b">
              <div className="container mx-auto px-4 py-4">
                <div className="flex items-center justify-between gap-4">
                  <h1 className="text-2xl font-bold">YT-Archiver</h1>
                  <div className="flex items-center gap-2">
                    <Navigation />
                    <ThemeToggle />
                  </div>
                </div>
              </div>
            </header>
            <main className="container mx-auto px-4 py-8">{children}</main>
            <footer className="border-t mt-auto">
              <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
                <p>
                  YT-Archiver v2.0 - Desenvolvido para arquivamento ético de
                  conteúdo público
                </p>
              </div>
            </footer>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
