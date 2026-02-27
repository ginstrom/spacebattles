# Space Battle Manual

When you launch the game, you will see the enemy ship (top) and your ship
(bottom). The right panel shows each ship status and weapon list.

## Battle Sequence

1. Your turn starts in the `fire` phase.
2. Click any active weapon on your ship card to fire it.
3. You may fire multiple weapons in the same turn (as long as each weapon can
   fire).
4. Click `End Turn` to hand control to the computer.
5. The computer fires one available weapon, then its turn ends.
6. Cooldowns tick down when each ship's turn finishes.
7. The battle ends when either ship reaches `0 HP`.

## Editing User-Facing Configs (`data/weapons.yaml`)

User-editable gameplay config currently lives in:

- `data/weapons.yaml`

Each top-level key is a weapon name, and each weapon supports:

- `damage_min` (int): minimum damage on a hit
- `damage_max` (int): maximum damage on a hit
- `cooldown` (int): turns before that weapon can fire again
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
