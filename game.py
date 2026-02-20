import pygame
from player import Player

pygame.init()
pygame.display.set_caption("Myst")

screen = pygame.display.set_mode((1920, 1080))
#Set l'ecran du jeu et la resolution

def starting_game():
    
    create_map_image(procedural_gen())

    map = pygame.image.load('assets/map_game.png')
    # Mise en place du background du jeu par le png de la map avec l'algo de generation procedurale
    #Ligne a modifier, ne pas prendre le png ( Laissez Louis.L faire)

    screen.blit(map, (0, 0))
    # screen.blit(Coordonnes salle de spawn, ( faire spawn en 0 0)) permet de dessiner la map et la salle de spawn au centre de l'ecran
    screen.blit(game.player.image, game.player.rect)
    # Fais apparaitre le sprit du joueur

    pygame.display.flip

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quitgame()
    # Si le joueur ferme pygame, le jeu se ferme aussi (Fonction quitgame dans le fichier menu)
