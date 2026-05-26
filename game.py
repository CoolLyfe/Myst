import pygame
import sys
import threading
import asyncio
import time
from procedural_gen import create_map_image
from player import Player
from monster import BasicMonster, ShadowMonster, LightMonster, TankMonster
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
    lamap = pygame.image.fromstring(map_surface_pil.tobytes(), map_surface_pil.size, map_surface_pil.mode).convert_alpha()
    background = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
    fog_image = pygame.image.load("assets/fog_of_war.png").convert_alpha()
    heart_image = pygame.image.load("assets/heart.png").convert_alpha()
    heal_potion_image = pygame.image.load("assets/heal_potion.png").convert_alpha()

    # --- Joueur Local ---
    player_size = 115
    player_start_x = start_data[0] * cell_size + cell_size // 2
    player_start_y = start_data[1] * cell_size + cell_size // 2
    player = Player(player_start_x, player_start_y, player_size)
    player.spectating = False

    # --- Entités Multi ---
    remote_players = {} # id -> Player
    synced_monsters = {} # id -> BasicMonster

    # --- Camera ---
    def get_camera_offset(cx, cy):
        cam_x = cx - SCREEN_W // 2
        cam_y = cy - SCREEN_H // 2
        cam_x = max(0, min(cam_x, MAP_W - SCREEN_W))
        cam_y = max(0, min(cam_y, MAP_H - SCREEN_H))
        return cam_x, cam_y

    # --- Boucle principale ---
    clock = pygame.time.Clock()
    paused = False
    spectate_index = 0

    # Pause menu buttons
    pause_buttons = [
        {"label": "Resume", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 - 100, 300, 80)},
        {"label": "Quit to Menu", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 20, 300, 80)}
    ]
    # Death menu layouts
    death_btns_solo = [
        {"label": "Try Again", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 20, 300, 80)},
        {"label": "Quit to Menu", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 140, 300, 80)}
    ]
    death_btns_host_spec = [
        {"label": "Try Again", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 20, 300, 80)},
        {"label": "Spectate", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 140, 300, 80)},
        {"label": "Quit to Menu", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 260, 300, 80)}
    ]
    death_btns_client = [
        {"label": "Spectate", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 20, 300, 80)},
        {"label": "Quit to Menu", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 140, 300, 80)}
    ]
    pause_font = pygame.font.SysFont("Chiller", 60)

    click_feedback_btn = None
    click_feedback_timer = 0

    try:
        while True:
            if not network.running:
                if getattr(network.data, 'server_restarting', False):
                    print("[GAME] Server is restarting, reconnecting...")
                    return "retry"
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
                        if player.alive:
                            if (event.key == pygame.K_SPACE) and not player.attacking:
                                player.create_attack_hitbox(width=40, height=90)
                                player.sword_swing_sfx.play()
                            if event.key == pygame.K_e:
                                if player.nb_potions > 0 and player.health < player.max_health:
                                    player.nb_potions -= 1
                                    player.health = min(player.max_health, player.health + 2)
                                    try:
                                        player.drink_potion_sfx.play()
                                    except Exception:
                                        pass
                        elif getattr(player, 'spectating', False):
                            if event.key == pygame.K_RIGHT:
                                spectate_index += 1
                            elif event.key == pygame.K_LEFT:
                                spectate_index -= 1

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos
                    if paused:
                        for btn in pause_buttons:
                            if btn["rect"].collidepoint(pos):
                                click_feedback_btn = btn
                                click_feedback_timer = time.time() + 0.1

                                # Force immediate redraw for visual feedback
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
                                    return
                    elif not player.alive and not getattr(player, 'spectating', False):
                        for btn in death_buttons:
                            if btn["rect"].collidepoint(pos):
                                if btn["label"] == "Try Again":
                                    if is_host and not is_solo and 'server' in locals():
                                        asyncio.run_coroutine_threadsafe(server.broadcast_restart(), server.loop)
                                        time.sleep(0.2)
                                    return "retry"
                                elif btn["label"] == "Spectate":
                                    player.spectating = True
                                elif btn["label"] == "Quit to Menu":
                                    return
            if not paused:

                # Récupération état réseau
                net_state = network.data.get_game_state()
                remote_data = net_state["players"]
                monsters_data = net_state["monsters"]

                alive_pids = sorted([pid for pid, pdata in remote_data.items() if pdata.get("health", 1) > 0])

                # Dynamic death buttons selection
                if is_solo:
                    death_buttons = death_btns_solo
                elif is_host:
                    death_buttons = death_btns_host_spec if alive_pids else death_btns_solo
                else:
                    death_buttons = death_btns_client

                # Host specific spectate logic: force back to death menu if everyone is dead
                if is_host and getattr(player, 'spectating', False) and not alive_pids:
                    player.spectating = False

                is_free_cam = getattr(player, 'spectating', False) and not alive_pids

                # Contrôles joueur local
                keys = pygame.key.get_pressed()
                dx = dy = 0
                speedcross = int(player.speed * 0.7071)
                moved = False

                if player.alive or is_free_cam:
                    if not player.attacking and (keys[pygame.K_z] or keys[pygame.K_UP]):
                        if not player.attacking and (keys[pygame.K_q] or keys[pygame.K_LEFT]):
                            dx -= speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                            dx += speedcross
                            dy -= speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                            dy += speedcross
                        elif not player.attacking and (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
                            dx += speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                            dx -= speedcross
                            dy -= speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                            dy += speedcross
                        else :
                            dy -= player.speed
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                            dy += player.speed
                    elif not player.attacking and (keys[pygame.K_s] or keys[pygame.K_DOWN]):
                        if not player.attacking and (keys[pygame.K_q] or keys[pygame.K_LEFT]):
                            dx -= speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                            dx += speedcross
                            dy += speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                            dy -= speedcross
                        elif not player.attacking and (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
                            dx += speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                            dx -= speedcross
                            dy += speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                            dy -= speedcross
                        else :
                            dy += player.speed
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                            dy -= player.speed
                    elif not player.attacking and (keys[pygame.K_q] or keys[pygame.K_LEFT]):
                        dx -= player.speed
                        moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                        dx += player.speed
                    elif not player.attacking and (keys[pygame.K_d] or keys[pygame.K_RIGHT]):
                        dx += player.speed
                        moved = player.move(dx, dy, MAP_W, MAP_H, lamap)
                        dx -= player.speed

                    running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                    player.set_running(running)
                else:
                    running = False
                    player.set_running(False)

                player.update_animation(delta_ms, moved)

                if moved and not player.attacking and player.alive:
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

            # Process pending hits from the server
            with network.data.lock:
                hits = list(network.data.pending_hits)
                network.data.pending_hits.clear()

            for hit in hits:
                if player.hit_timer <= 0:
                    player.take_damage(hit.get("damage", 1))
                    mx = hit.get("monster_x", player.rect.centerx)
                    my = hit.get("monster_y", player.rect.centery)
                    dx = player.rect.centerx - mx
                    dy = player.rect.centery - my
                    dist = (dx**2 + dy**2)**0.5
                    if dist > 0:
                        player.kb_vx = (dx/dist) * 20
                        player.kb_vy = (dy/dist) * 20

            # Apply smooth knockback locally
            if getattr(player, 'kb_vx', 0) != 0 or getattr(player, 'kb_vy', 0) != 0:
                old_dir = player.direction
                player.move(player.kb_vx, player.kb_vy, lamap.get_width(), lamap.get_height(), lamap)
                player.direction = old_dir
                player.kb_vx *= 0.8
                player.kb_vy *= 0.8
                if abs(player.kb_vx) < 1: player.kb_vx = 0
                if abs(player.kb_vy) < 1: player.kb_vy = 0

            # Rendu
            screensize = pygame.display.get_window_size()
            SCREEN_W, SCREEN_H = screensize[0], screensize[1]

            if getattr(player, 'spectating', False) and alive_pids:
                spectate_pid = alive_pids[spectate_index % len(alive_pids)]
                if spectate_pid in remote_players:
                    cx, cy = remote_players[spectate_pid].rect.center
                else:
                    cx, cy = remote_data[spectate_pid]["pos"]
            else:
                cx, cy = player.rect.centerx, player.rect.centery

            cam_x, cam_y = get_camera_offset(cx, cy)

            background_scaled = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
            screen.blit(background_scaled, (0, 0))
            screen.blit(lamap, (-cam_x, -cam_y))

            # Affichage joueurs distants
            for pid, pdata in remote_data.items():
                if pdata.get("health", 1) <= 0:
                    continue
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
            else:
                img = player.image.copy()
                img_rect = player.image.get_rect(center=(player_screen_x, player_screen_y))

            if player.alive:
                if player.hit_timer > 0:
                    tinted_img = img.copy()
                    tinted_img.fill((40, 0, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
                    screen.blit(tinted_img, img_rect)

                    # Draw red overlay on screen edges
                    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    # Three layers of 8px to create a smoother, slimmer fade (24px total)
                    pygame.draw.rect(overlay, (255, 0, 0, 210), overlay.get_rect(), 10)
                    pygame.draw.rect(overlay, (255, 0, 0, 140), overlay.get_rect().inflate(-20, -20), 10)
                    pygame.draw.rect(overlay, (255, 0, 0, 70), overlay.get_rect().inflate(-40, -40), 10)
                    screen.blit(overlay, (0, 0))

                    player.hit_timer -= 1
                else:
                    screen.blit(img, img_rect)

            # Affichage monstres
            # print(f"Processing {len(monsters_data)} monsters")
            for mid, mdata in monsters_data.items():
                if not mdata["alive"]: continue
                if mid not in synced_monsters:
                    mtype = mdata.get("type", "basic")
                    if mtype == "shadow":
                        synced_monsters[mid] = ShadowMonster(mdata["pos"][0], mdata["pos"][1])
                    elif mtype == "light":
                        synced_monsters[mid] = LightMonster(mdata["pos"][0], mdata["pos"][1])
                    elif mtype == "tank":
                        synced_monsters[mid] = TankMonster(mdata["pos"][0], mdata["pos"][1])
                    else:
                        synced_monsters[mid] = BasicMonster(mdata["pos"][0], mdata["pos"][1], 150)
                    synced_monsters[mid].health = mdata.get("health", 80)
                    # print(f"New monster {mid} at {mdata['pos']}")
                
                m = synced_monsters[mid]

                # Update hit timer and health from server
                if m.health > mdata.get("health", 0):
                    m.hit_timer = 10
                m.health = mdata.get("health", 0)

                m.rect.center = mdata["pos"]
                m.update_hitbox()

                # Update monster direction based on movement if server provides it
                m.direction = mdata.get("dir", "down")
                m.update_animation(delta_ms, mdata.get("moving", False), mdata.get("attacking", 0) > 0)

                m_screen_x = m.rect.centerx - cam_x
                m_screen_y = m.rect.centery - cam_y
                m_blit_rect = m.image.get_rect(center=(m_screen_x, m_screen_y))

                if m.hit_timer > 0:
                    # Create a red-tinted version of the image
                    tinted_img = m.image.copy()
                    # Using a lower red value for a more subtle glow
                    tinted_img.fill((40, 0, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
                    screen.blit(tinted_img, m_blit_rect)
                    m.hit_timer -= 1
                else:
                    screen.blit(m.image, m_blit_rect)

                # Collision attaque joueur local -> monstre
                if player.alive and not paused and player.attacking:
                    if player.attack_hitbox.colliderect(m.hitbox):
                        if mid not in player.hit_targets and m.hit_timer <= 0:
                            network.hit_monster(mid, player.attack)
                            player.hit_targets.add(mid)
                            m.take_damage(player.attack)

            # Affichage brouillard
            fog_scaled = pygame.transform.scale(fog_image, (SCREEN_W, SCREEN_H))
            screen.blit(fog_scaled, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            # screen.blit(fog_scaled, (0, 0), special_flags=pygame.BLEND_RGBA_MULT) # Removed second blit to improve visibility

            if not player.alive and not getattr(player, 'spectating', False):
                is_wipe = not alive_pids
                
                if is_host and is_wipe:
                    # Full dark grey overlay
                    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    overlay.fill((40, 40, 40, 200)) # Dark grey semi-transparent
                    screen.blit(overlay, (0, 0))
                    msg = "GAME OVER"
                    text_color = (220, 220, 220)
                else:
                    # Red fill
                    death_overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    death_overlay.fill((100, 0, 0, 180)) # Dark red semi-transparent
                    screen.blit(death_overlay, (0, 0))
                    msg = "YOU DIED"
                    text_color = (255, 0, 0)

                death_font = pygame.font.SysFont("Chiller", 150)
                sub_font = pygame.font.SysFont("Chiller", 60)

                death_surf = death_font.render(msg, True, text_color)
                death_rect = death_surf.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 50))
                screen.blit(death_surf, death_rect)

                # Draw Death Menu Buttons
                for btn in death_buttons:
                    color = (80, 80, 80) if (click_feedback_btn == btn and current_time < click_feedback_timer) else (30, 30, 30)
                    pygame.draw.rect(screen, color, btn["rect"])
                    pygame.draw.rect(screen, (255, 255, 255), btn["rect"], 2)
                    label_surf = pause_font.render(btn["label"], True, (255, 255, 255))
                    label_rect = label_surf.get_rect(center=btn["rect"].center)
                    screen.blit(label_surf, label_rect)
            elif getattr(player, 'spectating', False):
                if alive_pids:
                    spec_pid = alive_pids[spectate_index % len(alive_pids)]
                    spec_txt = f"SPECTATING Player {spec_pid} - Use LEFT/RIGHT arrows - ESC for Menu"
                else:
                    spec_txt = "SPECTATING (Free Cam) - Use WASD/Arrows - ESC for Menu"
                spec_surf = pause_font.render(spec_txt, True, (255, 255, 255))
                screen.blit(spec_surf, (SCREEN_W // 2 - spec_surf.get_width() // 2, 20))

            # HUD
            if player.alive:
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
