"""pytest file built from docs/manual.md"""


def test_code_12():
    from src.models.ship import Ship
    from src.models.weapon import Weapon

    # Create a ship with a laser
    laser = Weapon("Laser", (10, 20), cooldown=2, hit_chance=90, charges=5)
    ship = Ship("Testing Ship", 100, 100, [laser])

    # Apply damage
    ship.take_damage(30)
    assert ship.hp == 70

    # Caution- no assertions.
