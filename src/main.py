import pygame
import random
from dataclasses import dataclass

# ----------------------------
# Config
# ----------------------------
WIDTH, HEIGHT = 900, 700
FPS = 60

BG = (15, 18, 26)
PANEL_BG = (28, 34, 50)
PANEL_BORDER = (55, 70, 110)
WHITE = (240, 240, 240)
GRAY = (120, 120, 120)
GREEN = (80, 220, 120)
RED = (230, 80, 80)
BLUE = (90, 160, 255)
YELLOW = (245, 220, 90)

PLAYER_TURN = "player"
CPU_TURN = "cpu"

PANEL_W = 320       # expanded panel width
TAB_W = 22          # toggle tab width
TAB_H = 64          # toggle tab height
PANEL_PAD = 14      # padding inside panel
MSG_H = 68          # message strip height


# ----------------------------
# Data Models
# ----------------------------
@dataclass
class Weapon:
    name: str
    damage_range: tuple[int, int]
    charges: int | None  # None = infinite, else consumes

    def can_fire(self) -> bool:
        return self.charges is None or self.charges > 0

    def fire(self) -> int:
        if not self.can_fire():
            return 0
        if self.charges is not None:
            self.charges -= 1
        return random.randint(*self.damage_range)


@dataclass
class Ship:
    name: str
    max_hp: int
    hp: int
    weapons: dict[str, Weapon]

    def is_dead(self) -> bool:
        return self.hp <= 0

    def take_damage(self, dmg: int) -> None:
        self.hp = max(0, self.hp - dmg)


# ----------------------------
# UI Helpers
# ----------------------------
def hp_color(hp: int, max_hp: int) -> tuple[int, int, int]:
    pct = hp / max_hp if max_hp > 0 else 0
    if pct > 0.4:
        return GREEN
    elif pct > 0.2:
        return YELLOW
    return RED


def draw_enemy_icon(surf: pygame.Surface, cx: int, cy: int, size: int) -> None:
    """Downward-pointing triangle representing the enemy ship."""
    half = size // 2
    points = [
        (cx, cy + half),
        (cx - half, cy - half),
        (cx + half, cy - half),
    ]
    pygame.draw.polygon(surf, (90, 130, 200), points)
    pygame.draw.polygon(surf, PANEL_BORDER, points, 2)


def draw_player_icon(surf: pygame.Surface, cx: int, cy: int, size: int) -> None:
    """Circle with a small head circle and a vertical body line inside."""
    half = size // 2
    pygame.draw.circle(surf, (180, 110, 70), (cx, cy), half)
    pygame.draw.circle(surf, PANEL_BORDER, (cx, cy), half, 2)
    head_r = max(4, size // 9)
    head_cy = cy - half // 3
    pygame.draw.circle(surf, WHITE, (cx, head_cy), head_r)
    body_top = head_cy + head_r
    body_bot = cy + half // 3
    pygame.draw.line(surf, WHITE, (cx, body_top), (cx, body_bot), 2)


# ----------------------------
# Stars
# ----------------------------
def make_stars(n: int = 150) -> list[tuple[int, int, int, int]]:
    """Return list of (x, y, brightness, size) tuples spread across the full window."""
    stars = []
    for _ in range(n):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        brightness = random.randint(120, 255)
        size = random.randint(1, 3)
        stars.append((x, y, brightness, size))
    return stars


# ----------------------------
# Text Helpers
# ----------------------------
def wrap_text(font: pygame.font.Font, text: str, max_w: int) -> list[str]:
    """Word-wrap text to fit within max_w pixels, return list of line strings."""
    words = text.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [""]


# ----------------------------
# Draw: Map (left area)
# ----------------------------
def draw_map(
    surf: pygame.Surface,
    map_w: int,
    stars: list[tuple[int, int, int, int]],
    player: Ship,
    cpu: Ship,
    turn: str,
    winner: str | None,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
) -> None:
    """Draw the starfield, ships, HP bars, labels, and active-turn highlight ring."""
    # Clip drawing to the map area
    clip_rect = pygame.Rect(0, 0, map_w, HEIGHT)
    surf.set_clip(clip_rect)

    # Starfield
    for sx, sy, brightness, size in stars:
        if sx < map_w:
            c = (brightness, brightness, brightness)
            if size <= 1:
                surf.set_at((sx, sy), c)
            else:
                pygame.draw.circle(surf, c, (sx, sy), size // 2)

    surf.set_clip(None)

    # Vertical divider line at the map/panel boundary
    pygame.draw.line(surf, PANEL_BORDER, (map_w, 0), (map_w, HEIGHT), 1)

    # --- CPU ship (upper center of map) ---
    cpu_cx = map_w // 2
    cpu_cy = HEIGHT // 4
    icon_size = 64

    # Active turn highlight ring
    if turn == CPU_TURN and winner is None:
        pygame.draw.circle(surf, BLUE, (cpu_cx, cpu_cy), icon_size // 2 + 10, 2)

    draw_enemy_icon(surf, cpu_cx, cpu_cy, icon_size)

    # CPU name label
    name_surf = small_font.render(cpu.name, True, WHITE)
    surf.blit(name_surf, name_surf.get_rect(centerx=cpu_cx, top=cpu_cy + icon_size // 2 + 12))

    # CPU HP bar
    bar_w = 100
    bar_h = 8
    bar_x = cpu_cx - bar_w // 2
    bar_y = cpu_cy + icon_size // 2 + 12 + name_surf.get_height() + 4
    pygame.draw.rect(surf, (60, 60, 80), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    fill_w = int(bar_w * max(0, cpu.hp) / cpu.max_hp) if cpu.max_hp > 0 else 0
    if fill_w > 0:
        pygame.draw.rect(
            surf, hp_color(cpu.hp, cpu.max_hp),
            (bar_x, bar_y, fill_w, bar_h), border_radius=4,
        )

    # --- Player ship (lower center of map) ---
    player_cx = map_w // 2
    player_cy = HEIGHT * 3 // 4

    # Active turn highlight ring
    if turn == PLAYER_TURN and winner is None:
        pygame.draw.circle(surf, BLUE, (player_cx, player_cy), icon_size // 2 + 10, 2)

    draw_player_icon(surf, player_cx, player_cy, icon_size)

    # Player name label (above icon for bottom ship — place below and above both work;
    # put it above so it doesn't run into the bottom edge)
    p_name_surf = small_font.render(player.name, True, WHITE)
    surf.blit(
        p_name_surf,
        p_name_surf.get_rect(centerx=player_cx, bottom=player_cy - icon_size // 2 - 12),
    )

    # Player HP bar (above icon)
    p_bar_y = player_cy - icon_size // 2 - 12 - bar_h - 4
    p_bar_x = player_cx - bar_w // 2
    pygame.draw.rect(surf, (60, 60, 80), (p_bar_x, p_bar_y, bar_w, bar_h), border_radius=4)
    p_fill_w = int(bar_w * max(0, player.hp) / player.max_hp) if player.max_hp > 0 else 0
    if p_fill_w > 0:
        pygame.draw.rect(
            surf, hp_color(player.hp, player.max_hp),
            (p_bar_x, p_bar_y, p_fill_w, bar_h), border_radius=4,
        )


# ----------------------------
# Draw: Info Card
# ----------------------------
def draw_info_card(
    surf: pygame.Surface,
    rect: pygame.Rect,
    font: pygame.font.Font,
    ship: Ship,
    is_player: bool,
    active_turn: bool,
    winner: str | None,
    weapon_buttons_out: dict[str, pygame.Rect],
) -> None:
    """
    Draw a rounded card with name, HP bar, HP text, weapons label, and weapon
    buttons (player) or weapon text list (CPU). No ship icon column.
    """
    border_color = BLUE if (active_turn and winner is None) else PANEL_BORDER
    pygame.draw.rect(surf, PANEL_BG, rect, border_radius=12)
    pygame.draw.rect(surf, border_color, rect, 2, border_radius=12)

    pad = 12
    tx = rect.x + pad
    ty = rect.y + pad
    content_w = rect.width - 2 * pad
    line_h = font.get_linesize() + 2

    # Ship name
    name_surf = font.render(ship.name, True, WHITE)
    surf.blit(name_surf, (tx, ty))
    ty += line_h + 4

    # Graphical HP bar
    bar_h = 10
    bar_w = content_w
    pygame.draw.rect(surf, (50, 55, 75), (tx, ty, bar_w, bar_h), border_radius=5)
    fill_w = int(bar_w * max(0, ship.hp) / ship.max_hp) if ship.max_hp > 0 else 0
    if fill_w > 0:
        pygame.draw.rect(
            surf, hp_color(ship.hp, ship.max_hp),
            (tx, ty, fill_w, bar_h), border_radius=5,
        )
    ty += bar_h + 4

    # HP text
    hp_str = f"HP: {ship.hp} / {ship.max_hp}"
    hp_surf = font.render(hp_str, True, hp_color(ship.hp, ship.max_hp))
    surf.blit(hp_surf, (tx, ty))
    ty += line_h + 6

    # Weapons label
    weapons_label = font.render("Weapons:", True, GRAY)
    surf.blit(weapons_label, (tx, ty))
    ty += line_h

    if is_player:
        weapon_buttons_out.clear()
        btn_h = line_h + 8
        btn_gap = 6
        bx = tx
        for wname, w in ship.weapons.items():
            charges_part = str(w.charges) if w.charges is not None else "\u221e"
            label = f"{charges_part}x {wname}"
            enabled = active_turn and w.can_fire() and winner is None
            color = BLUE if enabled else GRAY
            text_color = WHITE if enabled else (160, 160, 160)

            btn_surf = font.render(label, True, text_color)
            btn_w = btn_surf.get_width() + 24
            # Wrap to next row if it would overflow
            if bx + btn_w > rect.right - pad and bx > tx:
                bx = tx
                ty += btn_h + btn_gap

            btn_rect = pygame.Rect(bx, ty, btn_w, btn_h)
            pygame.draw.rect(surf, color, btn_rect, border_radius=8)
            pygame.draw.rect(surf, (30, 30, 45), btn_rect, 1, border_radius=8)
            surf.blit(btn_surf, (bx + 12, ty + (btn_h - btn_surf.get_height()) // 2))

            weapon_buttons_out[wname] = btn_rect
            bx += btn_w + btn_gap
    else:
        for wname, w in ship.weapons.items():
            charges_part = str(w.charges) if w.charges is not None else "\u221e"
            weapon_line = f"  {charges_part}x {wname}"
            w_surf = font.render(weapon_line, True, WHITE)
            surf.blit(w_surf, (tx, ty))
            ty += line_h


# ----------------------------
# Draw: Side Panel
# ----------------------------
def draw_side_panel(
    surf: pygame.Surface,
    panel_x: int,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    player: Ship,
    cpu: Ship,
    turn: str,
    winner: str | None,
    message: str,
    weapon_buttons_out: dict[str, pygame.Rect],
) -> None:
    """
    Draw the full right-side panel: dark background, CPU info card (top),
    message strip (middle), player info card (bottom).
    """
    panel_rect = pygame.Rect(panel_x, 0, PANEL_W, HEIGHT)
    pygame.draw.rect(surf, PANEL_BG, panel_rect)
    pygame.draw.line(surf, PANEL_BORDER, (panel_x, 0), (panel_x, HEIGHT), 1)

    inner_x = panel_x + PANEL_PAD
    inner_w = PANEL_W - 2 * PANEL_PAD

    # Distribute vertical space: cpu card, message strip, player card
    # Give equal height to both cards; message strip is fixed MSG_H
    remaining_h = HEIGHT - 2 * PANEL_PAD - MSG_H
    card_h = remaining_h // 2 - PANEL_PAD // 2

    cpu_card_rect = pygame.Rect(inner_x, PANEL_PAD, inner_w, card_h)
    msg_y = cpu_card_rect.bottom + PANEL_PAD // 2
    msg_rect = pygame.Rect(inner_x, msg_y, inner_w, MSG_H)
    player_card_rect = pygame.Rect(inner_x, msg_rect.bottom + PANEL_PAD // 2, inner_w, card_h)

    # CPU info card
    draw_info_card(
        surf, cpu_card_rect, font, cpu,
        is_player=False,
        active_turn=(turn == CPU_TURN),
        winner=winner,
        weapon_buttons_out={},
    )

    # Message strip
    pygame.draw.rect(surf, (20, 24, 38), msg_rect, border_radius=8)
    pygame.draw.rect(surf, PANEL_BORDER, msg_rect, 1, border_radius=8)

    lines = wrap_text(small_font, message, inner_w - 12)
    line_h = small_font.get_linesize() + 2
    total_text_h = len(lines) * line_h
    text_y = msg_rect.y + (msg_rect.height - total_text_h) // 2
    for line in lines:
        line_surf = small_font.render(line, True, WHITE)
        surf.blit(line_surf, (msg_rect.x + 8, text_y))
        text_y += line_h

    # Player info card
    draw_info_card(
        surf, player_card_rect, font, player,
        is_player=True,
        active_turn=(turn == PLAYER_TURN),
        winner=winner,
        weapon_buttons_out=weapon_buttons_out,
    )


# ----------------------------
# Draw: Toggle Tab
# ----------------------------
def draw_toggle_tab(
    surf: pygame.Surface,
    panel_x: int,
    panel_expanded: bool,
    small_font: pygame.font.Font,
) -> pygame.Rect:
    """
    Draw the rounded-corner toggle tab and return its pygame.Rect.
    When expanded the tab protrudes slightly into the map; when collapsed
    it sits at the right window edge.
    """
    if panel_expanded:
        tab_x = panel_x - TAB_W + 4
    else:
        tab_x = WIDTH - TAB_W

    tab_y = HEIGHT // 2 - TAB_H // 2
    tab_rect = pygame.Rect(tab_x, tab_y, TAB_W, TAB_H)

    pygame.draw.rect(surf, PANEL_BG, tab_rect, border_radius=8)
    pygame.draw.rect(surf, PANEL_BORDER, tab_rect, 2, border_radius=8)

    arrow = "<" if panel_expanded else ">"
    arrow_surf = small_font.render(arrow, True, WHITE)
    surf.blit(arrow_surf, arrow_surf.get_rect(center=tab_rect.center))

    return tab_rect


# ----------------------------
# Game Setup
# ----------------------------
def make_game() -> tuple[Ship, Ship]:
    player = Ship(
        name="Player",
        max_hp=750,
        hp=750,
        weapons={
            "Laser": Weapon("Laser", (40, 70), charges=2),
            "Ion Beam": Weapon("Ion Beam", (80, 120), charges=1),
        },
    )

    cpu = Ship(
        name="Computer",
        max_hp=500,
        hp=500,
        weapons={
            "Laser": Weapon("Laser", (35, 65), charges=3),
        },
    )

    return player, cpu


# ----------------------------
# Main
# ----------------------------
def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Turn-Based Ship Duel")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 28)
    big = pygame.font.SysFont(None, 44)
    small_font = pygame.font.SysFont(None, 22)

    player, cpu = make_game()
    stars = make_stars()

    turn = PLAYER_TURN
    message = "Your turn: choose a weapon."
    winner: str | None = None

    cpu_fire_at_ms: int | None = None
    CPU_DELAY_MS = 900

    # weapon_buttons maps weapon name -> pygame.Rect; populated by draw_side_panel
    # each frame and consumed by the event loop on the next frame.
    weapon_buttons: dict[str, pygame.Rect] = {}

    panel_expanded: bool = True
    # Placeholder rect — updated to real value on first draw call each frame.
    toggle_tab_rect: pygame.Rect = pygame.Rect(WIDTH - TAB_W, HEIGHT // 2 - TAB_H // 2, TAB_W, TAB_H)

    running = True
    while running:
        clock.tick(FPS)
        now = pygame.time.get_ticks()

        # --- Derived layout values ---
        panel_x = WIDTH - PANEL_W if panel_expanded else WIDTH
        map_w = WIDTH - PANEL_W if panel_expanded else WIDTH

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if winner is not None:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    player, cpu = make_game()
                    turn = PLAYER_TURN
                    message = "Your turn: choose a weapon."
                    winner = None
                    cpu_fire_at_ms = None
                    weapon_buttons.clear()
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                # Toggle tab takes priority
                if toggle_tab_rect.collidepoint(pos):
                    panel_expanded = not panel_expanded
                    weapon_buttons.clear()
                elif turn == PLAYER_TURN:
                    for wname, btn_rect in weapon_buttons.items():
                        w = player.weapons.get(wname)
                        if w and btn_rect.collidepoint(pos) and w.can_fire():
                            dmg = w.fire()
                            cpu.take_damage(dmg)
                            message = f"You fired {w.name} for {dmg} damage."

                            if cpu.is_dead():
                                winner = "Player"
                                message = "You win! Press R to restart."
                            else:
                                turn = CPU_TURN
                                cpu_fire_at_ms = now + CPU_DELAY_MS
                            break

        # --- CPU Turn Logic ---
        if winner is None and turn == CPU_TURN:
            if cpu_fire_at_ms is not None and now >= cpu_fire_at_ms:
                available = [w for w in cpu.weapons.values() if w.can_fire()]
                if not available:
                    message = "Computer has no weapons left. Your turn."
                    turn = PLAYER_TURN
                    cpu_fire_at_ms = None
                else:
                    w = random.choice(available)
                    dmg = w.fire()
                    player.take_damage(dmg)
                    message = f"Computer fired {w.name} for {dmg} damage."

                    if player.is_dead():
                        winner = "Computer"
                        message = "You lose. Press R to restart."
                    else:
                        turn = PLAYER_TURN
                        message += " Your turn: choose a weapon."
                    cpu_fire_at_ms = None

        # --- Draw ---
        screen.fill(BG)

        # 1. Map (always drawn)
        draw_map(screen, map_w, stars, player, cpu, turn, winner, font, small_font)

        # 2. Side panel or collapsed message bar
        if panel_expanded:
            draw_side_panel(
                screen, panel_x, font, small_font, player, cpu, turn, winner,
                message, weapon_buttons,
            )
        else:
            # Semi-transparent overlay bar at the bottom of the screen
            bar_h = 40
            overlay = pygame.Surface((WIDTH, bar_h), pygame.SRCALPHA)
            overlay.fill((10, 12, 22, 200))
            screen.blit(overlay, (0, HEIGHT - bar_h))
            msg_surf = small_font.render(message, True, WHITE)
            screen.blit(
                msg_surf,
                msg_surf.get_rect(center=(WIDTH // 2, HEIGHT - bar_h // 2)),
            )

        # 3. Toggle tab (always drawn; captures its rect for next frame's hit-test)
        toggle_tab_rect = draw_toggle_tab(screen, panel_x, panel_expanded, small_font)

        # 4. Winner overlay (always drawn when applicable)
        if winner is not None:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            wtxt = big.render(f"{winner} wins!", True, WHITE)
            rtxt = font.render("Press R to restart", True, WHITE)
            screen.blit(wtxt, wtxt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
            screen.blit(rtxt, rtxt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25)))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
