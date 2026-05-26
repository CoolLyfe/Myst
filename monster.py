import pygame
from entity import Entity


class BasicMonster(Entity):
    @classmethod
    def clear_cache(cls):
        pass # Stub to prevent errors in game.py

    def __init__(self, pos_x, pos_y, sprite_size=150, health=80, attack=12, speed=8):
        super().__init__(
            health=health,
            attack=attack,
            speed=speed,
            nb_potions=0,
            image_path="assets/base_monstre.png",
            pos_x=pos_x,
            pos_y=pos_y,
            sprite_size=sprite_size,
            hitbox_width=int(sprite_size * 0.55),
            hitbox_height=int(sprite_size * 0.75)
        )
        
        self.sprite_attackU = []
        self.sprite_attackL = []
        self.sprite_attackR = []
        self.sprite_attackD = []
        self.sprite_walkU = []
        self.sprite_walkL = []
        self.sprite_walkR = []
        self.sprite_walkD = []

        # Attack sprites (5 frames)
        for i in range(1, 6):
            img = pygame.image.load(f"assets/monstre/monstre_Uattack_{i}.png").convert_alpha()
            self.sprite_attackU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            img = pygame.image.load(f"assets/monstre/monstre_Lattack_{i}.png").convert_alpha()
            self.sprite_attackL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            img = pygame.image.load(f"assets/monstre/monstre_Rattack_{i}.png").convert_alpha()
            self.sprite_attackR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            img = pygame.image.load(f"assets/monstre/monstre_Dattack_{i}-removebg-preview.png").convert_alpha()
            self.sprite_attackD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        # Walk sprites (4 frames)
        for i in range(1, 5):
            img = pygame.image.load(f"assets/monstre/monstre_Uwalk_{i}.png").convert_alpha()
            self.sprite_walkU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            img = pygame.image.load(f"assets/monstre/monstre_Lwalk_{i}.png").convert_alpha()
            self.sprite_walkL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            img = pygame.image.load(f"assets/monstre/monstre_Rwalk_{i}.png").convert_alpha()
            self.sprite_walkR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            img = pygame.image.load(f"assets/monstre/monstre_Dwalk_{i}.png").convert_alpha()
            self.sprite_walkD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        # Setup base image from sprites
        self.image = self.sprite_walkD[0]
        
        self.anim_timer = 0
        self.anim_rate = 100 # 10fps for attack
        self.attack_anim_index = 0
        self.walk_anim_index = 0
        
    def update_animation(self, dt_ms, is_moving, is_attacking):
        self.attacking = is_attacking
        
        if self.attacking:
            if self.direction == 'up': frames = self.sprite_attackU
            elif self.direction == 'left': frames = self.sprite_attackL
            elif self.direction == 'right': frames = self.sprite_attackR
            else: frames = self.sprite_attackD
            
            self.anim_timer += dt_ms
            if self.anim_timer >= self.anim_rate:
                self.anim_timer = 0
                self.attack_anim_index += 1
            
            if len(frames) > 0:
                self.attack_anim_index = self.attack_anim_index % len(frames)
                self.image = frames[self.attack_anim_index]
        elif is_moving:
            if self.direction == 'up': frames = self.sprite_walkU
            elif self.direction == 'left': frames = self.sprite_walkL
            elif self.direction == 'right': frames = self.sprite_walkR
            else: frames = self.sprite_walkD
            
            self.anim_timer += dt_ms
            if self.anim_timer >= self.anim_rate:
                self.anim_timer = 0
                self.walk_anim_index += 1
                
            # Safely clamp the index to prevent out-of-bounds
            if len(frames) > 0:
                self.walk_anim_index = self.walk_anim_index % len(frames)
                self.image = frames[self.walk_anim_index]
            self.attack_anim_index = 0
        else:
            # Idle
            if self.direction == 'up' and self.sprite_walkU: self.image = self.sprite_walkU[0]
            elif self.direction == 'left' and self.sprite_walkL: self.image = self.sprite_walkL[0]
            elif self.direction == 'right' and self.sprite_walkR: self.image = self.sprite_walkR[0]
            elif self.sprite_walkD: self.image = self.sprite_walkD[0]
            self.attack_anim_index = 0
            self.walk_anim_index = 0
            self.anim_timer = 0

class ShadowMonster(BasicMonster):
    def __init__(self, pos_x, pos_y):
        super().__init__(pos_x, pos_y, sprite_size=180, health=150, attack=20, speed=2)

class LightMonster(BasicMonster):
    def __init__(self, pos_x, pos_y):
        super().__init__(pos_x, pos_y, sprite_size=135, health=50, attack=8, speed=7)

class TankMonster(BasicMonster):
    def __init__(self, pos_x, pos_y):
        super().__init__(pos_x, pos_y, sprite_size=255, health=400, attack=35, speed=1)
