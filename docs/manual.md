# Space Battle Manual

When you launch the game, you will see the enemy ship (top) and your ship
(bottom). Status appears on the right. Each turn, press SPACE to fire and
RETURN to end the turn. Keep going until someone dies.

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
```
