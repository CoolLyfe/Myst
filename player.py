import pygame
from entity import Entity


class Player(Entity):
    def __init__(self, pos_x, pos_y, sprite_size):
        super().__init__(
            health=100,
            attack=10,
            speed=20,
            image_path="assets/player_standing_1.png",
            pos_x=pos_x,
            pos_y=pos_y,
            sprite_size=sprite_size,
            hitbox_width=int(sprite_size * 0.55),
            hitbox_height=int(sprite_size * 0.75)
        )
        self.size = sprite_size
        self.sprite_standing = []
        self.sprite_runU = []
        self.sprite_runL = []
        self.sprite_runR = []
        self.sprite_runD = []
        self.sprite_attackU = []
        self.sprite_attackL = []
        self.sprite_attackR = []
        self.sprite_attackD = []
            
        img = pygame.image.load("assets/player_standing_1.png").convert_alpha()
        self.sprite_standing.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player_standing_2.png").convert_alpha()
        self.sprite_standing.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player_standing_3.png").convert_alpha()
        self.sprite_standing.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player_Lrun_1.png").convert_alpha()
        self.sprite_runL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player_Lrun_2.png").convert_alpha()
        self.sprite_runL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player_Lrun_3.png").convert_alpha()
        self.sprite_runL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player_Rrun_1.png").convert_alpha()
        self.sprite_runR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player_Rrun_2.png").convert_alpha()
        self.sprite_runR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player_Rrun_3.png").convert_alpha()
        self.sprite_runR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player_Urun_1.png").convert_alpha()
        self.sprite_runU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player_Urun_2.png").convert_alpha()
        self.sprite_runU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player_Drun_1.png").convert_alpha()
        self.sprite_runD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player_Drun_2.png").convert_alpha()
        self.sprite_runD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player_Drun_3.png").convert_alpha()
        self.sprite_runD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))


        # Setup du joueur avec ses stats + son sprite
        # Animation state
        self.anim_index = 0
        self.anim_timer = 0
        self.anim_rate_walk = 150  # ms per frame when walking
        self.anim_rate_run = 80    # ms per frame when running
        self.running = False
        # Ensure there is a valid image surface set
        if len(self.sprite_standing) > 0:
            self.image = self.sprite_standing[0]
        else:
            self.image = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
        self.direction = getattr(self, 'direction', 'down')

    def set_running(self, running: bool):
        self.running = running

    def update_animation(self, dt_ms: int, moving: bool):
        
        # Choix de la liste d'images selon l'état
        if moving:
            rate = self.anim_rate_run if self.running else self.anim_rate_walk
            if self.direction == 'left':
                frames = self.sprite_runL
            elif self.direction == 'right':
                frames = self.sprite_runR
            elif self.direction == 'up':
                frames = self.sprite_runU
            elif self.direction == 'down':
                frames = self.sprite_runD
            else:
                frames = self.sprite_standing
        else:
            frames = self.sprite_standing
            rate = self.anim_rate_walk

        if not frames:
            return

        self.anim_timer += dt_ms
        while self.anim_timer >= rate:
            self.anim_timer -= rate
            self.anim_index = (self.anim_index + 1) % len(frames)

        self.image = frames[self.anim_index]

    def move(self, dx, dy, map_width, map_height, lamap):
        # Calcul de la nouvelle position proposee
        new_x = self.rect.centerx + dx
        new_y = self.rect.centery + dy

        # Bordures de la map ( limitation ecran )
        half = self.size // 2
        clamped_x = max(half, min(new_x, map_width - half))
        clamped_y = max(half, min(new_y, map_height - half))

        # Direction du joueur
        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"

        if dy > 0:
            self.direction = "down"
        elif dy < 0:
            self.direction = "up"

        # Test de collision transparence ( si map_surface fournie )
        if lamap is not None:
            test_rect = self.rect.copy()
            test_rect.center = (clamped_x, clamped_y)

            if not self.is_position_walkable(test_rect, lamap):
                return

        self.rect.center = (clamped_x, clamped_y)
        self.update_hitbox()
        # Deplacement du joueur + limite aux bords de la map + collision

    def is_position_walkable(self, rect, map_surface):
        pts = [
            rect.center,
            (rect.left, rect.top),
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
        ]

        # Check l'alpha de la map sous le joueur ( alpha = 0 => transparent => pas walkable )
        w, h = map_surface.get_size()
        for (px, py) in pts:
            ix = int(px)
            iy = int(py)

            if ix < 0 or iy < 0 or ix >= w or iy >= h:
                return False

            if map_surface.get_at((ix, iy)).a == 0:
                return False

        return True
