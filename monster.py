import pygame
import random
from entity import Entity

CHANCE_POTION_BASE = 0.22

class BasicMonster(Entity):
    _sprite_cache = {}

    @classmethod
    def get_sprites(cls, sprite_size):
        if sprite_size in cls._sprite_cache:
            return cls._sprite_cache[sprite_size]

        cache = {
            'attackU': [], 'attackL': [], 'attackR': [], 'attackD': [],
            'walkU':   [], 'walkL':   [], 'walkR':   [], 'walkD':   []
        }

        for i in range(1, 6):
            try:
                img = pygame.image.load(f"assets/monstre/monstre_Uattack_{i}.png").convert_alpha()
                cache['attackU'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except: pass
            try:
                img = pygame.image.load(f"assets/monstre/monstre_Lattack_{i}.png").convert_alpha()
                cache['attackL'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except: pass
            try:
                img = pygame.image.load(f"assets/monstre/monstre_Rattack_{i}.png").convert_alpha()
                cache['attackR'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except: pass
            try:
                img = pygame.image.load(f"assets/monstre/monstre_Dattack_{i}-removebg-preview.png").convert_alpha()
                cache['attackD'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except: pass

        for i in range(1, 5):
            try:
                img = pygame.image.load(f"assets/monstre/monstre_Uwalk_{i}.png").convert_alpha()
                cache['walkU'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except: pass
            try:
                img = pygame.image.load(f"assets/monstre/monstre_Lwalk_{i}.png").convert_alpha()
                cache['walkL'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except: pass
            try:
                img = pygame.image.load(f"assets/monstre/monstre_Rwalk_{i}.png").convert_alpha()
                cache['walkR'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except: pass
            try:
                img = pygame.image.load(f"assets/monstre/monstre_Dwalk_{i}.png").convert_alpha()
                cache['walkD'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except: pass

        cls._sprite_cache[sprite_size] = cache
        return cache

    @classmethod
    def clear_cache(cls):
        cls._sprite_cache.clear()

    def __init__(self, pos_x, pos_y, sprite_size=100, health=80, attack=12, speed=8):
        super().__init__(
            health=health, attack=attack, speed=speed, nb_potions=0,
            image_path="assets/base_monstre.png",
            pos_x=pos_x, pos_y=pos_y, sprite_size=sprite_size,
            hitbox_width=int(sprite_size * 0.55),
            hitbox_height=int(sprite_size * 0.75)
        )
        self.sprites   = self.get_sprites(sprite_size)
        self.xp_reward = 20
        self.luck      = 1.0

        if self.sprites['attackD']:
            self.image = self.sprites['attackD'][0]

        self.anim_timer     = 0
        self.anim_rate      = 100
        self.walk_anim_rate = 150
        self.anim_index     = 0

    def update_animation(self, dt_ms, is_moving, is_attacking):
        self.attacking = is_attacking

        if self.attacking:
            if self.direction == 'up':    frames = self.sprites['attackU']
            elif self.direction == 'left': frames = self.sprites['attackL']
            elif self.direction == 'right':frames = self.sprites['attackR']
            else:                          frames = self.sprites['attackD']
            self.anim_timer += dt_ms
            if self.anim_timer >= self.anim_rate:
                self.anim_timer  = 0
                self.anim_index += 1
                if self.anim_index >= len(frames): self.anim_index = 0
            if frames and 0 <= self.anim_index < len(frames):
                self.image = frames[self.anim_index]

        elif is_moving:
            if self.direction == 'up':    frames = self.sprites['walkU']
            elif self.direction == 'left': frames = self.sprites['walkL']
            elif self.direction == 'right':frames = self.sprites['walkR']
            else:                          frames = self.sprites['walkD']
            self.anim_timer += dt_ms
            if self.anim_timer >= self.walk_anim_rate:
                self.anim_timer  = 0
                self.anim_index += 1
                if self.anim_index >= len(frames): self.anim_index = 0
            if frames and 0 <= self.anim_index < len(frames):
                self.image = frames[self.anim_index]

        else:
            # idle directionnele : premiere frame d'attaque selon la direction
            if self.direction == 'up':    self.image = self.sprites['attackU'][0] if self.sprites['attackU'] else self.image
            elif self.direction == 'left': self.image = self.sprites['attackL'][0] if self.sprites['attackL'] else self.image
            elif self.direction == 'right':self.image = self.sprites['attackR'][0] if self.sprites['attackR'] else self.image
            else:                          self.image = self.sprites['attackD'][0] if self.sprites['attackD'] else self.image
            self.anim_index = 0
            self.anim_timer = 0


class ShadowMonster(BasicMonster):
    def __init__(self, pos_x, pos_y):
        super().__init__(pos_x, pos_y, sprite_size=180, health=150, attack=20, speed=2)
        self.xp_reward = 55
        self.luck      = 1.4

class LightMonster(BasicMonster):
    def __init__(self, pos_x, pos_y):
        super().__init__(pos_x, pos_y, sprite_size=135, health=50, attack=8, speed=7)
        self.xp_reward = 18
        self.luck      = 0.8

class TankMonster(BasicMonster):
    def __init__(self, pos_x, pos_y):
        super().__init__(pos_x, pos_y, sprite_size=255, health=400, attack=35, speed=1)
        self.xp_reward = 120
        self.luck      = 2.0
