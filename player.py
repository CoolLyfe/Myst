from entity import Entity


class Player(Entity):
    def __init__(self, pos_x, pos_y, sprite_size):
        super().__init__(
            health=100,
            attack=10,
            speed=20,
            image_path="assets/sprite_test.png",
            pos_x=pos_x,
            pos_y=pos_y,
            sprite_size=sprite_size,
            hitbox_width=int(sprite_size * 0.55),
            hitbox_height=int(sprite_size * 0.75)
        )
        self.size = sprite_size
        # Setup du joueur avec ses stats + son sprite

    def move(self, dx, dy, map_width, map_height, lamap):
        # Calcul de la nouvelle position proposee
        new_x = self.rect.centerx + dx
        new_y = self.rect.centery + dy

        # Bordures de la map ( limitation ecran )
        half = self.size // 2
        clamped_x = max(half, min(new_x, map_width - half))
        clamped_y = max(half, min(new_y, map_height - half))

        # Direction du joueur
        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"

        if dy > 0:
            self.direction = "down"
        elif dy < 0:
            self.direction = "up"

        # Test de collision transparence ( si map_surface fournie )
        if lamap is not None:
            test_rect = self.rect.copy()
            test_rect.center = (clamped_x, clamped_y)

            if not self.is_position_walkable(test_rect, lamap):
                return

        self.rect.center = (clamped_x, clamped_y)
        self.update_hitbox()
        # Deplacement du joueur + limite aux bords de la map + collision

    def is_position_walkable(self, rect, map_surface):
        pts = [
            rect.center,
            (rect.left, rect.top),
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
        ]

        # Check l'alpha de la map sous le joueur ( alpha = 0 => transparent => pas walkable )
        w, h = map_surface.get_size()
        for (px, py) in pts:
            ix = int(px)
            iy = int(py)

            if ix < 0 or iy < 0 or ix >= w or iy >= h:
                return False

            if map_surface.get_at((ix, iy)).a == 0:
                return False

        return True
