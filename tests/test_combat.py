import unittest
from src.models.weapon import Weapon
from src.models.ship import Ship
from src.systems.combat import CombatSystem


class TestCombat(unittest.TestCase):
    def test_weapon_fire(self):
        w = Weapon("Laser", (10, 20), cooldown=2, hit_chance=100, charges=2)
        self.assertTrue(w.can_fire())
        hit, dmg = w.fire()
        self.assertTrue(hit)
        self.assertGreaterEqual(dmg, 10)
        self.assertLessEqual(dmg, 20)
        self.assertEqual(w.charges, 1)
        self.assertEqual(w.current_cooldown_seconds, 10.0)
        self.assertFalse(w.can_fire())

        w.tick_seconds(5.0)
        w.tick_seconds(5.0)
        self.assertTrue(w.can_fire())
        w.fire()
        self.assertEqual(w.charges, 0)
        self.assertFalse(w.can_fire())
        hit, dmg = w.fire()
        self.assertFalse(hit)
        self.assertEqual(dmg, 0)

    def test_ship_damage(self):
        s = Ship("Test", 100, 100, [])
        s.take_damage(30)
        self.assertEqual(s.hp, 70)
        s.take_damage(100)
        self.assertEqual(s.hp, 0)
        self.assertTrue(s.is_dead())
        self.assertEqual(s.hull_hp, 0)

    def test_ship_initializes_hull_shields_and_systems(self):
        s = Ship("Test", 100, 100, [])
        self.assertEqual(s.hull_max_hp, 100)
        self.assertEqual(s.hull_hp, 100)
        self.assertEqual(s.shield_max_hp, 100)
        self.assertEqual(len(s.shields), 6)
        self.assertTrue(all(v == 100 for v in s.shields))
        self.assertIn("weapons", s.systems)

    def test_combat_system(self):
        w = Weapon("Laser", (10, 10), cooldown=1, hit_chance=100, charges=1)
        attacker = Ship("Attacker", 100, 100, [w])
        defender = Ship("Defender", 100, 100, [])
        defender.shields = [0, 0, 0, 0, 0, 0]

        success, dmg = CombatSystem.execute_attack(attacker, w, defender)
        self.assertTrue(success)
        self.assertEqual(dmg, 10)
        self.assertEqual(defender.hp, 90)
        self.assertEqual(w.charges, 0)

    def test_combat_system_on_cooldown(self):
        w = Weapon("Laser", (10, 10), cooldown=1, hit_chance=100, charges=1)
        w.current_cooldown_seconds = 1.0
        attacker = Ship("Attacker", 100, 100, [w])
        defender = Ship("Defender", 100, 100, [])
        success, dmg = CombatSystem.execute_attack(attacker, w, defender)
        self.assertFalse(success)
        self.assertEqual(dmg, 0)

    def test_directional_shield_absorbs_damage_before_hull(self):
        w = Weapon("Laser", (10, 10), cooldown=1, hit_chance=100, charges=1)
        attacker = Ship("Attacker", 100, 100, [w], x=0.0, y=-100.0)
        defender = Ship("Defender", 100, 100, [], x=0.0, y=0.0, heading=0.0)
        defender.shields = [20, 20, 20, 20, 20, 20]

        success, _ = CombatSystem.execute_attack(attacker, w, defender)
        self.assertTrue(success)
        self.assertEqual(defender.shields[0], 10)
        self.assertEqual(defender.hull_hp, 100)

    def test_overflow_damage_uses_70_30_hull_system_split(self):
        w = Weapon("Laser", (10, 10), cooldown=1, hit_chance=100, charges=1)
        attacker = Ship("Attacker", 100, 100, [w], x=0.0, y=-100.0)
        defender = Ship(
            "Defender",
            100,
            100,
            [],
            x=0.0,
            y=0.0,
            heading=0.0,
            systems={"weapons": {"current": 10, "max": 10}},
        )
        defender.shields = [0, 20, 20, 20, 20, 20]

        success, _ = CombatSystem.execute_attack(attacker, w, defender)
        self.assertTrue(success)
        self.assertEqual(defender.hull_hp, 93)
        self.assertEqual(defender.systems["weapons"]["current"], 7)

    def test_ship_destroyed_when_hull_reaches_zero(self):
        w = Weapon("Laser", (10, 10), cooldown=1, hit_chance=100, charges=1)
        attacker = Ship("Attacker", 100, 100, [w], x=0.0, y=-100.0)
        defender = Ship("Defender", 5, 5, [], x=0.0, y=0.0, heading=0.0)
        defender.shields = [0, 0, 0, 0, 0, 0]

        success, _ = CombatSystem.execute_attack(attacker, w, defender)
        self.assertTrue(success)
        self.assertEqual(defender.hull_hp, 0)
        self.assertTrue(defender.is_dead())


if __name__ == '__main__':
    unittest.main()
