"use client";

import { ReactNode } from "react";
import { ThemeProvider } from "@/components/common/theme-provider";
import { GlobalPlayerProvider } from "@/contexts/global-player-context";
import GlobalPlayer from "@/components/common/global-player";

interface ProvidersProps {
  children: ReactNode;
}

export default function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>
      <GlobalPlayerProvider>
        {children}
        <GlobalPlayer />
      </GlobalPlayerProvider>
    </ThemeProvider>
  );
}
