import pygame
from game import Game

pygame.init()
pygame.display.set_caption("Myst")
screen = pygame.display.set_mode((1920, 1080))

background = pygame.image.load('../assets/background.png')

game = Game()
running = True

while running:
    screen.blit(background, (0, 0))
    screen.blit(game.player.image, game.player.rect)

    pressed = game.pressed

    if pressed.get(pygame.K_RIGHT) and game.player.rect.x + game.player.rect.width < screen.get_width():
        game.player.move_right()
    if pressed.get(pygame.K_LEFT) and game.player.rect.x > 0:
        game.player.move_left()
    if pressed.get(pygame.K_UP) and game.player.rect.y > 0:
        game.player.move_up()
    if pressed.get(pygame.K_DOWN) and game.player.rect.y + game.player.rect.height < screen.get_height():
        game.player.move_down()

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            game.pressed[event.key] = True
        elif event.type == pygame.KEYUP:
            game.pressed[event.key] = False

pygame.quit()

