from entity import Entity
import pygame
import math


class BasicMonster(Entity):
    def __init__(self, pos_x, pos_y, sprite_size=100):
        super().__init__(
            health=80,
            attack=12,
            speed=4,
            nb_potions=0,
            image_path="assets/base_monstre.png",
            pos_x=pos_x,
            pos_y=pos_y,
            sprite_size=sprite_size,
            hitbox_width=int(sprite_size * 0.55),
            hitbox_height=int(sprite_size * 0.75)
        )

        self.detection_range = 500
        self.attack_range = 80
        self.attack_cooldown = 1000
        self.last_attack = 0
        self.state = "idle"

    def update_ai(self, player):
        # Distance entre joueur et monstre
        distance_x = player.rect.centerx - self.rect.centerx
        distance_y = player.rect.centery - self.rect.centery
        distance = math.sqrt(distance_x**2 + distance_y**2)

       
        # idle
        if distance > self.detection_range:
            self.state = "idle"
            return

        # chase
        if distance > self.attack_range:
            self.state = "chase"
            if distance != 0:
                distance_x /= distance
                distance_y /= distance
            self.rect.x += distance_x * self.speed
            self.rect.y += distance_y * self.speed

            self.update_hitbox()

            if abs(distance_x) > abs(distance_y):
                if distance_x > 0:
                    self.direction = "right"
                else:
                    self.direction = "left"
            else:
                if distance_y > 0:
                    self.direction = "down"
                else:
                    self.direction = "up"

  

        # attaque
        else:
            self.state = "attack"
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack > self.attack_cooldown:
                self.create_attack_hitbox(width=50, height=70)
                self.check_attack_collision(player)
                self.last_attack = current_time
            else:
                self.reset_attack()
