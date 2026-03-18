import pygame
from player import Player
from monster import BasicMonster
from procedural_gen import procedural_gen

pygame.init()
pygame.display.set_caption("Myst")
clock = pygame.time.Clock()
screen = pygame.display.set_mode((1920, 1080))
map_x = 0
map_y = 0

map = pygame.image.load("assets/map_game.png")
# Mise en place du background du jeu par le png de la map avec l'algo de generation procedural_gen
# # Ligne a modifier, ne pas prendre le png ( Laissez Louis.L faire)
# map_width = map.get_width()
# map_height = map.get_height()


# Set l'ecran du jeu et la resolution
def starting_game():
    player = Player()
    monster = BasicMonster(700, 350)
    pressed = {}
    # Creation du joueur + du monstre + dico des touches appuyer

    running = True
    # create_map_image(procedural_gen())
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                pressed[event.key] = True

            elif event.type == pygame.KEYUP:
                pressed[event.key] = False

        if pressed.get(pygame.K_RIGHT):
            player.move_right()

        if pressed.get(pygame.K_LEFT):
            player.move_left()

        if pressed.get(pygame.K_UP):
            player.move_up()

        if pressed.get(pygame.K_DOWN):
            player.move_down()

        screen.blit(map, (0, 0))
        # screen.blit(Coordonnes salle de spawn, ( faire spawn en 0 0)) permet de dessiner la map et la salle de spawn au centre de l'ecran

        screen.blit(player.image, player.rect)
        # Fais apparaitre le sprit du joueur

        screen.blit(monster.image, monster.rect)
        # Fais apparaitre le sprit du monstre

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
