from entity import Entity


class Player(Entity):
    def __init__(self):
        super().__init__(
            health=100,
            attack=5,
            speed=5,
            image_path="assets/sprite_test.png",
            pos_x=0,
            pos_y=0,
            hitbox_width=40,
            hitbox_height=60
        )
        # Setup du joueur avec ses stats + son sprite + les mouvements des touches sont deplaces dans le game.py
