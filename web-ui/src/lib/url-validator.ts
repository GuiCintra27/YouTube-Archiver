/**
 * Valida e detecta tipo de URL (vídeo ou playlist)
 */

export type UrlType = "video" | "playlist" | "unknown";

export interface UrlValidation {
  isValid: boolean;
  type: UrlType;
  message?: string;
}

/**
 * Detecta se uma URL é de vídeo ou playlist do YouTube
 */
export function detectUrlType(url: string): UrlType {
  try {
    const urlObj = new URL(url);

    // YouTube
    if (
      urlObj.hostname.includes("youtube.com") ||
      urlObj.hostname.includes("youtu.be")
    ) {
      // Playlist
      if (urlObj.searchParams.has("list")) {
        return "playlist";
      }
      // Vídeo
      if (
        urlObj.searchParams.has("v") ||
        urlObj.pathname.includes("/watch") ||
        urlObj.hostname.includes("youtu.be")
      ) {
        return "video";
      }
    }

    // HLS/M3U8 (considerado vídeo único)
    if (url.includes(".m3u8") || url.includes("/hls/")) {
      return "video";
    }

    return "unknown";
  } catch {
    return "unknown";
  }
}

/**
 * Valida se a URL corresponde ao tipo esperado
 */
export function validateUrl(
  url: string,
  expectedType: UrlType
): UrlValidation {
  if (!url.trim()) {
    return {
      isValid: false,
      type: "unknown",
      message: "Digite uma URL",
    };
  }

  // Validar formato básico de URL
  try {
    new URL(url);
  } catch {
    return {
      isValid: false,
      type: "unknown",
      message: "URL inválida",
    };
  }

  const detectedType = detectUrlType(url);

  // Se não conseguiu detectar, permitir (pode ser stream HLS customizado)
  if (detectedType === "unknown") {
    return {
      isValid: true,
      type: "unknown",
      message: "Tipo de URL não reconhecido. Tentando download...",
    };
  }

  // Validar se o tipo corresponde
  if (expectedType !== detectedType) {
    const messages = {
      video: "Esta URL parece ser de uma playlist. Selecione 'Playlist' acima.",
      playlist:
        "Esta URL parece ser de um vídeo único. Selecione 'Vídeo Único' acima.",
    };

    return {
      isValid: false,
      type: detectedType,
      message: messages[expectedType as "video" | "playlist"],
    };
  }

  return {
    isValid: true,
    type: detectedType,
  };
}
