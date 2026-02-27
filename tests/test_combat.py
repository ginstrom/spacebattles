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
        self.assertEqual(w.current_cooldown, 2)
        self.assertFalse(w.can_fire())

        w.tick()
        w.tick()
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

    def test_combat_system(self):
        w = Weapon("Laser", (10, 10), cooldown=1, hit_chance=100, charges=1)
        attacker = Ship("Attacker", 100, 100, [w])
        defender = Ship("Defender", 100, 100, [])

        success, dmg = CombatSystem.execute_attack(attacker, w, defender)
        self.assertTrue(success)
        self.assertEqual(dmg, 10)
        self.assertEqual(defender.hp, 90)
        self.assertEqual(w.charges, 0)

    def test_combat_system_on_cooldown(self):
        w = Weapon("Laser", (10, 10), cooldown=1, hit_chance=100, charges=1)
        w.current_cooldown = 1
        attacker = Ship("Attacker", 100, 100, [w])
        defender = Ship("Defender", 100, 100, [])
        success, dmg = CombatSystem.execute_attack(attacker, w, defender)
        self.assertFalse(success)
        self.assertEqual(dmg, 0)


if __name__ == '__main__':
    unittest.main()
