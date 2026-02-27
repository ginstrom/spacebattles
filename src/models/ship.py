"""
Data model for ships, managing their state, health points (HP),
and weapon systems.
"""
from dataclasses import dataclass
from src.models.weapon import Weapon


@dataclass
class Ship:
    name: str
    max_hp: int
    hp: int
    weapons: list[Weapon]

    def is_dead(self) -> bool:
        return self.hp <= 0

    def take_damage(self, dmg: int) -> None:
        self.hp = max(0, self.hp - dmg)
