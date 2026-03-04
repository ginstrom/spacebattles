#!/usr/bin/env bash
set -euo pipefail

uv run python -m src.tools.capture_demo_gif "$@"
