import pygame
from entity import Entity


class Player(Entity):
    def __init__(self, pos_x, pos_y, sprite_size):
        super().__init__(
            health=3,
            attack=10,
            speed=10,
            nb_potions=2,
            image_path="assets/player/player_standing_1.png",
            pos_x=pos_x,
            pos_y=pos_y,
            sprite_size=sprite_size,
            hitbox_width=int(sprite_size * 0.7),
            hitbox_height=int(sprite_size * 0.8),
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

        img = pygame.image.load("assets/player/player_standing_1.png").convert_alpha()
        self.sprite_standing.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_standing_2.png").convert_alpha()
        self.sprite_standing.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_standing_3.png").convert_alpha()
        self.sprite_standing.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player/player_Lrun_1.png").convert_alpha()
        self.sprite_runL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Lrun_2.png").convert_alpha()
        self.sprite_runL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Lrun_3.png").convert_alpha()
        self.sprite_runL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player/player_Rrun_1.png").convert_alpha()
        self.sprite_runR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Rrun_2.png").convert_alpha()
        self.sprite_runR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Rrun_3.png").convert_alpha()
        self.sprite_runR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player/player_Urun_1.png").convert_alpha()
        self.sprite_runU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Urun_2.png").convert_alpha()
        self.sprite_runU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Urun_3.png").convert_alpha()
        self.sprite_runU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player/player_Drun_1.png").convert_alpha()
        self.sprite_runD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Drun_2.png").convert_alpha()
        self.sprite_runD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Drun_3.png").convert_alpha()
        self.sprite_runD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player/player_Lattaque_1.png").convert_alpha()
        self.sprite_attackL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Lattaque_2.png").convert_alpha()
        self.sprite_attackL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Lattaque_3.png").convert_alpha()
        self.sprite_attackL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Lattaque_4.png").convert_alpha()
        self.sprite_attackL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player/player_Rattaque_1.png").convert_alpha()
        self.sprite_attackR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Rattaque_2.png").convert_alpha()
        self.sprite_attackR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Rattaque_3.png").convert_alpha()
        self.sprite_attackR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Rattaque_4.png").convert_alpha()
        self.sprite_attackR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player/player_Uattaque_1.png").convert_alpha()
        self.sprite_attackU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Uattaque_2.png").convert_alpha()
        self.sprite_attackU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Uattaque_3.png").convert_alpha()
        self.sprite_attackU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Uattaque_4.png").convert_alpha()
        self.sprite_attackU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        img = pygame.image.load("assets/player/player_Dattaque_1.png").convert_alpha()
        self.sprite_attackD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Dattaque_2.png").convert_alpha()
        self.sprite_attackD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Dattaque_3.png").convert_alpha()
        self.sprite_attackD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
        img = pygame.image.load("assets/player/player_Dattaque_4.png").convert_alpha()
        self.sprite_attackD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        self.sword_swing_sfx = pygame.mixer.Sound("assets/sound/sword_swing.mp3")
        self.sword_swing_sfx.set_volume(0.3)

        self.drink_potion_sfx = pygame.mixer.Sound("assets/sound/drink_potion.mp3")
        self.drink_potion_sfx.set_volume(0.5)

        self.footstep_sfx = pygame.mixer.Sound("assets/sound/running_player.mp3")
        self.footstep_sfx.set_volume(1)
        self.footstep_channel = None

        self.anim_index = 0
        self.anim_timer = 0
        self.anim_rate_walk = 150
        self.anim_rate_run = 50
        # Attack animation state
        self.attack_anim_index = 0
        self.attack_anim_timer = 0
        self.attack_rate = 80
        self.running = False

        if len(self.sprite_standing) > 0:
            self.image = self.sprite_standing[0]
        else:
            self.image = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
        self.direction = getattr(self, 'direction', 'down')

    def set_running(self, running: bool):
        self.running = running

    def start_footsteps(self):
        if self.footstep_channel is None or not self.footstep_channel.get_busy():
            self.footstep_channel = self.footstep_sfx.play(-1)

    def stop_footsteps(self):
        if self.footstep_channel is not None:
            self.footstep_channel.stop()
            self.footstep_channel = None

    def create_attack_hitbox(self, width=60, height=60):
        super().create_attack_hitbox(width=width, height=height)
        self.attack_anim_index = 0
        self.attack_anim_timer = 0

    def update_animation(self, dt_ms: int, moving: bool):
        if getattr(self, 'attacking', False):
            if self.direction == 'left' and self.sprite_attackL:
                frames = self.sprite_attackL
            elif self.direction == 'right' and self.sprite_attackR:
                frames = self.sprite_attackR
            elif self.direction == 'up' and self.sprite_attackU:
                frames = self.sprite_attackU
            elif self.direction == 'down' and self.sprite_attackD:
                frames = self.sprite_attackD
            else:
                frames = self.sprite_attackR if self.sprite_attackR else self.sprite_attackL

            if not frames:
                return

            self.attack_anim_timer += dt_ms
            while self.attack_anim_timer >= self.attack_rate:
                self.attack_anim_timer -= self.attack_rate
                self.attack_anim_index += 1
                if self.attack_anim_index >= len(frames):
                    # Fin de l'animation d'attaque
                    self.attack_anim_index = 0
                    self.attack_anim_timer = 0
                    self.reset_attack()
                    break

            # Clamp index and appliquer l'image
            idx = max(0, min(self.attack_anim_index, len(frames) - 1))
            self.image = frames[idx]
            return

        # Si pas d'attaque : animation de marche/standing
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

    def move(self, dx, dy, map_width, map_height, lamap, map_data=None):
        # Calcul de la nouvelle position proposee
        new_x = self.rect.centerx + dx
        new_y = self.rect.centery + dy

        # Bordures de la map ( limitation ecran )
        half = self.size // 2
        clamped_x = max(half, min(new_x, map_width - half))
        clamped_y = max(half, min(new_y, map_height - half))


        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"

        if dy > 0:
            self.direction = "down"
        elif dy < 0:
            self.direction = "up"

        # Test de collision (geometrique si map_data fourni, sinon alpha)
        if map_data is not None:
            # Check 5 points to cover the hitbox (center and 4 corners)
            hw = self.hitbox.width // 2
            hh = self.hitbox.height // 2
            pts_to_check = [
                (clamped_x, clamped_y),
                (clamped_x - hw, clamped_y - hh),
                (clamped_x + hw, clamped_y - hh),
                (clamped_x - hw, clamped_y + hh),
                (clamped_x + hw, clamped_y + hh)
            ]
            for px, py in pts_to_check:
                if not self.is_position_walkable_geom(px, py, map_data):
                    return False
        elif lamap is not None:
            test_rect = self.rect.copy()
            test_rect.center = (clamped_x, clamped_y)
            if not self.is_position_walkable(test_rect, lamap):
                return False

        self.rect.center = (clamped_x, clamped_y)
        self.update_hitbox()
        # Deplacement du joueur + limite aux bords de la map + collision
        return True

    def is_position_walkable_geom(self, x, y, map_data):
        cell_size = 2000
        gap = 400
        wall_thick = 120

        grid_x = int(x // cell_size)
        grid_y = int(y // cell_size)

        if not (0 <= grid_x < len(map_data[0]) and 0 <= grid_y < len(map_data)):
            return False

        room = map_data[grid_y][grid_x]
        if room[0] == 0:
            return False

        # Check inside room (with gap and wall thickness)
        room_left = grid_x * cell_size + gap // 2 + wall_thick
        room_right = (grid_x + 1) * cell_size - gap // 2 - wall_thick
        room_top = grid_y * cell_size + gap // 2 + wall_thick
        room_bottom = (grid_y + 1) * cell_size - gap // 2 - wall_thick

        if room_left <= x <= room_right and room_top <= y <= room_bottom:
            return True

        # Check inside corridors
        thickness = cell_size // 12
        half_thick = thickness // 2
        center_x = grid_x * cell_size + cell_size // 2
        center_y = grid_y * cell_size + cell_size // 2

        for conn in room[1]:
            if conn == "N" and y < center_y:
                if center_x - half_thick <= x <= center_x + half_thick:
                    return True
            elif conn == "S" and y > center_y:
                if center_x - half_thick <= x <= center_x + half_thick:
                    return True
            elif conn == "E" and x > center_x:
                if center_y - half_thick <= y <= center_y + half_thick:
                    return True
            elif conn == "O" and x < center_x:
                if center_y - half_thick <= y <= center_y + half_thick:
                    return True

        return False

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
