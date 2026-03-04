"""Capture a short gameplay GIF by enabling in-process frame capture mode."""

from __future__ import annotations

import argparse
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CaptureConfig:
    duration: int = 10
    output: str = "assets/demo/gameplay.gif"
    fps: int = 20
    caption: str = "Image #1: Automated demo run showing two waypoint clicks with visible cursor, then laser fire."
    game_command: tuple[str, ...] = ("uv", "run", "python", "-m", "src.main")


def capture_demo_gif(cfg: CaptureConfig) -> None:
    output_path = Path(cfg.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["SPACEBATTLE_DEMO_SCRIPT"] = "1"
    env["SPACEBATTLE_WINDOWED"] = "1"
    env["SPACEBATTLE_CAPTURE_GIF"] = "1"
    env["SPACEBATTLE_CAPTURE_DURATION"] = str(cfg.duration)
    env["SPACEBATTLE_CAPTURE_FPS"] = str(cfg.fps)
    env["SPACEBATTLE_CAPTURE_OUTPUT"] = cfg.output
    env["SPACEBATTLE_CAPTURE_CAPTION"] = cfg.caption

    game_proc = subprocess.Popen(cfg.game_command, env=env)
    game_proc.wait()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture a gameplay GIF from internal frames.")
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--output", default="assets/demo/gameplay.gif")
    parser.add_argument("--fps", type=int, default=20)
    parser.add_argument("--caption", default=CaptureConfig.caption)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = CaptureConfig(
        duration=args.duration,
        output=args.output,
        fps=args.fps,
        caption=args.caption,
    )
    capture_demo_gif(cfg)


if __name__ == "__main__":
    main()
