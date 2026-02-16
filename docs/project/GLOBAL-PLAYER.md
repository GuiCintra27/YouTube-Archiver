# Global Player com Picture-in-Picture

## Visão Geral

O Global Player é um player de vídeo persistente que permite reproduzir vídeos em background enquanto navega pelo site, com suporte a Picture-in-Picture (PiP) nativo do navegador.

## Funcionalidades

### Mini Barra de Controle

Quando um vídeo é minimizado, uma barra de controle fixa aparece no rodapé da página com:

- **Thumbnail** do vídeo atual
- **Título e canal/pasta** do vídeo
- **Controle de volume** (botão mute + slider)
- **Botão PiP** - Ativa Picture-in-Picture nativo do navegador
- **Botão Play/Pause** - Controla reprodução
- **Botão Fechar** - Encerra a reprodução

### Picture-in-Picture Nativo

O PiP usa a API nativa do navegador, permitindo:

- Janela flutuante que fica acima de outras aplicações
- Continua tocando mesmo ao trocar de aba ou minimizar o navegador
- Controles básicos na janela PiP (play/pause, fechar)

### Persistência entre Páginas

O player está no `layout.tsx`, então:

- Continua tocando ao navegar entre páginas (Local, Drive, Biblioteca, etc.)
- Mantém o estado de reprodução (tempo atual, volume, etc.)
- Não recarrega o vídeo ao mudar de página

---

## Arquitetura

### Estrutura de Arquivos

```
frontend/src/
├── contexts/
│   └── global-player-context.tsx   # Contexto global do player
├── components/
│   └── common/
│       ├── global-player.tsx       # Componente da mini barra
│       └── videos/
│           └── video-player.tsx    # Modal do player (com botão minimizar)
└── app/
    └── layout.tsx                  # Provider e GlobalPlayer
```

### Fluxo de Dados

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  VideoPlayer    │────▶│ GlobalPlayerContext  │────▶│  GlobalPlayer   │
│  (Modal)        │     │ (Estado Global)      │     │  (Mini Barra)   │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
     playVideo()              video, source              Renderiza se
     com currentTime          isActive, startTime        isActive=true
```

### Context API

```typescript
interface GlobalPlayerVideo {
  id: string;
  title: string;
  subtitle: string;  // canal ou path
  path: string;
  thumbnail?: string;
  size: number;
}

interface GlobalPlayerContextType {
  video: GlobalPlayerVideo | null;
  source: "local" | "drive";
  isActive: boolean;
  startTime: number;
  playVideo: (video, source, startTime?) => void;
  stopVideo: () => void;
}
```

---

## Uso

### Minimizar um Vídeo

1. Abra qualquer vídeo (clicando no card)
2. No modal do player, clique no ícone de minimizar (⤓) no canto superior direito
3. O modal fecha e a mini barra aparece no rodapé
4. O vídeo continua do tempo exato onde estava

### Ativar Picture-in-Picture

1. Com a mini barra visível, clique no botão PiP
2. Uma janela flutuante do navegador aparece com o vídeo
3. Navegue livremente pelo site ou outras aplicações
4. O vídeo continua tocando na janela PiP

### Controle de Volume

- Clique no ícone de volume para mutar/desmutar
- Arraste o slider para ajustar o volume (0-100%)

---

## Detalhes Técnicos

### Vidstack Player

O GlobalPlayer usa o Vidstack com configurações específicas:

```tsx
<MediaPlayer
  ref={playerRef}
  src={{ src: videoUrl, type: "video/mp4" }}
  autoPlay
  load="eager"  // Importante: força carregamento mesmo quando oculto
>
  <MediaProvider />
</MediaPlayer>
```

**Nota:** O `load="eager"` é essencial pois o player fica visualmente oculto (off-screen) e o padrão `load="visible"` impediria o carregamento.

### Eventos Importantes

- `can-play`: Indica que o vídeo está pronto para reprodução
- `onPlay` / `onPause`: Sincroniza estado do botão play/pause
- `onEnded`: Fecha o player quando o vídeo termina

### Estados do Player

```typescript
const [isPlaying, setIsPlaying] = useState(false);
const [isReady, setIsReady] = useState(false);  // Bloqueia interação até can-play
const [volume, setVolume] = useState(1);
const [isMuted, setIsMuted] = useState(false);
```

---

## Compatibilidade

### Navegadores Suportados

| Navegador | PiP | Mini Barra |
|-----------|-----|------------|
| Chrome    | ✅  | ✅         |
| Firefox   | ✅  | ✅         |
| Safari    | ✅  | ✅         |
| Edge      | ✅  | ✅         |

### Limitações

- **Mobile**: PiP pode não funcionar em alguns dispositivos móveis
- **iOS Safari**: PiP requer interação do usuário para ativar
- **Fullscreen**: Sair do fullscreen antes de usar PiP

---

## Solução de Problemas

### Player não carrega (loading infinito)

**Causa:** Falta `load="eager"` no MediaPlayer
**Solução:** Verificar se a prop `load="eager"` está presente

### PiP não ativa

**Causa:** Vídeo não está pronto (`isReady=false`)
**Solução:** Aguardar o loading terminar (botão mostra spinner enquanto carrega)

### Volume não funciona

**Causa:** Player não está pronto ou está mutado
**Solução:** Verificar estado de mute e se o player está pronto

### Vídeo para ao navegar

**Causa:** GlobalPlayer não está no layout
**Solução:** Verificar se `<GlobalPlayer />` está em `layout.tsx` fora do `{children}`
