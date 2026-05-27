import pygame

# Table d'xp par niveau (l'index = le niveau actuel, la valeur = xp nécessaire pour passer au suivant)
XP_PAR_NIVEAU = [0, 50, 120, 220, 350, 520, 730, 990, 1300, 1670, 2100]

def xp_pour_niveau(niveau):
    if niveau < len(XP_PAR_NIVEAU):
        return XP_PAR_NIVEAU[niveau]
    return XP_PAR_NIVEAU[-1] + (niveau - len(XP_PAR_NIVEAU) + 1) * 600

def bonus_degats_niveau(niveau):
    return round(niveau * 0.18, 2)

def bonus_pv_niveau(niveau):
    return niveau * 1


class Entity(pygame.sprite.Sprite):
    def __init__(self, health, attack, speed, nb_potions, image_path,
                 pos_x, pos_y, sprite_size, hitbox_width=None, hitbox_height=None):
        super().__init__()
        self.health     = health
        self.max_health = health
        self.attack     = attack
        self.speed      = speed
        self.nb_potions = nb_potions

        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (sprite_size, sprite_size))
        self.rect  = self.image.get_rect()
        self.rect.x = pos_x
        self.rect.y = pos_y

        if hitbox_width is None:
            hitbox_width  = self.rect.width
        if hitbox_height is None:
            hitbox_height = self.rect.height

        self.hitbox = pygame.Rect(0, 0, hitbox_width, hitbox_height)
        self.hitbox.center = self.rect.center

        self.attack_hitbox  = pygame.Rect(0, 0, 0, 0)
        self.hit_targets    = set()
        self.attacking      = False
        self.direction      = "down"
        self.alive          = True
        self.hit_timer      = 0
        self.invincible_timer = 0
        self.kb_vx = 0
        self.kb_vy = 0

    def update(self, dt_ms):
        if self.hit_timer > 0:
            self.hit_timer -= dt_ms
        if self.invincible_timer > 0:
            self.invincible_timer -= dt_ms

    def update_hitbox(self):
        self.hitbox.center = self.rect.center

    def move_right(self):
        self.rect.x += self.speed
        self.direction = "right"
        self.update_hitbox()

    def move_left(self):
        self.rect.x -= self.speed
        self.direction = "left"
        self.update_hitbox()

    def move_up(self):
        self.rect.y -= self.speed
        self.direction = "up"
        self.update_hitbox()

    def move_down(self):
        self.rect.y += self.speed
        self.direction = "down"
        self.update_hitbox()

    def take_damage(self, damage):
        if self.invincible_timer > 0:
            return
        self.health -= damage
        self.hit_timer = 300
        if self.health <= 0:
            self.health = 0
            self.alive  = False

    def create_attack_hitbox(self, width=60, height=60):
        if self.direction == "right":
            self.attack_hitbox = pygame.Rect(self.hitbox.right, self.hitbox.centery - height // 2, width, height)
        elif self.direction == "left":
            self.attack_hitbox = pygame.Rect(self.hitbox.left - width, self.hitbox.centery - height // 2, width, height)
        elif self.direction == "up":
            self.attack_hitbox = pygame.Rect(self.hitbox.centerx - height // 2, self.hitbox.top - width, height, width)
        elif self.direction == "down":
            self.attack_hitbox = pygame.Rect(self.hitbox.centerx - height // 2, self.hitbox.bottom, height, width)
        self.attacking = True

    def check_attack_collision(self, target):
        if self.attacking and self.attack_hitbox.colliderect(target.hitbox):
            target.take_damage(self.attack)
            return True
        return False

    def reset_attack(self):
        self.attacking = False
        self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
        self.hit_targets.clear()

    def draw_hitbox(self, screen, cam_x=0, cam_y=0):
        debug_rect = pygame.Rect(self.hitbox.x - cam_x, self.hitbox.y - cam_y,
                                 self.hitbox.width, self.hitbox.height)
        pygame.draw.rect(screen, (255, 0, 0), debug_rect, 2)

    def draw_attack_hitbox(self, screen, cam_x=0, cam_y=0):
        if self.attacking:
            debug_rect = pygame.Rect(self.attack_hitbox.x - cam_x, self.attack_hitbox.y - cam_y,
                                     self.attack_hitbox.width, self.attack_hitbox.height)
            pygame.draw.rect(screen, (0, 255, 0), debug_rect, 2)
