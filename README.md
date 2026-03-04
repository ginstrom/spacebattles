# Space Battle

A space game written using pygame.

## Gameplay Demo

![Image #1: Automated demo run showing two waypoint clicks with visible cursor, then laser fire against the CPU ship.](assets/demo/gameplay.gif)

_Image #1: Scripted 10-second run harness that auto-unpauses, sets two waypoints with visible cursor clicks, and fires._

## Capture a New 10-Second GIF

```bash
make capture-gif
```

Equivalent direct command:

```bash
./scripts/capture_demo_gif.sh --duration 10 --output assets/demo/gameplay.gif --fps 20
```

Requirements:
- `ffmpeg` installed and on `PATH`
- A working display/SDL environment for pygame
