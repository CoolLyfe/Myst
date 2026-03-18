import pygame
import sys
from procedural_gen import procedural_gen, create_map_image
from player import Player

# --- Initialisation ---
pygame.init()
pygame.mouse.set_visible(False) 
cell_size = 1000
procedural_gen_data = procedural_gen()
map_data = procedural_gen_data[0]
start_data = procedural_gen_data[1]
map_surface = create_map_image(map_data, cell_size)

# Fenêtre adaptée à la taille de la map
MAP_W, MAP_H = map_surface.size
SCREEN_W, SCREEN_H = 1000, 600
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
pygame.display.set_caption("Myst")

# Charge le background après l'initialisation de l'écran
background = pygame.image.load("assets/background_jsp.png").convert()
background = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
lamap = pygame.image.load("assets/map_game.png").convert_alpha()

# --- Joueur ---
player_size = 100
player_start_x = start_data[0] * cell_size + cell_size // 2 - player_size // 2
player_start_y = start_data[1] * cell_size + cell_size // 2 - player_size // 2
player = Player(player_start_x, player_start_y, player_size)

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



    # Caméra centrée sur le joueur
    cam_x, cam_y = get_camera_offset(player)

    # Background fixe couvrant l'écran
    screen.blit(background, (0, 0))

    # Affichage map
    screen.blit(lamap, (-cam_x, -cam_y))

    # Affichage joueur (sprite)
    player_screen_x = player.rect.centerx - cam_x
    player_screen_y = player.rect.centery - cam_y
    # create a rect for blitting based on the image size
    blit_rect = player.image.get_rect(center=(player_screen_x, player_screen_y))
    screen.blit(player.image, blit_rect)

    pygame.display.flip()
    clock.tick(60)
