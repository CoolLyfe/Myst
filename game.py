import pygame
from player import Player
from monster import BasicMonster
from procedural_gen import procedural_gen, create_map_image

pygame.init()
pygame.display.set_caption("Myst")
clock = pygame.time.Clock()
screen = pygame.display.set_mode((1920, 1080))

# Set l'ecran du jeu et la resolution
def starting_game():
    map_data = procedural_gen()
    create_map_image(map_data)
    game_map = pygame.image.load("assets/map_game.png").convert()
    game_map = pygame.transform.scale(game_map, (1920, 1080))
    # Mise en place du background du jeu par le png de la map avec l'algo de generation procedural_gen
    # # Ligne a modifier, ne pas prendre le png ( Laissez Louis.L faire)

    player_size = 100
    player_start_x = 300
    player_start_y = 300
    player = Player(player_start_x, player_start_y, player_size)

    monster_size = 100
    monster = BasicMonster(700, 350, monster_size)

    pressed = {}
    # Creation du joueur + du monstre + dico des touches appuyer

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                pressed[event.key] = True

                if event.key == pygame.K_z:
                    player.create_attack_hitbox(width=60, height=40)
                    print(f"attacking: {player.attacking}")

            elif event.type == pygame.KEYUP:
                pressed[event.key] = False

        dx = 0
        dy = 0

        if pressed.get(pygame.K_RIGHT):
            dx += player.speed

        if pressed.get(pygame.K_LEFT):
            dx -= player.speed

        if pressed.get(pygame.K_UP):
            dy -= player.speed

        if pressed.get(pygame.K_DOWN):
            dy += player.speed

        player.move(dx, dy, 1920, 1080, game_map)

        screen.blit(game_map, (0, 0))
        # screen.blit(Coordonnes salle de spawn, ( faire spawn en 0 0)) permet de dessiner la map et la salle de spawn au centre de l'ecran

        screen.blit(player.image, player.rect)
        # Fais apparaitre le sprit du joueur

        screen.blit(monster.image, monster.rect)
        # Fais apparaitre le sprit du monstre

        player.check_attack_collision(monster)

        player.draw_hitbox(screen)
        monster.draw_hitbox(screen)
        player.draw_attack_hitbox(screen)

        player.reset_attack()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

