import pygame

class Player(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.health = 
        self.max_health = 
        self.attack = 
        self.speed= 
        self.image = pygame.image.load('../assets/')# player
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0

    def move_right(self):
        self.rect.x += self.speed
    def move_left(self):
        self.rect.x -= self.speed
    def move_up(self):
        self.rect.y += self.speed
    def move_down(self):
        self.rect.y -= self.speed
