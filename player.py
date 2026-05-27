import pygame
import json
import os
from entity import Entity, xp_pour_niveau, bonus_degats_niveau, bonus_pv_niveau

KEYBINDS_FILE = "keybinds.json"
DEFAULT_KEYBINDS = {
    "haut":    pygame.K_z,
    "bas":     pygame.K_s,
    "gauche":  pygame.K_q,
    "droite":  pygame.K_d,
    "attaque": pygame.K_SPACE,
    "potion":  pygame.K_e,
    "sprint":  pygame.K_LSHIFT,
}

def load_keybinds():
    if os.path.exists(KEYBINDS_FILE):
        try:
            with open(KEYBINDS_FILE, "r") as f:
                raw = json.load(f)
            return {k: int(v) for k, v in raw.items() if k not in ("vol_musique", "vol_effets")}
        except:
            pass
    return DEFAULT_KEYBINDS.copy()

def load_vol_effets():
    """Retourne le volume des effets sauvegardé (défaut 0.5)."""
    if os.path.exists(KEYBINDS_FILE):
        try:
            with open(KEYBINDS_FILE, "r") as f:
                raw = json.load(f)
            return float(raw.get("vol_effets", 0.5))
        except:
            pass
    return 0.5


class Player(Entity):
    def __init__(self, pos_x, pos_y, sprite_size):
        super().__init__(
            health=10, attack=10, speed=10, nb_potions=2,
            image_path="assets/player/player_standing_1.png",
            pos_x=pos_x, pos_y=pos_y, sprite_size=sprite_size,
            hitbox_width=int(sprite_size * 0.7),
            hitbox_height=int(sprite_size * 0.8),
        )
        self.size = sprite_size

        def load_frames(prefix, count):
            frames = []
            for i in range(1, count + 1):
                try:
                    img = pygame.image.load(f"assets/player/player_{prefix}_{i}.png").convert_alpha()
                    frames.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
                except Exception:
                    pass
            return frames

        self.sprite_standing = load_frames("standing", 3)
        self.sprite_runL     = load_frames("Lrun", 3)
        self.sprite_runR     = load_frames("Rrun", 3)
        self.sprite_runU     = load_frames("Urun", 3)
        self.sprite_runD     = load_frames("Drun", 3)
        self.sprite_attackL  = load_frames("Lattaque", 4)
        self.sprite_attackR  = load_frames("Rattaque", 4)
        self.sprite_attackU  = load_frames("Uattaque", 4)
        self.sprite_attackD  = load_frames("Dattaque", 4)

        self.sword_swing_sfx  = pygame.mixer.Sound("assets/sound/sword_swing.mp3")
        self.sword_swing_sfx.set_volume(0.3)
        self.drink_potion_sfx = pygame.mixer.Sound("assets/sound/drink_potion.mp3")
        self.drink_potion_sfx.set_volume(0.5)
        self.footstep_sfx     = pygame.mixer.Sound("assets/sound/running_player.mp3")
        self.footstep_sfx.set_volume(1)
        self.footstep_channel = None

        self.anim_index        = 0
        self.anim_timer        = 0
        self.anim_rate_walk    = 150
        self.anim_rate_run     = 50
        self.attack_anim_index = 0
        self.attack_anim_timer = 0
        self.attack_rate       = 80
        self.running           = False

        self.dashing                     = False
        self.dash_timer                  = 0
        self.dash_duration               = 180
        self.dash_speed_multiplier       = 2.5
        self.dash_cooldown               = 0
        self.dash_cooldown_duration      = 800
        self.dash_invincibility_duration = 200
        self.dash_direction_vector       = pygame.math.Vector2(0, 0)

        # Système de niveaux
        self.niveau     = 1
        self.xp         = 0
        self.xp_suivant = xp_pour_niveau(self.niveau)
        self.nb_kills   = 0

        if self.sprite_standing:
            self.image = self.sprite_standing[0]
        else:
            self.image = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
        self.direction = getattr(self, 'direction', 'down')

    def gagner_xp(self, montant):
        """Ajoute de l'xp et monte de niveau si besoin. Retourne True si level up."""
        self.xp += montant
        level_up = False
        while self.xp >= self.xp_suivant:
            self.xp        -= self.xp_suivant
            self.niveau    += 1
            level_up        = True
            self._appliquer_bonus_niveau()
            self.xp_suivant = xp_pour_niveau(self.niveau)
        return level_up

    def _appliquer_bonus_niveau(self):
        # +1 pv max et +18% degats par niveau
        bonus_pv = bonus_pv_niveau(self.niveau)
        self.max_health += bonus_pv
        self.health      = min(self.health + bonus_pv, self.max_health)
        self.attack      = round(10 + bonus_degats_niveau(self.niveau) * 10, 2)

    def set_running(self, running: bool):
        self.running = running

    def start_footsteps(self):
        if self.footstep_channel is None or not self.footstep_channel.get_busy():
            self.footstep_channel = self.footstep_sfx.play(-1)

    def stop_footsteps(self):
        if self.footstep_channel is not None:
            self.footstep_channel.stop()
            self.footstep_channel = None

    def create_attack_hitbox(self, width=75, height=75):
        super().create_attack_hitbox(width=width, height=height)
        self.attack_anim_index = 0
        self.attack_anim_timer = 0

    def start_dash(self, kb=None):
        if self.dash_cooldown > 0 or self.dashing or self.attacking:
            return False

        self.dashing          = True
        self.dash_timer       = self.dash_duration
        self.dash_cooldown    = self.dash_cooldown_duration
        self.invincible_timer = self.dash_invincibility_duration

        if kb is None:
            kb = DEFAULT_KEYBINDS

        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[kb["haut"]]:   dy -= 1
        if keys[kb["bas"]]:    dy += 1
        if keys[kb["gauche"]]: dx -= 1
        if keys[kb["droite"]]: dx += 1

        if dx == 0 and dy == 0:
            if self.direction == "up":     dy = -1
            elif self.direction == "down":  dy =  1
            elif self.direction == "left":  dx = -1
            elif self.direction == "right": dx =  1

        self.dash_direction_vector = pygame.math.Vector2(dx, dy)
        if self.dash_direction_vector.length() > 0:
            self.dash_direction_vector.normalize_ip()
        return True

    def update(self, dt_ms: int, moving: bool):
        super().update(dt_ms)
        if self.dash_cooldown > 0: self.dash_cooldown -= dt_ms
        if self.dashing:
            self.dash_timer -= dt_ms
            if self.dash_timer <= 0: self.dashing = False

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
                    self.attack_anim_index = 0
                    self.attack_anim_timer = 0
                    self.reset_attack()
                    break

            idx = max(0, min(self.attack_anim_index, len(frames) - 1))
            self.image = frames[idx]
            return

        if moving:
            rate = self.anim_rate_run if self.running else self.anim_rate_walk
            if self.direction == 'left':   frames = self.sprite_runL
            elif self.direction == 'right': frames = self.sprite_runR
            elif self.direction == 'up':    frames = self.sprite_runU
            elif self.direction == 'down':  frames = self.sprite_runD
            else:                           frames = self.sprite_standing
        else:
            frames = self.sprite_standing
            rate   = self.anim_rate_walk

        if not frames:
            return

        self.anim_timer += dt_ms
        while self.anim_timer >= rate:
            self.anim_timer -= rate
            self.anim_index  = (self.anim_index + 1) % len(frames)

        self.image = frames[self.anim_index]

    def move(self, dx, dy, map_width, map_height, lamap, map_data=None):
        new_x = self.rect.centerx + dx
        new_y = self.rect.centery + dy

        half      = self.size // 2
        clamped_x = max(half, min(new_x, map_width  - half))
        clamped_y = max(half, min(new_y, map_height - half))

        if dx > 0:   self.direction = "right"
        elif dx < 0: self.direction = "left"
        if dy > 0:   self.direction = "down"
        elif dy < 0: self.direction = "up"

        if map_data is not None:
            hw = self.hitbox.width  // 2
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
        return True

    def is_position_walkable_geom(self, x, y, map_data):
        cell_size  = 2000
        gap        = 400
        wall_thick = 120

        grid_x = int(x // cell_size)
        grid_y = int(y // cell_size)

        if not (0 <= grid_x < len(map_data[0]) and 0 <= grid_y < len(map_data)):
            return False

        room = map_data[grid_y][grid_x]
        if room[0] == 0:
            return False

        room_left   = grid_x * cell_size + gap // 2 + wall_thick
        room_right  = (grid_x + 1) * cell_size - gap // 2 - wall_thick
        room_top    = grid_y * cell_size + gap // 2 + wall_thick
        room_bottom = (grid_y + 1) * cell_size - gap // 2 - wall_thick

        if room_left <= x <= room_right and room_top <= y <= room_bottom:
            return True

        thickness  = cell_size // 12
        half_thick = thickness // 2
        center_x   = grid_x * cell_size + cell_size // 2
        center_y   = grid_y * cell_size + cell_size // 2

        for conn in room[1]:
            if conn == "N" and y < center_y:
                if center_x - half_thick <= x <= center_x + half_thick: return True
            elif conn == "S" and y > center_y:
                if center_x - half_thick <= x <= center_x + half_thick: return True
            elif conn == "E" and x > center_x:
                if center_y - half_thick <= y <= center_y + half_thick: return True
            elif conn == "O" and x < center_x:
                if center_y - half_thick <= y <= center_y + half_thick: return True

        return False

    def is_position_walkable(self, rect, map_surface):
        pts = [
            rect.center,
            (rect.left, rect.top),
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
        ]
        w, h = map_surface.get_size()
        for (px, py) in pts:
            ix, iy = int(px), int(py)
            if ix < 0 or iy < 0 or ix >= w or iy >= h:
                return False
            if map_surface.get_at((ix, iy)).a == 0:
                return False
        return True
