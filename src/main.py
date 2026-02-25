import pygame
import random
from dataclasses import dataclass

# ----------------------------
# Config
# ----------------------------
WIDTH, HEIGHT = 900, 700
FPS = 60

SHIP_W, SHIP_H = 160, 60
TOP_Y = 80
BOTTOM_Y = HEIGHT - 140

BG = (15, 18, 26)
WHITE = (240, 240, 240)
GRAY = (120, 120, 120)
GREEN = (80, 220, 120)
RED = (230, 80, 80)
BLUE = (90, 160, 255)
YELLOW = (245, 220, 90)

PLAYER_TURN = "player"
CPU_TURN = "cpu"

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
    rect: pygame.Rect
    weapons: dict[str, Weapon]

    def is_dead(self) -> bool:
        return self.hp <= 0

    def take_damage(self, dmg: int) -> None:
        self.hp = max(0, self.hp - dmg)

# ----------------------------
# UI Helpers
# ----------------------------
class Button:
    def __init__(self, rect: pygame.Rect, label: str):
        self.rect = rect
        self.label = label

    def draw(self, surf, font, enabled=True):
        color = BLUE if enabled else GRAY
        pygame.draw.rect(surf, color, self.rect, border_radius=10)
        pygame.draw.rect(surf, (30, 30, 40), self.rect, 2, border_radius=10)
        text = font.render(self.label, True, WHITE if enabled else (200, 200,
200))
        surf.blit(text, text.get_rect(center=self.rect.center))

    def hit(self, pos) -> bool:
        return self.rect.collidepoint(pos)

def draw_hp_bar(surf, rect, hp, max_hp):
    # Background
    pygame.draw.rect(surf, (40, 40, 55), rect, border_radius=8)
    # Fill
    pct = 0 if max_hp == 0 else hp / max_hp
    fill_w = int(rect.w * pct)
    fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.h)
    fill_color = GREEN if pct > 0.4 else YELLOW if pct > 0.2 else RED
    pygame.draw.rect(surf, fill_color, fill_rect, border_radius=8)
    pygame.draw.rect(surf, (10, 10, 18), rect, 2, border_radius=8)

# ----------------------------
# Game Setup
# ----------------------------
def make_game():
    player_rect = pygame.Rect(WIDTH // 2 - SHIP_W // 2, BOTTOM_Y, SHIP_W,
SHIP_H)
    cpu_rect = pygame.Rect(WIDTH // 2 - SHIP_W // 2, TOP_Y, SHIP_W, SHIP_H)

    player = Ship(
        name="Player",
        max_hp=750,
        hp=750,
        rect=player_rect,
        weapons={
            "Laser": Weapon("Laser", (40, 70), charges=2),      # 2 shots
            "Ion Beam": Weapon("Ion Beam", (80, 120), charges=1),  # 1 shot
        },
    )

    cpu = Ship(
        name="Computer",
        max_hp=500,
        hp=500,
        rect=cpu_rect,
        weapons={
            "Laser": Weapon("Laser", (35, 65), charges=3),  # 3 shots
        },
    )

    return player, cpu

# ----------------------------
# Main
# ----------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Turn-Based Ship Duel (Skeleton)")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 28)
    big = pygame.font.SysFont(None, 44)

    player, cpu = make_game()

    # Buttons for player weapons
    btns = []
    bx, by = 40, HEIGHT - 90
    bw, bh = 180, 46
    gap = 14
    weapon_order = ["Laser", "Ion Beam"]
    for i, wname in enumerate(weapon_order):
        btns.append(Button(pygame.Rect(bx + i * (bw + gap), by, bw, bh),
wname))

    turn = PLAYER_TURN
    message = "Your turn: choose a weapon."
    winner = None

    # CPU delayed action
    cpu_fire_at_ms = None
    CPU_DELAY_MS = 900

    running = True
    while running:
        dt = clock.tick(FPS)
        now = pygame.time.get_ticks()

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
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if turn == PLAYER_TURN:
                    pos = event.pos
                    for b in btns:
                        w = player.weapons.get(b.label)
                        if w and b.hit(pos) and w.can_fire():
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
                # Pick any available CPU weapon
                available = [w for w in cpu.weapons.values() if w.can_fire()]
                if not available:
                    # If CPU is out of shots, just pass (or make this a loss
                    # condition if you want)
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

        # Title / status
        title = big.render("Immobile Ship Duel (Turn-Based)", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 18))

        msg = font.render(message, True, WHITE)
        screen.blit(msg, (40, 80 + 120))

        # Ships
        pygame.draw.rect(screen, (60, 90, 140), cpu.rect, border_radius=12)
        pygame.draw.rect(screen, (10, 10, 18), cpu.rect, 2, border_radius=12)

        pygame.draw.rect(screen, (140, 80, 60), player.rect, border_radius=12)
        pygame.draw.rect(screen, (10, 10, 18), player.rect, 2,
border_radius=12)

        # HP bars
        cpu_hp_bar = pygame.Rect(cpu.rect.x, cpu.rect.y - 28, cpu.rect.w, 16)
        player_hp_bar = pygame.Rect(player.rect.x, player.rect.y + cpu.rect.h +
12, player.rect.w, 16)

        draw_hp_bar(screen, cpu_hp_bar, cpu.hp, cpu.max_hp)
        draw_hp_bar(screen, player_hp_bar, player.hp, player.max_hp)

        cpu_hp_text = font.render(f"{cpu.name} HP: {cpu.hp}/{cpu.max_hp}",
True, WHITE)
        player_hp_text = font.render(f"{player.name} HP:
{player.hp}/{player.max_hp}", True, WHITE)
        screen.blit(cpu_hp_text, (cpu.rect.x, cpu_hp_bar.y - 22))
        screen.blit(player_hp_text, (player.rect.x, player_hp_bar.y + 18))

        # Weapon buttons + ammo counts
        for b in btns:
            w = player.weapons[b.label]
            enabled = (turn == PLAYER_TURN) and w.can_fire() and winner is None
            label = b.label
            if w.charges is None:
                ammo = "∞"
            else:
                ammo = str(w.charges)
            b.label = f"{label} ({ammo})"  # show charges on the button
            b.draw(screen, font, enabled=enabled)
            b.label = label  # restore for logic

        # Turn indicator
        turn_text = font.render(f"Turn: {turn}", True, WHITE if winner is None
else YELLOW)
        screen.blit(turn_text, (WIDTH - 160, HEIGHT - 40))

        if winner is not None:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))
            wtxt = big.render(f"{winner} wins!", True, WHITE)
            rtxt = font.render("Press R to restart", True, WHITE)
            screen.blit(wtxt, wtxt.get_rect(center=(WIDTH // 2, HEIGHT // 2 -
20)))
            screen.blit(rtxt, rtxt.get_rect(center=(WIDTH // 2, HEIGHT // 2 +
25)))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
