"""Jeu Davstarship avec Pygame.

Ce fichier garde tout le code Pygame au même endroit pour rester facile à
présenter :
1. on charge les images et les sons ;
2. on met à jour la partie ;
3. on dessine l'écran.
"""

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

FPS = 60
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
AUDIO_EXTENSIONS = {".wav", ".ogg", ".mp3"}

# Les noms des fichiers peuvent être en anglais ou en français.
IMAGE_KEYWORDS = {
    "background": ("background", "space", "fond", "espace"),
    "ship": ("ship", "vaisseau", "davstarship"),
    "coin": ("coin", "piece", "pièce"),
    "asteroid_little": ("little", "small", "petit", "mini"),
    "asteroid_mid": ("mid", "medium", "moyen"),
    "asteroid_big": ("big", "large", "grand", "gros"),
}
SOUND_KEYWORDS = {
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
MUSIC_KEYWORDS = ("soundtrack", "music", "musique", "space", "jeu", "game")


class DavstarshipGame:
    """Objet principal : il contient l'état du jeu et les fonctions Pygame."""

    def __init__(self) -> None:
        pygame.init()

        # Le son peut échouer sur certains ordinateurs : le jeu reste jouable.
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

        self.player_y = SCREEN_HEIGHT - PLAYER_HEIGHT - PLAYER_Y_MARGIN
        self.stars = self.make_stars()
        self.images = self.load_images()
        self.music_path = self.find_asset(MUSIC_KEYWORDS, AUDIO_EXTENSIONS)
        self.sounds = self.load_sounds()

        self.reset_values("welcome")
        self.start_background_music()

    # ------------------------------------------------------------------
    # Chargement des assets
    # ------------------------------------------------------------------
    def asset_files(self, extensions: set[str]) -> list[Path]:
        """Liste tous les fichiers du dossier assets avec les bonnes extensions."""
        if not ASSET_DIR.exists():
            return []
        return [
            path
            for path in ASSET_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() in extensions
        ]

    def find_asset(self, keywords: tuple[str, ...], extensions: set[str]) -> Path | None:
        """Trouve un fichier dont le nom correspond à un mot-clé.

        Exemple : `soundtrack.mp3` est trouvé avant `my_soundtrack.mp3` parce
        qu'on teste d'abord les noms exacts, puis les noms qui contiennent le mot.
        """
        files = self.asset_files(extensions)
        for exact_match in (True, False):
            for keyword in keywords:
                for path in files:
                    name = path.stem.lower()
                    if name == keyword or (not exact_match and keyword in name):
                        return path
        return None

    def load_image(self, key: str, size: tuple[int, int]) -> pygame.Surface | None:
        """Charge une image si elle existe, sinon retourne None."""
        path = self.find_asset(IMAGE_KEYWORDS[key], IMAGE_EXTENSIONS)
        if path is None:
            return None
        try:
            image = pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None
        return pygame.transform.smoothscale(image, size)

    def load_images(self) -> dict[str, pygame.Surface | None]:
        """Charge toutes les images possibles du jeu."""
        images: dict[str, pygame.Surface | None] = {
            "background": self.load_image("background", (SCREEN_WIDTH, SCREEN_HEIGHT)),
            "ship": self.load_image("ship", (PLAYER_WIDTH, PLAYER_HEIGHT)),
            "coin": self.load_image("coin", (COIN_SIZE, COIN_SIZE)),
        }
        for variant, size in ASTEROID_VARIANT_SIZES.items():
            images[f"asteroid_{variant}"] = self.load_image(
                f"asteroid_{variant}", (size, size)
            )
        return images

    def load_sounds(self) -> dict[str, pygame.mixer.Sound | None]:
        """Charge les sons des pièces et de l'explosion."""
        sounds: dict[str, pygame.mixer.Sound | None] = {"coin": None, "death": None}
        if not self.audio_enabled:
            return sounds

        for name, keywords in SOUND_KEYWORDS.items():
            path = self.find_asset(keywords, AUDIO_EXTENSIONS)
            if path is None:
                continue
            try:
                sounds[name] = pygame.mixer.Sound(path)
            except pygame.error:
                sounds[name] = None
        return sounds

    def start_background_music(self) -> None:
        """Lance soundtrack.mp3 en boucle si le fichier existe."""
        if not self.audio_enabled or self.music_path is None:
            return
        try:
            pygame.mixer.music.load(self.music_path)
            pygame.mixer.music.play(-1)
        except pygame.error:
            self.music_path = None

    # ------------------------------------------------------------------
    # État et boucle du jeu
    # ------------------------------------------------------------------
    def make_stars(self) -> list[tuple[int, int, int]]:
        """Crée des étoiles fixes pour le fond si aucune image n'est fournie."""
        return [
            (
                self.rng.randrange(0, SCREEN_WIDTH),
                self.rng.randrange(0, SCREEN_HEIGHT),
                self.rng.choice((1, 1, 2)),
            )
            for _ in range(95)
        ]

    def reset_values(self, state: str = "playing") -> None:
        """Réinitialise les valeurs d'une partie."""
        self.state = state
        self.player_x = (SCREEN_WIDTH - PLAYER_WIDTH) / 2
        self.objects: list[FallingObject] = []
        self.coins = 0
        self.elapsed = 0.0
        self.asteroid_timer = 0.0
        self.coin_timer = 0.0
        self.last_run_time = 0.0

    def start_game(self) -> None:
        """Démarre ou redémarre une partie."""
        self.reset_values("playing")
        self.start_background_music()

    def run(self) -> None:
        """Boucle principale : événements, mise à jour, dessin."""
        while True:
            delta = self.clock.tick(FPS) / 1000
            self.handle_events()
            if self.state == "playing":
                self.update(delta)
            self.draw()

    def handle_events(self) -> None:
        """Gère clavier, souris et fermeture de la fenêtre."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit_game()
                if self.state in {"welcome", "game_over"} and event.key in {
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                }:
                    self.start_game()

            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and self.state in {"welcome", "game_over"}
                and self.button_rect().collidepoint(event.pos)
            ):
                self.start_game()

    def quit_game(self) -> None:
        """Quitte Pygame proprement."""
        pygame.quit()
        sys.exit()

    def update(self, delta: float) -> None:
        """Met à jour le vaisseau, les objets et les collisions."""
        self.move_player(delta)
        self.elapsed += delta
        self.asteroid_timer += delta
        self.coin_timer += delta
        self.spawn_objects()
        self.update_falling_objects(delta)

    def move_player(self, delta: float) -> None:
        """Déplace le vaisseau uniquement à gauche et à droite."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player_x -= PLAYER_SPEED * delta
        if keys[pygame.K_RIGHT]:
            self.player_x += PLAYER_SPEED * delta
        self.player_x = max(0, min(SCREEN_WIDTH - PLAYER_WIDTH, self.player_x))

    def spawn_objects(self) -> None:
        """Fait apparaître astéroïdes et pièces en haut de l'écran."""
        if self.asteroid_timer >= asteroid_spawn_interval(self.elapsed):
            self.objects.append(random_falling_object("asteroid", self.rng))
            self.asteroid_timer = 0.0

        if self.coin_timer >= coin_spawn_interval(self.elapsed):
            self.objects.append(random_falling_object("coin", self.rng))
            self.coin_timer = 0.0

    def update_falling_objects(self, delta: float) -> None:
        """Fait tomber les objets et réagit aux collisions."""
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
                self.game_over()
                return
            remaining.append(obj)

        self.objects = remaining

    def game_over(self) -> None:
        """Arrête la partie quand le vaisseau touche une météorite."""
        self.state = "game_over"
        self.last_run_time = self.elapsed
        if self.audio_enabled:
            pygame.mixer.music.stop()
        self.play_sound("death")

    def play_sound(self, name: str) -> None:
        """Joue un son si le fichier existe."""
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()

    # ------------------------------------------------------------------
    # Dessin de l'écran
    # ------------------------------------------------------------------
    def draw(self) -> None:
        """Dessine l'écran correspondant à l'état actuel."""
        self.draw_background()
        if self.state == "welcome":
            self.draw_welcome()
        elif self.state == "playing":
            self.draw_gameplay()
        else:
            self.draw_game_over()
        pygame.display.flip()

    def draw_background(self) -> None:
        """Dessine le fond spatial, avec image ou étoiles simples."""
        background = self.images.get("background")
        if background is not None:
            self.screen.blit(background, (0, 0))
            return

        self.screen.fill((3, 6, 24))
        for x, y, radius in self.stars:
            pygame.draw.circle(self.screen, (205, 220, 255), (x, y), radius)

    def draw_gameplay(self) -> None:
        """Dessine les objets, le vaisseau et le compteur."""
        for obj in self.objects:
            if obj.kind == "asteroid":
                self.draw_asteroid(obj)
            else:
                self.draw_coin(obj)
        self.draw_ship()
        self.draw_hud()

    def draw_ship(self) -> None:
        """Dessine l'image du vaisseau ou un vaisseau simple de secours."""
        ship = self.images.get("ship")
        x, y = int(self.player_x), int(self.player_y)
        if ship is not None:
            self.screen.blit(ship, (x, y))
            return

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
        """Dessine une météorite little/mid/big ou un caillou de secours."""
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
        """Dessine l'image de la pièce ou une pièce simple de secours."""
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
        """Affiche le temps et les pièces pendant la partie."""
        time_text = self.font.render(
            f"Temps : {self.elapsed:05.1f}s", True, (235, 245, 255)
        )
        coin_text = self.font.render(f"Pièces : {self.coins}", True, (255, 230, 100))
        self.screen.blit(time_text, (18, 16))
        self.screen.blit(coin_text, (SCREEN_WIDTH - coin_text.get_width() - 18, 16))

    def draw_text_lines(
        self,
        lines: list[tuple[str, pygame.font.Font, tuple[int, int, int]]],
        start_y: float,
    ) -> None:
        """Affiche plusieurs lignes centrées."""
        y = start_y
        for text, font, color in lines:
            rendered = font.render(text, True, color)
            self.screen.blit(rendered, ((SCREEN_WIDTH - rendered.get_width()) / 2, y))
            y += font.get_height() + 10

    def button_rect(self) -> pygame.Rect:
        """Zone cliquable du bouton démarrer/recommencer."""
        return pygame.Rect((SCREEN_WIDTH - 300) // 2, 370, 300, 58)

    def draw_button(self, label: str) -> None:
        """Dessine un bouton simple."""
        rect = self.button_rect()
        pygame.draw.rect(self.screen, (20, 130, 170), rect, border_radius=14)
        pygame.draw.rect(self.screen, (120, 235, 255), rect, width=3, border_radius=14)
        rendered = self.font.render(label, True, (245, 255, 255))
        self.screen.blit(rendered, rendered.get_rect(center=rect.center))

    def draw_welcome(self) -> None:
        """Page d'accueil avant de commencer."""
        self.draw_text_lines(
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
            150,
        )
        self.draw_button("Démarrer le vol")
        hint = self.small_font.render(
            "Entrée ou Espace fonctionne aussi", True, (180, 255, 190)
        )
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) / 2, 446))

    def draw_game_over(self) -> None:
        """Page de résumé après le crash."""
        self.draw_text_lines(
            [
                ("Crash !", self.big_font, (255, 95, 95)),
                (
                    f"Temps de vol : {self.last_run_time:.1f} secondes",
                    self.font,
                    (235, 245, 255),
                ),
                (f"Pièces récoltées : {self.coins}", self.font, (255, 230, 120)),
            ],
            150,
        )
        self.draw_button("Recommencer")
        hint = self.small_font.render(
            "Entrée / Espace : recommencer    Échap : quitter",
            True,
            (205, 215, 235),
        )
        self.screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) / 2, 446))


def main() -> None:
    """Lance le jeu."""
    DavstarshipGame().run()


if __name__ == "__main__":
    main()
