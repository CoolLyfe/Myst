import pygame


class Entity(pygame.sprite.Sprite):
    def __init__(
        self,
        health,
        attack,
        speed,
        image_path,
        pos_x,
        pos_y,
        hitbox_width=None,
        hitbox_height=None,
    ):
        super().__init__()
        self.health = health
        self.max_health = health
        self.attack = attack
        self.speed = speed

        self.image = pygame.image.load(image_path)
        self.rect = self.image.get_rect()
        self.rect.x = pos_x
        self.rect.y = pos_y
        # Setup des stats + image + position de base de l'entite

        if hitbox_width is None:
            hitbox_width = self.rect.width
        if hitbox_height is None:
            hitbox_height = self.rect.height

        self.hitbox = pygame.Rect(
            self.rect.x, self.rect.y, hitbox_width, hitbox_height)
        # Setup de la hitbox de l'entite

        self.alive = True

        self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
        self.attacking = False

    def update_hitbox(self):
        self.hitbox.center = self.rect.center
        # Permet de garder la hitbox au meme endroit que le sprite

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.alive = False
        # Gere la perte de pv + la mort

    def attack_target(self, target):
        target.take_damage(self.attack)
        # Permet d'infliger les degats de l'entite a une autre

    def move_right(self):
        self.rect.x += self.speed
        self.update_hitbox()

    def move_left(self):
        self.rect.x -= self.speed
        self.update_hitbox()

    def move_up(self):
        self.rect.y -= self.speed
        self.update_hitbox()

    def move_down(self):
        self.rect.y += self.speed
        self.update_hitbox()
        # Deplacement de base de l'entite

    def draw_hitbox(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.hitbox, 2)
        # Affiche la hitbox pour debug

    def create_attack_hitbox(self, width, height, direction):
        if direction == "right":
            self.attack_hitbox = pygame.Rect(
                self.hitbox.right, self.hitbox.centery - height // 2, width, height
            )
        elif direction == "left":
            self.attack_hitbox = pygame.Rect(
                self.hitbox.left - width,
                self.hitbox.centery - height // 2,
                width,
                height,
            )
        elif direction == "up":
            self.attack_hitbox = pygame.Rect(
                self.hitbox.centerx - width // 2,
                self.hitbox.top - height,
                width,
                height,
            )
        elif direction == "down":
            self.attack_hitbox = pygame.Rect(
                self.hitbox.centerx - width // 2, self.hitbox.bottom, width, height
            )

        self.attacking = True

    def check_attack_collision(self, target):
        if self.attacking and self.attack_hitbox.colliderect(target.hitbox):
            self.attack_target(target)

    def reset_attack(self):
        self.attacking = False

    def draw_attack_hitbox(self, screen):
        if self.attacking:
            pygame.draw.rect(screen, (0, 255, 0), self.attack_hitbox, 2)
