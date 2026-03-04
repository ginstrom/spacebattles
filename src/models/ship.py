"""
Data model for ships, managing their state, health points (HP),
and weapon systems.
"""
from dataclasses import dataclass, field
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
    shield_max_hp: int = 100
    shields: list[int] = field(default_factory=list)
    systems: dict[str, dict[str, int]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.shields:
            self.shields = [int(self.shield_max_hp)] * 6
        elif len(self.shields) != 6:
            normalized = list(self.shields[:6])
            while len(normalized) < 6:
                normalized.append(int(self.shield_max_hp))
            self.shields = normalized

        if "weapons" not in self.systems:
            weapon_count = len(self.weapons)
            self.systems["weapons"] = {"current": weapon_count, "max": weapon_count}

    def is_dead(self) -> bool:
        return self.hull_hp <= 0

    def take_damage(self, dmg: int) -> None:
        self.hp = max(0, self.hp - dmg)

    @property
    def hull_max_hp(self) -> int:
        return self.max_hp

    @hull_max_hp.setter
    def hull_max_hp(self, value: int) -> None:
        self.max_hp = max(0, int(value))
        self.hp = min(self.hp, self.max_hp)

    @property
    def hull_hp(self) -> int:
        return self.hp

    @hull_hp.setter
    def hull_hp(self, value: int) -> None:
        self.hp = max(0, min(int(value), self.max_hp))

    def alive_system_names(self) -> list[str]:
        names: list[str] = []
        for name, state in self.systems.items():
            if state.get("current", 0) > 0 and state.get("max", 0) > 0:
                names.append(name)
        return names

    def absorb_shield_damage(self, shield_idx: int, damage: int) -> int:
        if damage <= 0:
            return 0
        idx = shield_idx % 6
        available = max(0, self.shields[idx])
        absorbed = min(available, damage)
        self.shields[idx] = available - absorbed
        return damage - absorbed

    def apply_overflow_damage(self, overflow_damage: int, hull_ratio: float = 0.7) -> None:
        if overflow_damage <= 0:
            return
        alive_systems = self.alive_system_names()
        if not alive_systems:
            self.take_damage(overflow_damage)
            return

        hull_damage = int(round(float(overflow_damage) * hull_ratio))
        hull_damage = max(0, min(hull_damage, overflow_damage))
        system_damage = overflow_damage - hull_damage

        if system_damage > 0:
            per_system = system_damage // len(alive_systems)
            remainder = system_damage % len(alive_systems)
            rolled_into_hull = 0
            for idx, name in enumerate(alive_systems):
                planned = per_system + (1 if idx < remainder else 0)
                current = self.systems[name]["current"]
                applied = min(current, planned)
                self.systems[name]["current"] = current - applied
                rolled_into_hull += planned - applied
            hull_damage += rolled_into_hull

        self.take_damage(hull_damage)
