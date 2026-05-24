import pygame
import sys
import threading
import asyncio
import time
from procedural_gen import create_map_image
from player import Player
from monster import BasicMonster
from server import ServerNetwork
from client import ClientNetwork, run_client_network


def game(is_host=False, server_ip="127.0.0.1", is_solo=False, room_name=None):
    # --- Initialisation Réseau ---
    if is_host:
        host_addr = "127.0.0.1" if is_solo else "0.0.0.0"
        max_players = 1 if is_solo else 999
        server = ServerNetwork(host=host_addr, max_clients=max_players, room_name=room_name)
        def start_server():
            asyncio.run(server.start())
        threading.Thread(target=start_server, daemon=True).start()
        if is_solo:
            print("[GAME] Solo server started (Private).")
        else:
            print(f"[GAME] Host server started for room: {room_name}")
        time.sleep(1)
    elif room_name:
        # Client discovery
        discovered_ip, discovered_port = ClientNetwork.discover_room(room_name)
        if discovered_ip:
            server_ip = discovered_ip
        else:
            print(f"[GAME] Could not find room: {room_name}")
            return False

    network = ClientNetwork(server_ip=server_ip)
    threading.Thread(target=run_client_network, args=(network,), daemon=True).start()

    # --- Initialisation Pygame ---
    pygame.init()
    
    print("[GAME] Waiting for server map data...")
    start_wait = time.time()
    while network.data.map_data is None:
        time.sleep(0.1)
        if time.time() - start_wait > 10:
            print("[GAME] Connection timed out! Make sure the server is running.")
            return
    
    print("[GAME] Connection successful! Map received.")
    
    map_data = network.data.map_data
    start_data = network.data.start_data
    cell_size = 2000
    
    # --- Loading Map in Background ---
    # We use a thread to create the map image so we can keep pumping events
    # This prevents the "Not Responding" OS message.
    map_surface_pil = None
    def load_map_thread():
        nonlocal map_surface_pil
        map_surface_pil = create_map_image(map_data, cell_size)
    
    # Create a temporary window for loading feedback
    temp_screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
    font = pygame.font.SysFont("Chiller", 100)
    loading_text = font.render("Loading Map... Please wait", True, (255, 255, 255))
    
    thread = threading.Thread(target=load_map_thread)
    thread.start()
    
    while map_surface_pil is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        temp_screen.fill((0, 0, 0))
        text_rect = loading_text.get_rect(center=(1920 // 2, 1080 // 2))
        temp_screen.blit(loading_text, text_rect)
        pygame.display.flip()
        time.sleep(0.1)

    # Fenêtre adaptée à la taille de la map
    MAP_W, MAP_H = map_surface_pil.size
    SCREEN_W, SCREEN_H = 1920, 1080
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
    pygame.display.set_caption("Myst Multiplayer")

    background = pygame.image.load("assets/background_jsp.png").convert()
    lamap = pygame.image.load("assets/map_game.png").convert_alpha()
    background = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
    fog_image = pygame.image.load("assets/fog_of_war.png").convert_alpha()
    heart_image = pygame.image.load("assets/heart.png").convert_alpha()
    heal_potion_image = pygame.image.load("assets/heal_potion.png").convert_alpha()

    # --- Joueur Local ---
    player_size = 115
    player_start_x = start_data[0] * cell_size + cell_size // 2
    player_start_y = start_data[1] * cell_size + cell_size // 2
    player = Player(player_start_x, player_start_y, player_size)

    # --- Entités Multi ---
    remote_players = {} # id -> Player
    synced_monsters = {} # id -> BasicMonster

    # --- Camera ---
    def get_camera_offset(player):
        cam_x = player.rect.centerx - SCREEN_W // 2
        cam_y = player.rect.centery - SCREEN_H // 2
        cam_x = max(0, min(cam_x, MAP_W - SCREEN_W))
        cam_y = max(0, min(cam_y, MAP_H - SCREEN_H))
        return cam_x, cam_y

    # --- Boucle principale ---
    clock = pygame.time.Clock()
    paused = False
    
    # Pause menu buttons
    pause_buttons = [
        {"label": "Resume", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 - 100, 300, 80)},
        {"label": "Quit to Menu", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 20, 300, 80)}
    ]
    pause_font = pygame.font.SysFont("Chiller", 60)
    
    click_feedback_btn = None
    click_feedback_timer = 0

    try:
        while True:
            if not network.running:
                print("[GAME] Disconnected from server.")
                break

            delta_ms = clock.tick(60)
            current_time = time.time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if is_host and 'server' in locals() and server.loop and server.loop.is_running():
                        asyncio.run_coroutine_threadsafe(server.stop(), server.loop)
                        time.sleep(0.2)
                    network.leave()
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        paused = not paused
                    if not paused:
                        if (event.key == pygame.K_SPACE) and not player.attacking:
                            player.create_attack_hitbox(width=40, height=90)
                            player.sword_swing_sfx.play()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and paused:
                    pos = event.pos
                    for btn in pause_buttons:
                        if btn["rect"].collidepoint(pos):
                            click_feedback_btn = btn
                            click_feedback_timer = time.time() + 0.1
                            
                            # Force immediate redraw for visual feedback
                            # (Duplicate rendering logic briefly for feedback)
                            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                            overlay.fill((0, 0, 0, 150))
                            screen.blit(overlay, (0, 0))
                            for b in pause_buttons:
                                color = (80, 80, 80) if b == btn else (30, 30, 30)
                                pygame.draw.rect(screen, color, b["rect"])
                                pygame.draw.rect(screen, (255, 255, 255), b["rect"], 2)
                                l_surf = pause_font.render(b["label"], True, (255, 255, 255))
                                l_rect = l_surf.get_rect(center=b["rect"].center)
                                screen.blit(l_surf, l_rect)
                            pygame.display.flip()
                            time.sleep(0.05)

                            if btn["label"] == "Resume":
                                paused = False
                            elif btn["label"] == "Quit to Menu":
                                return # This will trigger the 'finally' block

            if not paused:
                # Récupération état réseau
                net_state = network.data.get_game_state()
                remote_data = net_state["players"]
                monsters_data = net_state["monsters"]

                # Contrôles joueur local
                keys = pygame.key.get_pressed()
                dx = dy = 0
                speedcross = int(player.speed * 0.7071)
                moved = False

                if not player.attacking:
                    if (keys[pygame.K_z] or keys[pygame.K_UP]):
                        if (keys[pygame.K_q] or keys[pygame.K_LEFT]):
                            dx -= speedcross; dy -= speedcross
                        elif (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
                            dx += speedcross; dy -= speedcross
                        else:
                            dy -= player.speed
                        moved = True
                    elif (keys[pygame.K_s] or keys[pygame.K_DOWN]):
                        if (keys[pygame.K_q] or keys[pygame.K_LEFT]):
                            dx -= speedcross; dy += speedcross
                        elif (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
                            dx += speedcross; dy += speedcross
                        else:
                            dy += player.speed
                        moved = True
                    elif (keys[pygame.K_q] or keys[pygame.K_LEFT]):
                        dx -= player.speed
                        moved = True
                    elif (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
                        dx += player.speed
                        moved = True
                
                if moved:
                    moved = player.move(dx, dy, MAP_W, MAP_H, lamap)

                running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                player.set_running(running)
                player.update_animation(delta_ms, moved)

                if moved and not player.attacking:
                    player.start_footsteps()
                else:
                    player.stop_footsteps()

                # Envoi état local au serveur
                network.data.update_local_state(player.rect.center, player.direction, player.attacking, moved, running, player.health)
            else:
                player.stop_footsteps()
                player.update_animation(0, False) # Force standing frame
                # Still get network state to stay synced
                net_state = network.data.get_game_state()
                remote_data = net_state["players"]
                monsters_data = net_state["monsters"]

            # Rendu
            screensize = pygame.display.get_window_size()
            SCREEN_W, SCREEN_H = screensize[0], screensize[1]
            cam_x, cam_y = get_camera_offset(player)

            background_scaled = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
            screen.blit(background_scaled, (0, 0))
            screen.blit(lamap, (-cam_x, -cam_y))

            # Affichage joueurs distants
            for pid, pdata in remote_data.items():
                if pid not in remote_players:
                    remote_players[pid] = Player(pdata["pos"][0], pdata["pos"][1], 115)
                
                rp = remote_players[pid]
                rp.rect.center = pdata["pos"]
                rp.direction = pdata["dir"]
                rp.attacking = pdata["attacking"]
                rp.set_running(pdata.get("running", False))
                rp.update_animation(delta_ms, pdata.get("moving", False))
                
                rp_screen_x = rp.rect.centerx - cam_x
                rp_screen_y = rp.rect.centery - cam_y
                rp_blit_rect = rp.image.get_rect(center=(rp_screen_x, rp_screen_y))
                screen.blit(rp.image, rp_blit_rect)

            # Affichage joueur local
            player_screen_x = player.rect.centerx - cam_x
            player_screen_y = player.rect.centery - cam_y
            if getattr(player, 'attacking', False):
                scale = 1.25
                img = pygame.transform.scale(player.image, (int(player.image.get_width()*scale), int(player.image.get_height()*scale)))
                img_rect = img.get_rect(center=(player_screen_x, player_screen_y))
                screen.blit(img, img_rect)
            else:
                player_blit_rect = player.image.get_rect(center=(player_screen_x, player_screen_y))
                screen.blit(player.image, player_blit_rect)

            # Affichage monstres
            for mid, mdata in monsters_data.items():
                if not mdata["alive"]: continue
                if mid not in synced_monsters:
                    synced_monsters[mid] = BasicMonster(mdata["pos"][0], mdata["pos"][1], 150)
                
                m = synced_monsters[mid]
                m.rect.center = mdata["pos"]
                m.update_hitbox()
                
                # Update monster direction based on movement if server provides it
                m.direction = mdata.get("dir", "down")
                
                m_screen_x = m.rect.centerx - cam_x
                m_screen_y = m.rect.centery - cam_y
                m_blit_rect = m.image.get_rect(center=(m_screen_x, m_screen_y))
                screen.blit(m.image, m_blit_rect)
                
                # Collision attaque joueur local -> monstre
                if not paused and player.attacking:
                    if player.check_attack_collision(m):
                        network.hit_monster(mid, player.attack)

            # Affichage brouillard
            fog_scaled = pygame.transform.scale(fog_image, (SCREEN_W, SCREEN_H))
            screen.blit(fog_scaled, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(fog_scaled, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # HUD
            heart_scaled = pygame.transform.scale(heart_image, (SCREEN_W // 25, SCREEN_H // 25))
            heal_potion_scaled = pygame.transform.scale(heal_potion_image, (SCREEN_W // 25, SCREEN_H // 25))
            for i in range(player.health):
                screen.blit(heart_scaled, (SCREEN_W // 40 + i * (heart_scaled.get_width() + 5), SCREEN_H // 40))
            for i in range(player.nb_potions):
                screen.blit(heal_potion_scaled, (SCREEN_W // 40 + i * (heal_potion_scaled.get_width() + 5), SCREEN_H // 35 + heart_scaled.get_height()))

            # Draw Pause Menu Overlay
            if paused:
                # Semi-transparent overlay
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                screen.blit(overlay, (0, 0))
                
                for btn in pause_buttons:
                    color = (80, 80, 80) if (click_feedback_btn == btn and current_time < click_feedback_timer) else (30, 30, 30)
                    pygame.draw.rect(screen, color, btn["rect"])
                    pygame.draw.rect(screen, (255, 255, 255), btn["rect"], 2)
                    label_surf = pause_font.render(btn["label"], True, (255, 255, 255))
                    label_rect = label_surf.get_rect(center=btn["rect"].center)
                    screen.blit(label_surf, label_rect)

            pygame.display.flip()
    finally:
        if is_host and 'server' in locals() and server.loop and server.loop.is_running():
            asyncio.run_coroutine_threadsafe(server.stop(), server.loop)
            time.sleep(0.2)
        network.leave()
        pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "host":
        game(is_host=True)
    elif len(sys.argv) > 2:
        game(is_host=False, server_ip=sys.argv[2])
    else:
        print("Usage: python game.py [host|join] [ip]")
        print("Example: python game.py host")
        print("Example: python game.py join 127.0.0.1")
        # Default for convenience
        choice = input("1. Host\n2. Join\nChoice: ")
        if choice == "1":
            game(is_host=True, is_solo=False)
        else:
            ip = input("IP (default 127.0.0.1): ") or "127.0.0.1"
            game(is_host=False, server_ip=ip)
