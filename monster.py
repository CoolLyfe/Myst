import pygame
from entity import Entity


class BasicMonster(Entity):
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
        self.sprite_attackU = []
        self.sprite_attackL = []
        self.sprite_attackR = []
        self.sprite_attackD = []
        
        # Mapping for filenames (to handle the different naming conventions)
        # Note: some files have "-removebg-preview" suffix
        for i in range(1, 6):
            # Up
            img = pygame.image.load(f"assets/monstre/monstre_Uattack_{i}.png").convert_alpha()
            self.sprite_attackU.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            # Left
            img = pygame.image.load(f"assets/monstre/monstre_Lattack_{i}.png").convert_alpha()
            self.sprite_attackL.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            # Right
            img = pygame.image.load(f"assets/monstre/monstre_Rattack_{i}.png").convert_alpha()
            self.sprite_attackR.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
            # Down (has removebg suffix)
            img = pygame.image.load(f"assets/monstre/monstre_Dattack_{i}-removebg-preview.png").convert_alpha()
            self.sprite_attackD.append(pygame.transform.scale(img, (sprite_size, sprite_size)))

        # Setup base image from sprites
        self.image = self.sprite_attackD[0]
        
        self.anim_timer = 0
        self.anim_rate = 100 # 10fps for attack
        self.attack_anim_index = 0
        
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
                if self.attack_anim_index >= len(frames):
                    self.attack_anim_index = 0
            
            if 0 <= self.attack_anim_index < len(frames):
                self.image = frames[self.attack_anim_index]
        else:
            # Use first frame of attack as "directional idle/walk"
            if self.direction == 'up': self.image = self.sprite_attackU[0]
            elif self.direction == 'left': self.image = self.sprite_attackL[0]
            elif self.direction == 'right': self.image = self.sprite_attackR[0]
            else: self.image = self.sprite_attackD[0]
            self.attack_anim_index = 0
            self.anim_timer = 0
