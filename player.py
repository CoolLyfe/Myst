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

    def move(self, dx, dy, map_w, map_h, map_surface=None):
        # Calcul de la nouvelle position proposée
        new_x = self.rect.centerx + dx
        new_y = self.rect.centery + dy

        # Bordures de la map (limitation écran)
        half = self.size // 2
        clamped_x = max(half, min(new_x, map_w - half))
        clamped_y = max(half, min(new_y, map_h - half))

        # Test de collision transparence (si map_surface fournie)
        if map_surface is not None:
            test_rect = self.rect.copy()
            test_rect.center = (clamped_x, clamped_y)
            if not self.is_position_walkable(test_rect, map_surface):
                return 

        self.rect.center = (clamped_x, clamped_y)

    def is_position_walkable(self, rect, map_surface):
        pts = [
            rect.center,
            (rect.left, rect.top),
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
        ]

        #check l'alpha de la map sous le jouer (alpha = 0 => transparent => pas walkable)

        w, h = map_surface.get_size()
        for (px, py) in pts:
            ix = int(px)
            iy = int(py)
            if ix < 0 or iy < 0 or ix >= w or iy >= h:
                return False
            if map_surface.get_at((ix, iy)).a == 0:
                return False

        return True
