import pygame
from entity import Entity


class BasicMonster(Entity):
    # Class-level cache to avoid reloading images for every monster instance
    _sprite_cache = {
        'U': [],
        'L': [],
        'R': [],
        'D': []
    }
    _cache_initialized = False

    def __init__(self, pos_x, pos_y, sprite_size=100):
        super().__init__(
            health=80,
            attack=12,
            speed=8,
            nb_potions=0,
            image_path="assets/base_monstre.png",
            pos_x=pos_x,
            pos_y=pos_y,
            sprite_size=sprite_size,
            hitbox_width=int(sprite_size * 0.55),
            hitbox_height=int(sprite_size * 0.75)
        )
        
        # Reset cache if Pygame was restarted or if it's empty
        if not BasicMonster._cache_initialized or not BasicMonster._sprite_cache['U']:
            BasicMonster._init_cache(sprite_size)
            
        self.sprite_attackU = BasicMonster._sprite_cache['U']
        self.sprite_attackL = BasicMonster._sprite_cache['L']
        self.sprite_attackR = BasicMonster._sprite_cache['R']
        self.sprite_attackD = BasicMonster._sprite_cache['D']

        # Setup base image from sprites
        self.image = self.sprite_attackD[0]
        
        self.anim_timer = 0
        self.anim_rate = 100 # 10fps for attack
        self.attack_anim_index = 0

    @classmethod
    def clear_cache(cls):
        """Call this when restarting the game to ensure sprites are reloaded."""
        cls._sprite_cache = {'U': [], 'L': [], 'R': [], 'D': []}
        cls._cache_initialized = False

    @classmethod
    def _init_cache(cls, sprite_size):
        print(f"[CLIENT] Initializing BasicMonster sprite cache...")
        cls.clear_cache()
        for i in range(1, 6):
            try:
                # Up
                img = pygame.image.load(f"assets/monstre/monstre_Uattack_{i}.png").convert_alpha()
                cls._sprite_cache['U'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
                # Left
                img = pygame.image.load(f"assets/monstre/monstre_Lattack_{i}.png").convert_alpha()
                cls._sprite_cache['L'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
                # Right
                img = pygame.image.load(f"assets/monstre/monstre_Rattack_{i}.png").convert_alpha()
                cls._sprite_cache['R'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
                # Down (has removebg suffix)
                img = pygame.image.load(f"assets/monstre/monstre_Dattack_{i}-removebg-preview.png").convert_alpha()
                cls._sprite_cache['D'].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            except Exception as e:
                print(f"[CLIENT] Error loading monster sprites: {e}")
        cls._cache_initialized = True
        
    def update_animation(self, dt_ms, is_moving, is_attacking):
        self.attacking = is_attacking
        
        if self.attacking:
            if self.direction == 'up': frames = self.sprite_attackU
            elif self.direction == 'left': frames = self.sprite_attackL
            elif self.direction == 'right': frames = self.sprite_attackR
            else: frames = self.sprite_attackD
            
            if not frames: return # Safety check
            
            self.anim_timer += dt_ms
            if self.anim_timer >= self.anim_rate:
                self.anim_timer = 0
                self.attack_anim_index += 1
                if self.attack_anim_index >= len(frames):
                    self.attack_anim_index = 0
            
            self.image = frames[self.attack_anim_index]
        else:
            # Use first frame of attack as "directional idle/walk"
            try:
                if self.direction == 'up': self.image = self.sprite_attackU[0]
                elif self.direction == 'left': self.image = self.sprite_attackL[0]
                elif self.direction == 'right': self.image = self.sprite_attackR[0]
                else: self.image = self.sprite_attackD[0]
            except IndexError:
                pass # Use default image from Entity if frames are empty
            self.attack_anim_index = 0
            self.anim_timer = 0
