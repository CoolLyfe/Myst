import pygame

class Player(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.health = 
        self.max_health =
        self.attack =
        self.speed=
        self.image = pygame.image.load('assets/sprite_test.png')# player
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

    # Code a ranger mais laisser dans player
    pressed = game.pressed

    if pressed.get(pygame.K_RIGHT) and game.player.rect.x + game.player.rect.width < screen.get_width():
        game.player.move_right()
    if pressed.get(pygame.K_LEFT) and game.player.rect.x > 0:
        game.player.move_left()
    if pressed.get(pygame.K_UP) and game.player.rect.y > 0:
        game.player.move_up()
    if pressed.get(pygame.K_DOWN) and game.player.rect.y + game.player.rect.height < screen.get_height():
        game.player.move_down()
    # Code pour verifier si le joueur appuie sur les touches pour bouger

    elif event.type == pygame.KEYDOWN:
        game.pressed[event.key] = True
    elif event.type == pygame.KEYUP:
        game.pressed[event.key] = False
    # Code pour verifier si le joueur laisse la touche appuier longtemps ou pas
