import pygame

class Monster(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.health = 200
        self.max_health = 200
        self.attack = 0
        self.image = pygame.image.load("assets/monstre_test.png")
        # Set la vie/attaques du monstres et prend le fichier pour son skin
        self.rect = self.image.get_rect()
        self.rect.x = 700
        self.rect.y = 350
        # Position de base du monstre dans la map
