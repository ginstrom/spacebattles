# Directional Shields Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add six directional shields that absorb incoming damage before hull/system damage, render shields as six visible ring segments around ships, and show per-shield plus hull health in ship cards.

**Architecture:** Extend `Ship` with explicit combat-state fields (`hull_hp`, six directional shield pools, and system health map), then route all damage through a new directional damage resolver in combat. Keep UI rendering read-only against ship state: map ring segments derive from shield percentages, and card rows derive from shield/hull values. Treat weapon health as the first ship-system implementation behind a generic `systems` structure so future systems can be added without changing the damage pipeline.

**Tech Stack:** Python 3, pygame, pytest/unittest, existing `src/models`, `src/systems`, `src/ui`, `src/screens` modules.

---

## Scope Decisions For This Plan

1. Shield layout: six equal 60-degree sectors around defender heading.
2. Direction mapping: incoming attack vector is converted into defender-local angle; that angle picks the impacted shield sector.
3. Damage order: impacted shield -> overflow distributed to hull and systems.
4. Overflow distribution rule (initial): 70% hull, 30% systems; system portion is split across alive systems (currently weapons).
5. Destroyed condition: `hull_hp <= 0`.
6. Shield visuals: segment thickness scales with shield percentage; depleted segment renders as thin/dim.

### Task 1: Model directional shields and hull/system state

**Files:**
- Modify: `src/models/ship.py`
- Modify: `src/screens/battle_screen.py`
- Test: `tests/test_screens.py`
- Test: `tests/test_combat.py`

**Step 1: Write failing model tests for new ship state**

Add tests that assert new ships initialize:
- `hull_max_hp` and `hull_hp`
- `shield_max_hp` and `shields` length 6
- `systems` map containing at least `weapons` with current/max values

**Step 2: Run focused tests to confirm failure**

Run: `uv run pytest tests/test_combat.py tests/test_screens.py -k "ship or profile" -q`
Expected: failures for missing ship fields.

**Step 3: Implement ship state extensions**

In `Ship`:
- Replace legacy `hp/max_hp` ownership with hull-first fields (`hull_hp`, `hull_max_hp`) while preserving read compatibility via properties (`hp`, `max_hp`) during migration.
- Add shield constants/fields for six sectors.
- Add helpers:
  - `is_dead()` uses `hull_hp`
  - shield percentage lookup for rendering
  - `alive_system_names()` for damage routing

In `BattleScreen._make_game()`:
- Initialize ships with hull and shield defaults from config (use sane defaults if shield config is absent to avoid breaking existing YAML).
- Initialize `systems["weapons"]` health from weapon count/capacity.

**Step 4: Re-run focused tests**

Run: `uv run pytest tests/test_combat.py tests/test_screens.py -k "ship or profile" -q`
Expected: PASS for updated initialization behavior.

### Task 2: Implement directional damage resolution in combat system

**Files:**
- Modify: `src/systems/combat.py`
- Modify: `src/models/ship.py`
- Test: `tests/test_combat.py`

**Step 1: Write failing combat tests for shield-first damage**

Add tests covering:
- hit from a given direction reduces only one shield segment
- overflow after shield depletion applies to hull + systems per split
- no hull/system damage when shield fully absorbs
- ship destruction when hull reaches zero

**Step 2: Run failing combat tests**

Run: `uv run pytest tests/test_combat.py -q`
Expected: FAIL on missing directional shield behavior.

**Step 3: Implement minimal directional resolver**

In `CombatSystem`:
- Add helper to compute impacted shield index from attacker/defender positions and defender heading.
- Replace direct `defender_ship.take_damage(dmg)` with:
  - absorb into selected shield
  - compute overflow
  - apply overflow across hull/systems
- Return structured result (or maintain tuple and add optional details) so callers can message shield hits later.

In `Ship`:
- Add methods for shield absorption and overflow application to keep domain logic in model.

**Step 4: Re-run combat tests**

Run: `uv run pytest tests/test_combat.py -q`
Expected: PASS.

### Task 3: Update battle flow to use hull destruction and richer combat outcomes

**Files:**
- Modify: `src/screens/battle_screen.py`
- Test: `tests/test_screens.py`

**Step 1: Write failing screen tests for destruction checks/messages**

Add/adjust tests ensuring:
- battle ends when `hull_hp` reaches zero
- existing hit/miss messaging still works with combat return shape

**Step 2: Run targeted screen tests**

Run: `uv run pytest tests/test_screens.py -k "cpu_update or handle_event_weapon_click or wins" -q`
Expected: FAIL where old `hp` assumptions remain.

**Step 3: Implement battle-screen integration**

- Update player/cpu fire paths to consume updated combat results.
- Keep existing UX text, adding shield-specific info only if trivial (`Shield 3 absorbed X`).
- Ensure `_finish_game` checks remain based on `is_dead()` only.

**Step 4: Re-run targeted screen tests**

Run: `uv run pytest tests/test_screens.py -k "cpu_update or handle_event_weapon_click or wins" -q`
Expected: PASS.

### Task 4: Render six shield segments around each ship

**Files:**
- Modify: `src/ui/map.py`
- Test: `tests/test_ui.py`

**Step 1: Write failing map/UI tests for segmented shield ring**

Add tests that verify:
- ring rendering uses six arc/segment draws instead of one circle outline
- segment draw thickness changes with shield strength (high > low)
- map no longer calls single-ring `draw.circle` for shield boundary

**Step 2: Run targeted UI tests**

Run: `uv run pytest tests/test_ui.py -k "map_draw" -q`
Expected: FAIL until segmented drawing exists.

**Step 3: Implement segmented rendering in map**

In `Map.draw()`:
- replace single circle shield ring with helper `draw_shield_segments(ship, cx, cy)`.
- draw 6 sectors in ship-local orientation (sector 0 centered on forward direction).
- map shield percent to line width (example: 1-6 px).

**Step 4: Re-run targeted UI tests**

Run: `uv run pytest tests/test_ui.py -k "map_draw" -q`
Expected: PASS.

### Task 5: Show per-shield and hull health in ship cards

**Files:**
- Modify: `src/ui/elements.py`
- Test: `tests/test_ui.py`

**Step 1: Write failing card tests for shield/hull rows**

Add tests that assert `draw_info_card` renders text/rows for:
- `Hull: current / max`
- six shield lines (or compact 2x3 grid labels)

**Step 2: Run targeted card tests**

Run: `uv run pytest tests/test_ui.py -k "draw_info_card" -q`
Expected: FAIL on missing shield/hull display.

**Step 3: Implement info-card health layout updates**

- Replace legacy single HP bar with hull bar + per-shield indicators.
- Keep weapon button layout intact by making health block vertically compact.
- Preserve CPU/player shared rendering behavior.

**Step 4: Re-run targeted card tests**

Run: `uv run pytest tests/test_ui.py -k "draw_info_card" -q`
Expected: PASS.

### Task 6: Add configuration defaults and migration safety

**Files:**
- Modify: `data/ships.yaml`
- Modify: `src/screens/battle_screen.py`
- Test: `tests/test_screens.py`

**Step 1: Write failing tests for config-driven shield values**

Add tests for:
- loading explicit `shield_max_hp` (and optional per-sector values if present)
- fallback defaults when fields are absent

**Step 2: Run targeted config tests**

Run: `uv run pytest tests/test_screens.py -k "profiles_are_loaded_from_config" -q`
Expected: FAIL before parser updates.

**Step 3: Implement config parsing updates**

- Extend ship config schema with shield settings.
- Keep backward compatibility with current files by defaulting fields.

**Step 4: Re-run targeted config tests**

Run: `uv run pytest tests/test_screens.py -k "profiles_are_loaded_from_config" -q`
Expected: PASS.

### Task 7: Full verification and cleanup

**Files:**
- Modify: `tests/test_combat.py`
- Modify: `tests/test_ui.py`
- Modify: `tests/test_screens.py`
- Optional doc note: `docs/manual.md`

**Step 1: Run full test suite**

Run: `uv run pytest -q`
Expected: PASS.

**Step 2: Manual gameplay verification**

Run: `make run`
Check:
- attacks from different directions reduce different shield segments
- depleted shield allows overflow into hull/systems
- ring segment thickness updates as shields drop
- card tracks six shields + hull
- ship is destroyed exactly when hull reaches 0

**Step 3: Commit in logical slices**

Suggested commit sequence:
1. `feat(ship): add hull and six-shield combat state`
2. `feat(combat): route damage through directional shields and overflow`
3. `feat(ui): render segmented shield ring and card shield metrics`
4. `test: cover shield direction, overflow, and ui rendering`

## Risks and Mitigations

1. Risk: heading math can map attacks to wrong sector near boundaries.
Mitigation: add boundary-angle tests at 59/60/61 degrees and normalize with modulo helpers.
2. Risk: card layout overflow can hide weapon controls on small heights.
Mitigation: cap health block height and abbreviate shield labels (`S1..S6`).
3. Risk: return-signature changes in `CombatSystem.execute_attack` break callers/tests.
Mitigation: add transitional compatibility path and update all call sites in same commit.

## Out of Scope (for this plan)

1. Shield regeneration over time.
2. System-specific debuffs beyond health tracking.
3. New systems besides weapons.
4. Detailed combat log panel/history.
