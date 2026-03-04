"""
The entry point for the real-time Ship Duel application.
Initializes the game engine and the ScreenManager.
"""
import logging
import os
import subprocess
import sys
from pathlib import Path

import pygame
from src.constants import WIDTH, HEIGHT, FPS
from src.core.screen_manager import ScreenManager
from src.screens.menu_screen import MenuScreen


def configure_logging(log_path: str | Path = "spacebattle.log") -> Path:
    resolved_path = Path(log_path).resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(resolved_path, mode="w", encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
        force=True,
    )
    logging.getLogger(__name__).info("logging initialized: %s", resolved_path)
    return resolved_path


def build_game() -> tuple[ScreenManager, pygame.time.Clock]:
    pygame.init()
    if hasattr(pygame.key, "stop_text_input"):
        pygame.key.stop_text_input()
    windowed = os.getenv("SPACEBATTLE_WINDOWED", "0") == "1"
    screen_flags = 0 if windowed else pygame.FULLSCREEN
    screen = pygame.display.set_mode((WIDTH, HEIGHT), screen_flags)
    pygame.display.set_caption("Ship Duel")
    clock = pygame.time.Clock()

    manager = ScreenManager(screen)
    manager.set_screen(MenuScreen)
    return manager, clock


def _escape_drawtext(value: str) -> str:
    return (
        value.replace("\\", r"\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
    )


def build_capture_ffmpeg_command(
    width: int,
    height: int,
    fps: int,
    caption: str,
    output_path: str,
) -> list[str]:
    drawtext = (
        "drawtext="
        f"text='{_escape_drawtext(caption)}':"
        "x=20:y=h-th-20:fontsize=22:fontcolor=white:"
        "box=1:boxcolor=0x000000AA:boxborderw=10"
    )
    filter_complex = (
        f"[0:v]fps={fps},scale=960:-1:flags=lanczos,{drawtext},split[s0][s1];"
        "[s0]palettegen=max_colors=256[p];"
        "[s1][p]paletteuse=dither=sierra2_4a"
    )
    return [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
        "-filter_complex",
        filter_complex,
        output_path,
    ]


def _capture_config_from_env() -> tuple[int, int, str, str] | None:
    if os.getenv("SPACEBATTLE_CAPTURE_GIF", "0") != "1":
        return None
    duration = int(os.getenv("SPACEBATTLE_CAPTURE_DURATION", "10"))
    fps = int(os.getenv("SPACEBATTLE_CAPTURE_FPS", "20"))
    output = os.getenv("SPACEBATTLE_CAPTURE_OUTPUT", "assets/demo/gameplay.gif")
    caption = os.getenv(
        "SPACEBATTLE_CAPTURE_CAPTION",
        "Image #1: Automated demo run showing two waypoint clicks with visible cursor, then laser fire.",
    )
    return duration, fps, output, caption


def run_game_loop(manager: ScreenManager, clock: pygame.time.Clock) -> None:
    capture_cfg = _capture_config_from_env()
    if capture_cfg is None:
        while manager.running:
            dt = clock.tick(FPS)
            manager.handle_events()
            manager.update(dt)
            manager.draw()
        return

    duration, capture_fps, output_path, caption = capture_cfg
    frame_target = max(1, duration * capture_fps)
    width, height = manager.screen.get_size()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_cmd = build_capture_ffmpeg_command(width, height, capture_fps, caption, output_path)
    ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    frame_interval_ms = 1000.0 / float(capture_fps)
    capture_clock_ms = 0.0
    frames_written = 0
    try:
        while manager.running and frames_written < frame_target:
            dt = clock.tick(FPS)
            manager.handle_events()
            manager.update(dt)
            manager.draw()
            capture_clock_ms += float(dt)
            while capture_clock_ms >= frame_interval_ms and frames_written < frame_target:
                if ffmpeg_proc.stdin is None:
                    break
                ffmpeg_proc.stdin.write(pygame.image.tostring(manager.screen, "RGB"))
                capture_clock_ms -= frame_interval_ms
                frames_written += 1
    finally:
        if ffmpeg_proc.stdin is not None:
            ffmpeg_proc.stdin.close()
        ffmpeg_proc.wait(timeout=15)


def main() -> None:
    configure_logging()
    manager, clock = build_game()
    try:
        run_game_loop(manager, clock)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
