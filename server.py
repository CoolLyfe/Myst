import socket
import asyncio
import json
import time
import random
from procedural_gen import procedural_gen


class ServerNetwork:
    def __init__(self, host="0.0.0.0", port=8001, max_clients=999, room_name=None):
        self.host          = host
        self.port          = port
        self.max_clients   = max_clients
        self.room_name     = room_name
        self.clients       = {}
        self.player_states = {}
        self.monster_states= {}
        self.next_player_id= 1
        self.running       = False
        self.restarting    = False
        self.boss_room     = None
        self.boss_active   = False
        self.boss_spawned  = False
        self.boss_defeated = False
        self.projectiles   = []

        # Drops posés par terre aprés la mort d'un monstre
        self.potion_drops   = {}
        self.next_drop_id   = 1

        # Coffres placés dans les salles
        self.coffre_states  = {}
        self.next_coffre_id = 1

        print("[SERVEUR] Géneration de la carte...")
        self.map_data, self.start_data = procedural_gen()
        print(f"[SERVEUR] Carte générée, spawn : {self.start_data}")

        self.init_monsters()
        self.init_coffres()

    def init_monsters(self):
        monster_id_counter = 1
        for grid_y in range(len(self.map_data)):
            for grid_x in range(len(self.map_data[grid_y])):
                room      = self.map_data[grid_y][grid_x]
                room_type = room[0]
                if room_type == 2:
                    self.boss_room = (grid_x, grid_y)
                if room_type in [3, 5]:
                    nb_monsters = random.randint(2, 4) if room_type == 3 else random.randint(3, 6)
                    for _ in range(nb_monsters):
                        mtype = random.choice(["shadow", "light", "tank"])
                        if mtype == "shadow":
                            hp, speed, det_range, atk_range, cd_max = 150, 2, 800, 100, 30
                            hw, hh = 80, 80
                            xp_reward = 55
                            luck = 1.4
                        elif mtype == "light":
                            hp, speed, det_range, atk_range, cd_max = 50, 5, 1000, 80, 14
                            hw, hh = 60, 60
                            xp_reward = 18
                            luck = 0.8
                        elif mtype == "tank":
                            hp, speed, det_range, atk_range, cd_max = 400, 1, 600, 150, 50
                            hw, hh = 130, 130
                            xp_reward = 120
                            luck = 2.0

                        cell_size  = 2000
                        gap        = 400
                        wall_thick = 120
                        margin_x   = wall_thick + hw + 20
                        margin_y   = wall_thick + hh + 20
                        room_left   = grid_x * cell_size + gap // 2 + margin_x
                        room_right  = (grid_x + 1) * cell_size - gap // 2 - margin_x
                        room_top    = grid_y * cell_size + gap // 2 + margin_y
                        room_bottom = (grid_y + 1) * cell_size - gap // 2 - margin_y

                        spawn_x  = random.uniform(room_left, room_right)
                        spawn_y  = random.uniform(room_top, room_bottom)
                        attempts = 0
                        while not self.is_pos_walkable_with_hitbox(spawn_x, spawn_y, hw, hh) and attempts < 10:
                            spawn_x = random.uniform(room_left, room_right)
                            spawn_y = random.uniform(room_top, room_bottom)
                            attempts += 1

                        self.monster_states[str(monster_id_counter)] = {
                            "pos": [spawn_x, spawn_y],
                            "health": hp, "alive": True,
                            "type": mtype, "speed": speed,
                            "detection_range": det_range,
                            "attack_range": atk_range,
                            "attack_cooldown_max": cd_max,
                            "attack_cooldown": 0, "attacking": 0,
                            "patrol_timer": 0, "patrol_dir": "down",
                            "hitbox_hw": hw, "hitbox_hh": hh,
                            "xp_reward": xp_reward, "luck": luck
                        }
                        monster_id_counter += 1

    def init_coffres(self):
        for grid_y in range(len(self.map_data)):
            for grid_x in range(len(self.map_data[grid_y])):
                room_type = self.map_data[grid_y][grid_x][0]
                if room_type == 3 and random.random() < 0.35:
                    self._placer_coffre(grid_x, grid_y, qualite=1)
                elif room_type == 4:
                    for _ in range(random.randint(1, 3)):
                        self._placer_coffre(grid_x, grid_y, qualite=random.randint(1, 2))

    def _placer_coffre(self, grid_x, grid_y, qualite=1):
        cell_size = 2000
        cx = grid_x * cell_size + cell_size // 2 + random.randint(-350, 350)
        cy = grid_y * cell_size + cell_size // 2 + random.randint(-350, 350)
        cid = str(self.next_coffre_id)
        self.next_coffre_id += 1

        # Tirage aleatoire du type de recompense : potion (50%), xp (25%), bonus dégats (25%)
        type_rec = random.choice(["potion", "potion", "xp", "degats"])
        if type_rec == "potion":
            recompense = {"type": "potion", "quantite": qualite}
        elif type_rec == "xp":
            recompense = {"type": "xp", "quantite": qualite * random.randint(30, 60)}
        else:
            recompense = {"type": "degats", "quantite": qualite}

        self.coffre_states[cid] = {"x": cx, "y": cy, "recompense": recompense, "etat": "ferme"}

    def is_walkable(self, x, y):
        grid_x = int(x // 2000)
        grid_y = int(y // 2000)

        # Quand le boss est actif, il est strictement confiné dans les murs de sa salle
        if self.boss_active and self.boss_room:
            bgx, bgy   = self.boss_room
            cell_size  = 2000
            gap        = 400
            wall_thick = 120
            room_left   = bgx * cell_size + gap // 2 + wall_thick
            room_right  = (bgx + 1) * cell_size - gap // 2 - wall_thick
            room_top    = bgy * cell_size + gap // 2 + wall_thick
            room_bottom = (bgy + 1) * cell_size - gap // 2 - wall_thick
            return (room_left <= x <= room_right and room_top <= y <= room_bottom)

        if not (0 <= grid_x < 8 and 0 <= grid_y < 5):
            return False

        room = self.map_data[grid_y][grid_x]
        if room[0] == 0:
            return False

        cell_size  = 2000
        gap        = 400
        wall_thick = 120
        room_left   = grid_x * cell_size + gap // 2 + wall_thick
        room_right  = (grid_x + 1) * cell_size - gap // 2 - wall_thick
        room_top    = grid_y * cell_size + gap // 2 + wall_thick
        room_bottom = (grid_y + 1) * cell_size - gap // 2 - wall_thick

        if room_left <= x <= room_right and room_top <= y <= room_bottom:
            return True

        thickness  = cell_size // 12
        half_thick = thickness // 2
        center_x   = grid_x * cell_size + cell_size // 2
        center_y   = grid_y * cell_size + cell_size // 2

        for conn in room[1]:
            if conn == "N" and y < center_y:
                if center_x - half_thick <= x <= center_x + half_thick: return True
            elif conn == "S" and y > center_y:
                if center_x - half_thick <= x <= center_x + half_thick: return True
            elif conn == "E" and x > center_x:
                if center_y - half_thick <= y <= center_y + half_thick: return True
            elif conn == "O" and x < center_x:
                if center_y - half_thick <= y <= center_y + half_thick: return True

        return False

    def is_pos_walkable_with_hitbox(self, x, y, hw, hh):
        for dx, dy in [(0, 0), (-hw, -hh), (hw, -hh), (-hw, hh), (hw, hh)]:
            if not self.is_walkable(x + dx, y + dy):
                return False
        return True

    async def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.setblocking(False)
        self.running = True
        print(f"[SERVEUR] UDP en écoute sur {self.host}:{self.port}")
        self.loop = asyncio.get_running_loop()
        asyncio.create_task(self.broadcast_loop())
        asyncio.create_task(self.monster_ai_loop())
        if self.room_name:
            asyncio.create_task(self.lan_announcer())
        while self.running:
            try:
                data, addr = await self.loop.sock_recvfrom(self.sock, 8192)
                await self.handle_message(data, addr)
            except Exception as e:
                if self.running:
                    print(f"[SERVEUR] Erreur recv : {e}")
                await asyncio.sleep(0.01)

    async def handle_message(self, data, addr):
        try:
            msg = json.loads(data.decode())
        except Exception:
            return

        msg_type = msg.get("type")

        if msg_type == "join":
            if addr not in self.clients:
                if len(self.clients) >= self.max_clients:
                    return
                pid = str(self.next_player_id)
                self.next_player_id += 1
                self.clients[addr]       = pid
                self.player_states[pid]  = {
                    "pos": [self.start_data[0] * 2000 + 1000, self.start_data[1] * 2000 + 1000],
                    "dir": "down", "anim": 0,
                    "attacking": False, "moving": False,
                    "running": False, "health": 3,
                    "niveau": 1, "xp": 0,
                    "last_seen": time.time()
                }
                print(f"[SERVEUR] Joueur {pid} connecté depuis {addr}")
            pid     = self.clients[addr]
            welcome = {"type": "welcome", "id": pid, "map": self.map_data, "start": self.start_data}
            await self.send_to(welcome, addr)

        elif msg_type == "update":
            pid = self.clients.get(addr)
            if pid:
                state = msg.get("state", {})
                self.player_states[pid].update(state)
                self.player_states[pid]["last_seen"] = time.time()

        elif msg_type == "attack":
            pid = self.clients.get(addr)
            if pid:
                self.player_states[pid]["attacking"] = True

        elif msg_type == "hit_monster":
            mid = str(msg.get("monster_id"))
            dmg = msg.get("damage", 10)
            if mid in self.monster_states:
                if self.monster_states[mid].get("state") == "SPAWN":
                    return
                mstate = self.monster_states[mid]
                if not mstate["alive"]:
                    return
                mstate["health"] -= dmg

                pid = self.clients.get(addr)
                if pid and pid in self.player_states:
                    ppos = self.player_states[pid]["pos"]
                    mpos = mstate["pos"]
                    dx   = mpos[0] - ppos[0]
                    dy   = mpos[1] - ppos[1]
                    dist = (dx**2 + dy**2)**0.5
                    if dist > 0:
                        mstate["kb_vx"] = (dx / dist) * 15
                        mstate["kb_vy"] = (dy / dist) * 15

                print(f"[SERVEUR] Monstre {mid} — {dmg} dégats, pv : {mstate['health']}")

                if mstate["health"] <= 0:
                    mstate["alive"] = False
                    print(f"[SERVEUR] Monstre {mid} mort")

                    if mstate.get("type") == "boss":
                        self.boss_active   = False
                        self.boss_defeated = True
                        print("[SERVEUR] Boss vaincu ! Envoi boss_defeated à tous.")
                        for caddr in list(self.clients.keys()):
                            await self.send_to({"type": "boss_defeated"}, caddr)

                    # XP envoyé seulement au joueur qui a tué
                    if pid:
                        xp_gain = mstate.get("xp_reward", 20)
                        for caddr, cid in self.clients.items():
                            if cid == pid:
                                await self.send_to({"type": "xp_gain", "amount": xp_gain}, caddr)

                    # Drop de potion aleatoire selon la luck
                    luck   = mstate.get("luck", 1.0)
                    chance = 0.22 * luck
                    if random.random() < chance:
                        drop_id = str(self.next_drop_id)
                        self.next_drop_id += 1
                        self.potion_drops[drop_id] = {
                            "x": mstate["pos"][0], "y": mstate["pos"][1],
                            "soin": 1, "alive": True
                        }

        elif msg_type == "open_chest":
            cid = str(msg.get("coffre_id"))
            pid = self.clients.get(addr)
            if cid in self.coffre_states and pid:
                coffre = self.coffre_states[cid]
                if coffre["etat"] == "ferme":
                    coffre["etat"] = "ouvert"
                    recompense = coffre.get("recompense", {"type": "potion", "quantite": 1})
                    await self.send_to({"type": "chest_reward", "recompense": recompense}, addr)

        elif msg_type == "pickup_potion":
            drop_id = str(msg.get("drop_id"))
            if drop_id in self.potion_drops and self.potion_drops[drop_id]["alive"]:
                self.potion_drops[drop_id]["alive"] = False
                soin = self.potion_drops[drop_id]["soin"]
                await self.send_to({"type": "chest_reward",
                                    "recompense": {"type": "potion", "quantite": soin}}, addr)

        elif msg_type == "leave":
            pid = self.clients.pop(addr, None)
            if pid:
                self.player_states.pop(pid, None)
                print(f"[SERVEUR] Joueur {pid} déconnecté")

    async def broadcast_loop(self):
        while self.running:
            now       = time.time()
            to_remove = []
            for addr, pid in list(self.clients.items()):
                if now - self.player_states[pid]["last_seen"] > 5.0:
                    to_remove.append(addr)
            for addr in to_remove:
                pid = self.clients.pop(addr)
                self.player_states.pop(pid)
                print(f"[SERVEUR] Joueur {pid} timeout")

            if self.clients:
                sync_monsters = {}
                for mid, mstate in self.monster_states.items():
                    sync_monsters[mid] = {
                        "pos":      mstate["pos"],
                        "health":   mstate["health"],
                        "alive":    mstate["alive"],
                        "type":     mstate.get("type", "shadow"),
                        "dir":      mstate.get("dir", "down"),
                        "moving":   mstate.get("moving", False),
                        "attacking":mstate.get("attacking", 0),
                        "state":    mstate.get("state", "WALK")
                    }

                sync_drops = {
                    k: {"x": v["x"], "y": v["y"], "soin": v["soin"]}
                    for k, v in self.potion_drops.items() if v["alive"]
                }

                sync_coffres = {
                    k: {"x": v["x"], "y": v["y"], "etat": v["etat"]}
                    for k, v in self.coffre_states.items()
                }

                sync_msg = {
                    "type":         "sync",
                    "players":      self.player_states,
                    "monsters":     sync_monsters,
                    "projectiles":  [{"x": p["x"], "y": p["y"]} for p in self.projectiles],
                    "boss_active":  self.boss_active,
                    "boss_room":    self.boss_room,
                    "drops_potion": sync_drops,
                    "coffres":      sync_coffres,
                }
                for addr in self.clients:
                    await self.send_to(sync_msg, addr)

            await asyncio.sleep(1 / 30)

    async def monster_ai_loop(self):
        while self.running:
            if not hasattr(self, "projectiles"): self.projectiles = []

            # Mise a jour des projectiles
            active_projs = []
            for p in self.projectiles:
                p["timer"] -= 50
                if p["timer"] > 0:
                    p["x"] += p["vx"]
                    p["y"] += p["vy"]
                    hit_pid = None
                    for pid, pstate in self.player_states.items():
                        if pstate.get("health", 1) <= 0: continue
                        dist = ((pstate["pos"][0] - p["x"])**2 + (pstate["pos"][1] - p["y"])**2)**0.5
                        if dist < 40:
                            hit_pid = pid
                            break
                    if hit_pid:
                        for addr, cid in self.clients.items():
                            if cid == hit_pid:
                                asyncio.create_task(self.send_to(
                                    {"type": "hit_player", "damage": p["damage"],
                                     "monster_x": p["x"], "monster_y": p["y"]}, addr))
                    elif self.is_walkable(p["x"], p["y"]):
                        active_projs.append(p)
            self.projectiles = active_projs

            # Activation du boss quand un joueur entre dans sa salle
            if self.boss_room and not self.boss_spawned:
                bgx, bgy = self.boss_room
                for pid, pstate in self.player_states.items():
                    if pstate.get("health", 1) <= 0: continue
                    p_gx = int(pstate["pos"][0] // 2000)
                    p_gy = int(pstate["pos"][1] // 2000)
                    if p_gx == bgx and p_gy == bgy:
                        self.boss_active  = True
                        self.boss_spawned = True
                        spawn_x = bgx * 2000 + 1000
                        spawn_y = bgy * 2000 + 1000
                        self.monster_states["boss_1"] = {
                            "pos": [spawn_x, spawn_y],
                            "health": 1, "max_health": 150,
                            "alive": True, "type": "boss",
                            "speed": 3.0, "state": "SPAWN",
                            "cooldown_timer": 800, "action_timer": 10000,
                            "action_queue": [], "in_giga_combo": False,
                            "force_attack_next": False, "last_action": None,
                            "move_dir": [0, 0], "attack_cooldown": 0, "attacking": 0,
                            "hitbox_hw": 60, "hitbox_hh": 60,
                            "xp_reward": 500, "luck": 3.0
                        }
                        print("[SERVEUR] Boss activé ! Portes verrouillées.")
                        break

            for mid, mstate in self.monster_states.items():
                if not mstate["alive"]: continue

                hw = mstate.get("hitbox_hw", 30)
                hh = mstate.get("hitbox_hh", 30)

                kb_vx = mstate.get("kb_vx", 0)
                kb_vy = mstate.get("kb_vy", 0)
                is_knocked_back = abs(kb_vx) > 1 or abs(kb_vy) > 1

                if is_knocked_back:
                    new_x = mstate["pos"][0] + kb_vx
                    new_y = mstate["pos"][1] + kb_vy
                    if self.is_pos_walkable_with_hitbox(new_x, new_y, hw, hh):
                        mstate["pos"][0] = new_x
                        mstate["pos"][1] = new_y
                    else:
                        if self.is_pos_walkable_with_hitbox(new_x, mstate["pos"][1], hw, hh): mstate["pos"][0] = new_x
                        if self.is_pos_walkable_with_hitbox(mstate["pos"][0], new_y, hw, hh): mstate["pos"][1] = new_y
                    mstate["kb_vx"] = kb_vx * 0.8
                    mstate["kb_vy"] = kb_vy * 0.8

                if mstate.get("attack_cooldown", 0) > 0:
                    mstate["attack_cooldown"] -= 1

                if mstate.get("attacking", 0) > 0:
                    mstate["attacking"] -= 1
                    if mstate["attacking"] == 1:
                        for pid, pstate in self.player_states.items():
                            if pstate.get("health", 1) <= 0: continue
                            dist_hit = ((pstate["pos"][0] - mstate["pos"][0])**2 + (pstate["pos"][1] - mstate["pos"][1])**2)**0.5
                            atk_range = mstate.get("attack_range", 80)
                            if dist_hit < atk_range + 20:
                                for addr, cid in self.clients.items():
                                    if cid == pid:
                                        await self.send_to(
                                            {"type": "hit_player", "damage": 1,
                                             "monster_x": mstate["pos"][0], "monster_y": mstate["pos"][1]}, addr)

                if not self.player_states: continue

                # IA du boss gérée séparément dans boss.py
                if mstate.get("type") == "boss":
                    from boss import server_update_boss
                    boss_walkable_fn = lambda x, y: self.is_pos_walkable_with_hitbox(x, y, hw, hh)
                    hits, new_projs  = server_update_boss(mstate, self.player_states, boss_walkable_fn, 50)
                    if new_projs:
                        self.projectiles.extend(new_projs)
                    for hit in hits:
                        for addr, cid in self.clients.items():
                            if cid == hit["pid"]:
                                await self.send_to(
                                    {"type": "hit_player", "damage": hit["damage"],
                                     "monster_x": hit["x"], "monster_y": hit["y"]}, addr)
                    continue

                m_grid_x = int(mstate["pos"][0] // 2000)
                m_grid_y = int(mstate["pos"][1] // 2000)

                target_pid = None
                min_dist   = float('inf')
                for pid, pstate in self.player_states.items():
                    if pstate.get("health", 1) <= 0: continue
                    p_grid_x = int(pstate["pos"][0] // 2000)
                    p_grid_y = int(pstate["pos"][1] // 2000)
                    if m_grid_x != p_grid_x or m_grid_y != p_grid_y: continue
                    dist_sq = (pstate["pos"][0] - mstate["pos"][0])**2 + (pstate["pos"][1] - mstate["pos"][1])**2
                    if dist_sq < min_dist:
                        min_dist   = dist_sq
                        target_pid = pid

                if target_pid and not is_knocked_back:
                    tpos = self.player_states[target_pid]["pos"]
                    dx   = tpos[0] - mstate["pos"][0]
                    dy   = tpos[1] - mstate["pos"][1]
                    dist = (dx**2 + dy**2)**0.5
                    if dist > mstate.get("detection_range", 500):
                        target_pid = None

                if target_pid is None and not is_knocked_back:
                    if mstate.get("patrol_timer", 0) <= 0:
                        mstate["patrol_dir"]   = random.choice(["up", "down", "left", "right"])
                        mstate["patrol_timer"] = 40
                    else:
                        mstate["patrol_timer"] -= 1

                    speed = mstate.get("speed", 3)
                    p_dir = mstate.get("patrol_dir", "down")
                    vx, vy = 0, 0
                    if p_dir == "up":    vy = -speed
                    elif p_dir == "down": vy =  speed
                    elif p_dir == "left": vx = -speed
                    elif p_dir == "right":vx =  speed

                    new_x = mstate["pos"][0] + vx
                    new_y = mstate["pos"][1] + vy
                    if self.is_pos_walkable_with_hitbox(new_x, new_y, hw, hh):
                        mstate["pos"][0] = new_x
                        mstate["pos"][1] = new_y
                        mstate["moving"] = True
                    else:
                        mstate["moving"] = False
                        if self.is_pos_walkable_with_hitbox(new_x, mstate["pos"][1], hw, hh):
                            mstate["pos"][0] = new_x
                            mstate["moving"] = True
                        elif self.is_pos_walkable_with_hitbox(mstate["pos"][0], new_y, hw, hh):
                            mstate["pos"][1] = new_y
                            mstate["moving"] = True
                    mstate["dir"] = p_dir

                elif target_pid and not is_knocked_back:
                    tpos = self.player_states[target_pid]["pos"]
                    dx   = tpos[0] - mstate["pos"][0]
                    dy   = tpos[1] - mstate["pos"][1]
                    dist = (dx**2 + dy**2)**0.5
                    atk_range = mstate.get("attack_range", 80)
                    if dist <= atk_range:
                        if mstate.get("attack_cooldown", 0) <= 0:
                            mstate["attack_cooldown"] = mstate.get("attack_cooldown_max", 40)
                            mstate["attacking"]       = 10
                    else:
                        speed = mstate.get("speed", 3)
                        vx    = (dx / dist) * speed
                        vy    = (dy / dist) * speed
                        new_x = mstate["pos"][0] + vx
                        new_y = mstate["pos"][1] + vy
                        if self.is_pos_walkable_with_hitbox(new_x, new_y, hw, hh):
                            mstate["pos"][0] = new_x
                            mstate["pos"][1] = new_y
                            mstate["moving"] = True
                        else:
                            mstate["moving"] = False
                            if self.is_pos_walkable_with_hitbox(new_x, mstate["pos"][1], hw, hh):
                                mstate["pos"][0] = new_x
                                mstate["moving"] = True
                            elif self.is_pos_walkable_with_hitbox(mstate["pos"][0], new_y, hw, hh):
                                mstate["pos"][1] = new_y
                                mstate["moving"] = True
                        if abs(dx) > abs(dy):
                            mstate["dir"] = "right" if dx > 0 else "left"
                        else:
                            mstate["dir"] = "down" if dy > 0 else "up"

            await asyncio.sleep(1 / 20)

    async def send_to(self, msg, addr):
        try:
            data = json.dumps(msg).encode()
            await self.loop.sock_sendto(self.sock, data, addr)
        except Exception:
            pass

    async def lan_announcer(self):
        broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_sock.setblocking(False)
        msg = f"MYST_SERVER:{self.room_name}:{self.port}".encode()
        print(f"[SERVEUR] Annonce LAN pour la salle : {self.room_name}")

        def get_broadcast_ips():
            ips = ["<broadcast>", "255.255.255.255"]
            try:
                host_name = socket.gethostname()
                _, _, ip_list = socket.gethostbyname_ex(host_name)
                for ip in ip_list:
                    parts = ip.split('.')
                    if len(parts) == 4 and ip != "127.0.0.1":
                        ips.append(f"{parts[0]}.{parts[1]}.{parts[2]}.255")
            except: pass
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                parts = ip.split('.')
                if len(parts) == 4:
                    ips.append(f"{parts[0]}.{parts[1]}.{parts[2]}.255")
                s.close()
            except: pass
            return list(set(ips))

        bcast_ips = get_broadcast_ips()
        print(f"[SERVEUR] Broadcast sur : {bcast_ips}")
        while self.running:
            for bip in bcast_ips:
                try:
                    broadcast_sock.sendto(msg, (bip, 8002))
                except: pass
            await asyncio.sleep(2.0)
        broadcast_sock.close()

    async def broadcast_restart(self):
        self.restarting = True
        print("[SERVEUR] Redémarrage en cours...")
        for addr in self.clients:
            await self.send_to({"type": "restart"}, addr)
        await asyncio.sleep(0.1)

    async def stop(self):
        if self.restarting:
            print("[SERVEUR] Arrêt pour redémarrage.")
            self.running = False
            return
        print("[SERVEUR] Arrêt du serveur...")
        for addr in self.clients:
            await self.send_to({"type": "shutdown"}, addr)
        await asyncio.sleep(0.1)
        self.running = False


def run_server():
    server = ServerNetwork()
    asyncio.run(server.start())


if __name__ == "__main__":
    run_server()
