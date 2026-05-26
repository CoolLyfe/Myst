import pygame
import math
import random
import os
import re
from enum import Enum, auto
from entity import Entity

class BossState(Enum):
    WALK = auto()       # Déplacement continu (Phase neutre / Cooldown)
    DASH = auto()       # Attaque : Dash 8 directions
    SHOOT = auto()      # Attaque : Tir 4 directions
    REST = auto()       # Repos : Courte pause statique
    HEAL = auto()       # Soin : Régénération si HP < 50%
    TELEPORT = auto()   # Déplacement instantané près du joueur

# ==========================================
# CLASSE CLIENT (Rendu et Animations)
# ==========================================
class Boss(Entity):
    _sprite_cache = {}

    @classmethod
    def get_sprites(cls, sprite_size):
        if sprite_size in cls._sprite_cache:
            return cls._sprite_cache[sprite_size]

        cache = {}
        states = ["WALK", "DASH", "SHOOT", "REST", "HEAL", "TELEPORT"]
        
        for state in states:
            cache[state] = []
            
        # Mots-clés (en minuscules pour une recherche flexible)
        keywords = {
            "WALK": ["stand", "walk"],
            "DASH": ["dashd", "dash"],
            "SHOOT": ["shoot", "attack"],
            "REST": ["stand", "rest"],
            "HEAL": ["heal"],
            "TELEPORT": ["tp", "teleport"]
        }

        boss_dir = "assets/boss"
        if os.path.exists(boss_dir):
            # On liste tous les fichiers PNG du dossier
            files = [f for f in os.listdir(boss_dir) if f.lower().endswith(".png")]
            
            # Fonction pour extraire le numéro de la frame pour le tri (ex: boss_tp_4 -> 4)
            def get_frame_num(filename):
                nums = re.findall(r'\d+', filename)
                return int(nums[-1]) if nums else 0
                
            files.sort(key=get_frame_num)

            for state in states:
                kw_list = keywords[state]
                for f in files:
                    f_lower = f.lower()
                    # On cherche si l'un des mots-clés est dans le nom du fichier
                    if any(kw in f_lower for kw in kw_list):
                        try:
                            path = os.path.join(boss_dir, f)
                            img = pygame.image.load(path).convert_alpha()
                            cache[state].append(pygame.transform.scale(img, (sprite_size, sprite_size)))
                        except:
                            pass

        # Fallback si rien n'a été trouvé pour éviter un crash
        for state in states:
            if not cache[state]:
                surf = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
                if state == "WALK": surf.fill((100, 100, 100))
                elif state == "DASH": surf.fill((255, 100, 0))
                elif state == "SHOOT": surf.fill((255, 0, 0))
                elif state == "REST": surf.fill((50, 50, 200))
                elif state == "HEAL": surf.fill((0, 255, 0))
                elif state == "TELEPORT": surf.fill((200, 0, 255))
                cache[state].append(surf)

        cls._sprite_cache[sprite_size] = cache
        return cache

    def __init__(self, pos_x, pos_y, sprite_size=200):
        super().__init__(
            health=150, attack=1, speed=5, nb_potions=0,
            image_path="assets/base_monstre.png", 
            pos_x=pos_x, pos_y=pos_y, sprite_size=sprite_size
        )
        
        # --- VISUEL TEMPORAIRE ---
        self.image = pygame.Surface((sprite_size, sprite_size))
        self.image.fill((200, 20, 20))
        self.sprites = self.get_sprites(sprite_size)
        self.state = "WALK"
        self.image = self.sprites[self.state][0]
        
        # État pour d'éventuelles animations
        self.state = BossState.WALK
        # Variables d'animation
        self.anim_timer = 0
        self.anim_rate = 100 # Vitesse de l'animation en ms (10 fps)
        self.anim_index = 0

    def update_animation(self, dt_ms, is_moving, is_attacking):
        """Met à jour l'animation du boss pour le client (appelé par game.py)."""
        self.attacking = is_attacking
        # Ajoute ici la logique de défilement des sprites quand tu en auras.
        
        current_state = getattr(self, 'state', 'WALK')
        # Si l'état n'existe pas dans le cache, on retombe sur WALK
        if current_state not in self.sprites:
            current_state = "WALK"
            
        frames = self.sprites[current_state]
        if not frames:
            return
            
        self.anim_timer += dt_ms
        if self.anim_timer >= self.anim_rate:
            self.anim_timer -= self.anim_rate
            self.anim_index += 1
            if self.anim_index >= len(frames):
                self.anim_index = 0
                
        # Sécurité si on change d'état vers une animation avec moins de frames
        self.anim_index = min(self.anim_index, len(frames) - 1)
        self.image = frames[self.anim_index]
        
        self.update_hitbox()

# ==========================================
# IA SERVEUR (Logique et Multijoueur)
# ==========================================

def server_update_boss(mstate, player_states, is_walkable_fn, dt_ms):
    """
    Point d'entrée de l'IA du boss côté serveur.
    """
    hits = []
    new_projectiles = []
    
    target_pid, target_pos = _server_find_closest_player(mstate, player_states)
    b_state = mstate.get("state", "WALK")
    mstate["moving"] = False

    if b_state == "WALK":
        _server_boss_walk(mstate, target_pid, target_pos, is_walkable_fn, dt_ms, new_projectiles)
    elif b_state == "DASH":
        _server_boss_dash(mstate, player_states, is_walkable_fn, dt_ms, hits)
    elif b_state == "SHOOT":
        _server_boss_shoot(mstate, dt_ms)
    elif b_state == "REST":
        _server_boss_rest(mstate, dt_ms)
    elif b_state == "HEAL":
        _server_boss_heal(mstate, dt_ms)
    elif b_state == "TELEPORT":
        _server_boss_teleport(mstate, dt_ms)

    return hits, new_projectiles

# ------------------------------------------
# SOUS-FONCTIONS SERVEUR (Helpers)
# ------------------------------------------

def _server_find_closest_player(mstate, player_states):
    target_pid = None
    min_dist = float('inf')
    for pid, pstate in player_states.items():
        if pstate.get("health", 1) <= 0: continue
        dist_sq = (pstate["pos"][0] - mstate["pos"][0])**2 + (pstate["pos"][1] - mstate["pos"][1])**2
        if dist_sq < min_dist:
            min_dist = dist_sq
            target_pid = pid
    target_pos = player_states[target_pid]["pos"] if target_pid else mstate["pos"]
    return target_pid, target_pos

def _server_end_boss_action(mstate):
    mstate["state"] = "WALK"
    if mstate.get("force_attack_next") and not mstate.get("in_giga_combo"):
        mstate["cooldown_timer"] = 0
    else:
        mod = 0.15 if mstate.get("in_giga_combo") else 1.0
        mstate["cooldown_timer"] = 1000 * mod * random.uniform(0.8, 1.2)
    mstate["pause_timer"] = 200 if mstate.get("in_giga_combo") else 800

def _server_boss_walk(mstate, target_pid, target_pos, is_walkable_fn, dt_ms, new_projectiles):
    mstate.setdefault("pause_timer", 0)
    
    # 1. Gestion de la pause ou du déplacement
    if mstate["pause_timer"] > 0:
        mstate["pause_timer"] -= dt_ms
    elif target_pid:
        _server_move_towards_target(mstate, target_pos, is_walkable_fn)

    # 2. Gestion du cooldown pour la prochaine action
    if target_pid:
        mstate["cooldown_timer"] -= dt_ms
        if mstate["cooldown_timer"] <= 0:
            _server_boss_pick_next_action(mstate, target_pos, new_projectiles, is_walkable_fn)

def _server_move_towards_target(mstate, target_pos, is_walkable_fn):
    dx = target_pos[0] - mstate["pos"][0]
    dy = target_pos[1] - mstate["pos"][1]
    dist = (dx**2 + dy**2)**0.5
    if dist > 0:
        vx = (dx/dist) * mstate["speed"]
        vy = (dy/dist) * mstate["speed"]
        new_x = mstate["pos"][0] + vx
        new_y = mstate["pos"][1] + vy
        
        if is_walkable_fn(new_x, new_y):
            mstate["pos"][0], mstate["pos"][1] = new_x, new_y
            mstate["moving"] = True
        else:
            if is_walkable_fn(new_x, mstate["pos"][1]): mstate["pos"][0] = new_x
            if is_walkable_fn(mstate["pos"][0], new_y): mstate["pos"][1] = new_y
        
        if abs(dx) > abs(dy): 
            mstate["dir"] = "right" if dx > 0 else "left"
        else: 
            mstate["dir"] = "down" if dy > 0 else "up"

def _server_boss_pick_next_action(mstate, target_pos, new_projectiles, is_walkable_fn):
    if mstate.get("action_queue"):
        next_act = mstate["action_queue"].pop(0)
    else:
        mstate["in_giga_combo"] = False
        if mstate.get("force_attack_next"):
            mstate["force_attack_next"] = False
            next_act = random.choice(["DASH", "SHOOT"])
        else:
            weights = {"DASH": 30, "SHOOT": 20, "TELEPORT": 15, "REST": 5, "HEAL": 10, "GIGA_COMBO": 20}
            if mstate.get("health", 150) >= mstate.get("max_health", 150) * 0.5: 
                weights["HEAL"] = 0
            if mstate.get("last_action") in weights: 
                weights[mstate["last_action"]] *= 2.0
            
            chosen = random.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]
            
            if chosen == "GIGA_COMBO":
                mstate["in_giga_combo"] = True
                if "action_queue" not in mstate: mstate["action_queue"] = []
                for _ in range(random.randint(3, 4)):
                    mstate["action_queue"].extend(["TELEPORT", "DASH", "TELEPORT", "SHOOT"])
                next_act = mstate["action_queue"].pop(0)
            else:
                next_act = chosen
            
    mstate["state"] = next_act
    mstate["last_action"] = next_act
    _server_boss_start_action(mstate, next_act, target_pos, new_projectiles, is_walkable_fn)

def _server_boss_start_action(mstate, action, target_pos, new_projectiles, is_walkable_fn):
    if action == "DASH":
        dx = target_pos[0] - mstate["pos"][0]
        dy = target_pos[1] - mstate["pos"][1]
        angle = math.atan2(dy, dx)
        snap_angle = (round(8 * angle / (2 * math.pi)) % 8) * (math.pi / 4)
        mstate["move_dir"] = [math.cos(snap_angle), math.sin(snap_angle)]
        mstate["action_timer"] = random.randint(1000, 1500)
        mstate["dash_speed"] = 80.0
        mstate["attacking"] = 10
        
    elif action == "SHOOT":
        mstate["action_timer"] = 400
        mstate["attacking"] = 10
        dx = target_pos[0] - mstate["pos"][0]
        dy = target_pos[1] - mstate["pos"][1]
        angle = math.atan2(dy, dx)
        snap_angle = (round(8 * angle / (2 * math.pi)) % 8) * (math.pi / 4)
        mstate["move_dir"] = [math.cos(snap_angle), math.sin(snap_angle)]
        
        speed = 20.0
        for angle_offset in [-0.6, -0.3, 0, 0.3, 0.6]:
            a = snap_angle + angle_offset
            new_projectiles.append({
                "x": mstate["pos"][0], "y": mstate["pos"][1],
                "vx": math.cos(a) * speed, "vy": math.sin(a) * speed,
                "timer": 2000, "damage": 1
            })
            
    elif action == "REST": 
        mstate["action_timer"] = 50
        
    elif action == "HEAL": 
        mstate["action_timer"] = 1500
        
    elif action == "TELEPORT":
        mstate["action_timer"] = 400
        mstate.pop("tp_target_x", None)
        mstate.pop("tp_target_y", None)
        
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            dist_tp = random.uniform(250, 600)
            new_x = target_pos[0] + math.cos(angle) * dist_tp
            new_y = target_pos[1] + math.sin(angle) * dist_tp
            
            # Vérifie si la position de TP est dans la même salle
            same_room = (int(new_x // 2000) == int(target_pos[0] // 2000) and 
                         int(new_y // 2000) == int(target_pos[1] // 2000))
            if is_walkable_fn(new_x, new_y) and same_room:
                mstate["tp_target_x"] = new_x
                mstate["tp_target_y"] = new_y
                break
                
        if "tp_target_x" not in mstate:
            mstate["tp_target_x"] = mstate["pos"][0]
            mstate["tp_target_y"] = mstate["pos"][1]

def _server_boss_dash(mstate, player_states, is_walkable_fn, dt_ms, hits):
    mstate["action_timer"] -= dt_ms
    dash_spd = mstate.get("dash_speed", 80.0)
    new_x = mstate["pos"][0] + mstate["move_dir"][0] * dash_spd
    new_y = mstate["pos"][1] + mstate["move_dir"][1] * dash_spd
    
    if is_walkable_fn(new_x, new_y):
        mstate["pos"][0], mstate["pos"][1] = new_x, new_y
        mstate["moving"] = True
    else:
        if is_walkable_fn(new_x, mstate["pos"][1]): mstate["pos"][0] = new_x
        if is_walkable_fn(mstate["pos"][0], new_y): mstate["pos"][1] = new_y
        
    for pid, pstate in player_states.items():
        if pstate.get("health", 1) <= 0: continue
        dist_hit = ((pstate["pos"][0] - mstate["pos"][0])**2 + (pstate["pos"][1] - mstate["pos"][1])**2)**0.5
        if dist_hit < 150:
            hits.append({"pid": pid, "damage": 1, "x": mstate["pos"][0], "y": mstate["pos"][1]})
            
    if mstate["action_timer"] <= 0: 
        _server_end_boss_action(mstate)

def _server_boss_shoot(mstate, dt_ms):
    mstate["action_timer"] -= dt_ms
    if mstate["action_timer"] <= 0: 
        _server_end_boss_action(mstate)

def _server_boss_rest(mstate, dt_ms):
    mstate["action_timer"] -= dt_ms
    if mstate["action_timer"] <= 0: 
        _server_end_boss_action(mstate)

def _server_boss_heal(mstate, dt_ms):
    mstate["action_timer"] -= dt_ms
    if mstate["action_timer"] <= 0:
        mstate["health"] = min(mstate.get("max_health", 150), mstate["health"] + mstate.get("max_health", 150) * 0.15)
        _server_end_boss_action(mstate)

def _server_boss_teleport(mstate, dt_ms):
    mstate["action_timer"] -= dt_ms
    if mstate["action_timer"] <= 0:
        mstate["pos"][0] = mstate.get("tp_target_x", mstate["pos"][0])
        mstate["pos"][1] = mstate.get("tp_target_y", mstate["pos"][1])
        mstate["force_attack_next"] = True
        _server_end_boss_action(mstate)