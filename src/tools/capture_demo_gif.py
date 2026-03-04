"""Capture a short gameplay GIF by recording the running game window via ffmpeg."""

from __future__ import annotations

import argparse
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CaptureConfig:
    duration: int = 10
    output: str = "assets/demo/gameplay.gif"
    fps: int = 20
    display: str = ":0.0"
    geometry: str = "1280x720"
    startup_delay: float = 1.5
    game_command: tuple[str, ...] = ("uv", "run", "python", "-m", "src.main")


def build_ffmpeg_command(cfg: CaptureConfig) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-f",
        "x11grab",
        "-framerate",
        str(cfg.fps),
        "-video_size",
        cfg.geometry,
        "-i",
        cfg.display,
        "-t",
        str(cfg.duration),
        cfg.output,
    ]


def capture_demo_gif(cfg: CaptureConfig) -> None:
    output_path = Path(cfg.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    game_proc = subprocess.Popen(cfg.game_command)
    try:
        time.sleep(cfg.startup_delay)
        subprocess.run(build_ffmpeg_command(cfg), check=True)
    finally:
        if game_proc.poll() is None:
            game_proc.terminate()
            try:
                game_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                game_proc.kill()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture a gameplay GIF using ffmpeg.")
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--output", default="assets/demo/gameplay.gif")
    parser.add_argument("--fps", type=int, default=20)
    parser.add_argument("--display", default=":0.0")
    parser.add_argument("--geometry", default="1280x720")
    parser.add_argument("--startup-delay", type=float, default=1.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = CaptureConfig(
        duration=args.duration,
        output=args.output,
        fps=args.fps,
        display=args.display,
        geometry=args.geometry,
        startup_delay=args.startup_delay,
    )
    capture_demo_gif(cfg)


if __name__ == "__main__":
    main()
