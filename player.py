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
        # Setup du joueur avec ses stats + son sprite

    def move(self, dx, dy, map_width, map_height, lamap):
        self.rect.x += dx
        self.rect.y += dy

        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"

        if dy > 0:
            self.direction = "down"
        elif dy < 0:
            self.direction = "up"

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.right > map_width:
            self.rect.right = map_width
        if self.rect.bottom > map_height:
            self.rect.bottom = map_height

        self.update_hitbox()
        # Deplacement du joueur + limite aux bords de la map
