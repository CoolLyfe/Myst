import pygame
import sys
from procedural_gen import procedural_gen, create_map_image
from player import Player
from monster import BasicMonster


def game():
    # --- Initialisation ---
    pygame.init()
    #pygame.mouse.set_visible(False)
    cell_size = 2000
    map_data, start_data = procedural_gen()
    map_surface = create_map_image(map_data, cell_size)

    # Fenêtre adaptée à la taille de la map
    MAP_W, MAP_H = map_surface.size
    SCREEN_W, SCREEN_H = 1000, 600
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
    pygame.display.set_caption("Myst")

    background = pygame.image.load("assets/background_jsp.png").convert()
    lamap = pygame.image.load("assets/map_game.png").convert_alpha()
    background = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
    fog_image = pygame.image.load("assets/fog_of_war.png").convert_alpha()

    # --- Joueur ---
    player_size = 115
    player_size = 115
    player_start_x = start_data[0] * cell_size + cell_size // 2
    player_start_y = start_data[1] * cell_size + cell_size // 2
    player = Player(player_start_x, player_start_y, player_size)
    # Attaque gérée par `player.attacking` et `player.create_attack_hitbox()`

    # --- Monstre ---
    monster_size = 150
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
        delta_ms = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_SPACE) and not player.attacking:
                    player.create_attack_hitbox(width=40, height=90)
                    player.sword_swing_sfx.play()


        # Contrôles joueur
        keys = pygame.key.get_pressed()
        dx = dy = 0
        speedcross = int(player.speed * 0.7071)  # speed / sqrt(2)
        moved = False

        if not player.attacking and (keys[pygame.K_z] or keys[pygame.K_UP]) and not (keys[pygame.K_q] or keys[pygame.K_LEFT]) and not (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
            dy -= player.speed
            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
        elif not player.attacking and (keys[pygame.K_s] or keys[pygame.K_DOWN]) and not (keys[pygame.K_q] or keys[pygame.K_LEFT]) and not (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
            dy += player.speed
            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
        elif not player.attacking and (keys[pygame.K_q] or keys[pygame.K_LEFT]) and not (keys[pygame.K_z] or keys[pygame.K_UP]) and not (keys[pygame.K_s] or keys[pygame.K_DOWN]):
            dx -= player.speed
            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
        elif not player.attacking and (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and not (keys[pygame.K_z] or keys[pygame.K_UP]) and not (keys[pygame.K_s] or keys[pygame.K_DOWN]):
            dx += player.speed
            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
        #les deplacements en croisee
        elif not player.attacking and (keys[pygame.K_z] or keys[pygame.K_UP]) and (keys[pygame.K_q] or keys[pygame.K_LEFT]):
            if player.is_position_walkable(player.rect.move(dx - player.speed, 0), lamap):    
                dx -= speedcross
                moved = player.move(dx, dy, MAP_W, MAP_H, lamap) or moved
            if player.is_position_walkable(player.rect.move(0, dy - player.speed), lamap):
                dy -= speedcross
                moved = player.move(dx, dy, MAP_W, MAP_H, lamap) or moved
        elif not player.attacking and (keys[pygame.K_z] or keys[pygame.K_UP]) and (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
            if player.is_position_walkable(player.rect.move(dx + player.speed, 0), lamap):
                dx += speedcross
                moved = player.move(dx, dy, MAP_W, MAP_H, lamap) or moved
            if player.is_position_walkable(player.rect.move(0, dy - player.speed), lamap):
                dy -= speedcross
                moved = player.move(dx, dy, MAP_W, MAP_H, lamap) or moved
        elif not player.attacking and (keys[pygame.K_s] or keys[pygame.K_DOWN]) and (keys[pygame.K_q] or keys[pygame.K_LEFT]):
            if player.is_position_walkable(player.rect.move(dx - player.speed, 0), lamap):
                dx -= speedcross
                moved = player.move(dx, dy, MAP_W, MAP_H, lamap) or moved
            if player.is_position_walkable(player.rect.move(0, dy + player.speed), lamap):
                dy += speedcross
                moved = player.move(dx, dy, MAP_W, MAP_H, lamap) or moved
        elif not player.attacking and (keys[pygame.K_s] or keys[pygame.K_DOWN]) and (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
            if player.is_position_walkable(player.rect.move(dx + player.speed, 0), lamap):
                dx += speedcross
                moved = player.move(dx, dy, MAP_W, MAP_H, lamap) or moved
            if player.is_position_walkable(player.rect.move(0, dy + player.speed), lamap):
                dy += speedcross
                moved = player.move(dx, dy, MAP_W, MAP_H, lamap) or moved

        running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        player.set_running(running)
        player.update_animation(delta_ms, moved)

        if moved and not player.attacking:
            player.start_footsteps()
        else:
            player.stop_footsteps()

        screensize = pygame.display.get_window_size()
        SCREEN_W, SCREEN_H = screensize[0], screensize[1]

        cam_x, cam_y = get_camera_offset(player)

        background = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
        screen.blit(background, (0, 0))
        
        screen.blit(lamap, (-cam_x, -cam_y))

        player_screen_x = player.rect.centerx - cam_x
        player_screen_y = player.rect.centery - cam_y

        if getattr(player, 'attacking', False): # je sais pas ce que ca fait c'est un tuto qu l'utilise mais ca marche donc pas touche.
            scale = 1.25
            Nw = int(player.image.get_width() * scale)
            Nh = int(player.image.get_height() * scale)
            img = pygame.transform.scale(player.image, (Nw, Nh))
            img_rect = img.get_rect(center=(player_screen_x, player_screen_y))
            screen.blit(img, img_rect)
        else:
            player_blit_rect = player.image.get_rect(center=(player_screen_x, player_screen_y))
            screen.blit(player.image, player_blit_rect)

        # Affichage monstre
        monster_screen_x = monster.rect.centerx - cam_x
        monster_screen_y = monster.rect.centery - cam_y
        monster_blit_rect = monster.image.get_rect(center=(monster_screen_x, monster_screen_y))
        screen.blit(monster.image, monster_blit_rect)

        # Affichage brouillard
        fog_scaled = pygame.transform.scale(fog_image, (SCREEN_W, SCREEN_H))
        screen.blit(fog_scaled, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Collision attaque joueur -> monstre
        player.check_attack_collision(monster)

        # Debug hitbox
        #player.draw_hitbox(screen, cam_x, cam_y)
        #monster.draw_hitbox(screen, cam_x, cam_y)
        #player.draw_attack_hitbox(screen, cam_x, cam_y)
        
        pygame.display.flip()


if __name__ == "__main__":
    game()
