# Global Player with Picture-in-Picture

[PT-BR](../GLOBAL-PLAYER.md) | **EN**

## Overview

Global Player is a persistent video player that allows you to play videos in the background while browsing the website, with native browser Picture-in-Picture (PiP) support.

## Features

### Mini Control Bar

When a video is minimized, a sticky control bar appears in the page footer with:

- **Thumbnail** of the current video
- **Title and channel/folder** of the video
- **Volume control** (mute button + slider)
- **PiP Button** - Activates browser-native Picture-in-Picture
- **Play/Pause button** - Controls playback
- **Close Button** - Ends playback

### Native Picture-in-Picture

PiP uses the browser's native API, allowing you to:

- Floating window that sits above other applications
- Continues playing even when switching tabs or minimizing the browser
- Basic controls in the PiP window (play/pause, close)

### Persistence between Pages

The player is at `layout.tsx`, so:

- Keeps playing when navigating between pages (Location, Drive, Library, etc.)
- Maintains playback state (current time, volume, etc.)
- Does not reload the video when changing pages

---

## Architecture

### File Structure

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

### Data Flow

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

## Usage

### Minimize a Video

1. Open any video (by clicking on the card)
2. In the player modal, click the minimize icon (⤓) in the top right corner
3. The modal closes and the mini bar appears in the footer
4. The video continues from the exact time where it was

### Enable Picture-in-Picture

1. With the mini bar visible, click the PiP button
2. A floating browser window appears with the video
3. Browse the website or other applications freely
4. The video keeps playing in the PiP window

### Volume Control

- Click volume icon to mute/unmute
- Drag the slider to adjust the volume (0-100%)

---

## Technical Details

### Vidstack Player

GlobalPlayer uses Vidstack with specific settings:

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

**Note:** `load="eager"` is essential because the player is visually hidden (off-screen) and the default `load="visible"` would prevent loading.

### Important Events

- `can-play`: Indicates that the video is ready for playback
- `onPlay` / `onPause`: Synchronizes play/pause button state
- `onEnded`: Closes the player when the video ends

### Player States

```typescript
const [isPlaying, setIsPlaying] = useState(false);
const [isReady, setIsReady] = useState(false);  // Bloqueia interação até can-play
const [volume, setVolume] = useState(1);
const [isMuted, setIsMuted] = useState(false);
```

---

## Compatibility

### Supported Browsers

| Browser | PiP | Mini Bar |
|-----------|-----|------------|
| Chrome | ✅ | ✅ |
| Firefox | ✅ | ✅ |
| Safari | ✅ | ✅ |
| Edge | ✅ | ✅ |

### Limitations

- **Mobile**: PiP may not work on some mobile devices
- **iOS Safari**: PiP requires user interaction to activate
- **Fullscreen**: Exit fullscreen before using PiP

---

## Troubleshooting

### Player does not load (infinite loading)

**Cause:** `load="eager"` is missing in MediaPlayer
**Solution:** Check if the `load="eager"` prop is present

### PiP does not activate

**Cause:** Video is not ready (`isReady=false`)
**Solution:** Wait for loading to finish (button shows spinner while loading)

### Volume does not work

**Cause:** Player is not ready or is mutated
**Solution:** Check mute status and whether the player is ready

### Video stops when browsing

**Cause:** GlobalPlayer is not in the layout
**Solution:** Check if `<GlobalPlayer />` is in `layout.tsx` outside of `{children}`
