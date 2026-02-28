# Logging Design

Date: 2026-02-28

## Goal

Add structured logging to the game, starting with pause-state changes. Each log entry carries an in-game timestamp that counts only unpaused gameplay time (accumulated at frame rate, not wall clock).

## Decisions

| Concern | Decision |
|---|---|
| Destination | File (`spacebattle.log` in project root) + stderr |
| Format | Python `logging` module |
| Game timestamp | Decimal seconds, e.g. `T+12.345s` |
| Log file path | `spacebattle.log` (project root, overwritten each run) |

## Components

### In-game timer (`BattleScreen`)

- `self.game_time_ms: int = 0` added in `__init__`
- `update(dt)` already returns early when paused or game over; add `self.game_time_ms += dt` after that guard — accumulates only during active gameplay
- Reset to `0` on restart (inside the `K_r` handler)

### Logging setup (`main.py`)

Configured once at startup via `logging.basicConfig`:

```python
import logging, sys

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler("spacebattle.log"),
        logging.StreamHandler(sys.stderr),
    ]
)
```

### Logger (`battle_screen.py`)

```python
import logging
_log = logging.getLogger(__name__)  # src.screens.battle_screen
```

### Log call site (`_toggle_pause`)

```python
_log.info("T+%.3fs %s", self.game_time_ms / 1000, "paused" if self.is_paused else "unpaused")
```

Sample output:
```
INFO src.screens.battle_screen T+0.000s unpaused
INFO src.screens.battle_screen T+12.345s paused
INFO src.screens.battle_screen T+12.345s unpaused
```

## Tests

- `test_game_time_accumulates_when_running` — call `update(500)` twice while unpaused; assert `game_time_ms == 1000`
- `test_game_time_frozen_when_paused` — call `update(500)` while paused; assert `game_time_ms == 0`
- `test_toggle_pause_logs_state` — mock `_log`, toggle pause twice, assert two `info` calls with correct state strings (`"unpaused"` then `"paused"`)
