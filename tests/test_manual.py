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
  weapon_type: light
  tech_level: 2
  tech_arc_bonus_deg_per_level: 10
Ion Demo:
  damage_min: 20
  damage_max: 30
  cooldown: 2
  hit_chance: 70
  charges: null
  weapon_type: heavy
  firing_arc_deg: 75
"""
    cfg = tmp_path / "sample_weapons.yaml"
    cfg.write_text(sample)

    loaded = Weapon.load_weapons(Path(cfg))

    assert loaded["Test Laser"].damage_range == (12, 20)
    assert loaded["Test Laser"].cooldown == 1
    assert loaded["Test Laser"].hit_chance == 85
    assert loaded["Test Laser"].charges == 4
    assert loaded["Test Laser"].weapon_type == "light"
    assert loaded["Test Laser"].tech_level == 2
    assert loaded["Test Laser"].firing_arc_deg == 130.0
    assert loaded["Test Laser"].facing_deg == 0.0

    assert loaded["Ion Demo"].damage_range == (20, 30)
    assert loaded["Ion Demo"].charges is None
    assert loaded["Ion Demo"].weapon_type == "heavy"
    assert loaded["Ion Demo"].firing_arc_deg == 75.0
    assert loaded["Ion Demo"].facing_deg == 0.0


def test_manual_yaml_config_default_arc_uses_weapon_type_inference(tmp_path):
    sample = """
Pulse Laser:
  damage_min: 10
  damage_max: 14
  cooldown: 1
  hit_chance: 95
Plasma Cannon:
  damage_min: 30
  damage_max: 40
  cooldown: 3
  hit_chance: 70
"""
    cfg = tmp_path / "sample_weapons_defaults.yaml"
    cfg.write_text(sample)

    loaded = Weapon.load_weapons(Path(cfg))
    assert loaded["Pulse Laser"].weapon_type == "light"
    assert loaded["Pulse Laser"].firing_arc_deg == 120.0
    assert loaded["Pulse Laser"].facing_deg == 0.0
    assert loaded["Plasma Cannon"].weapon_type == "heavy"
    assert loaded["Plasma Cannon"].firing_arc_deg == 60.0
    assert loaded["Plasma Cannon"].facing_deg == 0.0


def test_manual_references_generated_screenshots():
    manual_text = Path("docs/manual.md").read_text(encoding="utf-8")
    expected_links = [
        "images/manual/battle-overview.png",
        "images/manual/waypoint-planning.png",
        "images/manual/combat-fire-exchange.png",
        "images/manual/weapon-arc-preview.png",
        "images/manual/zoomed-map.png",
        "images/manual/distance-falloff-details.png",
    ]
    for link in expected_links:
        assert link in manual_text
