"""Pygame entry point for Davstarship."""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pygame

from davstarship.game_objects import (
    ASTEROID_VARIANT_SIZES,
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
from davstarship.persistence import (
    DEFAULT_PILOT_ID,
    load_point_balance,
    load_shop_state,
    save_point_balance,
    save_shop_state,
)

FPS = 60
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
AUDIO_EXTENSIONS = {".wav", ".ogg", ".mp3"}


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
        self.point_balance = load_point_balance()
        self.pilots = [
            {
                "id": "earth racer",
                "name": "earth racer",
                "price": 0,
                "speed": 360.0,
            },
            {
                "id": "moon racer",
                "name": "moon racer",
                "price": 50,
                "speed": 460.0,
            },
            {
                "id": "sun racer",
                "name": "sun racer",
                "price": 120,
                "speed": 560.0,
            },
        ]
        self.owned_pilots, self.equipped_pilot_id = load_shop_state()
        if not any(pilot["id"] == self.equipped_pilot_id for pilot in self.pilots):
            self.equipped_pilot_id = DEFAULT_PILOT_ID
        self.owned_pilots.add(DEFAULT_PILOT_ID)
        self.selected_pilot_index = self.pilot_index(self.equipped_pilot_id)
        self.shop_message = ""
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
        self.images = self._load_images()
        self.music_path = self._find_asset(
            ("soundtrack", "music", "musique", "space", "jeu", "game"),
            AUDIO_EXTENSIONS,
        )
        self.sounds = self._load_sounds()
        self.start_background_music()

    def _asset_files(self, extensions: set[str]) -> list[Path]:
        """Return all files in assets matching the requested extensions."""
        if not ASSET_DIR.exists():
            return []
        return [
            path
            for path in ASSET_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in extensions
        ]

    def _find_asset(self, keywords: tuple[str, ...], extensions: set[str]) -> Path | None:
        """Find an asset whose filename matches or contains a keyword."""
        files = self._asset_files(extensions)
        for keyword in keywords:
            for path in files:
                if path.stem.lower() == keyword:
                    return path
        for keyword in keywords:
            for path in files:
                if keyword in path.stem.lower():
                    return path
        return None

    def _load_scaled_image(
        self, keywords: tuple[str, ...], size: tuple[int, int]
    ) -> pygame.Surface | None:
        """Load and scale the first image matching any keyword."""
        path = self._find_asset(keywords, IMAGE_EXTENSIONS)
        if path is None:
            return None
        try:
            image = pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None
        return pygame.transform.smoothscale(image, size)

    def _load_images(self) -> dict[str, pygame.Surface | None]:
        """Load optional image assets and keep drawable fallbacks available."""
        images: dict[str, pygame.Surface | None] = {
            "background": self._load_scaled_image(
                ("background", "space", "fond", "espace"),
                (SCREEN_WIDTH, SCREEN_HEIGHT),
            ),
            "ship": self._load_scaled_image(
                ("ship", "vaisseau", "davstarship"),
                (PLAYER_WIDTH, PLAYER_HEIGHT),
            ),
            "coin": self._load_scaled_image(
                ("coin", "piece", "pièce"),
                (COIN_SIZE, COIN_SIZE),
            ),
        }
        asteroid_keywords = {
            "little": ("little", "small", "petit", "mini"),
            "mid": ("mid", "medium", "moyen"),
            "big": ("big", "large", "grand", "gros"),
        }
        for variant, keywords in asteroid_keywords.items():
            size = ASTEROID_VARIANT_SIZES[variant]
            images[f"asteroid_{variant}"] = self._load_scaled_image(
                keywords, (size, size)
            )
        return images

    def _load_sounds(self) -> dict[str, pygame.mixer.Sound | None]:
        """Load optional sounds from the assets folder."""
        sounds: dict[str, pygame.mixer.Sound | None] = {"coin": None, "death": None}
        if not self.audio_enabled:
            return sounds
        sound_keywords = {
            "coin": ("coin", "piece", "pièce"),
            "death": (
                "explosion",
                "collision",
                "colision",
                "meteor",
                "meteorite",
                "météor",
                "météorite",
                "death",
                "crash",
            ),
        }
        for name, keywords in sound_keywords.items():
            path = self._find_asset(keywords, AUDIO_EXTENSIONS)
            if path is not None:
                try:
                    sounds[name] = pygame.mixer.Sound(path)
                except pygame.error:
                    sounds[name] = None
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
        self.start_background_music()

    def start_background_music(self) -> None:
        """Play soundtrack.mp3 or another detected music asset on loop."""
        if not self.audio_enabled or self.music_path is None:
            return
        try:
            pygame.mixer.music.load(self.music_path)
            pygame.mixer.music.play(-1)
        except pygame.error:
            self.music_path = None

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
                if self.state == "shop":
                    if event.key in {pygame.K_ESCAPE, pygame.K_BACKSPACE}:
                        self.state = "welcome"
                    elif event.key == pygame.K_LEFT:
                        self.select_previous_pilot()
                    elif event.key == pygame.K_RIGHT:
                        self.select_next_pilot()
                    elif event.key in {pygame.K_RETURN, pygame.K_SPACE}:
                        self.buy_or_equip_selected_pilot()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif self.state in {"welcome", "game_over"} and event.key in {
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                }:
                    self.reset()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "shop":
                    if self.previous_pilot_button_rect().collidepoint(event.pos):
                        self.select_previous_pilot()
                    elif self.next_pilot_button_rect().collidepoint(event.pos):
                        self.select_next_pilot()
                    elif self.shop_action_button_rect().collidepoint(event.pos):
                        self.buy_or_equip_selected_pilot()
                    elif self.back_button_rect().collidepoint(event.pos):
                        self.state = "welcome"
                elif (
                    self.state in {"welcome", "game_over"}
                    and self.start_button_rect().collidepoint(event.pos)
                ):
                    self.reset()
                elif (
                    self.state in {"welcome", "game_over"}
                    and self.shop_button_rect().collidepoint(event.pos)
                ):
                    self.state = "shop"

    def pilot_index(self, pilot_id: str) -> int:
        """Return the index of a pilot by id, or the default pilot index."""
        for index, pilot in enumerate(self.pilots):
            if pilot["id"] == pilot_id:
                return index
        return 0

    def current_pilot(self) -> dict[str, str | float | int]:
        """Return the pilot currently selected in the shop."""
        return self.pilots[self.selected_pilot_index]

    def equipped_pilot(self) -> dict[str, str | float | int]:
        """Return the currently equipped pilot."""
        for pilot in self.pilots:
            if pilot["id"] == self.equipped_pilot_id:
                return pilot
        return self.pilots[0]

    def current_player_speed(self) -> float:
        """Return the gameplay speed of the equipped pilot."""
        speed = self.equipped_pilot().get("speed", PLAYER_SPEED)
        return float(speed) if isinstance(speed, (float, int)) else PLAYER_SPEED

    def select_previous_pilot(self) -> None:
        """Select the previous pilot in the shop carousel."""
        self.selected_pilot_index = (self.selected_pilot_index - 1) % len(self.pilots)
        self.shop_message = ""

    def select_next_pilot(self) -> None:
        """Select the next pilot in the shop carousel."""
        self.selected_pilot_index = (self.selected_pilot_index + 1) % len(self.pilots)
        self.shop_message = ""

    def is_pilot_owned(self, pilot_id: str) -> bool:
        """Return whether the player owns the given pilot."""
        return pilot_id in self.owned_pilots

    def save_current_shop_state(self) -> None:
        """Persist the current shop ownership and equipment state."""
        save_shop_state(self.owned_pilots, self.equipped_pilot_id)

    def buy_or_equip_selected_pilot(self) -> None:
        """Buy the selected pilot when possible, then equip it."""
        pilot = self.current_pilot()
        pilot_id = str(pilot["id"])
        price = int(pilot["price"])
        if self.is_pilot_owned(pilot_id):
            self.equipped_pilot_id = pilot_id
            self.save_current_shop_state()
            self.shop_message = f"{pilot['name']} équipé !"
            return

        if self.point_balance < price:
            missing_points = price - self.point_balance
            self.shop_message = f"Il manque {missing_points} points."
            return

        self.point_balance -= price
        self.owned_pilots.add(pilot_id)
        self.equipped_pilot_id = pilot_id
        save_point_balance(self.point_balance)
        self.save_current_shop_state()
        self.shop_message = f"{pilot['name']} acheté et équipé !"

    def selected_pilot_status(self) -> str:
        """Return the shop status label for the selected pilot."""
        pilot = self.current_pilot()
        pilot_id = str(pilot["id"])
        price = int(pilot["price"])
        if pilot_id == self.equipped_pilot_id:
            return "Équipé"
        if self.is_pilot_owned(pilot_id):
            return "Possédé"
        if self.point_balance >= price:
            return "Acheter"
        return "Pas assez de points"

    def selected_pilot_action_label(self) -> str:
        """Return the main button label for the selected pilot."""
        pilot = self.current_pilot()
        pilot_id = str(pilot["id"])
        price = int(pilot["price"])
        if pilot_id == self.equipped_pilot_id:
            return "Équipé"
        if self.is_pilot_owned(pilot_id):
            return "Équiper"
        if self.point_balance >= price:
            return "Acheter"
        return "Pas assez de points"

    def update(self, delta: float) -> None:
        """Update all gameplay objects."""
        keys = pygame.key.get_pressed()
        player_speed = self.current_player_speed()
        if keys[pygame.K_LEFT]:
            self.player_x -= player_speed * delta
        if keys[pygame.K_RIGHT]:
            self.player_x += player_speed * delta
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
                    self.point_balance += 1
                    save_point_balance(self.point_balance)
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
        elif self.state == "shop":
            self.draw_shop()
        else:
            self.draw_game_over()
        pygame.display.flip()

    def draw_space_background(self) -> None:
        """Draw the space background image or a static fallback."""
        background = self.images.get("background")
        if background is not None:
            self.screen.blit(background, (0, 0))
            return
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
        """Draw the ship image or a temporary pixel-art style fallback."""
        ship = self.images.get("ship")
        position = (int(self.player_x), int(self.player_y))
        if ship is not None:
            self.screen.blit(ship, position)
            return

        x, y = position
        pygame.draw.polygon(
            self.screen,
            (70, 210, 255),
            [
                (x + PLAYER_WIDTH // 2, y),
                (x + 8, y + PLAYER_HEIGHT),
                (x + PLAYER_WIDTH - 8, y + PLAYER_HEIGHT),
            ],
        )
        pygame.draw.rect(self.screen, (15, 80, 170), (x + 20, y + 20, 14, 20))
        pygame.draw.rect(self.screen, (255, 135, 35), (x + 12, y + 39, 9, 14))
        pygame.draw.rect(self.screen, (255, 135, 35), (x + 33, y + 39, 9, 14))

    def draw_asteroid(self, obj: FallingObject) -> None:
        """Draw a variant asteroid image or fallback shape."""
        asteroid = self.images.get(f"asteroid_{obj.variant}")
        if asteroid is not None:
            self.screen.blit(asteroid, (int(obj.x), int(obj.y)))
            return

        center = (int(obj.x + obj.width / 2), int(obj.y + obj.height / 2))
        points = []
        for step in range(9):
            angle = (math.tau / 9) * step
            radius = obj.width / 2 * (0.76 + 0.22 * ((step * 5) % 3))
            points.append(
                (
                    center[0] + math.cos(angle) * radius,
                    center[1] + math.sin(angle) * radius,
                )
            )
        pygame.draw.polygon(self.screen, (118, 104, 99), points)
        pygame.draw.polygon(self.screen, (68, 61, 65), points, width=3)

    def draw_coin(self, obj: FallingObject) -> None:
        """Draw the coin image or a temporary fallback."""
        coin = self.images.get("coin")
        if coin is not None:
            self.screen.blit(coin, (int(obj.x), int(obj.y)))
            return

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
        balance_text = self.font.render(
            f"Points : {self.point_balance}", True, (140, 255, 170)
        )
        time_text = self.font.render(
            f"Temps : {self.elapsed:05.1f}s", True, (235, 245, 255)
        )
        self.screen.blit(time_text, (18, 16))
        self.screen.blit(coin_text, (SCREEN_WIDTH - coin_text.get_width() - 18, 16))
        self.screen.blit(
            balance_text, (SCREEN_WIDTH - balance_text.get_width() - 18, 52)
        )

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
        return pygame.Rect((SCREEN_WIDTH - 300) // 2, 340, 300, 58)

    def shop_button_rect(self) -> pygame.Rect:
        """Return the main menu shop button rectangle."""
        return pygame.Rect((SCREEN_WIDTH - 300) // 2, 414, 300, 58)

    def previous_pilot_button_rect(self) -> pygame.Rect:
        """Return the previous-pilot button rectangle."""
        return pygame.Rect(70, 220, 70, 58)

    def next_pilot_button_rect(self) -> pygame.Rect:
        """Return the next-pilot button rectangle."""
        return pygame.Rect(SCREEN_WIDTH - 140, 220, 70, 58)

    def shop_action_button_rect(self) -> pygame.Rect:
        """Return the buy/equip button rectangle."""
        return pygame.Rect((SCREEN_WIDTH - 300) // 2, 420, 300, 52)

    def back_button_rect(self) -> pygame.Rect:
        """Return the shop back button rectangle."""
        return pygame.Rect((SCREEN_WIDTH - 260) // 2, 492, 260, 50)

    def draw_button(self, label: str, rect: pygame.Rect | None = None) -> None:
        """Draw a clickable menu button."""
        rect = rect or self.start_button_rect()
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
            start_y=130,
        )
        balance = self.font.render(
            f"Solde de points : {self.point_balance}", True, (140, 255, 170)
        )
        self.screen.blit(balance, ((SCREEN_WIDTH - balance.get_width()) / 2, 276))
        self.draw_button("Démarrer le vol", self.start_button_rect())
        self.draw_button("Boutique", self.shop_button_rect())
        hint = self.small_font.render(
            "Entrée ou Espace fonctionne aussi", True, (180, 255, 190)
        )
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) / 2, 492))

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
        balance = self.font.render(
            f"Solde de points : {self.point_balance}", True, (140, 255, 170)
        )
        self.screen.blit(balance, ((SCREEN_WIDTH - balance.get_width()) / 2, 292))
        self.draw_button("Recommencer", self.start_button_rect())
        self.draw_button("Boutique", self.shop_button_rect())
        hint = self.small_font.render(
            "Entrée / Espace : recommencer    Échap : quitter",
            True,
            (205, 215, 235),
        )
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) / 2, 492))

    def draw_shop(self) -> None:
        """Draw the pilot shop page."""
        pilot = self.current_pilot()
        status = self.selected_pilot_status()
        action_label = self.selected_pilot_action_label()
        price = int(pilot["price"])
        speed = float(pilot["speed"])

        title = self.big_font.render("Boutique", True, (85, 220, 255))
        self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) / 2, 34))
        balance = self.font.render(
            f"Solde de points : {self.point_balance}", True, (140, 255, 170)
        )
        self.screen.blit(balance, ((SCREEN_WIDTH - balance.get_width()) / 2, 96))

        self.draw_pilot_preview(pilot, (SCREEN_WIDTH // 2, 200))
        self.draw_button("←", self.previous_pilot_button_rect())
        self.draw_button("→", self.next_pilot_button_rect())

        info_lines = [
            (str(pilot["name"]).title(), self.font, (245, 255, 255)),
            (f"Vitesse : {speed:.0f}", self.small_font, (230, 240, 255)),
            (f"Prix : {price} points", self.small_font, (255, 230, 120)),
            (f"Statut : {status}", self.small_font, (140, 255, 170)),
        ]
        self.draw_center_text(info_lines, start_y=305)

        message_color = (
            (255, 135, 95)
            if status == "Pas assez de points"
            else (180, 255, 190)
        )
        if self.shop_message:
            message = self.small_font.render(self.shop_message, True, message_color)
            self.screen.blit(message, ((SCREEN_WIDTH - message.get_width()) / 2, 396))

        self.draw_button(action_label, self.shop_action_button_rect())
        self.draw_button("Retour au menu", self.back_button_rect())
        hint = self.small_font.render(
            "← / → : changer    Entrée : acheter / équiper    Échap : retour",
            True,
            (205, 215, 235),
        )
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) / 2, 558))

    def draw_pilot_preview(
        self, pilot: dict[str, str | float | int], center: tuple[int, int]
    ) -> None:
        """Draw the selected pilot preview with pygame primitives only."""
        pilot_id = str(pilot["id"])
        x, y = center

        if pilot_id == "moon racer":
            self.draw_astronaut_pilot(
                center,
                suit_color=(170, 180, 190),
                accent_color=(220, 230, 245),
                visor_color=(105, 150, 185),
                glow_color=(150, 155, 170),
            )
            pygame.draw.circle(self.screen, (215, 215, 205), (x + 46, y - 62), 13)
            pygame.draw.circle(self.screen, (155, 155, 150), (x + 42, y - 65), 3)
            pygame.draw.circle(self.screen, (155, 155, 150), (x + 50, y - 58), 2)
        elif pilot_id == "sun racer":
            for radius, color in (
                (78, (120, 55, 0)),
                (66, (205, 95, 15)),
                (54, (255, 170, 35)),
            ):
                pygame.draw.circle(self.screen, color, center, radius, width=3)
            self.draw_astronaut_pilot(
                center,
                suit_color=(255, 128, 24),
                accent_color=(255, 222, 70),
                visor_color=(255, 245, 160),
                glow_color=(255, 180, 40),
            )
            for angle in range(0, 360, 45):
                ray_x = x + math.cos(math.radians(angle)) * 72
                ray_y = y + math.sin(math.radians(angle)) * 72
                pygame.draw.line(
                    self.screen, (255, 210, 70), center, (ray_x, ray_y), width=2
                )
        else:
            self.draw_astronaut_pilot(
                center,
                suit_color=(45, 145, 230),
                accent_color=(70, 210, 110),
                visor_color=(110, 215, 255),
                glow_color=(80, 180, 120),
            )
            pygame.draw.arc(
                self.screen,
                (70, 210, 110),
                pygame.Rect(x - 54, y - 72, 108, 108),
                math.radians(205),
                math.radians(335),
                width=4,
            )

    def draw_astronaut_pilot(
        self,
        center: tuple[int, int],
        suit_color: tuple[int, int, int],
        accent_color: tuple[int, int, int],
        visor_color: tuple[int, int, int],
        glow_color: tuple[int, int, int],
    ) -> None:
        """Draw a small pilot body using simple pygame shapes."""
        x, y = center
        pygame.draw.circle(self.screen, glow_color, (x, y - 54), 38, width=3)
        pygame.draw.circle(self.screen, suit_color, (x, y - 54), 31)
        pygame.draw.circle(self.screen, (230, 240, 255), (x, y - 54), 22)
        pygame.draw.ellipse(self.screen, visor_color, (x - 17, y - 61, 34, 18))
        pygame.draw.rect(
            self.screen, suit_color, (x - 27, y - 26, 54, 68), border_radius=12
        )
        pygame.draw.rect(
            self.screen, accent_color, (x - 12, y - 15, 24, 30), border_radius=6
        )
        pygame.draw.rect(
            self.screen, (20, 35, 55), (x - 7, y - 8, 14, 5), border_radius=2
        )
        pygame.draw.line(
            self.screen, suit_color, (x - 27, y - 8), (x - 55, y + 18), 12
        )
        pygame.draw.line(
            self.screen, suit_color, (x + 27, y - 8), (x + 55, y + 18), 12
        )
        pygame.draw.circle(self.screen, accent_color, (x - 58, y + 21), 8)
        pygame.draw.circle(self.screen, accent_color, (x + 58, y + 21), 8)
        pygame.draw.rect(
            self.screen, suit_color, (x - 23, y + 34, 18, 42), border_radius=6
        )
        pygame.draw.rect(
            self.screen, suit_color, (x + 5, y + 34, 18, 42), border_radius=6
        )
        pygame.draw.rect(
            self.screen, accent_color, (x - 27, y + 70, 26, 10), border_radius=4
        )
        pygame.draw.rect(
            self.screen, accent_color, (x + 1, y + 70, 26, 10), border_radius=4
        )


def main() -> None:
    """Launch Davstarship."""
    DavstarshipGame().run()


if __name__ == "__main__":
    main()
