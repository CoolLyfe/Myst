import pygame
import sys
from procedural_gen import procedural_gen, create_map_image
from player import Player
from monster import BasicMonster


def game():
    # --- Initialisation ---
    pygame.init()
    # pygame.mouse.set_visible(False)
    cell_size = 1500
    map_data = procedural_gen()
    map_surface = create_map_image(map_data, cell_size)

    # Fenêtre adaptée à la taille de la map
    MAP_W, MAP_H = map_surface.size
    SCREEN_W, SCREEN_H = 1000, 600
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
    pygame.display.set_caption("Myst")

    lamap = pygame.image.load("assets/map_game.png").convert_alpha()

    # --- Joueur ---
    player_size = 100
    player_start_x = MAP_W // 2
    player_start_y = MAP_H // 2
    player = Player(player_start_x, player_start_y, player_size)

    # --- Monstre ---
    monster_size = 100
    monster = BasicMonster(player_start_x + 300, player_start_y, monster_size)

    # --- Camera ---
    def get_camera_offset(player):
        cam_x = player.rect.centerx - SCREEN_W // 2
        cam_y = player.rect.centery - SCREEN_H // 2
        # Limite la caméra aux bords de la map
        cam_x = max(0, min(cam_x, MAP_W - SCREEN_W))
        cam_y = max(0, min(cam_y, MAP_H - SCREEN_H))
        return cam_x, cam_y

    # --- Boucle principale ---
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.create_attack_hitbox(width=60, height=40)

        # Contrôles joueur
        keys = pygame.key.get_pressed()
        dx = dy = 0

        if keys[pygame.K_z] or keys[pygame.K_UP]:
            dy -= player.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += player.speed
        if keys[pygame.K_q] or keys[pygame.K_LEFT]:
            dx -= player.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += player.speed

        player.move(dx, dy, MAP_W, MAP_H, lamap)

        screensize = pygame.display.get_window_size()
        SCREEN_W, SCREEN_H = screensize[0], screensize[1]

        # Caméra centrée sur le joueur
        cam_x, cam_y = get_camera_offset(player)

        # Fond écran
        screen.fill((0, 0, 0))

        # Affichage map
        screen.blit(lamap, (-cam_x, -cam_y))

        # Affichage joueur
        player_screen_x = player.rect.centerx - cam_x
        player_screen_y = player.rect.centery - cam_y
        player_blit_rect = player.image.get_rect(center=(player_screen_x, player_screen_y))
        screen.blit(player.image, player_blit_rect)

        # Affichage monstre
        monster_screen_x = monster.rect.centerx - cam_x
        monster_screen_y = monster.rect.centery - cam_y
        monster_blit_rect = monster.image.get_rect(center=(monster_screen_x, monster_screen_y))
        screen.blit(monster.image, monster_blit_rect)

        # Collision attaque joueur -> monstre
        player.check_attack_collision(monster)

        # Debug hitbox
        player.draw_hitbox(screen, cam_x, cam_y)
        monster.draw_hitbox(screen, cam_x, cam_y)
        player.draw_attack_hitbox(screen, cam_x, cam_y)

        player.reset_attack()

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    game()
