import pygame

class Player(pygame.sprite.Sprite):

    def __init__(self, x, y, size=None):
        super().__init__()
        self.health = 10
        self.max_health = 10
        self.attack = 2
        self.speed = 10
        self.image = pygame.image.load('assets/sprite_test.png').convert_alpha()
        if size is not None:
            self.size = size
            self.image = pygame.transform.scale(self.image, (size, size))
        else:
            self.size = self.image.get_width()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def move(self, dx, dy, map_w, map_h):
        new_x = self.rect.centerx + dx
        new_y = self.rect.centery + dy
        half = self.size // 2
        clamped_x = max(half, min(new_x, map_w - half))
        clamped_y = max(half, min(new_y, map_h - half))
        self.rect.center = (clamped_x, clamped_y)
