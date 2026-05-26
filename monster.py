from entity import Entity
import pygame
import math
import random


class Monster(Entity):

    def __init__(
        self,
        health,
        attack,
        speed,
        image_path,
        pos_x,
        pos_y,
        sprite_size,

        detection_range=500,
        attack_range=80,
        attack_cooldown=1000
    ):

        super().__init__(
            health=health,
            attack=attack,
            speed=speed,
            nb_potions=0,
            image_path=image_path,
            pos_x=pos_x,
            pos_y=pos_y,
            sprite_size=sprite_size,
            hitbox_width=int(sprite_size * 0.55),
            hitbox_height=int(sprite_size * 0.75)
        )

        # Stats IA
        self.detection_range = detection_range
        self.attack_range = attack_range
        self.attack_cooldown = attack_cooldown
        self.last_attack = 0
        self.state = "idle"
        self.patrol_direction = random.choice([
            "up",
            "down",
            "left",
            "right"
        ])

        self.last_patrol_change = 0
        self.patrol_delay = 2000

  
    # Deplacement avec collision
    def move(self, dx, dy, map_width, map_height, lamap):

        old_x = self.rect.x
        old_y = self.rect.y

        self.rect.x += dx
        self.update_hitbox()

        if not self.can_move(lamap):
            self.rect.x = old_x
            self.update_hitbox()

        self.rect.y += dy
        self.update_hitbox()

        if not self.can_move(lamap):
            self.rect.y = old_y
            self.update_hitbox()

        # Bordures map
        self.rect.x = max(0, min(self.rect.x, map_width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, map_height - self.rect.height))

        self.update_hitbox()

  
    # Check collisions
    def can_move(self, lamap):

        points = [
            (self.hitbox.left, self.hitbox.top),
            (self.hitbox.right, self.hitbox.top),
            (self.hitbox.left, self.hitbox.bottom),
            (self.hitbox.right, self.hitbox.bottom)
        ]

        for point in points:

            try:
                pixel = lamap.get_at((int(point[0]), int(point[1])))

                if pixel.a == 0:
                    return False

            except:
                return False

        return True

    # IA principale
    def update_ai(self, player, map_width, map_height, lamap):

        distance_x = player.rect.centerx - self.rect.centerx
        distance_y = player.rect.centery - self.rect.centery

        distance = math.sqrt(distance_x**2 + distance_y**2)

        # Patrol
        if distance > self.detection_range:

            self.state = "idle"

            current_time = pygame.time.get_ticks()

            if current_time - self.last_patrol_change > self.patrol_delay:

                self.patrol_direction = random.choice([
                    "up",
                    "down",
                    "left",
                    "right"
                ])

                self.last_patrol_change = current_time

            dx = 0
            dy = 0

            if self.patrol_direction == "up":
                dy = -self.speed

            elif self.patrol_direction == "down":
                dy = self.speed

            elif self.patrol_direction == "left":
                dx = -self.speed

            elif self.patrol_direction == "right":
                dx = self.speed

            self.move(dx, dy, map_width, map_height, lamap)

            return

        
        # Chasae
        if distance > self.attack_range:
            self.state = "chase"
            if distance != 0:
                distance_x /= distance
                distance_y /= distance
            dx = distance_x * self.speed
            dy = distance_y * self.speed
            self.move(dx, dy, map_width, map_height, lamap)


        # Attaque
        else:
            self.state = "attack"
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack > self.attack_cooldown:
                self.create_attack_hitbox(width=50, height=70)
                self.check_attack_collision(player)
                self.last_attack = current_time
            else:
                self.reset_attack()



# Types de monstres

class ShadowMonster(Monster):

    def __init__(self, pos_x, pos_y, sprite_size=120):

        super().__init__(
            health=150,
            attack=20,
            speed=2,

            image_path="assets/base_monstre.png",

            pos_x=pos_x,
            pos_y=pos_y,
            sprite_size=sprite_size,

            detection_range=400,
            attack_range=90,
            attack_cooldown=1500
        )


class LightMonster(Monster):

    def __init__(self, pos_x, pos_y, sprite_size=90):

        super().__init__(
            health=50,
            attack=8,
            speed=7,

            image_path="assets/base_monstre.png",

            pos_x=pos_x,
            pos_y=pos_y,
            sprite_size=sprite_size,

            detection_range=700,
            attack_range=70,
            attack_cooldown=700
        )


class TankMonster(Monster):

    def __init__(self, pos_x, pos_y, sprite_size=170):

        super().__init__(
            health=400,
            attack=35,
            speed=1,

            image_path="assets/base_monstre.png",

            pos_x=pos_x,
            pos_y=pos_y,
            sprite_size=sprite_size,

            detection_range=350,
            attack_range=120,
            attack_cooldown=2500
        )
