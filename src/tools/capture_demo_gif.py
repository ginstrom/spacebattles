"""Capture a short gameplay GIF by recording the running game window via ffmpeg."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CaptureConfig:
    duration: int = 10
    output: str = "assets/demo/gameplay.gif"
    fps: int = 20
    display: str = field(default_factory=lambda: os.environ.get("DISPLAY", ":0.0"))
    geometry: str = "1280x720"
    startup_delay: float = 1.5
    use_xvfb: bool = False
    caption: str = "Image #1: Automated demo run showing waypoint navigation and laser fire."
    game_command: tuple[str, ...] = ("uv", "run", "python", "-m", "src.main")


def _escape_drawtext(value: str) -> str:
    return (
        value.replace("\\", r"\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
    )


def build_ffmpeg_command(cfg: CaptureConfig) -> list[str]:
    drawtext = (
        "drawtext="
        f"text='{_escape_drawtext(cfg.caption)}':"
        "x=20:y=h-th-20:fontsize=22:fontcolor=white:"
        "box=1:boxcolor=0x000000AA:boxborderw=10"
    )
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
        f"{cfg.display}+0,0",
        "-t",
        str(cfg.duration),
        "-vf",
        drawtext,
        cfg.output,
    ]


def _start_xvfb(cfg: CaptureConfig) -> subprocess.Popen[bytes] | None:
    if not cfg.use_xvfb:
        return None
    if shutil.which("Xvfb") is None:
        raise RuntimeError("Xvfb is required for scripted capture but was not found on PATH.")
    return subprocess.Popen(
        [
            "Xvfb",
            cfg.display,
            "-screen",
            "0",
            f"{cfg.geometry}x24",
            "-nolisten",
            "tcp",
        ]
    )


def capture_demo_gif(cfg: CaptureConfig) -> None:
    output_path = Path(cfg.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["DISPLAY"] = cfg.display
    env["SPACEBATTLE_DEMO_SCRIPT"] = "1"
    env["SPACEBATTLE_WINDOWED"] = "1"

    xvfb_proc = _start_xvfb(cfg)
    game_proc = subprocess.Popen(cfg.game_command, env=env)
    try:
        time.sleep(cfg.startup_delay)
        subprocess.run(build_ffmpeg_command(cfg), check=True, env=env)
    finally:
        if game_proc.poll() is None:
            game_proc.terminate()
            try:
                game_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                game_proc.kill()
        if xvfb_proc is not None and xvfb_proc.poll() is None:
            xvfb_proc.terminate()
            try:
                xvfb_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                xvfb_proc.kill()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture a gameplay GIF using ffmpeg.")
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--output", default="assets/demo/gameplay.gif")
    parser.add_argument("--fps", type=int, default=20)
    parser.add_argument("--display", default=os.environ.get("DISPLAY", ":0.0"))
    parser.add_argument("--geometry", default="1280x720")
    parser.add_argument("--startup-delay", type=float, default=1.5)
    parser.add_argument("--caption", default=CaptureConfig.caption)
    parser.add_argument("--xvfb", action="store_true")
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
        use_xvfb=args.xvfb,
        caption=args.caption,
    )
    capture_demo_gif(cfg)


if __name__ == "__main__":
    main()
