"""Pygame entry point for Davstarship."""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pygame

from davstarship.game_objects import (
    COIN_SIZE,
    PLAYER_HEIGHT,
    PLAYER_SPEED,
    PLAYER_WIDTH,
    PLAYER_Y_MARGIN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    FallingObject,
    asteroid_spawn_interval,
    coin_spawn_interval,
    random_falling_object,
    rects_overlap,
)

FPS = 60
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"


class DavstarshipGame:
    """Main game state and pygame rendering layer."""

    def __init__(self) -> None:
        pygame.init()
        self.audio_enabled = True
        try:
            pygame.mixer.init()
        except pygame.error:
            self.audio_enabled = False
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Davstarship")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 34)
        self.big_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 26)
        self.rng = random.Random()
        self.state = "welcome"
        self.player_x = (SCREEN_WIDTH - PLAYER_WIDTH) / 2
        self.player_y = SCREEN_HEIGHT - PLAYER_HEIGHT - PLAYER_Y_MARGIN
        self.objects: list[FallingObject] = []
        self.coins = 0
        self.elapsed = 0.0
        self.asteroid_timer = 0.0
        self.coin_timer = 0.0
        self.last_run_time = 0.0
        self.stars = [
            (
                self.rng.randrange(0, SCREEN_WIDTH),
                self.rng.randrange(0, SCREEN_HEIGHT),
                self.rng.choice((1, 1, 2)),
            )
            for _ in range(95)
        ]
        self.sounds = self._load_sounds()

    def _load_sounds(self) -> dict[str, pygame.mixer.Sound | None]:
        """Load optional sounds that can be added later in assets/sounds."""
        sounds: dict[str, pygame.mixer.Sound | None] = {"coin": None, "death": None}
        if not self.audio_enabled:
            return sounds
        for name in sounds:
            path = ASSET_DIR / "sounds" / f"{name}.wav"
            if path.exists():
                sounds[name] = pygame.mixer.Sound(path)
        return sounds

    def reset(self) -> None:
        """Start a fresh flight."""
        self.state = "playing"
        self.player_x = (SCREEN_WIDTH - PLAYER_WIDTH) / 2
        self.objects.clear()
        self.coins = 0
        self.elapsed = 0.0
        self.asteroid_timer = 0.0
        self.coin_timer = 0.0
        if self.audio_enabled:
            pygame.mixer.music.stop()
            music_path = ASSET_DIR / "sounds" / "space_music.ogg"
            if music_path.exists():
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1)

    def run(self) -> None:
        """Run the game loop until the window is closed."""
        while True:
            delta = self.clock.tick(FPS) / 1000
            self.handle_events()
            if self.state == "playing":
                self.update(delta)
            self.draw()

    def handle_events(self) -> None:
        """Handle keyboard and quit events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if self.state in {"welcome", "game_over"} and event.key in {
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                }:
                    self.reset()
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and self.state in {"welcome", "game_over"}
                and self.start_button_rect().collidepoint(event.pos)
            ):
                self.reset()

    def update(self, delta: float) -> None:
        """Update all gameplay objects."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player_x -= PLAYER_SPEED * delta
        if keys[pygame.K_RIGHT]:
            self.player_x += PLAYER_SPEED * delta
        self.player_x = max(0, min(SCREEN_WIDTH - PLAYER_WIDTH, self.player_x))

        self.elapsed += delta
        self.asteroid_timer += delta
        self.coin_timer += delta

        if self.asteroid_timer >= asteroid_spawn_interval(self.elapsed):
            self.objects.append(random_falling_object("asteroid", self.rng))
            self.asteroid_timer = 0.0

        if self.coin_timer >= coin_spawn_interval(self.elapsed):
            self.objects.append(random_falling_object("coin", self.rng))
            self.coin_timer = 0.0

        player_rect = (self.player_x, self.player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
        remaining: list[FallingObject] = []
        for obj in self.objects:
            obj.update(delta)
            if obj.is_off_screen():
                continue
            if rects_overlap(player_rect, obj.rect):
                if obj.kind == "coin":
                    self.coins += 1
                    self.play_sound("coin")
                    continue
                self.die()
                return
            remaining.append(obj)
        self.objects = remaining

    def die(self) -> None:
        """End the current run and show the summary screen."""
        self.state = "game_over"
        self.last_run_time = self.elapsed
        if self.audio_enabled:
            pygame.mixer.music.stop()
        self.play_sound("death")

    def play_sound(self, name: str) -> None:
        """Play an optional sound effect if an asset exists."""
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()

    def draw(self) -> None:
        """Draw the current screen."""
        self.draw_space_background()
        if self.state == "welcome":
            self.draw_welcome()
        elif self.state == "playing":
            self.draw_gameplay()
        else:
            self.draw_game_over()
        pygame.display.flip()

    def draw_space_background(self) -> None:
        """Draw a static space background until a real image is supplied."""
        self.screen.fill((3, 6, 24))
        for x, y, radius in self.stars:
            pygame.draw.circle(self.screen, (205, 220, 255), (x, y), radius)

    def draw_gameplay(self) -> None:
        """Draw the ship, asteroids, coins, and HUD."""
        for obj in self.objects:
            if obj.kind == "asteroid":
                self.draw_asteroid(obj)
            else:
                self.draw_coin(obj)
        self.draw_ship()
        self.draw_hud()

    def draw_ship(self) -> None:
        """Draw a temporary pixel-art style ship using simple shapes."""
        x = int(self.player_x)
        y = int(self.player_y)
        pygame.draw.polygon(
            self.screen,
            (70, 210, 255),
            [(x + PLAYER_WIDTH // 2, y), (x + 8, y + PLAYER_HEIGHT), (x + PLAYER_WIDTH - 8, y + PLAYER_HEIGHT)],
        )
        pygame.draw.rect(self.screen, (15, 80, 170), (x + 20, y + 20, 14, 20))
        pygame.draw.rect(self.screen, (255, 135, 35), (x + 12, y + 39, 9, 14))
        pygame.draw.rect(self.screen, (255, 135, 35), (x + 33, y + 39, 9, 14))

    def draw_asteroid(self, obj: FallingObject) -> None:
        """Draw a temporary asteroid placeholder."""
        center = (int(obj.x + obj.width / 2), int(obj.y + obj.height / 2))
        points = []
        for step in range(9):
            angle = (math.tau / 9) * step
            radius = obj.width / 2 * (0.76 + 0.22 * ((step * 5) % 3))
            points.append((center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius))
        pygame.draw.polygon(self.screen, (118, 104, 99), points)
        pygame.draw.polygon(self.screen, (68, 61, 65), points, width=3)

    def draw_coin(self, obj: FallingObject) -> None:
        """Draw a temporary coin placeholder."""
        center = (int(obj.x + COIN_SIZE / 2), int(obj.y + COIN_SIZE / 2))
        pygame.draw.circle(self.screen, (255, 210, 55), center, COIN_SIZE // 2)
        pygame.draw.circle(self.screen, (168, 110, 18), center, COIN_SIZE // 2, width=3)
        pygame.draw.line(
            self.screen,
            (255, 242, 145),
            (center[0] - 4, center[1] - 8),
            (center[0] - 4, center[1] + 8),
            width=3,
        )

    def draw_hud(self) -> None:
        """Draw current time and coin count."""
        coin_text = self.font.render(f"Pièces : {self.coins}", True, (255, 230, 100))
        time_text = self.font.render(f"Temps : {self.elapsed:05.1f}s", True, (235, 245, 255))
        self.screen.blit(time_text, (18, 16))
        self.screen.blit(coin_text, (SCREEN_WIDTH - coin_text.get_width() - 18, 16))

    def draw_center_text(
        self,
        lines: list[tuple[str, pygame.font.Font, tuple[int, int, int]]],
        start_y: float | None = None,
    ) -> float:
        """Draw multiple centered text lines and return the next y position."""
        total_height = sum(font.get_height() + 10 for _, font, _ in lines)
        y = start_y if start_y is not None else (SCREEN_HEIGHT - total_height) / 2
        for text, font, color in lines:
            rendered = font.render(text, True, color)
            self.screen.blit(rendered, ((SCREEN_WIDTH - rendered.get_width()) / 2, y))
            y += font.get_height() + 10
        return y

    def start_button_rect(self) -> pygame.Rect:
        """Return the welcome/retry button rectangle."""
        return pygame.Rect((SCREEN_WIDTH - 300) // 2, 370, 300, 58)

    def draw_button(self, label: str) -> None:
        """Draw a clickable start or retry button."""
        rect = self.start_button_rect()
        pygame.draw.rect(self.screen, (20, 130, 170), rect, border_radius=14)
        pygame.draw.rect(self.screen, (120, 235, 255), rect, width=3, border_radius=14)
        rendered = self.font.render(label, True, (245, 255, 255))
        self.screen.blit(rendered, rendered.get_rect(center=rect.center))

    def draw_welcome(self) -> None:
        """Draw the opening page."""
        self.draw_center_text(
            [
                ("DAVSTARSHIP", self.big_font, (85, 220, 255)),
                (
                    "Survis le plus longtemps possible dans l'espace",
                    self.small_font,
                    (230, 240, 255),
                ),
                (
                    "Récupère les pièces et évite les astéroïdes",
                    self.small_font,
                    (255, 230, 120),
                ),
                ("Flèches gauche/droite : piloter", self.small_font, (205, 215, 235)),
            ],
            start_y=150,
        )
        self.draw_button("Démarrer le vol")
        hint = self.small_font.render("Entrée ou Espace fonctionne aussi", True, (180, 255, 190))
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) / 2, 446))

    def draw_game_over(self) -> None:
        """Draw the final summary page."""
        self.draw_center_text(
            [
                ("Crash !", self.big_font, (255, 95, 95)),
                (
                    f"Temps de vol : {self.last_run_time:.1f} secondes",
                    self.font,
                    (235, 245, 255),
                ),
                (f"Pièces récoltées : {self.coins}", self.font, (255, 230, 120)),
            ],
            start_y=150,
        )
        self.draw_button("Recommencer")
        hint = self.small_font.render(
            "Entrée / Espace : recommencer    Échap : quitter",
            True,
            (205, 215, 235),
        )
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) / 2, 446))


def main() -> None:
    """Launch Davstarship."""
    DavstarshipGame().run()


if __name__ == "__main__":
    main()
