from entity import Entity


class BasicMonster(Entity):
    def __init__(self, pos_x=700, pos_y=350):
        super().__init__(
            health=100,
            attack=10,
            speed=1,
            image_path="assets/bas_monstre.png",
            pos_x=pos_x,
            pos_y=pos_y,
            hitbox_width=50,
            hitbox_height=70
        )
        # Setup du monstre basique avec ses stats + son sprite
