import pygame
import sys
import threading
import asyncio
import time
import json
import os
from procedural_gen import create_map_image
from player import Player, load_keybinds, load_vol_effets
from monster import ShadowMonster, LightMonster, TankMonster
from server import ServerNetwork
from client import ClientNetwork, run_client_network
from boss import Boss


def game(is_host=False, server_ip="127.0.0.1", is_solo=False, room_name=None):
    # Chargement des touches personnalisées dés le début
    kb = load_keybinds()

    if is_host:
        host_addr   = "127.0.0.1" if is_solo else "0.0.0.0"
        max_players = 1 if is_solo else 999
        server      = ServerNetwork(host=host_addr, max_clients=max_players, room_name=room_name)
        def start_server():
            asyncio.run(server.start())
        threading.Thread(target=start_server, daemon=True).start()
        if is_solo:
            print("[JEU] Serveur solo démarré.")
        else:
            print(f"[JEU] Serveur hôte démarré pour la salle : {room_name}")
        time.sleep(1)
    elif room_name:
        discovered_ip, discovered_port = ClientNetwork.discover_room(room_name)
        if discovered_ip:
            server_ip = discovered_ip
        else:
            print(f"[JEU] Salle introuvable : {room_name}")
            return False

    network = ClientNetwork(server_ip=server_ip)
    threading.Thread(target=run_client_network, args=(network,), daemon=True).start()

    pygame.init()

    print("[JEU] En attente des données serveur...")
    start_wait = time.time()
    while network.data.map_data is None:
        time.sleep(0.1)
        if time.time() - start_wait > 10:
            print("[JEU] Timeout de connexion !")
            return

    print("[JEU] Connexion réussie, carte reçue.")

    map_data   = network.data.map_data
    start_data = network.data.start_data
    cell_size  = 2000

    # Chargement de la carte en thread pour ne pas bloquer pygame
    map_surface_pil = None
    def load_map_thread():
        nonlocal map_surface_pil
        map_surface_pil = create_map_image(map_data, cell_size)

    temp_screen  = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
    font         = pygame.font.SysFont("Chiller", 100)
    loading_text = font.render("Chargement de la carte…", True, (255, 255, 255))

    thread = threading.Thread(target=load_map_thread)
    thread.start()

    while map_surface_pil is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        temp_screen.fill((0, 0, 0))
        temp_screen.blit(loading_text, loading_text.get_rect(center=(1920 // 2, 1080 // 2)))
        pygame.display.flip()
        time.sleep(0.1)

    MAP_W, MAP_H       = map_surface_pil.size
    SCREEN_W, SCREEN_H = 1920, 1080
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
    pygame.display.set_caption("Myst Multiplayer")

    background        = pygame.image.load("assets/background_jsp.png").convert()
    lamap             = pygame.image.fromstring(map_surface_pil.tobytes(), map_surface_pil.size, map_surface_pil.mode).convert_alpha()
    background        = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
    fog_image         = pygame.image.load("assets/fog_of_war.png").convert_alpha()
    heart_image       = pygame.image.load("assets/heart.png").convert_alpha()
    heal_potion_image = pygame.image.load("assets/heal_potion.png").convert_alpha()

    player_size    = 120
    player_start_x = start_data[0] * cell_size + cell_size // 2
    player_start_y = start_data[1] * cell_size + cell_size // 2
    player         = Player(player_start_x, player_start_y, player_size)
    player.spectating = False

    # Applique le volume des effets sauvegardé dans les paramétres
    vol_sfx = load_vol_effets()
    player.sword_swing_sfx.set_volume(vol_sfx * 0.6)
    player.drink_potion_sfx.set_volume(vol_sfx)
    player.footstep_sfx.set_volume(vol_sfx)

    remote_players  = {}
    synced_monsters = {}
    _morts_comptabilises = set()  # évite de compter deux fois le meme kill

    # Images des coffres
    try:
        coffre_ferme_img  = pygame.image.load("assets/coffre/coffre_ferme.png").convert_alpha()
        coffre_ouvert_img = pygame.image.load("assets/coffre/coffre_ouvert.png").convert_alpha()
        COFFRE_SIZE = 64
        coffre_ferme_img  = pygame.transform.scale(coffre_ferme_img,  (COFFRE_SIZE, COFFRE_SIZE))
        coffre_ouvert_img = pygame.transform.scale(coffre_ouvert_img, (COFFRE_SIZE, COFFRE_SIZE))
    except:
        coffre_ferme_img  = None
        coffre_ouvert_img = None
        COFFRE_SIZE = 48

    def get_camera_offset(cx, cy):
        cam_x = max(0, min(cx - SCREEN_W // 2, MAP_W - SCREEN_W))
        cam_y = max(0, min(cy - SCREEN_H // 2, MAP_H - SCREEN_H))
        return cam_x, cam_y

    clock  = pygame.time.Clock()
    paused = False
    spectate_index = 0

    hud_font = pygame.font.SysFont("Chiller", 32)
    xp_font  = pygame.font.SysFont("Chiller", 28)

    # Notifications flottantes (level up et loots)
    levelup_msg        = ""
    levelup_timer      = 0
    loot_notifications = []
    damage_numbers     = []  # chiffres de degats flottants au dessus des monstres
    boss_defeated      = False

    # Boutons d'interface
    victory_buttons = [
        {"label": "Retour au menu", "rect": pygame.Rect(SCREEN_W // 2 - 200, SCREEN_H // 2 + 60,  400, 80)},
        {"label": "Rejouer",        "rect": pygame.Rect(SCREEN_W // 2 - 200, SCREEN_H // 2 + 170, 400, 80)},
    ]
    pause_buttons = [
        {"label": "Resume",       "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 - 100, 300, 80)},
        {"label": "Quit to Menu", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 +  20, 300, 80)}
    ]
    death_btns_solo = [
        {"label": "Try Again",    "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 +  20, 300, 80)},
        {"label": "Quit to Menu", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 140, 300, 80)}
    ]
    death_btns_host_spec = [
        {"label": "Try Again",    "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 +  20, 300, 80)},
        {"label": "Spectate",     "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 140, 300, 80)},
        {"label": "Quit to Menu", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 260, 300, 80)}
    ]
    death_btns_client = [
        {"label": "Spectate",     "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 +  20, 300, 80)},
        {"label": "Quit to Menu", "rect": pygame.Rect(SCREEN_W // 2 - 150, SCREEN_H // 2 + 140, 300, 80)}
    ]
    pause_font = pygame.font.SysFont("Chiller", 60)

    click_feedback_btn   = None
    click_feedback_timer = 0

    # Musique dynamique : casu au départ, boss quand le boss arrive
    current_music = None
    try:
        pygame.mixer.music.load("assets/sound/music_casu.mp3")
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)
        current_music = "casu"
    except Exception as e:
        print(f"[JEU] Impossible de charger la musique : {e}")

    try:
        while True:
            if not network.running:
                if getattr(network.data, 'server_restarting', False):
                    print("[JEU] Serveur en redémarrage, reconnexion...")
                    return "retry"
                print("[JEU] Déconnecté du serveur.")
                break

            delta_ms     = clock.tick(60)
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
                            if event.key == kb["attaque"] and not player.attacking:
                                player.create_attack_hitbox(width=40, height=90)
                                player.sword_swing_sfx.play()
                            if event.key == kb["potion"]:
                                if player.nb_potions > 0 and player.health < player.max_health:
                                    player.nb_potions -= 1
                                    player.health = min(player.max_health, player.health + 2)
                                    try:
                                        player.drink_potion_sfx.play()
                                    except Exception:
                                        pass
                            if event.key == kb["sprint"]:
                                player.start_dash(kb)
                        elif getattr(player, 'spectating', False):
                            if event.key == pygame.K_RIGHT:
                                spectate_index += 1
                            elif event.key == pygame.K_LEFT:
                                spectate_index -= 1

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos

                    if boss_defeated:
                        for btn in victory_buttons:
                            if btn["rect"].collidepoint(pos):
                                click_feedback_btn   = btn
                                click_feedback_timer = time.time() + 0.1
                                if btn["label"] == "Retour au menu":
                                    return
                                elif btn["label"] == "Rejouer":
                                    if is_host and 'server' in locals():
                                        asyncio.run_coroutine_threadsafe(server.broadcast_restart(), server.loop)
                                        time.sleep(0.2)
                                    return "retry"
                    elif paused:
                        for btn in pause_buttons:
                            if btn["rect"].collidepoint(pos):
                                click_feedback_btn   = btn
                                click_feedback_timer = time.time() + 0.1
                                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                                overlay.fill((0, 0, 0, 150))
                                screen.blit(overlay, (0, 0))
                                for b in pause_buttons:
                                    color = (80, 80, 80) if b == btn else (30, 30, 30)
                                    pygame.draw.rect(screen, color, b["rect"])
                                    pygame.draw.rect(screen, (255, 255, 255), b["rect"], 2)
                                    l_surf = pause_font.render(b["label"], True, (255, 255, 255))
                                    screen.blit(l_surf, l_surf.get_rect(center=b["rect"].center))
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
                net_state     = network.data.get_game_state()
                remote_data   = net_state["players"]
                monsters_data = net_state["monsters"]
                projectiles_data = net_state.get("projectiles", [])
                boss_active   = net_state.get("boss_active", False)
                boss_room     = net_state.get("boss_room", None)
                boss_defeated = net_state.get("boss_defeated", False)
                drops_potion  = net_state.get("drops_potion", {})
                if not isinstance(drops_potion, dict): drops_potion = {}
                coffres_data  = net_state.get("coffres", {})
                if not isinstance(coffres_data, dict): coffres_data = {}

                alive_pids = sorted([pid for pid, pdata in remote_data.items() if pdata.get("health", 1) > 0])

                if is_solo:
                    death_buttons = death_btns_solo
                elif is_host:
                    death_buttons = death_btns_host_spec if alive_pids else death_btns_solo
                else:
                    death_buttons = death_btns_client

                if is_host and getattr(player, 'spectating', False) and not alive_pids:
                    player.spectating = False

                is_free_cam = getattr(player, 'spectating', False) and not alive_pids

                keys       = pygame.key.get_pressed()
                dx = dy    = 0
                speedcross = int(player.speed * 0.7071)
                moved      = False

                if player.dashing:
                    dash_displacement = player.speed * player.dash_speed_multiplier
                    dx_dash = player.dash_direction_vector.x * dash_displacement
                    dy_dash = player.dash_direction_vector.y * dash_displacement
                    moved_x = player.move(dx_dash, 0, MAP_W, MAP_H, lamap, map_data=map_data)
                    moved_y = player.move(0, dy_dash, MAP_W, MAP_H, lamap, map_data=map_data)
                    moved   = moved_x or moved_y
                    player.stop_footsteps()

                if (player.alive or is_free_cam) and not player.dashing:
                    if not player.attacking and keys[kb["haut"]]:
                        if keys[kb["gauche"]]:
                            dx -= speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                            dx += speedcross
                            dy -= speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                            dy += speedcross
                        elif keys[kb["droite"]]:
                            dx += speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                            dx -= speedcross
                            dy -= speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                            dy += speedcross
                        else:
                            dy -= player.speed
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                            dy += player.speed
                    elif not player.attacking and keys[kb["bas"]]:
                        if keys[kb["gauche"]]:
                            dx -= speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                            dx += speedcross
                            dy += speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                            dy -= speedcross
                        elif keys[kb["droite"]]:
                            dx += speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                            dx -= speedcross
                            dy += speedcross
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                            dy -= speedcross
                        else:
                            dy += player.speed
                            moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                            dy -= player.speed
                    elif not player.attacking and keys[kb["gauche"]]:
                        dx -= player.speed
                        moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                        dx += player.speed
                    elif not player.attacking and keys[kb["droite"]]:
                        dx += player.speed
                        moved = player.move(dx, dy, MAP_W, MAP_H, lamap, map_data=map_data)
                        dx -= player.speed

                    running = keys[kb["sprint"]]
                    player.set_running(running if moved else False)
                    if not moved: running = False

                # Confinement du joueur dans la salle du boss pendant le combat
                if moved and boss_active and boss_room and player.alive:
                    bgx, bgy = boss_room
                    p_gx = int(player.rect.centerx // 2000)
                    p_gy = int(player.rect.centery // 2000)
                    if p_gx == bgx and p_gy == bgy:
                        gap        = 400
                        room_left   = bgx * cell_size + gap // 2 + player.size // 2
                        room_right  = (bgx + 1) * cell_size - gap // 2 - player.size // 2
                        room_top    = bgy * cell_size + gap // 2 + player.size // 2
                        room_bottom = (bgy + 1) * cell_size - gap // 2 - player.size // 2
                        cx = max(room_left, min(player.rect.centerx, room_right))
                        cy = max(room_top,  min(player.rect.centery, room_bottom))
                        player.rect.centerx = cx
                        player.rect.centery = cy
                        player.update_hitbox()

                player.update(delta_ms, moved)

                if moved and not player.attacking and player.alive:
                    player.start_footsteps()
                else:
                    player.stop_footsteps()

                network.data.update_local_state(
                    player.rect.center, player.direction,
                    player.attacking, moved, running, player.health,
                    niveau=player.niveau, xp=player.xp
                )

                # Ramassage automatique des potions au sol (rayon 60px)
                if player.alive:
                    for drop_id, drop in list(drops_potion.items()):
                        dist = ((player.rect.centerx - drop["x"])**2 + (player.rect.centery - drop["y"])**2)**0.5
                        if dist < 60:
                            network.ramasser_potion(drop_id)
                            player.nb_potions += drop.get("soin", 1)

                # Ouverture de coffre avec la touche F au contact
                if player.alive and keys[pygame.K_f]:
                    for cid, coffre in coffres_data.items():
                        if coffre["etat"] == "ferme":
                            dist = ((player.rect.centerx - coffre["x"])**2 + (player.rect.centery - coffre["y"])**2)**0.5
                            if dist < 80:
                                network.ouvrir_coffre(cid)

            else:
                player.stop_footsteps()
                player.update(0, False)
                net_state        = network.data.get_game_state()
                remote_data      = net_state["players"]
                monsters_data    = net_state["monsters"]
                projectiles_data = net_state.get("projectiles", [])
                boss_active      = net_state.get("boss_active", False)
                boss_room        = net_state.get("boss_room", None)
                boss_defeated    = net_state.get("boss_defeated", False)
                drops_potion     = net_state.get("drops_potion", {})
                if not isinstance(drops_potion, dict): drops_potion = {}
                coffres_data     = net_state.get("coffres", {})
                if not isinstance(coffres_data, dict): coffres_data = {}

            # Changement de musique dynamique selon l'état du boss
            if boss_active and current_music == "casu":
                try:
                    pygame.mixer.music.load("assets/sound/music_boss.mp3")
                    pygame.mixer.music.play(-1)
                    current_music = "boss"
                except: pass
            elif not boss_active and current_music == "boss":
                try:
                    pygame.mixer.music.load("assets/sound/music_casu.mp3")
                    pygame.mixer.music.play(-1)
                    current_music = "casu"
                except: pass

            # Traitement des rewards (XP, coffres, potions)
            with network.data.lock:
                rewards = list(network.data.pending_rewards)
                network.data.pending_rewards.clear()

            for rew in rewards:
                if rew.get("type") == "xp_gain":
                    gained = rew.get("amount", 0)
                    lvl_up = player.gagner_xp(gained)
                    loot_notifications.append({"txt": f"+ {gained} XP", "col": (60, 180, 255), "timer": current_time + 2.5})
                    if lvl_up:
                        levelup_msg   = f"NIVEAU {player.niveau} !"
                        levelup_timer = current_time + 2.5
                elif rew.get("type") == "chest_reward":
                    rec   = rew.get("recompense", {})
                    rtype = rec.get("type", "potion")
                    qty   = rec.get("quantite", 1)
                    if rtype == "potion":
                        player.nb_potions += qty
                        loot_notifications.append({"txt": f"+ {qty} potion{'s' if qty > 1 else ''}", "col": (80, 255, 120), "timer": current_time + 2.5})
                    elif rtype == "xp":
                        lvl_up = player.gagner_xp(qty)
                        loot_notifications.append({"txt": f"+ {qty} XP", "col": (60, 180, 255), "timer": current_time + 2.5})
                        if lvl_up:
                            levelup_msg   = f"NIVEAU {player.niveau} !"
                            levelup_timer = current_time + 2.5
                    elif rtype == "degats":
                        player.attack = round(player.attack + qty * 0.5, 2)
                        loot_notifications.append({"txt": f"+ {qty * 0.5} ATK", "col": (255, 120, 40), "timer": current_time + 2.5})

            # Traitement des dégats reçus
            with network.data.lock:
                hits = list(network.data.pending_hits)
                network.data.pending_hits.clear()

            for hit in hits:
                if player.hit_timer <= 0:
                    player.take_damage(hit.get("damage", 1))
                    mx   = hit.get("monster_x", player.rect.centerx)
                    my   = hit.get("monster_y", player.rect.centery)
                    ddx  = player.rect.centerx - mx
                    ddy  = player.rect.centery - my
                    dist = (ddx**2 + ddy**2)**0.5
                    if dist > 0:
                        player.kb_vx = (ddx / dist) * 20
                        player.kb_vy = (ddy / dist) * 20

            # Knockback progressif
            if getattr(player, 'kb_vx', 0) != 0 or getattr(player, 'kb_vy', 0) != 0:
                old_dir = player.direction
                player.move(player.kb_vx, player.kb_vy, MAP_W, MAP_H, lamap, map_data=map_data)
                player.direction = old_dir
                player.kb_vx *= 0.8
                player.kb_vy *= 0.8
                if abs(player.kb_vx) < 1: player.kb_vx = 0
                if abs(player.kb_vy) < 1: player.kb_vy = 0

            # =================== RENDU ===================
            screensize         = pygame.display.get_window_size()
            SCREEN_W, SCREEN_H = screensize[0], screensize[1]

            if getattr(player, 'spectating', False) and alive_pids:
                spectate_pid = alive_pids[spectate_index % len(alive_pids)]
                cx, cy = (remote_players[spectate_pid].rect.center
                          if spectate_pid in remote_players else remote_data[spectate_pid]["pos"])
            else:
                cx, cy = player.rect.centerx, player.rect.centery

            cam_x, cam_y = get_camera_offset(cx, cy)

            background_scaled = pygame.transform.scale(background, (SCREEN_W, SCREEN_H))
            screen.blit(background_scaled, (0, 0))
            screen.blit(lamap, (-cam_x, -cam_y))

            # Drops de potions au sol
            for drop_id, drop in drops_potion.items():
                sx, sy = int(drop["x"] - cam_x), int(drop["y"] - cam_y)
                if -40 < sx < SCREEN_W + 40 and -40 < sy < SCREEN_H + 40:
                    pygame.draw.ellipse(screen, (30, 180, 60),  (sx - 12, sy - 16, 24, 24))
                    pygame.draw.ellipse(screen, (80, 255, 120), (sx - 8,  sy - 12, 16, 16))
                    pygame.draw.rect(screen,   (200, 255, 200), (sx - 3,  sy - 20,  6,  8))

            # Coffres avec vrais sprites
            for cid, coffre in coffres_data.items():
                sx, sy = int(coffre["x"] - cam_x), int(coffre["y"] - cam_y)
                if -80 < sx < SCREEN_W + 80 and -80 < sy < SCREEN_H + 80:
                    img = coffre_ferme_img if coffre["etat"] == "ferme" else coffre_ouvert_img
                    if img:
                        screen.blit(img, (sx - COFFRE_SIZE // 2, sy - COFFRE_SIZE // 2))
                    else:
                        col = (80, 50, 15) if coffre["etat"] == "ouvert" else (160, 100, 30)
                        pygame.draw.rect(screen, col, (sx - 24, sy - 16, 48, 32))
                        pygame.draw.rect(screen, (140, 170, 200), (sx - 24, sy - 16, 48, 32), 2)
                    if coffre["etat"] == "ferme":
                        hint_c = hud_font.render("F", True, (190, 215, 235))
                        screen.blit(hint_c, (sx - hint_c.get_width() // 2, sy - COFFRE_SIZE // 2 - 16))

            # Joueurs distants
            for pid, pdata in remote_data.items():
                if pdata.get("health", 1) <= 0: continue
                if pid not in remote_players:
                    remote_players[pid] = Player(pdata["pos"][0], pdata["pos"][1], 115)
                rp = remote_players[pid]
                rp.rect.center = pdata["pos"]
                rp.direction   = pdata["dir"]
                rp.attacking   = pdata["attacking"]
                rp.set_running(pdata.get("running", False))
                rp.update(delta_ms, pdata.get("moving", False))
                rp_blit_rect = rp.image.get_rect(center=(rp.rect.centerx - cam_x, rp.rect.centery - cam_y))
                screen.blit(rp.image, rp_blit_rect)

            # Joueur local
            player_screen_x = player.rect.centerx - cam_x
            player_screen_y = player.rect.centery - cam_y
            if getattr(player, 'attacking', False):
                scale    = 1.25
                img      = pygame.transform.scale(player.image, (int(player.image.get_width() * scale), int(player.image.get_height() * scale)))
                img_rect = img.get_rect(center=(player_screen_x, player_screen_y))
            else:
                img      = player.image.copy()
                img_rect = player.image.get_rect(center=(player_screen_x, player_screen_y))

            if player.alive:
                if player.hit_timer > 0:
                    tinted_img = img.copy()
                    tinted_img.fill((40, 0, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
                    screen.blit(tinted_img, img_rect)
                    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    pygame.draw.rect(overlay, (255, 0, 0, 210), overlay.get_rect(), 10)
                    pygame.draw.rect(overlay, (255, 0, 0, 140), overlay.get_rect().inflate(-20, -20), 10)
                    pygame.draw.rect(overlay, (255, 0, 0, 70),  overlay.get_rect().inflate(-40, -40), 10)
                    screen.blit(overlay, (0, 0))
                elif player.invincible_timer > 0 and player.dashing:
                    inv_img = img.copy()
                    inv_img.set_alpha(150)
                    screen.blit(inv_img, img_rect)
                else:
                    screen.blit(img, img_rect)

            # Monstres
            for mid, mdata in monsters_data.items():
                # Comptage des kills — on garde un set des ids déjà morts pour ne pas doubler
                if not mdata["alive"]:
                    if mid not in _morts_comptabilises and mdata.get("type") != "boss":
                        _morts_comptabilises.add(mid)
                        player.nb_kills += 1
                    if mid in synced_monsters:
                        synced_monsters[mid].alive = False
                    continue

                if mid not in synced_monsters:
                    mtype = mdata.get("type", "shadow")
                    if mtype == "shadow":      synced_monsters[mid] = ShadowMonster(mdata["pos"][0], mdata["pos"][1])
                    elif mtype == "light":     synced_monsters[mid] = LightMonster(mdata["pos"][0], mdata["pos"][1])
                    elif mtype == "tank":      synced_monsters[mid] = TankMonster(mdata["pos"][0], mdata["pos"][1])
                    elif mtype == "boss":      synced_monsters[mid] = Boss(mdata["pos"][0], mdata["pos"][1], 150)
                    else:                      synced_monsters[mid] = ShadowMonster(mdata["pos"][0], mdata["pos"][1])
                    synced_monsters[mid].health = mdata.get("health", 150)

                m = synced_monsters[mid]

                if m.health > mdata.get("health", 0):
                    m.hit_timer = 300
                m.health    = mdata.get("health", 0)
                m.rect.center = mdata["pos"]
                m.update_hitbox()
                m.direction = mdata.get("dir", "down")
                if mdata.get("type") == "boss":
                    m.state = mdata.get("state", "WALK")
                m.update_animation(delta_ms, mdata.get("moving", False), mdata.get("attacking", 0) > 0)

                m_screen_x  = m.rect.centerx - cam_x
                m_screen_y  = m.rect.centery - cam_y
                m_blit_rect = m.image.get_rect(center=(m_screen_x, m_screen_y))

                # Traîné de dash pour le boss
                if mdata.get("type") == "boss":
                    if not hasattr(m, 'trail'): m.trail = []
                    if mdata.get("state") == "DASH":
                        m.trail.append((m.rect.centerx, m.rect.centery, m.image.copy()))
                        if len(m.trail) > 8: m.trail.pop(0)
                        for i, (wx, wy, t_img) in enumerate(m.trail):
                            alpha     = int(255 * (i / len(m.trail)) * 0.5)
                            trail_img = t_img.copy()
                            trail_img.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
                            screen.blit(trail_img, trail_img.get_rect(center=(wx - cam_x, wy - cam_y)))
                    else:
                        if m.trail: m.trail.clear()

                if m.hit_timer > 0:
                    tinted_img = m.image.copy()
                    tinted_img.fill((40, 0, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
                    screen.blit(tinted_img, m_blit_rect)
                    m.hit_timer -= delta_ms
                else:
                    screen.blit(m.image, m_blit_rect)

                # Collision attaque joueur -> monstre + damage number
                if player.alive and not paused and player.attacking:
                    if player.attack_hitbox.colliderect(m.hitbox):
                        if mid not in player.hit_targets and m.hit_timer <= 0:
                            if mdata.get("state") == "SPAWN":
                                continue
                            network.hit_monster(mid, player.attack)
                            player.hit_targets.add(mid)
                            m.take_damage(player.attack)
                            damage_numbers.append({
                                "x": m.rect.centerx, "y": m.rect.top - 20,
                                "val": round(player.attack, 1),
                                "timer": current_time + 1.0, "vy": -1.5
                            })

            # Projectiles
            for p in projectiles_data:
                pygame.draw.circle(screen, (255, 100, 0),
                                   (int(p["x"] - cam_x), int(p["y"] - cam_y)), 10)

            # Barre de vie du boss
            for mid, mdata in monsters_data.items():
                if mdata.get("type") == "boss" and mdata["alive"] and boss_active:
                    hp_ratio = mdata.get("health", 0) / mdata.get("max_health", 150)
                    bar_w, bar_h = SCREEN_W // 2, 30
                    bar_x, bar_y = SCREEN_W // 4, 50
                    pygame.draw.rect(screen, (50, 50, 50),  (bar_x, bar_y, bar_w, bar_h))
                    pygame.draw.rect(screen, (200, 0, 0),   (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))
                    pygame.draw.rect(screen, (255, 255, 255),(bar_x, bar_y, bar_w, bar_h), 2)
                    font_boss = pygame.font.SysFont("Chiller", 40)
                    txt = font_boss.render("BOSS", True, (255, 255, 255))
                    screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2, bar_y - 40))

            # Brouillard
            fog_scaled = pygame.transform.scale(fog_image, (SCREEN_W, SCREEN_H))
            screen.blit(fog_scaled, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            # Ecran de mort
            if not player.alive and not getattr(player, 'spectating', False):
                is_wipe = not alive_pids
                if is_host and is_wipe:
                    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    overlay.fill((40, 40, 40, 200))
                    screen.blit(overlay, (0, 0))
                    msg, text_color = "GAME OVER", (220, 220, 220)
                else:
                    death_overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                    death_overlay.fill((100, 0, 0, 180))
                    screen.blit(death_overlay, (0, 0))
                    msg, text_color = "YOU DIED", (255, 0, 0)

                death_font = pygame.font.SysFont("Chiller", 150)
                death_surf = death_font.render(msg, True, text_color)
                screen.blit(death_surf, death_surf.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 50)))

                for btn in death_buttons:
                    color = (80, 80, 80) if (click_feedback_btn == btn and current_time < click_feedback_timer) else (30, 30, 30)
                    pygame.draw.rect(screen, color, btn["rect"])
                    pygame.draw.rect(screen, (255, 255, 255), btn["rect"], 2)
                    label_surf = pause_font.render(btn["label"], True, (255, 255, 255))
                    screen.blit(label_surf, label_surf.get_rect(center=btn["rect"].center))

            elif getattr(player, 'spectating', False):
                spec_txt = (f"SPECTATEUR — Joueur {alive_pids[spectate_index % len(alive_pids)]}  ←→ pour changer"
                            if alive_pids else "SPECTATEUR libre — ZQSD/flèches  ÉCHAP menu")
                spec_surf = pause_font.render(spec_txt, True, (255, 255, 255))
                screen.blit(spec_surf, (SCREEN_W // 2 - spec_surf.get_width() // 2, 20))

            # HUD coeurs, potions, xp, niveau
            if player.alive:
                heart_scaled       = pygame.transform.scale(heart_image,       (SCREEN_W // 25, SCREEN_H // 25))
                heal_potion_scaled = pygame.transform.scale(heal_potion_image, (SCREEN_W // 25, SCREEN_H // 25))
                for i in range(player.health):
                    screen.blit(heart_scaled, (SCREEN_W // 40 + i * (heart_scaled.get_width() + 5), SCREEN_H // 40))
                for i in range(player.nb_potions):
                    screen.blit(heal_potion_scaled,
                                (SCREEN_W // 40 + i * (heal_potion_scaled.get_width() + 5),
                                 SCREEN_H // 35 + heart_scaled.get_height()))

                BAR_W  = 220
                BAR_H  = 12
                MARGE  = 18
                y_xp   = SCREEN_H // 35 + heart_scaled.get_height() + heal_potion_scaled.get_height() + 10
                ratio  = player.xp / player.xp_suivant if player.xp_suivant > 0 else 0
                pygame.draw.rect(screen, (30, 30, 30),   (MARGE, y_xp, BAR_W, BAR_H))
                pygame.draw.rect(screen, (60, 180, 255), (MARGE, y_xp, int(BAR_W * ratio), BAR_H))
                pygame.draw.rect(screen, (255, 255, 255),(MARGE, y_xp, BAR_W, BAR_H), 1)
                niv_txt = xp_font.render(f"Niv. {player.niveau}", True, (255, 220, 60))
                screen.blit(niv_txt, (MARGE, y_xp + BAR_H + 5))

            # Notification de level up
            if levelup_msg and current_time < levelup_timer:
                alpha_lu = min(255, int((levelup_timer - current_time) / 2.5 * 255))
                lu_font  = pygame.font.SysFont("Chiller", 90)
                lu_surf  = lu_font.render(levelup_msg, True, (255, 220, 60))
                lu_surf.set_alpha(alpha_lu)
                screen.blit(lu_surf, (SCREEN_W // 2 - lu_surf.get_width() // 2, SCREEN_H // 4))

            # Notifications de loot (potions, xp, degats) en haut à droite
            loot_notifications = [n for n in loot_notifications if current_time < n["timer"]]
            notif_font = pygame.font.SysFont("Chiller", 46)
            for i, notif in enumerate(loot_notifications):
                alpha_n = min(255, int((notif["timer"] - current_time) / 2.5 * 255))
                n_surf  = notif_font.render(notif["txt"], True, notif["col"])
                n_surf.set_alpha(alpha_n)
                nx   = SCREEN_W - n_surf.get_width() - 30
                ny   = SCREEN_H // 2 - i * 52
                bg_n = pygame.Surface((n_surf.get_width() + 20, n_surf.get_height() + 6), pygame.SRCALPHA)
                bg_n.fill((0, 0, 0, int(alpha_n * 0.5)))
                screen.blit(bg_n,   (nx - 10, ny - 3))
                screen.blit(n_surf, (nx, ny))

            # Chiffres de degats flottants au dessus des monstres
            dmg_font       = pygame.font.SysFont("Chiller", 44, bold=True)
            damage_numbers = [d for d in damage_numbers if current_time < d["timer"]]
            for dn in damage_numbers:
                dn["y"]   += dn["vy"]
                progress   = 1.0 - (dn["timer"] - current_time) / 1.0
                alpha_d    = max(0, int(255 * (1.0 - progress)))
                sx         = int(dn["x"] - cam_x)
                sy         = int(dn["y"] - cam_y)
                d_surf     = dmg_font.render(str(dn["val"]), True, (255, 60, 60))
                outline    = dmg_font.render(str(dn["val"]), True, (0, 0, 0))
                d_surf.set_alpha(alpha_d)
                outline.set_alpha(alpha_d)
                for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    screen.blit(outline, (sx - d_surf.get_width() // 2 + ox, sy + oy))
                screen.blit(d_surf, (sx - d_surf.get_width() // 2, sy))

            # Ecran de victoire après la mort du boss
            if boss_defeated:
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 200))
                screen.blit(overlay, (0, 0))

                vic_font  = pygame.font.SysFont("Chiller", 160)
                sub_font2 = pygame.font.SysFont("Chiller", 55)
                vic_surf  = vic_font.render("VICTOIRE !", True, (255, 215, 0))
                screen.blit(vic_surf, (SCREEN_W // 2 - vic_surf.get_width() // 2, SCREEN_H // 4))

                stats_txt = sub_font2.render(
                    f"Niveau {player.niveau}  —  {player.nb_kills} ennemis tués",
                    True, (200, 200, 200))
                screen.blit(stats_txt, (SCREEN_W // 2 - stats_txt.get_width() // 2, SCREEN_H // 2 - 20))

                for btn in victory_buttons:
                    color = (80, 80, 80) if (click_feedback_btn == btn and current_time < click_feedback_timer) else (30, 30, 30)
                    pygame.draw.rect(screen, color, btn["rect"])
                    pygame.draw.rect(screen, (255, 215, 0), btn["rect"], 2)
                    lbl = pause_font.render(btn["label"], True, (255, 255, 255))
                    screen.blit(lbl, lbl.get_rect(center=btn["rect"].center))

            # Menu pause
            if paused:
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                screen.blit(overlay, (0, 0))
                for btn in pause_buttons:
                    color = (80, 80, 80) if (click_feedback_btn == btn and current_time < click_feedback_timer) else (30, 30, 30)
                    pygame.draw.rect(screen, color, btn["rect"])
                    pygame.draw.rect(screen, (255, 255, 255), btn["rect"], 2)
                    label_surf = pause_font.render(btn["label"], True, (255, 255, 255))
                    screen.blit(label_surf, label_surf.get_rect(center=btn["rect"].center))

            pygame.display.flip()

    finally:
        try:
            pygame.mixer.music.stop()
        except: pass
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
        choice = input("1. Hôte\n2. Rejoindre\nChoix : ")
        if choice == "1":
            game(is_host=True, is_solo=False)
        else:
            ip = input("IP (défaut 127.0.0.1) : ") or "127.0.0.1"
            game(is_host=False, server_ip=ip)
