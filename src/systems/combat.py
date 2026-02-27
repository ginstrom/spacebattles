"""
Combat system that handles the execution of attacks between ships,
decoupling combat logic from the UI.
"""
from src.models.ship import Ship
from src.models.weapon import Weapon


class CombatSystem:
    @staticmethod
    def execute_attack(attacker_ship: Ship, weapon: Weapon,
                       defender_ship: Ship) -> tuple[bool, int]:
        if not weapon or not weapon.can_fire():
            return False, 0

        hit, dmg = weapon.fire()
        if hit:
            defender_ship.take_damage(dmg)
        return hit, dmg
