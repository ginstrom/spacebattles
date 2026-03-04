# Space Battle Manual

When you launch the game, you will see the enemy ship (top) and your ship
(bottom). The right panel shows each ship status and weapon list.

## Battle Sequence

1. The game starts paused.
2. Press `Space` to start or pause real-time combat.
3. While running, steer with `A` (turn left) and `D` (turn right).
4. While running, click any ready weapon on your ship card to fire it.
5. The computer steers toward you and fires automatically at intervals.
6. Weapon cooldowns are shown in seconds and tick down in real time.
7. The battle ends when either ship reaches `0 HP`.

## Movement and Waypoints

- Ship movement is continuous while unpaused.
- Movement speed is fixed at `screen height / 20 seconds`.
- Rotation speed is fixed at `90 degrees/second`.
- `A` turns your ship left and `D` turns your ship right.
- Your ship and the computer ship are clamped to map bounds.

### Planning a Route While Paused

1. Pause the game with `Space`.
2. Add waypoints by clicking on the map (left- or right-click).
3. A ghost route is drawn from your current position through all waypoints.
4. A ghost ship marker appears at the final waypoint.
5. A heading vector shows your current facing direction.
6. Unpause with `Space`; your ship will steer toward the first waypoint and continue through the queue.
7. Manual steering with `A` or `D` clears queued waypoints immediately.

## Editing User-Facing Configs (`data/weapons.yaml`)

User-editable gameplay config currently lives in:

- `data/weapons.yaml`

Each top-level key is a weapon name, and each weapon supports:

- `damage_min` (int): minimum damage on a hit
- `damage_max` (int): maximum damage on a hit
- `cooldown` (int): cooldown in turns from config (`1 turn = 5 seconds` in-game)
- `hit_chance` (int): percent hit chance from `1` to `100`
- `charges` (int or `null`): finite shots, or `null` for infinite

Example:

```yaml
Laser:
  damage_min: 40
  damage_max: 70
  cooldown: 2
  hit_chance: 90
  charges: null

Ion Beam:
  damage_min: 80
  damage_max: 120
  cooldown: 3
  hit_chance: 75
  charges: null
```

## Technical Reference

The game logic is modular. Here is an example of creating a ship and taking damage:

```python
from src.models.ship import Ship
from src.models.weapon import Weapon

# Create a ship with a laser
laser = Weapon("Laser", (10, 20), cooldown=2, hit_chance=90, charges=5)
ship = Ship("Testing Ship", 100, 100, [laser])

# Apply damage
ship.take_damage(30)
assert ship.hp == 70

# Weapon loader sample config parsing
from pathlib import Path
import tempfile

sample = '''
Test Laser:
  damage_min: 12
  damage_max: 20
  cooldown: 1
  hit_chance: 85
  charges: 4
'''
with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
    _ = f.write(sample)
    temp_path = f.name

loaded = Weapon.load_weapons(Path(temp_path))
assert loaded["Test Laser"].damage_range == (12, 20)
assert loaded["Test Laser"].charges == 4
```
