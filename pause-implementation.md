# Pause Implementation

## Summary

Pause/unpause now toggles on `KEYDOWN` for `Space`, while ignoring repeated keydown events
(`event.repeat != 0`) to prevent an immediate double-toggle back to paused state.

Logging is configured through a dedicated startup function that forces handler replacement,
so pause/unpause logs are reliably written to `spacebattle.log` even when another subsystem
preconfigured Python logging earlier.

## Bug History

### Attempt 1 — KEYUP trigger (broken)

The working tree once changed the trigger from `KEYDOWN` to `KEYUP`:

```python
# Broken: toggle on KEYUP
if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
    self.space_pressed = True
    return

if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
    if self.space_pressed:
        self._toggle_pause(now)   # ← never reached if KEYUP is lost
    self.space_pressed = False
    return
```

On Linux/SDL2, `KEYUP` events can fail to arrive — for example if the window loses focus
between press and release. Since the toggle depended entirely on `KEYUP`, pressing space
had no effect.

### Attempt 2 — KEYDOWN edge-trigger (also broken)

A subsequent fix used a `space_pressed` flag to gate the toggle:

```python
# Still broken: guard can get stuck True
if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
    if not self.space_pressed:
        self._toggle_pause(now)
        self.space_pressed = True
    return

if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
    self.space_pressed = False    # resets guard; doesn't trigger toggle
    return
```

This was intended to block OS key-repeat events (multiple KEYDOWN while key held).
However:

- `pygame.key.get_repeat()` returns `(0, 0)` — key repeat is **disabled** by default in
  pygame, so the guard is never needed.
- If a `KEYUP` is lost, `space_pressed` stays `True`, silently blocking every subsequent
  KEYDOWN. The user sees "space has no effect."

## The Fix

```python
if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
    if getattr(event, "repeat", 0):
        return
    self._toggle_pause(now)
    return
```

## Why This Design

| Concern | How it's handled |
|---|---|
| Toggle fires immediately | `KEYDOWN` triggers the action, no wait for release |
| Key repeat (OS auto-repeat) | `event.repeat` is ignored so hold-repeat does not re-toggle |
| KEYUP lost (window focus change, SDL2 quirk) | Harmless — no KEYUP dependency |
| Missing log lines in file | `logging.basicConfig(..., force=True)` ensures file handler is active |

## Files Changed

- `src/screens/battle_screen.py` — repeat-safe `KEYDOWN` pause handling
- `src/main.py` — centralized logging setup with forced handler replacement
- `tests/test_screens.py` — added `test_space_ignores_key_repeat`
- `tests/test_main.py` — added logging configuration regression test
