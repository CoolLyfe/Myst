import pygame
import random
from entity import Entity

CHANCE_POTION_BASE = 0.22


def _load_sprites(dossier, prefixe, directions, nb_attack, nb_walk, sprite_size):
    """Charge les sprites d'un monstre depuis un dossier dédié."""
    cache = {
        'attackU': [], 'attackL': [], 'attackR': [], 'attackD': [],
        'walkU':   [], 'walkL':   [], 'walkR':   [], 'walkD':   []
    }
    for d in directions:
        for i in range(1, nb_attack + 1):
            try:
                img = pygame.image.load(f"assets/monsters/{dossier}/{prefixe}_Attack_{d}_{i}.png").convert_alpha()
                cache[f'attack{d}'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except: pass
        for i in range(1, nb_walk + 1):
            try:
                img = pygame.image.load(f"assets/monsters/{dossier}/{prefixe}_Walk_{d}_{i}.png").convert_alpha()
                cache[f'walk{d}'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except: pass
    return cache


class BasicMonster(Entity):
    """Monstre de base — sprites dans assets/monsters/shadow/"""
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
            for d, key in [('U', 'attackU'), ('L', 'attackL'), ('R', 'attackR')]:
                try:
                    img = pygame.image.load(f"assets/monsters/shadow/monstre_{d}attack_{i}.png").convert_alpha()
                    cache[key].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
                except: pass
            try:
                img = pygame.image.load(f"assets/monsters/shadow/monstre_Dattack_{i}-removebg-preview.png").convert_alpha()
                cache['attackD'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except: pass

        for i in range(1, 5):
            for d, key in [('U', 'walkU'), ('L', 'walkL'), ('R', 'walkR'), ('D', 'walkD')]:
                try:
                    img = pygame.image.load(f"assets/monsters/shadow/monstre_{d}walk_{i}.png").convert_alpha()
                    cache[key].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
                except: pass

        cls._sprite_cache[sprite_size] = cache
        return cache

    @classmethod
    def clear_cache(cls):
        cls._sprite_cache.clear()

    def __init__(self, pos_x, pos_y, sprite_size=100, health=80, attack=12, speed=8):
        super().__init__(
            health=health, attack=attack, speed=speed, nb_potions=0,
            image_path="assets/monsters/base_monstre.png",
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
            if self.direction == 'up':     frames = self.sprites['attackU']
            elif self.direction == 'left':  frames = self.sprites['attackL']
            elif self.direction == 'right': frames = self.sprites['attackR']
            else:                           frames = self.sprites['attackD']
            self.anim_timer += dt_ms
            if self.anim_timer >= self.anim_rate:
                self.anim_timer  = 0
                self.anim_index += 1
                if self.anim_index >= len(frames): self.anim_index = 0
            if frames and 0 <= self.anim_index < len(frames):
                self.image = frames[self.anim_index]

        elif is_moving:
            if self.direction == 'up':     frames = self.sprites['walkU']
            elif self.direction == 'left':  frames = self.sprites['walkL']
            elif self.direction == 'right': frames = self.sprites['walkR']
            else:                           frames = self.sprites['walkD']
            self.anim_timer += dt_ms
            if self.anim_timer >= self.walk_anim_rate:
                self.anim_timer  = 0
                self.anim_index += 1
                if self.anim_index >= len(frames): self.anim_index = 0
            if frames and 0 <= self.anim_index < len(frames):
                self.image = frames[self.anim_index]

        else:
            if self.direction == 'up':     self.image = self.sprites['attackU'][0] if self.sprites['attackU'] else self.image
            elif self.direction == 'left':  self.image = self.sprites['attackL'][0] if self.sprites['attackL'] else self.image
            elif self.direction == 'right': self.image = self.sprites['attackR'][0] if self.sprites['attackR'] else self.image
            else:                           self.image = self.sprites['attackD'][0] if self.sprites['attackD'] else self.image
            self.anim_index = 0
            self.anim_timer = 0


class DirectionalMonster(BasicMonster):
    """Monstre avec sprites dans un dossier dédié — Small et Tank."""
    _cache_par_classe = {}

    @classmethod
    def get_sprites_custom(cls, dossier, prefixe, nb_attack, nb_walk, sprite_size):
        cle = (cls.__name__, sprite_size)
        if cle in cls._cache_par_classe:
            return cls._cache_par_classe[cle]
        cache = _load_sprites(dossier, prefixe, ['U', 'L', 'R', 'D'], nb_attack, nb_walk, sprite_size)
        cls._cache_par_classe[cle] = cache
        return cache

    def init_sprites_custom(self, dossier, prefixe, nb_attack, nb_walk, sprite_size):
        self.sprites = self.get_sprites_custom(dossier, prefixe, nb_attack, nb_walk, sprite_size)
        if self.sprites['attackD']:
            self.image = self.sprites['attackD'][0]


class ShadowMonster(BasicMonster):
    """Monstre lent et résistant — sprites dans assets/monsters/shadow/"""
    def __init__(self, pos_x, pos_y):
        super().__init__(pos_x, pos_y, sprite_size=180, health=150, attack=20, speed=2)
        self.xp_reward = 55
        self.luck      = 1.4


class LightMonster(DirectionalMonster):
    """Monstre rapide et fragile — sprites dans assets/monsters/light/"""
    def __init__(self, pos_x, pos_y):
        super().__init__(pos_x, pos_y, sprite_size=135, health=50, attack=8, speed=7)
        self.xp_reward = 18
        self.luck      = 0.8
        self.init_sprites_custom("light", "Small", nb_attack=3, nb_walk=4, sprite_size=135)


class TankMonster(DirectionalMonster):
    """Monstre lent avec énorme PV — sprites dans assets/monsters/tank/"""
    def __init__(self, pos_x, pos_y):
        super().__init__(pos_x, pos_y, sprite_size=255, health=400, attack=35, speed=1)
        self.xp_reward = 120
        self.luck      = 2.0
        self.init_sprites_custom("tank", "Tank", nb_attack=3, nb_walk=4, sprite_size=255)
