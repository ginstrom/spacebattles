"""
Data model for ship weapons, encompassing damage ranges,
charge management, and firing logic.
"""
import random
import yaml
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Weapon:
    name: str
    damage_range: tuple[int, int]
    cooldown: int
    hit_chance: int
    current_cooldown: int = 0
    charges: int | None = None  # None = infinite, else consumes

    @staticmethod
    def load_weapons(file_path: str | Path) -> dict[str, "Weapon"]:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        weapons = {}
        for wname, stats in data.items():
            weapons[wname] = Weapon(
                name=wname,
                damage_range=(stats["damage_min"], stats["damage_max"]),
                cooldown=stats["cooldown"],
                hit_chance=stats["hit_chance"],
                charges=stats.get("charges")
            )
        return weapons

    def can_fire(self) -> bool:
        return self.current_cooldown == 0 and (
            self.charges is None or self.charges > 0)

    def fire(self) -> tuple[bool, int]:
        """
        Returns (success, damage_dealt)
        """
        if not self.can_fire():
            return False, 0

        self.current_cooldown = self.cooldown

        if self.charges is not None:
            self.charges -= 1

        if random.randint(1, 100) > self.hit_chance:
            return False, 0

        return True, random.randint(*self.damage_range)

    def tick(self) -> None:
        if self.current_cooldown > 0:
            self.current_cooldown -= 1
