import socket
import asyncio
import json
import time
import threading
from procedural_gen import procedural_gen

class ServerNetwork:
    def __init__(self, host="0.0.0.0", port=8001):
        self.host = host
        self.port = port
        self.clients = {}  # addr -> player_id
        self.player_states = {} # player_id -> state
        self.monster_states = {} # monster_id -> state
        self.next_player_id = 1
        self.running = False
        
        print("[SERVER] Generating global map...")
        self.map_data, self.start_data = procedural_gen()
        print(f"[SERVER] Map generated at start {self.start_data}")
        
        # Initialize some monsters based on the map
        self.init_monsters()

    def init_monsters(self):
        # Place one monster in the spawn room for testing
        spawn_x = self.start_data[0] * 2000 + 1500
        spawn_y = self.start_data[1] * 2000 + 1000
        self.monster_states["1"] = {
            "pos": [spawn_x, spawn_y],
            "health": 80,
            "alive": True,
            "type": "basic"
        }

    async def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.setblocking(False)
        self.running = True
        print(f"[SERVER] UDP Server listening on {self.host}:{self.port}")

        self.loop = asyncio.get_running_loop()
        
        # Start background tasks
        asyncio.create_task(self.broadcast_loop())
        asyncio.create_task(self.monster_ai_loop())
        
        while self.running:
            try:
                data, addr = await self.loop.sock_recvfrom(self.sock, 8192)
                await self.handle_message(data, addr)
            except Exception as e:
                if self.running:
                    print(f"[SERVER] Recv Error: {e}")
                await asyncio.sleep(0.01)

    async def handle_message(self, data, addr):
        try:
            msg = json.loads(data.decode())
        except Exception as e:
            # print(f"[SERVER] Decode Error: {e}")
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
                sync_msg = {
                    "type": "sync",
                    "players": self.player_states,
                    "monsters": self.monster_states
                }
                for addr in self.clients:
                    await self.send_to(sync_msg, addr)
            
            await asyncio.sleep(1/30) # 30 FPS updates

    async def monster_ai_loop(self):
        while self.running:
            # Very simple AI for now: move towards nearest player
            for mid, mstate in self.monster_states.items():
                if not mstate["alive"]: continue
                
                if not self.player_states: continue
                
                # Find nearest player
                target_pid = None
                min_dist = float('inf')
                for pid, pstate in self.player_states.items():
                    dist_sq = (pstate["pos"][0] - mstate["pos"][0])**2 + (pstate["pos"][1] - mstate["pos"][1])**2
                    if dist_sq < min_dist:
                        min_dist = dist_sq
                        target_pid = pid
                
                if target_pid:
                    tpos = self.player_states[target_pid]["pos"]
                    dx = tpos[0] - mstate["pos"][0]
                    dy = tpos[1] - mstate["pos"][1]
                    dist = (dx**2 + dy**2)**0.5
                    
                    if 50 < dist < 1000: # Only move if player is somewhat close but not on top
                        speed = 3
                        mstate["pos"][0] += (dx/dist) * speed
                        mstate["pos"][1] += (dy/dist) * speed
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

    async def stop(self):
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
