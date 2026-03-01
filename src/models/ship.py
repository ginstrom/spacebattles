"""
Data model for ships, managing their state, health points (HP),
and weapon systems.
"""
from dataclasses import dataclass
from src.constants import HEIGHT
from src.models.weapon import Weapon


@dataclass
class Ship:
    name: str
    max_hp: int
    hp: int
    weapons: list[Weapon]
    x: float = 0.0
    y: float = 0.0
    heading: float = 0.0
    speed_px_s: float = HEIGHT / 20.0
    rotation_speed_deg_s: float = 90.0

    def is_dead(self) -> bool:
        return self.hp <= 0

    def take_damage(self, dmg: int) -> None:
        self.hp = max(0, self.hp - dmg)
