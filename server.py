import socket
import asyncio
import json
import time
import threading
from procedural_gen import procedural_gen

class ServerNetwork:
    def __init__(self, host="0.0.0.0", port=8001, max_clients=999, room_name=None):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.room_name = room_name
        self.clients = {}  # addr -> player_id
        self.player_states = {} # player_id -> state
        self.monster_states = {} # monster_id -> state
        self.next_player_id = 1
        self.running = False
        self.restarting = False

        print("[SERVER] Generating global map...")
        self.map_data, self.start_data = procedural_gen()
        print(f"[SERVER] Map generated at start {self.start_data}")

        # Initialize some monsters based on the map
        self.init_monsters()

    def init_monsters(self):
        import random
        monster_id_counter = 1

        # Loop through the map grid
        for grid_y in range(len(self.map_data)):
            for grid_x in range(len(self.map_data[grid_y])):
                room = self.map_data[grid_y][grid_x]
                room_type = room[0]

                # Spawn in classic (3) and fight (5) rooms
                if room_type in [3, 5]:
                    # Random number of monsters based on room type
                    if room_type == 3:
                        nb_monsters = random.randint(2, 4)
                    else: # type 5
                        nb_monsters = random.randint(3, 6)

                    for _ in range(nb_monsters):
                        mtype = random.choice(["basic", "shadow", "light", "tank"])
                        if mtype == "basic":
                            hp, speed, det_range, atk_range, cd_max = 80, 3, 500, 80, 40
                            hw, hh = 40, 45
                        elif mtype == "shadow":
                            hp, speed, det_range, atk_range, cd_max = 150, 2, 400, 90, 30
                            hw, hh = 65, 75
                        elif mtype == "light":
                            hp, speed, det_range, atk_range, cd_max = 50, 5, 700, 70, 14
                            hw, hh = 50, 60
                        elif mtype == "tank":
                            hp, speed, det_range, atk_range, cd_max = 400, 1, 350, 120, 50
                            hw, hh = 80, 80
                        
                        # Find a valid spawn position inside the room
                        cell_size = 2000
                        gap = 400
                        wall_thick = 120
                        # Margin includes wall thickness + monster hitbox + safety buffer
                        margin_x = wall_thick + hw + 20
                        margin_y = wall_thick + hh + 20
                        
                        room_left = grid_x * cell_size + gap // 2 + margin_x
                        room_right = (grid_x + 1) * cell_size - gap // 2 - margin_x
                        room_top = grid_y * cell_size + gap // 2 + margin_y
                        room_bottom = (grid_y + 1) * cell_size - gap // 2 - margin_y
                        
                        spawn_x = random.uniform(room_left, room_right)
                        spawn_y = random.uniform(room_top, room_bottom)
                        
                        # Verify position is actually walkable with hitbox
                        attempts = 0
                        while not self.is_pos_walkable_with_hitbox(spawn_x, spawn_y, hw, hh) and attempts < 10:
                            spawn_x = random.uniform(room_left, room_right)
                            spawn_y = random.uniform(room_top, room_bottom)
                            attempts += 1
                        
                        self.monster_states[str(monster_id_counter)] = {
                            "pos": [spawn_x, spawn_y],
                            "health": hp,
                            "alive": True,
                            "type": mtype,
                            "speed": speed,
                            "detection_range": det_range,
                            "attack_range": atk_range,
                            "attack_cooldown_max": cd_max,
                            "attack_cooldown": 0,
                            "attacking": 0,
                            "patrol_timer": 0,
                            "patrol_dir": "down",
                            "hitbox_hw": hw,
                            "hitbox_hh": hh
                        }
                        monster_id_counter += 1

    def is_walkable(self, x, y):
        # Determine which cell we are in
        grid_x = int(x // 2000)
        grid_y = int(y // 2000)

        if not (0 <= grid_x < 8 and 0 <= grid_y < 5):
            return False

        room = self.map_data[grid_y][grid_x]
        if room[0] == 0:
            return False

        # Check if inside room (with gap and wall thickness)
        cell_size = 2000
        gap = 400
        wall_thick = 120
        room_left = grid_x * cell_size + gap // 2 + wall_thick
        room_right = (grid_x + 1) * cell_size - gap // 2 - wall_thick
        room_top = grid_y * cell_size + gap // 2 + wall_thick
        room_bottom = (grid_y + 1) * cell_size - gap // 2 - wall_thick

        if room_left <= x <= room_right and room_top <= y <= room_bottom:
            return True

        # Check if inside corridors
        thickness = cell_size // 12
        half_thick = thickness // 2
        center_x = grid_x * cell_size + cell_size // 2
        center_y = grid_y * cell_size + cell_size // 2

        for conn in room[1]:
            if conn == "N" and y < center_y:
                if center_x - half_thick <= x <= center_x + half_thick:
                    return True
            elif conn == "S" and y > center_y:
                if center_x - half_thick <= x <= center_x + half_thick:
                    return True
            elif conn == "E" and x > center_x:
                if center_y - half_thick <= y <= center_y + half_thick:
                    return True
            elif conn == "O" and x < center_x:
                if center_y - half_thick <= y <= center_y + half_thick:
                    return True

        return False

    def is_pos_walkable_with_hitbox(self, x, y, hw, hh):
        # Check 5 points around the position to account for the entity's hitbox
        for dx, dy in [(0, 0), (-hw, -hh), (hw, -hh), (-hw, hh), (hw, hh)]:
            if not self.is_walkable(x + dx, y + dy):
                return False
        return True

    async def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Allow immediate reuse of the port after a crash or restart
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.setblocking(False)
        self.running = True
        print(f"[SERVER] UDP Server listening on {self.host}:{self.port}")

        self.loop = asyncio.get_running_loop()

        # Start background tasks
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
                    print(f"[SERVER] Recv Error: {e}")
                await asyncio.sleep(0.01)

    async def handle_message(self, data, addr):
        # Debug: track all incoming traffic
        # print(f"[SERVER] Data from {addr}: {data[:50]}...")
        try:
            msg = json.loads(data.decode())
        except Exception as e:
            # print(f"[SERVER] Decode Error from {addr}: {e}")
            return

        msg_type = msg.get("type")

        if msg_type == "join":
            if addr not in self.clients:
                if len(self.clients) >= self.max_clients:
                    # Ignore join request if full
                    return
                pid = str(self.next_player_id)
                self.next_player_id += 1
                self.clients[addr] = pid
                self.player_states[pid] = {
                    "pos": [self.start_data[0] * 2000 + 1000, self.start_data[1] * 2000 + 1000],
                    "dir": "down",
                    "anim": 0,
                    "attacking": False,
                    "moving": False,
                    "running": False,
                    "health": 3,
                    "last_seen": time.time()
                }
                print(f"[SERVER] Player {pid} joined from {addr}")

            pid = self.clients[addr]
            welcome = {
                "type": "welcome",
                "id": pid,
                "map": self.map_data,
                "start": self.start_data
            }
            await self.send_to(welcome, addr)

        elif msg_type == "update":
            pid = self.clients.get(addr)
            if pid:
                state = msg.get("state", {})
                self.player_states[pid].update(state)
                self.player_states[pid]["last_seen"] = time.time()

        elif msg_type == "attack":
            # Server could validate attack here
            # For now, we trust the client to tell us if they hit a monster
            # Or we can just relay the attack animation to others
            pid = self.clients.get(addr)
            if pid:
                self.player_states[pid]["attacking"] = True
                # In a real game, server would check hitboxes here

        elif msg_type == "hit_monster":
            mid = str(msg.get("monster_id"))
            dmg = msg.get("damage", 10)
            if mid in self.monster_states:
                self.monster_states[mid]["health"] -= dmg

                # Apply knockback
                pid = self.clients.get(addr)
                if pid and pid in self.player_states:
                    ppos = self.player_states[pid]["pos"]
                    mpos = self.monster_states[mid]["pos"]
                    dx = mpos[0] - ppos[0]
                    dy = mpos[1] - ppos[1]
                    dist = (dx**2 + dy**2)**0.5
                    if dist > 0:
                        kb_strength = 15
                        self.monster_states[mid]["kb_vx"] = (dx/dist) * kb_strength
                        self.monster_states[mid]["kb_vy"] = (dy/dist) * kb_strength

                print(f"[SERVER] Monster {mid} took {dmg} damage, health: {self.monster_states[mid]['health']}")
                if self.monster_states[mid]["health"] <= 0:
                    self.monster_states[mid]["alive"] = False
                    print(f"[SERVER] Monster {mid} died")

        elif msg_type == "leave":
            pid = self.clients.pop(addr, None)
            if pid:
                self.player_states.pop(pid, None)
                print(f"[SERVER] Player {pid} left gracefully")

    async def broadcast_loop(self):
        while self.running:
            now = time.time()
            # Handle timeouts
            to_remove = []
            for addr, pid in list(self.clients.items()):
                if now - self.player_states[pid]["last_seen"] > 5.0:
                    to_remove.append(addr)

            for addr in to_remove:
                pid = self.clients.pop(addr)
                self.player_states.pop(pid)
                print(f"[SERVER] Player {pid} timed out")

            if self.clients:
                # Optimize monster states for network transfer
                sync_monsters = {}
                for mid, mstate in self.monster_states.items():
                    # Only send essential fields to keep UDP packet size small
                    sync_monsters[mid] = {
                        "pos": mstate["pos"],
                        "health": mstate["health"],
                        "alive": mstate["alive"],
                        "type": mstate.get("type", "basic"),
                        "dir": mstate.get("dir", "down"),
                        "moving": mstate.get("moving", False),
                        "attacking": mstate.get("attacking", 0)
                    }

                sync_msg = {
                    "type": "sync",
                    "players": self.player_states,
                    "monsters": sync_monsters
                }
                for addr in self.clients:
                    await self.send_to(sync_msg, addr)

            await asyncio.sleep(1/30) # 30 FPS updates

    async def monster_ai_loop(self):
        import random
        while self.running:
            for mid, mstate in self.monster_states.items():
                if not mstate["alive"]: continue

                hw = mstate.get("hitbox_hw", 30)
                hh = mstate.get("hitbox_hh", 30)

                # Apply smooth knockback if any
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

                # Decrement attack cooldown
                if mstate.get("attack_cooldown", 0) > 0:
                    mstate["attack_cooldown"] -= 1

                # Decrement attacking timer
                if mstate.get("attacking", 0) > 0:
                    mstate["attacking"] -= 1
                    # Apply damage on the last frame of the attack animation (wind-up completion)
                    if mstate["attacking"] == 1:
                        for pid, pstate in self.player_states.items():
                            if pstate.get("health", 1) <= 0: continue
                            dist_hit = ((pstate["pos"][0] - mstate["pos"][0])**2 + (pstate["pos"][1] - mstate["pos"][1])**2)**0.5
                            atk_range = mstate.get("attack_range", 80)
                            if dist_hit < atk_range + 20: # Range for the actual strike with slight leniency
                                for addr, cid in self.clients.items():
                                    if cid == pid:
                                        await self.send_to({"type": "hit_player", "damage": 1, "monster_x": mstate["pos"][0], "monster_y": mstate["pos"][1]}, addr)

                if not self.player_states: continue

                m_grid_x = int(mstate["pos"][0] // 2000)
                m_grid_y = int(mstate["pos"][1] // 2000)

                # Find nearest player in the same room
                target_pid = None
                min_dist = float('inf')
                for pid, pstate in self.player_states.items():
                    if pstate.get("health", 1) <= 0:
                        continue

                    p_grid_x = int(pstate["pos"][0] // 2000)
                    p_grid_y = int(pstate["pos"][1] // 2000)

                    # Only aggro players in the exact same room cell
                    if m_grid_x != p_grid_x or m_grid_y != p_grid_y:
                        continue

                    dist_sq = (pstate["pos"][0] - mstate["pos"][0])**2 + (pstate["pos"][1] - mstate["pos"][1])**2
                    if dist_sq < min_dist:
                        min_dist = dist_sq
                        target_pid = pid

                if target_pid and not is_knocked_back:
                    tpos = self.player_states[target_pid]["pos"]
                    dx = tpos[0] - mstate["pos"][0]
                    dy = tpos[1] - mstate["pos"][1]
                    dist = (dx**2 + dy**2)**0.5

                    if dist > mstate.get("detection_range", 500):
                        target_pid = None # Too far, lose aggro

                if target_pid is None and not is_knocked_back:
                    # Patrol state
                    if mstate.get("patrol_timer", 0) <= 0:
                        mstate["patrol_dir"] = random.choice(["up", "down", "left", "right"])
                        mstate["patrol_timer"] = 40 # 2 seconds
                    else:
                        mstate["patrol_timer"] -= 1

                    speed = mstate.get("speed", 3)
                    p_dir = mstate.get("patrol_dir", "down")
                    vx, vy = 0, 0
                    if p_dir == "up": vy = -speed
                    elif p_dir == "down": vy = speed
                    elif p_dir == "left": vx = -speed
                    elif p_dir == "right": vx = speed

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
                    dx = tpos[0] - mstate["pos"][0]
                    dy = tpos[1] - mstate["pos"][1]
                    dist = (dx**2 + dy**2)**0.5

                    atk_range = mstate.get("attack_range", 80)
                    if dist <= atk_range: # Attack state
                        if mstate.get("attack_cooldown", 0) <= 0:
                            mstate["attack_cooldown"] = mstate.get("attack_cooldown_max", 40)
                            mstate["attacking"] = 10 # 0.5s animation duration
                    else: # Chase state
                        speed = mstate.get("speed", 3)
                        vx = (dx/dist) * speed
                        vy = (dy/dist) * speed

                        # Try moving in both axes
                        new_x = mstate["pos"][0] + vx
                        new_y = mstate["pos"][1] + vy

                        if self.is_pos_walkable_with_hitbox(new_x, new_y, hw, hh):
                            mstate["pos"][0] = new_x
                            mstate["pos"][1] = new_y
                            mstate["moving"] = True
                        else:
                            mstate["moving"] = False
                            # Try sliding along X
                            if self.is_pos_walkable_with_hitbox(new_x, mstate["pos"][1], hw, hh):
                                mstate["pos"][0] = new_x
                                mstate["moving"] = True
                            # Try sliding along Y
                            elif self.is_pos_walkable_with_hitbox(mstate["pos"][0], new_y, hw, hh):
                                mstate["pos"][1] = new_y
                                mstate["moving"] = True

                        # Update direction for animation
                        if abs(dx) > abs(dy):
                            mstate["dir"] = "right" if dx > 0 else "left"
                        else:
                            mstate["dir"] = "down" if dy > 0 else "up"

            await asyncio.sleep(1/20)

    async def send_to(self, msg, addr):
        try:
            data = json.dumps(msg).encode()
            await self.loop.sock_sendto(self.sock, data, addr)
        except Exception:
            pass

    async def lan_announcer(self):
        """Broadcasts the room name on the local network for discovery."""
        broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_sock.setblocking(False)

        msg = f"MYST_SERVER:{self.room_name}:{self.port}".encode()
        print(f"[SERVER] LAN Announcer started for room: {self.room_name}")

        def get_broadcast_ips():
            ips = ["<broadcast>", "255.255.255.255"]
            try:
                host_name = socket.gethostname()
                _, _, ip_list = socket.gethostbyname_ex(host_name)
                for ip in ip_list:
                    parts = ip.split('.')
                    if len(parts) == 4 and ip != "127.0.0.1":
                        ips.append(f"{parts[0]}.{parts[1]}.{parts[2]}.255")
            except Exception:
                pass
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                parts = ip.split('.')
                if len(parts) == 4:
                    ips.append(f"{parts[0]}.{parts[1]}.{parts[2]}.255")
                s.close()
            except Exception:
                pass
            return list(set(ips))

        bcast_ips = get_broadcast_ips()
        print(f"[SERVER] Announcing on IPs: {bcast_ips}")

        while self.running:
            for bip in bcast_ips:
                try:
                    # Send to the broadcast address of the local network
                    broadcast_sock.sendto(msg, (bip, 8002))
                except Exception:
                    pass
            await asyncio.sleep(2.0)
        broadcast_sock.close()

    async def broadcast_restart(self):
        self.restarting = True
        print("[SERVER] Broadcasting restart to clients...")
        msg = {"type": "restart"}
        for addr in self.clients:
            await self.send_to(msg, addr)
        await asyncio.sleep(0.1)

    async def stop(self):
        if self.restarting:
            print("[SERVER] Stopping server for restart (skipping shutdown broadcast)...")
            self.running = False
            return

        print("[SERVER] Shutting down...")
        shutdown_msg = {"type": "shutdown"}
        for addr in self.clients:
            await self.send_to(shutdown_msg, addr)
        await asyncio.sleep(0.1) # Give time for messages to be sent
        self.running = False

def run_server():
    server = ServerNetwork()
    asyncio.run(server.start())

if __name__ == "__main__":
    run_server()
