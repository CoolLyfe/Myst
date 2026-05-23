from entity import Entity


class BasicMonster(Entity):
    def __init__(self, pos_x, pos_y, sprite_size=100):
        super().__init__(
            health=80,
            attack=12,
            speed=8,
            nb_potions=0,
            image_path="assets/base_monstre.png",
            pos_x=pos_x,
            pos_y=pos_y,
            sprite_size=sprite_size,
            hitbox_width=int(sprite_size * 0.55),
            hitbox_height=int(sprite_size * 0.75)
        )
        # Setup du monstre basique avec ses stats + son sprite
