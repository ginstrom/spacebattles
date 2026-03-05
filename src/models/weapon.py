"""
Data model for ship weapons, encompassing damage ranges,
charge management, and firing logic.
"""
import random
import yaml
from dataclasses import dataclass
from pathlib import Path
from src.constants import COOLDOWN_SECONDS_PER_TURN


@dataclass
class Weapon:
    name: str
    damage_range: tuple[int, int]
    cooldown: int
    hit_chance: int
    current_cooldown_seconds: float = 0.0
    charges: int | None = None  # None = infinite, else consumes
    weapon_type: str = "heavy"
    tech_level: int = 1
    firing_arc_deg: float = 60.0
    facing_deg: float = 0.0

    @staticmethod
    def _default_weapon_type(name: str) -> str:
        return "light" if "laser" in name.lower() else "heavy"

    @staticmethod
    def _base_arc_for_type(weapon_type: str) -> float:
        return 120.0 if weapon_type.lower() == "light" else 60.0

    @staticmethod
    def load_weapons(file_path: str | Path) -> dict[str, "Weapon"]:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        weapons = {}
        for wname, stats in data.items():
            weapon_type = str(stats.get("weapon_type", Weapon._default_weapon_type(wname)))
            tech_level = max(1, int(stats.get("tech_level", 1)))
            if "firing_arc_deg" in stats:
                firing_arc_deg = float(stats["firing_arc_deg"])
            else:
                base_arc = Weapon._base_arc_for_type(weapon_type)
                tech_arc_bonus = float(stats.get("tech_arc_bonus_deg_per_level", 0.0))
                firing_arc_deg = base_arc + (tech_level - 1) * tech_arc_bonus
            firing_arc_deg = max(5.0, min(360.0, firing_arc_deg))
            facing_deg = float(stats.get("facing_deg", 0.0)) % 360.0
            weapons[wname] = Weapon(
                name=wname,
                damage_range=(stats["damage_min"], stats["damage_max"]),
                cooldown=stats["cooldown"],
                hit_chance=stats["hit_chance"],
                charges=stats.get("charges"),
                weapon_type=weapon_type,
                tech_level=tech_level,
                firing_arc_deg=firing_arc_deg,
                facing_deg=facing_deg,
            )
        return weapons

    def can_fire(self) -> bool:
        return self.current_cooldown_seconds <= 0.0 and (
            self.charges is None or self.charges > 0)

    @property
    def cooldown_seconds(self) -> float:
        return self.cooldown * COOLDOWN_SECONDS_PER_TURN

    def fire(self) -> tuple[bool, int]:
        """
        Returns (success, damage_dealt)
        """
        if not self.can_fire():
            return False, 0

        self.current_cooldown_seconds = self.cooldown_seconds

        if self.charges is not None:
            self.charges -= 1

        if random.randint(1, 100) > self.hit_chance:
            return False, 0

        return True, random.randint(*self.damage_range)

    def tick_seconds(self, dt_seconds: float) -> None:
        if self.current_cooldown_seconds > 0:
            self.current_cooldown_seconds = max(
                0.0, self.current_cooldown_seconds - dt_seconds
            )
