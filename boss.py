import pygame
import math
import random
from enum import Enum, auto
from entity import Entity

class BossState(Enum):
    WALK = auto()       # Déplacement continu (Phase neutre / Cooldown)
    DASH = auto()       # Attaque : Dash 8 directions
    SHOOT = auto()      # Attaque : Tir 4 directions
    REST = auto()       # Repos : Courte pause statique
    HEAL = auto()       # Soin : Régénération si HP < 50%
    TELEPORT = auto()   # Déplacement instantané près du joueur
    SPAWN = auto()      # Apparition : Canalisation 10s au centre

# ==========================================
# CLASSE CLIENT (Rendu et Animations)
# ==========================================
class Boss(Entity):
    def __init__(self, pos_x, pos_y, sprite_size=200):
        super().__init__(
            health=150, attack=1, speed=5, nb_potions=0,
            image_path="assets/base_monstre.png", 
            pos_x=pos_x, pos_y=pos_y, sprite_size=sprite_size
        )
        
        # Utilitaire intelligent pour charger les séquences d'images facilement
        def load_frames(action_name, max_frames):
            frames = []
            for i in range(1, max_frames + 1):
                try:
                    img = pygame.image.load(f"assets/boss/boss_{action_name}_{i}.png").convert_alpha()
                    frames.append(pygame.transform.scale(img, (sprite_size, sprite_size)))
                except Exception:
                    pass
            return frames

        # Groupement de toutes les animations dans un dictionnaire pour éviter les "if/elif" à répétition
        self.animations = {
            "WALK": load_frames("stand", 3),
            "DASH_D": load_frames("dashD", 3),
            "DASH_U": load_frames("dashU", 3),
            "DASH_L": load_frames("dashL", 3),
            "DASH_R": load_frames("dashR", 3),
            "SHOOT": load_frames("shoot", 3),
            "HEAL": load_frames("heal", 3),
            "TELEPORT": load_frames("tp", 5),
            "SPAWN": load_frames("spawn", 2)
        }
        self.animations["REST"] = self.animations["WALK"]
        if not self.animations["SPAWN"]:
            self.animations["SPAWN"] = self.animations["WALK"]

        # Chargement sécurisé des sons
        self.sound_map = {}
        sound_files = {
            "DASH": "boss_dash.mp3",
            "HEAL": "boss_heal.mp3",
            "TELEPORT": "boss_tp.mp3",
            "SHOOT": "boss_shoot.mp3"
        }
        
        for state, filename in sound_files.items():
            try:
                snd = pygame.mixer.Sound(f"assets/sound/{filename}")
                snd.set_volume(0.5)
                self.sound_map[state] = snd
            except Exception as e:
                print(f"[BOSS] Impossible de charger le son {filename} : {e}")

        if len(self.animations["WALK"]) > 0:
            self.image = self.animations["WALK"][0]
        else:
            self.image = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
            self.image.fill((200, 20, 20))
            
        self.state = "WALK"
        self.last_state = "WALK"
        
        # Variables d'animation
        self.anim_timer = 0
        self.anim_rate = 100 # Vitesse de l'animation en ms (10 fps)
        self.anim_index = 0

    def update_animation(self, dt_ms, is_moving, is_attacking):
        """Met à jour l'animation du boss pour le client (appelé par game.py)."""
        self.attacking = is_attacking
        
        current_state = getattr(self, 'state', 'WALK')
        
        # Résolution dynamique pour les directions du DASH
        if current_state == "DASH":
            dir_char = getattr(self, 'direction', 'down')[0].upper() # ex: 'up' -> 'U'
            current_state = f"DASH_{dir_char}"

        frames = self.animations.get(current_state, self.animations["WALK"])
            
        if current_state != self.last_state:
            self.anim_index = 0
            self.anim_timer = 0
            self.last_state = current_state
            
            # Joue le son correspondant à l'état s'il existe
            if current_state in self.sound_map:
                try:
                    self.sound_map[current_state].play()
                except Exception:
                    pass
            
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
    elif b_state == "SPAWN":
        _server_boss_spawn(mstate, dt_ms)

    return hits, new_projectiles

# ------------------------------------------
# SOUS-FONCTIONS SERVEUR (Helpers)
# ------------------------------------------

def _server_get_facing_direction(dx, dy):
    """Détermine la direction principale du regard (up/down/left/right)."""
    if abs(dx) > abs(dy):
        return "right" if dx > 0 else "left"
    return "down" if dy > 0 else "up"

def _server_get_snapped_direction(dx, dy):
    """Retourne un vecteur normalisé 'snappé' sur les 8 directions (multiples de 45°)."""
    angle = math.atan2(dy, dx)
    snap_angle = (round(8 * angle / (2 * math.pi)) % 8) * (math.pi / 4)
    return [math.cos(snap_angle), math.sin(snap_angle)]

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
        
        mstate["dir"] = _server_get_facing_direction(dx, dy)

def _server_boss_pick_next_action(mstate, target_pos, new_projectiles, is_walkable_fn):
    if mstate.get("action_queue"):
        next_act = mstate["action_queue"].pop(0)
    else:
        mstate["in_giga_combo"] = False
        if mstate.get("force_attack_next"):
            mstate["force_attack_next"] = False
            next_act = random.choice(["DASH", "SHOOT"])
        else:
            weights = {
                "DASH": 30, 
                "SHOOT": 20, 
                "TELEPORT": 15, 
                "REST": 5, 
                "HEAL": 10, 
                "GIGA_COMBO": 20
            }
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
    dx = target_pos[0] - mstate["pos"][0]
    dy = target_pos[1] - mstate["pos"][1]

    if action in ["DASH", "SHOOT"]:
        mstate["dir"] = _server_get_facing_direction(dx, dy)
        mstate["move_dir"] = _server_get_snapped_direction(dx, dy)

    if action == "DASH":
        mstate["action_timer"] = random.randint(1000, 1500)
        mstate["dash_speed"] = 40.0
        mstate["attacking"] = 10
        
    elif action == "SHOOT":
        mstate["action_timer"] = 400
        mstate["attacking"] = 10
        
        speed = 20.0
        angle = math.atan2(mstate["move_dir"][1], mstate["move_dir"][0])
        for angle_offset in [-0.6, -0.3, 0, 0.3, 0.6]:
            a = angle + angle_offset
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
    dash_spd = mstate.get("dash_speed", 40.0)
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

def _server_boss_spawn(mstate, dt_ms):
    mstate["action_timer"] -= dt_ms
    max_hp = mstate.get("max_health", 150)
    # Régénération fluide sur 10 secondes (10 000 ms)
    mstate["health"] = min(max_hp, mstate["health"] + (max_hp / 10000.0) * dt_ms)
    
    if mstate["action_timer"] <= 0:
        mstate["health"] = max_hp
        _server_end_boss_action(mstate)