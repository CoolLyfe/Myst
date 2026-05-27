import socket
import asyncio
import threading
import json
import time


class ClientData:
    def __init__(self):
        self.lock              = threading.Lock()
        self.player_id         = None
        self.map_data          = None
        self.start_data        = None
        self.players           = {}
        self.monsters          = {}
        self.pending_hits      = []
        self.pending_rewards   = []  # xp_gain et chest_reward arrivent ici
        self.projectiles       = []
        self.boss_active       = False
        self.boss_room         = None
        self.boss_defeated     = False
        self.server_restarting = False
        self.coffres           = {}
        self.drops_potion      = {}
        self.local_player_state = {
            "pos": [0, 0], "dir": "down",
            "attacking": False, "moving": False,
            "running": False, "health": 3,
            "niveau": 1, "xp": 0
        }

    def update_local_state(self, pos, direction, attacking, moving, running, health, niveau=1, xp=0):
        with self.lock:
            self.local_player_state.update({
                "pos": list(pos), "dir": direction,
                "attacking": attacking, "moving": moving,
                "running": running, "health": health,
                "niveau": niveau, "xp": xp
            })

    def get_game_state(self):
        with self.lock:
            return {
                "player_id":    self.player_id,
                "map_data":     self.map_data,
                "start_data":   self.start_data,
                "players":      self.players.copy(),
                "monsters":     self.monsters.copy(),
                "projectiles":  list(self.projectiles),
                "boss_active":  self.boss_active,
                "boss_room":    self.boss_room,
                "boss_defeated":self.boss_defeated,
                "coffres":      self.coffres.copy(),
                "drops_potion": dict(self.drops_potion),
            }


class ClientNetwork:
    def __init__(self, server_ip="127.0.0.1", server_port=8001):
        self.server_addr = (server_ip, server_port)
        self.data        = ClientData()
        self.running     = False
        self.loop        = None

    @staticmethod
    def discover_room(room_name, timeout=5.0):
        print(f"[CLIENT] Recherche de la salle : {room_name}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", 8002))
        sock.settimeout(1.0)
        debut = time.time()
        while time.time() - debut < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode()
                if msg.startswith("MYST_SERVER:"):
                    parts = msg.split(":")
                    if len(parts) == 3 and parts[1] == room_name:
                        port = int(parts[2])
                        print(f"[CLIENT] Salle trouvée : {addr[0]}:{port}")
                        sock.close()
                        return addr[0], port
            except socket.timeout:
                continue
            except Exception:
                break
        sock.close()
        return None, None

    async def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.running = True
        self.loop    = asyncio.get_running_loop()
        print(f"[CLIENT] Connexion à {self.server_addr}...")
        asyncio.create_task(self.listener())
        asyncio.create_task(self.sender())
        while self.running and self.data.player_id is None:
            await self.send_to({"type": "join"})
            await asyncio.sleep(1.0)
        while self.running:
            await asyncio.sleep(0.1)

    async def listener(self):
        while self.running:
            try:
                raw_data, _ = await self.loop.sock_recvfrom(self.sock, 65535)
                msg = json.loads(raw_data.decode())
                await self.handle_message(msg)
            except Exception:
                await asyncio.sleep(0.01)

    async def handle_message(self, msg):
        mtype = msg.get("type")

        if mtype == "welcome":
            with self.data.lock:
                self.data.player_id  = msg["id"]
                self.data.map_data   = msg["map"]
                self.data.start_data = msg["start"]
            print(f"[CLIENT] Connecté en tant que joueur {self.data.player_id}")

        elif mtype == "sync":
            with self.data.lock:
                all_players = msg.get("players", {})
                my_id = self.data.player_id
                self.data.players      = {k: v for k, v in all_players.items() if k != my_id}
                self.data.monsters     = msg.get("monsters", {})
                self.data.projectiles  = msg.get("projectiles", [])
                self.data.boss_active  = msg.get("boss_active", False)
                self.data.boss_room    = msg.get("boss_room", None)
                self.data.coffres      = msg.get("coffres", {})
                dp = msg.get("drops_potion", {})
                self.data.drops_potion = dp if isinstance(dp, dict) else {}

        elif mtype == "hit_player":
            with self.data.lock:
                self.data.pending_hits.append(msg)

        elif mtype == "xp_gain":
            with self.data.lock:
                self.data.pending_rewards.append(msg)

        elif mtype == "chest_reward":
            with self.data.lock:
                self.data.pending_rewards.append(msg)

        elif mtype == "boss_defeated":
            with self.data.lock:
                self.data.boss_defeated = True

        elif mtype == "restart":
            print("[CLIENT] Le serveur relance une partie...")
            with self.data.lock:
                self.data.server_restarting = True
            self.running = False

        elif mtype == "shutdown":
            print("[CLIENT] Le serveur s'arrête.")
            self.running = False

    async def sender(self):
        while self.running:
            if self.data.player_id:
                with self.data.lock:
                    state = self.data.local_player_state.copy()
                await self.send_to({"type": "update", "state": state})
            await asyncio.sleep(1 / 60)

    async def send_to(self, msg):
        try:
            data = json.dumps(msg).encode()
            await self.loop.sock_sendto(self.sock, data, self.server_addr)
        except Exception:
            pass

    def hit_monster(self, monster_id, damage):
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.send_to({"type": "hit_monster", "monster_id": str(monster_id), "damage": damage}),
                self.loop
            )

    def ouvrir_coffre(self, coffre_id):
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.send_to({"type": "open_chest", "coffre_id": str(coffre_id)}),
                self.loop
            )

    def ramasser_potion(self, drop_id):
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.send_to({"type": "pickup_potion", "drop_id": str(drop_id)}),
                self.loop
            )

    def leave(self):
        if self.loop and self.loop.is_running():
            fut = asyncio.run_coroutine_threadsafe(self.send_to({"type": "leave"}), self.loop)
            try:
                fut.result(timeout=0.5)
            except:
                pass


def run_client_network(network):
    asyncio.run(network.start())


if __name__ == "__main__":
    client = ClientNetwork()
    run_client_network(client)
