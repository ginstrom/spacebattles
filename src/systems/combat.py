"""
Combat system that handles the execution of attacks between ships,
decoupling combat logic from the UI.
"""
import math
from src.models.ship import Ship
from src.models.weapon import Weapon


class CombatSystem:
    @staticmethod
    def _distance_between(attacker_ship: Ship, defender_ship: Ship) -> float:
        return math.hypot(attacker_ship.x - defender_ship.x, attacker_ship.y - defender_ship.y)

    @staticmethod
    def _impact_shield_index(attacker_ship: Ship, defender_ship: Ship) -> int:
        dx = attacker_ship.x - defender_ship.x
        dy = attacker_ship.y - defender_ship.y
        incoming_heading = math.degrees(math.atan2(dx, -dy)) % 360.0
        relative_heading = (incoming_heading - defender_ship.heading) % 360.0
        return int(((relative_heading + 30.0) % 360.0) // 60.0)

    @staticmethod
    def execute_attack(attacker_ship: Ship, weapon: Weapon,
                       defender_ship: Ship) -> tuple[bool, int]:
        if not weapon or not weapon.can_fire():
            return False, 0

        distance_px = CombatSystem._distance_between(attacker_ship, defender_ship)
        hit, dmg = weapon.fire(
            hit_chance_override=weapon.effective_hit_chance(distance_px),
            damage_multiplier=weapon.effective_damage_multiplier(distance_px),
        )
        if hit:
            shield_idx = CombatSystem._impact_shield_index(attacker_ship, defender_ship)
            overflow = defender_ship.absorb_shield_damage(shield_idx, dmg)
            defender_ship.apply_overflow_damage(overflow, hull_ratio=0.7)
        return hit, dmg
