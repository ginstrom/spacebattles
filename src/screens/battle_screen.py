"""
The main battle screen implementation, managing turn-based combat
flow, player interaction, and CPU logic.
"""
import pygame
import random
from src.core.base_screen import BaseScreen
from src.constants import *
from src.models.ship import Ship
from src.models.weapon import Weapon
from src.utils.helpers import make_stars, wrap_text
from src.ui.map import Map
from src.ui.elements import draw_info_card
from src.systems.combat import CombatSystem


class BattleScreen(BaseScreen):
    def __init__(self, screen_manager):
        super().__init__(screen_manager)
        self.font = pygame.font.SysFont(None, 28)
        self.big_font = pygame.font.SysFont(None, 44)
        self.small_font = pygame.font.SysFont(None, 22)

        self.available_weapons = Weapon.load_weapons("data/weapons.yaml")
        self.player, self.cpu = self._make_game()
        self.map = Map(make_stars())

        self.turn = PLAYER_TURN
        self.phase = PHASE_FIRE
        self.message = "Your turn: choose a weapon."
        self.winner = None

        self.cpu_fire_at_ms = None
        self.CPU_DELAY_MS = 900

        self.weapon_buttons = {}
        self.weapon_detail_toggles = {}
        self.expanded_weapons = set()
        self.cpu_weapon_buttons = {}
        self.cpu_weapon_detail_toggles = {}
        self.cpu_expanded_weapons = set()
        self.ui_elements = {}
        self.panel_expanded = True
        self.toggle_tab_rect = pygame.Rect(
            WIDTH - TAB_W, HEIGHT // 2 - TAB_H // 2, TAB_W, TAB_H)

    def _make_game(self):
        # Create unique instances for each ship
        # To match the "From: [laser x 2] [ion beam x 1]" example:
        p_weapons = []
        laser = self.available_weapons["Laser"]
        ion = self.available_weapons["Ion Beam"]

        # Two lasers
        p_weapons.append(Weapon(laser.name, laser.damage_range,
                         laser.cooldown, laser.hit_chance, 0, laser.charges))
        p_weapons.append(Weapon(laser.name, laser.damage_range,
                         laser.cooldown, laser.hit_chance, 0, laser.charges))
        # One ion beam
        p_weapons.append(Weapon(ion.name, ion.damage_range,
                         ion.cooldown, ion.hit_chance, 0, ion.charges))

        c_weapons = []
        # Computer only gets Laser
        c_weapons.append(Weapon(laser.name, laser.damage_range,
                         laser.cooldown, laser.hit_chance, 0, laser.charges))

        player = Ship(
            name="Player",
            max_hp=750,
            hp=750,
            weapons=p_weapons,
        )
        cpu = Ship(
            name="Computer",
            max_hp=500,
            hp=500,
            weapons=c_weapons,
        )
        return player, cpu

    def handle_event(self, event):
        now = pygame.time.get_ticks()
        if self.winner is not None:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.player, self.cpu = self._make_game()
                self.turn = PLAYER_TURN
                self.phase = PHASE_FIRE
                self.message = "Your turn: choose a weapon."
                self.winner = None
                self.cpu_fire_at_ms = None
                self.weapon_buttons.clear()
                self.weapon_detail_toggles.clear()
                self.expanded_weapons.clear()
                self.cpu_weapon_buttons.clear()
                self.cpu_weapon_detail_toggles.clear()
                self.cpu_expanded_weapons.clear()
                self.ui_elements.clear()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.toggle_tab_rect.collidepoint(pos):
                self.panel_expanded = not self.panel_expanded
                self.weapon_buttons.clear()
                self.weapon_detail_toggles.clear()
                self.cpu_weapon_buttons.clear()
                self.cpu_weapon_detail_toggles.clear()
                self.ui_elements.clear()
            elif self.turn == PLAYER_TURN or self.turn == CPU_TURN:
                # Allow expanding weapons regardless of whose turn it is
                # Check player weapon detail toggles
                for idx, toggle_rect in self.weapon_detail_toggles.items():
                    if toggle_rect.collidepoint(pos):
                        if idx in self.expanded_weapons:
                            self.expanded_weapons.remove(idx)
                        else:
                            self.expanded_weapons.add(idx)
                        return

                # Check CPU weapon detail toggles
                for idx, toggle_rect in self.cpu_weapon_detail_toggles.items():
                    if toggle_rect.collidepoint(pos):
                        if idx in self.cpu_expanded_weapons:
                            self.cpu_expanded_weapons.remove(idx)
                        else:
                            self.cpu_expanded_weapons.add(idx)
                        return

                if self.turn == PLAYER_TURN and self.phase == PHASE_FIRE:
                    for idx, btn_rect in self.weapon_buttons.items():
                        if btn_rect.collidepoint(pos):
                            weapon = self.player.weapons[idx]
                            hit, dmg = CombatSystem.execute_attack(
                                self.player, weapon, self.cpu)
                            if hit:
                                self.message = (
                                    f"You fired {weapon.name} "
                                    f"for {dmg} damage. "
                                    "You can fire more weapons. "
                                    "Click 'End Turn'."
                                )
                            else:
                                self.message = (
                                    f"You fired {weapon.name} "
                                    "and MISSED. "
                                    "You can fire more weapons. "
                                    "Click 'End Turn'."
                                )

                            if self.cpu.is_dead():
                                self.winner = "Player"
                                self.message = "You win! Press R to restart."
                            break

                et_rect = self.ui_elements.get("end_turn")
                if et_rect and et_rect.collidepoint(pos):
                    self.turn = CPU_TURN
                    self.phase = PHASE_FIRE
                    self.cpu_fire_at_ms = now + self.CPU_DELAY_MS
                    self.message = "Computer is thinking..."
                    # Tick player weapons at end of turn
                    for w in self.player.weapons:
                        w.tick()

    def update(self, dt):
        now = pygame.time.get_ticks()
        if self.winner is None and self.turn == CPU_TURN:
            if self.phase == PHASE_FIRE:
                if (
                    self.cpu_fire_at_ms is not None
                    and now >= self.cpu_fire_at_ms
                ):
                    available = [w for w in self.cpu.weapons if w.can_fire()]
                    if not available:
                        self.message = "Computer has no weapons left."
                        self.phase = PHASE_END
                        self.cpu_fire_at_ms = now + self.CPU_DELAY_MS
                    else:
                        weapon = random.choice(available)
                        hit, dmg = CombatSystem.execute_attack(
                            self.cpu, weapon, self.player)
                        if hit:
                            self.message = (
                                f"Computer fired {weapon.name} "
                                f"for {dmg} damage."
                            )
                        else:
                            self.message = (
                                f"Computer fired {weapon.name} and MISSED."
                            )

                        if self.player.is_dead():
                            self.winner = "Computer"
                            self.message = "You lose. Press R to restart."
                        else:
                            self.phase = PHASE_END
                            self.cpu_fire_at_ms = now + self.CPU_DELAY_MS
            elif self.phase == PHASE_END:
                if (
                    self.cpu_fire_at_ms is not None
                    and now >= self.cpu_fire_at_ms
                ):
                    self.turn = PLAYER_TURN
                    self.phase = PHASE_FIRE
                    self.message = "Your turn: choose a weapon."
                    self.cpu_fire_at_ms = None
                    # Tick CPU weapons at start of player turn (which is end of
                    # CPU turn)
                    for w in self.cpu.weapons:
                        w.tick()

    def draw(self, screen):
        screen.fill(BG)
        panel_x = WIDTH - PANEL_W if self.panel_expanded else WIDTH
        map_w = WIDTH - PANEL_W if self.panel_expanded else WIDTH

        self.map.draw(screen, map_w, self.player, self.cpu,
                      self.turn, self.winner, self.font, self.small_font)

        if self.panel_expanded:
            self._draw_side_panel(screen, panel_x)
        else:
            self._draw_collapsed_bar(screen)

        self.toggle_tab_rect = self._draw_toggle_tab(screen, panel_x)

        if self.winner is not None:
            self._draw_winner_overlay(screen)

    def _draw_side_panel(self, surf, panel_x):
        panel_rect = pygame.Rect(panel_x, 0, PANEL_W, HEIGHT)
        pygame.draw.rect(surf, PANEL_BG, panel_rect)
        pygame.draw.line(surf, PANEL_BORDER, (panel_x, 0),
                         (panel_x, HEIGHT), 1)

        inner_x = panel_x + PANEL_PAD
        inner_w = PANEL_W - 2 * PANEL_PAD
        remaining_h = HEIGHT - 2 * PANEL_PAD - MSG_H
        card_h = remaining_h // 2 - PANEL_PAD // 2

        cpu_card_rect = pygame.Rect(inner_x, PANEL_PAD, inner_w, card_h)
        msg_y = cpu_card_rect.bottom + PANEL_PAD // 2
        msg_rect = pygame.Rect(inner_x, msg_y, inner_w, MSG_H)
        player_card_rect = pygame.Rect(
            inner_x, msg_rect.bottom + PANEL_PAD // 2, inner_w, card_h)

        draw_info_card(
            surf,
            cpu_card_rect,
            self.font,
            self.cpu,
            False,
            (self.turn == CPU_TURN),
            self.phase,
            self.winner,
            self.cpu_weapon_buttons,
            self.ui_elements,
            self.cpu_weapon_detail_toggles,
            self.cpu_expanded_weapons,
        )

        # Message strip
        pygame.draw.rect(surf, (20, 24, 38), msg_rect, border_radius=8)
        pygame.draw.rect(surf, PANEL_BORDER, msg_rect, 1, border_radius=8)
        lines = wrap_text(self.small_font, self.message, inner_w - 12)
        line_h = self.small_font.get_linesize() + 2
        text_y = msg_rect.y + (msg_rect.height - len(lines) * line_h) // 2
        for line in lines:
            line_surf = self.small_font.render(line, True, WHITE)
            surf.blit(line_surf, (msg_rect.x + 8, text_y))
            text_y += line_h

        draw_info_card(
            surf,
            player_card_rect,
            self.font,
            self.player,
            True,
            (self.turn == PLAYER_TURN),
            self.phase,
            self.winner,
            self.weapon_buttons,
            self.ui_elements,
            self.weapon_detail_toggles,
            self.expanded_weapons,
        )

    def _draw_collapsed_bar(self, screen):
        bar_h = 40
        overlay = pygame.Surface((WIDTH, bar_h), pygame.SRCALPHA)
        overlay.fill((10, 12, 22, 200))
        screen.blit(overlay, (0, HEIGHT - bar_h))
        msg_surf = self.small_font.render(self.message, True, WHITE)
        screen.blit(msg_surf, msg_surf.get_rect(
            center=(WIDTH // 2, HEIGHT - bar_h // 2)))

    def _draw_toggle_tab(self, surf, panel_x):
        if self.panel_expanded:
            tab_x = panel_x - TAB_W + 4
        else:
            tab_x = WIDTH - TAB_W
        tab_y = HEIGHT // 2 - TAB_H // 2
        tab_rect = pygame.Rect(tab_x, tab_y, TAB_W, TAB_H)
        pygame.draw.rect(surf, PANEL_BG, tab_rect, border_radius=8)
        pygame.draw.rect(surf, PANEL_BORDER, tab_rect, 2, border_radius=8)
        arrow = ">>" if self.panel_expanded else "<<"
        arrow_surf = self.small_font.render(arrow, True, WHITE)
        surf.blit(arrow_surf, arrow_surf.get_rect(center=tab_rect.center))
        return tab_rect

    def _draw_winner_overlay(self, screen):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        wtxt = self.big_font.render(f"{self.winner} wins!", True, WHITE)
        rtxt = self.font.render("Press R to restart", True, WHITE)
        screen.blit(wtxt, wtxt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        screen.blit(rtxt, rtxt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25)))
