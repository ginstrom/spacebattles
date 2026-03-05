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
    accuracy_falloff_per_100px: float = 0.0
    min_hit_chance: int = 0
    damage_falloff_per_100px: float = 0.0
    min_damage_multiplier: float = 0.0

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
            weapons[wname] = Weapon(
                name=wname,
                damage_range=(stats["damage_min"], stats["damage_max"]),
                cooldown=stats["cooldown"],
                hit_chance=stats["hit_chance"],
                charges=stats.get("charges"),
                weapon_type=weapon_type,
                tech_level=tech_level,
                firing_arc_deg=firing_arc_deg,
                accuracy_falloff_per_100px=float(
                    stats.get("accuracy_falloff_per_100px", 0.0)
                ),
                min_hit_chance=max(0, min(100, int(stats.get("min_hit_chance", 0)))),
                damage_falloff_per_100px=max(
                    0.0, float(stats.get("damage_falloff_per_100px", 0.0))
                ),
                min_damage_multiplier=max(
                    0.0, min(1.0, float(stats.get("min_damage_multiplier", 0.0)))
                ),
            )
        return weapons

    def effective_hit_chance(self, distance_px: float) -> int:
        distance_units = max(0.0, float(distance_px)) / 100.0
        reduced = self.hit_chance - (self.accuracy_falloff_per_100px * distance_units)
        floor = max(0, min(100, int(self.min_hit_chance)))
        return max(floor, min(100, int(round(reduced))))

    def effective_damage_multiplier(self, distance_px: float) -> float:
        distance_units = max(0.0, float(distance_px)) / 100.0
        multiplier = 1.0 - (self.damage_falloff_per_100px * distance_units)
        floor = max(0.0, min(1.0, float(self.min_damage_multiplier)))
        return max(floor, min(1.0, multiplier))

    def can_fire(self) -> bool:
        return self.current_cooldown_seconds <= 0.0 and (
            self.charges is None or self.charges > 0)

    @property
    def cooldown_seconds(self) -> float:
        return self.cooldown * COOLDOWN_SECONDS_PER_TURN

    def fire(
        self,
        *,
        hit_chance_override: int | None = None,
        damage_multiplier: float = 1.0,
    ) -> tuple[bool, int]:
        """
        Returns (success, damage_dealt)
        """
        if not self.can_fire():
            return False, 0

        self.current_cooldown_seconds = self.cooldown_seconds

        if self.charges is not None:
            self.charges -= 1

        hit_chance = self.hit_chance if hit_chance_override is None else hit_chance_override
        hit_chance = max(0, min(100, int(round(hit_chance))))
        if random.randint(1, 100) > hit_chance:
            return False, 0

        damage_multiplier = max(0.0, float(damage_multiplier))
        min_dmg = int(round(self.damage_range[0] * damage_multiplier))
        max_dmg = int(round(self.damage_range[1] * damage_multiplier))
        min_dmg = max(0, min_dmg)
        max_dmg = max(min_dmg, max_dmg)
        return True, random.randint(min_dmg, max_dmg)

    def tick_seconds(self, dt_seconds: float) -> None:
        if self.current_cooldown_seconds > 0:
            self.current_cooldown_seconds = max(
                0.0, self.current_cooldown_seconds - dt_seconds
            )
