"""Tests aligned to executable examples in docs/manual.md."""

from pathlib import Path

from src.models.ship import Ship
from src.models.weapon import Weapon


def test_manual_ship_damage_example():
    laser = Weapon("Laser", (10, 20), cooldown=2, hit_chance=90, charges=5)
    ship = Ship("Testing Ship", 100, 100, [laser])
    ship.take_damage(30)
    assert ship.hp == 70


def test_manual_yaml_config_example_parses_all_fields(tmp_path):
    sample = """
Test Laser:
  damage_min: 12
  damage_max: 20
  cooldown: 1
  hit_chance: 85
  charges: 4
Ion Demo:
  damage_min: 20
  damage_max: 30
  cooldown: 2
  hit_chance: 70
  charges: null
"""
    cfg = tmp_path / "sample_weapons.yaml"
    cfg.write_text(sample)

    loaded = Weapon.load_weapons(Path(cfg))

    assert loaded["Test Laser"].damage_range == (12, 20)
    assert loaded["Test Laser"].cooldown == 1
    assert loaded["Test Laser"].hit_chance == 85
    assert loaded["Test Laser"].charges == 4

    assert loaded["Ion Demo"].damage_range == (20, 30)
    assert loaded["Ion Demo"].charges is None
