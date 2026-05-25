import socket
import asyncio
import threading
import json
import time

class ClientData:
    def __init__(self):
        self.lock = threading.Lock()
        self.player_id = None
        self.map_data = None
        self.start_data = None
        self.players = {} # Other players: { "id": { "pos": [x,y], "dir": "down", ... } }
        self.monsters = {} # Monsters: { "id": { "pos": [x,y], "alive": True, ... } }
        self.pending_hits = [] # List of hits on the local player
        self.local_player_state = {
            "pos": [0, 0],
            "dir": "down",
            "attacking": False,
            "moving": False,
            "running": False,
            "health": 3
        }

    def update_local_state(self, pos, direction, attacking, moving, running, health):
        with self.lock:
            self.local_player_state.update({
                "pos": list(pos),
                "dir": direction,
                "attacking": attacking,
                "moving": moving,
                "running": running,
                "health": health
            })

    def get_game_state(self):
        with self.lock:
            return {
                "player_id": self.player_id,
                "map_data": self.map_data,
                "start_data": self.start_data,
                "players": self.players.copy(),
                "monsters": self.monsters.copy()
            }

class ClientNetwork:
    def __init__(self, server_ip="127.0.0.1", server_port=8001):
        self.server_addr = (server_ip, server_port)
        self.data = ClientData()
        self.running = False
        self.loop = None

    @staticmethod
    def discover_room(room_name, timeout=5.0):
        """Listens for LAN broadcasts and returns (ip, port) if room is found."""
        print(f"[CLIENT] Searching for room: {room_name}...")
        discovery_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discovery_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        discovery_sock.bind(("", 8002))
        discovery_sock.settimeout(1.0)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                data, addr = discovery_sock.recvfrom(1024)
                msg = data.decode()
                if msg.startswith("MYST_SERVER:"):
                    parts = msg.split(":")
                    if len(parts) == 3 and parts[1] == room_name:
                        port = int(parts[2])
                        print(f"[CLIENT] Room found at {addr[0]}:{port}")
                        discovery_sock.close()
                        return addr[0], port
            except socket.timeout:
                continue
            except Exception:
                break
        
        discovery_sock.close()
        return None, None

    async def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.running = True
        self.loop = asyncio.get_running_loop()
        
        print(f"[CLIENT] Connecting to {self.server_addr}...")
        
        # Start loops
        asyncio.create_task(self.listener())
        asyncio.create_task(self.sender())
        
        # Initial join request (send periodically until we get welcome)
        while self.running and self.data.player_id is None:
            await self.send_to({"type": "join"})
            await asyncio.sleep(1.0)
        
        while self.running:
            await asyncio.sleep(0.1)

    async def listener(self):
        while self.running:
            try:
                raw_data, _ = await self.loop.sock_recvfrom(self.sock, 8192)
                msg = json.loads(raw_data.decode())
                await self.handle_message(msg)
            except Exception:
                await asyncio.sleep(0.01)

    async def handle_message(self, msg):
        mtype = msg.get("type")
        if mtype == "welcome":
            with self.data.lock:
                self.data.player_id = msg["id"]
                self.data.map_data = msg["map"]
                self.data.start_data = msg["start"]
            print(f"[CLIENT] Joined as player {self.data.player_id}")
            
        elif mtype == "sync":
            with self.data.lock:
                # Update all players except ourselves
                all_players = msg.get("players", {})
                my_id = self.data.player_id
                self.data.players = {k: v for k, v in all_players.items() if k != my_id}
                self.data.monsters = msg.get("monsters", {})
        elif mtype == "hit_player":
            with self.data.lock:
                self.data.pending_hits.append(msg)
        elif mtype == "shutdown":
            print("[CLIENT] Server is shutting down. Disconnecting...")
            self.running = False

    async def sender(self):
        while self.running:
            if self.data.player_id:
                with self.data.lock:
                    state = self.data.local_player_state.copy()
                await self.send_to({"type": "update", "state": state})
            await asyncio.sleep(1/60) # Send updates at 60Hz

    async def send_to(self, msg):
        try:
            data = json.dumps(msg).encode()
            await self.loop.sock_sendto(self.sock, data, self.server_addr)
        except Exception as e:
            # print(f"[CLIENT] Send error: {e}")
            pass
            
    def hit_monster(self, monster_id, damage):
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.send_to({"type": "hit_monster", "monster_id": str(monster_id), "damage": damage}),
                self.loop
            )

    def leave(self):
        if self.loop and self.loop.is_running():
            # We use a Future to wait briefly for the send to complete
            fut = asyncio.run_coroutine_threadsafe(
                self.send_to({"type": "leave"}),
                self.loop
            )
            try:
                fut.result(timeout=0.5)
            except:
                pass

def run_client_network(network):
    asyncio.run(network.start())

if __name__ == "__main__":
    # Test script
    client = ClientNetwork()
    run_client_network(client)
