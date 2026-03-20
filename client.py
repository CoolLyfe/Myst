import socket
import asyncio
import threading
import time

class Data:
    def __init__(self):
        self.lock = threading.Lock()
        self.local_input = {}
        self.game_state = {}
        self.remote_input = {}

    def get_local_input(self):
        with self.lock:
            return self.local_input.copy()
        
    def set_local_input(self, input):
        with self.lock:
            self.local_input = input

class Network:
    def __init__(self):
        self.addr = ("127.0.0.1", 8001)
        pass
    
    async def _listener(self):
        while self.running:
            try:
                raw_data, addr = await asyncio.wait_for(self.loop.sock_recvfrom(self.socket, 1024), timeout=1.0)
                data = raw_data.decode()
                print(f"Received {data} from {addr}")
                                
                
            except asyncio.TimeoutError:
                    continue
                
            except ConnectionError:
                # Client disconnected
                continue
        return

    async def _sender(self, addr: tuple[str, int], data: str):
        await self.loop.sock_sendto(self.socket, data.encode(), addr)


    async def updater(self):
        asyncio.create_task(self._listener())

        while self.running:
            now = time.time()
            asyncio.create_task(self._sender(self.addr, "Pong"))
            await asyncio.sleep(max(0, time.time() - now + 1/30))
        return

    async def start_server(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # IPv4, UDP
        self.socket.bind(("127.0.0.1", 8000))
        self.socket.setblocking(False)
        self.running = True

        self.loop = asyncio.get_running_loop()
        await self.updater()



    def run(self):
        asyncio.run(self.start_server())
        if self.socket:
            self.socket.close()


network = Network()
thread = threading.Thread(target=network.run, daemon=True)
thread.start()

thread.join()

