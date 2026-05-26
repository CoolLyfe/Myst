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

class Boss(Entity):
    def __init__(self, pos_x, pos_y, sprite_size=200):
        # Initialisation de base (basée sur ta classe Entity)
        super().__init__(
            health=150, attack=1, speed=5, nb_potions=0,
            image_path="assets/base_monstre.png", # À remplacer par ton sprite de Boss
            pos_x=pos_x, pos_y=pos_y, sprite_size=sprite_size
        )
        
        # --- VISUEL TEMPORAIRE : CARRÉ ROUGE ---
        self.image = pygame.Surface((sprite_size, sprite_size))
        self.image.fill((200, 20, 20))
        
        # --- PARAMÈTRES RÉGLABLES (Game Design) ---
        self.walk_speed = 3.0
        self.dash_speed = 20.0
        
        # Cooldowns (en ms)
        self.base_cooldown = 1000       # Temps d'attente plus long
        self.giga_combo_modifier = 0.3  # Diviseur de cooldown pendant le Giga-Combo (ici ~x3.3 plus rapide)
        self.dash_duration = 1200
        self.rest_duration = 200
        self.heal_duration = 1500
        self.teleport_min_range = 250   # Distance minimum (évite d'apparaître sur le joueur)
        self.teleport_max_range = 600   # Distance maximum d'apparition après un TP
        
        # --- SYSTÈME DE PROBABILITÉS (Poids de base) ---
        # Chances de base pour déclencher chaque action
        self.base_weights = {
            BossState.DASH: 30,
            BossState.SHOOT: 20,
            BossState.TELEPORT: 25,
            BossState.REST: 5,
            BossState.HEAL: 10,
            "GIGA_COMBO": 10  # Action spéciale qui remplit la file d'attente
        }
        self.inertia_multiplier = 2.0   # Multiplicateur si l'action précédente est répétée
        
        # --- ÉTAT ET LOGIQUE D'IA ---
        self.state = BossState.WALK
        self.last_action = None         # Pour calculer l'inertie
        self.cooldown_timer = 0         # Timer avant la prochaine action
        self.action_timer = 0           # Timer de l'action en cours
        self.pause_timer = 0            # Temps d'arrêt très léger entre les actions
        self.current_dash_speed = 150.0
        
        self.force_attack_next = False  # Règle stricte post-téléportation
        
        # --- GIGA COMBO ---
        self.in_giga_combo = False
        self.action_queue = []          # File d'attente stricte pour les combos
        
        # Variables vectorielles
        self.move_dir = pygame.math.Vector2(0, 0)
        self.target_pos = pygame.math.Vector2(0, 0)

    def update(self, dt_ms, player):
        """
        Méthode principale appelée à chaque frame.
        Gère la State Machine du boss.
        """
        # Si mort, on ne fait rien
        if not self.alive:
            return
            
        self.target_pos = pygame.math.Vector2(player.rect.centerx, player.rect.centery)

        # --- GESTION DES ÉTATS ---
        if self.state == BossState.WALK:
            self._update_walk(dt_ms)
            
        elif self.state == BossState.DASH:
            self._update_dash(dt_ms)
            
        elif self.state == BossState.SHOOT:
            self._update_shoot(dt_ms)
            
        elif self.state == BossState.REST:
            self._update_rest(dt_ms)
            
        elif self.state == BossState.HEAL:
            self._update_heal(dt_ms)
            
        elif self.state == BossState.TELEPORT:
            self._update_teleport(dt_ms)

        # Mise à jour de la hitbox pour qu'elle suive le rect (hérité de Entity)
        self.update_hitbox()

    # ==========================================
    # LOGIQUE DES ÉTATS (STATE UPDATES)
    # ==========================================

    def _update_walk(self, dt_ms):
        """État normal : le boss se déplace toujours (vers le joueur) tout en réduisant son cooldown."""
        # 1. Très léger arrêt post-action ou déplacement vers le joueur
        if self.pause_timer > 0:
            self.pause_timer -= dt_ms
        else:
            boss_pos = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
            dist_vec = self.target_pos - boss_pos
            
            if dist_vec.length() > 0:
                move_vec = dist_vec.normalize() * self.walk_speed
                self.rect.centerx += move_vec.x
                self.rect.centery += move_vec.y

        # 2. Gestion du cooldown
        self.cooldown_timer -= dt_ms
        if self.cooldown_timer <= 0:
            self._pick_next_action()

    def _update_dash(self, dt_ms):
        """Exécute le dash dans la direction pré-calculée."""
        self.action_timer -= dt_ms
        
        # Déplacement très rapide
        self.rect.centerx += self.move_dir.x * self.current_dash_speed
        self.rect.centery += self.move_dir.y * self.current_dash_speed
        
        # Fin de l'attaque
        if self.action_timer <= 0:
            self._end_action(BossState.DASH)

    def _update_shoot(self, dt_ms):
        """Statique pendant un court instant pour tirer."""
        self.action_timer -= dt_ms
        if self.action_timer <= 0:
            # TODO : Instancier ton projectile ici en utilisant self.move_dir
            self._end_action(BossState.SHOOT)

    def _update_rest(self, dt_ms):
        """Statique. Repos pur."""
        self.action_timer -= dt_ms
        if self.action_timer <= 0:
            self._end_action(BossState.REST)

    def _update_heal(self, dt_ms):
        """Statique. Soin dans le temps."""
        self.action_timer -= dt_ms
        if self.action_timer <= 0:
            # Régénération de 15% de la santé max
            self.health = min(self.max_health, self.health + (self.max_health * 0.15))
            self._end_action(BossState.HEAL)

    def _update_teleport(self, dt_ms):
        """Prend quelques frames avant de se téléporter."""
        self.action_timer -= dt_ms
        if self.action_timer <= 0:
            # Calcule un point aléatoire autour du joueur dans un certain rayon
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(self.teleport_min_range, self.teleport_max_range)
            
            new_x = self.target_pos.x + math.cos(angle) * distance
            new_y = self.target_pos.y + math.sin(angle) * distance
            
            self.rect.centerx = new_x
            self.rect.centery = new_y
            
            # Règle absolue : Post-TP = Attaque obligatoire (sans cooldown)
            self.force_attack_next = True 
            
            self._end_action(BossState.TELEPORT)

    # ==========================================
    # MÉCANIQUES DE DÉCISION (IA)
    # ==========================================

    def _pick_next_action(self):
        """Logique décisionnelle du Boss pour choisir sa prochaine action."""
        
        # 1. PRIORITY : Giga-Combo (File d'attente)
        if self.action_queue:
            next_action = self.action_queue.pop(0)
            self._start_action(next_action)
            return
        else:
            # Si la file se vide, on n'est plus en Giga-Combo
            self.in_giga_combo = False

        # 2. PRIORITY : Danger après TP
        # Si la dernière action était un TP, on FORCE une attaque
        if self.force_attack_next:
            self.force_attack_next = False
            # 50/50 entre Dash et Shoot
            forced_action = random.choice([BossState.DASH, BossState.SHOOT])
            self._start_action(forced_action)
            return

        # 3. COMPORTEMENT NORMAL : Calcul des probabilités avec Inertie
        weights = self.base_weights.copy()
        
        # Règle stricte du Soin : Seulement si HP < 50%
        if self.health >= self.max_health * 0.5:
            weights[BossState.HEAL] = 0
            
        # Règle d'Inertie : Si le boss vient de faire une action, il y a plus de chance qu'il la refasse
        if self.last_action in weights:
            weights[self.last_action] *= self.inertia_multiplier
            
        # Extraction pour le random.choices
        actions = list(weights.keys())
        probabilities = list(weights.values())
        
        chosen_action = random.choices(actions, weights=probabilities, k=1)[0]
        
        if chosen_action == "GIGA_COMBO":
            self._trigger_giga_combo()
        else:
            self._start_action(chosen_action)

    def _start_action(self, action: BossState):
        """Initialise les variables nécessaires avant d'entrer dans un nouvel état."""
        self.state = action
        
        boss_pos = pygame.math.Vector2(self.rect.centerx, self.rect.centery)
        dist_vec = self.target_pos - boss_pos

        if action == BossState.DASH:
            # Mathématiques Vecteurs : Dash restreint à 8 directions (45° par tranche)
            if dist_vec.length() > 0:
                angle = math.atan2(dist_vec.y, dist_vec.x)
                # Arrondit à l'angle multiple de 45° le plus proche (math.pi / 4)
                octant = round(8 * angle / (2 * math.pi)) % 8
                snap_angle = octant * (math.pi / 4)
                
                self.move_dir = pygame.math.Vector2(math.cos(snap_angle), math.sin(snap_angle))
                # Pour l'animation
                self._update_facing_direction(self.move_dir)
            
            self.action_timer = random.randint(1000, 1500)
            self.current_dash_speed = random.uniform(18.0, 25.0)
            
        elif action == BossState.SHOOT:
            # Mathématiques Vecteurs : Tir restreint à 8 directions (45° par tranche)
            if dist_vec.length() > 0:
                angle = math.atan2(dist_vec.y, dist_vec.x)
                # Arrondit à l'angle multiple de 45° le plus proche (math.pi / 4)
                octant = round(8 * angle / (2 * math.pi)) % 8
                snap_angle = octant * (math.pi / 4)
                
                self.move_dir = pygame.math.Vector2(math.cos(snap_angle), math.sin(snap_angle))
                self._update_facing_direction(self.move_dir)

            self.action_timer = 400 # Temps d'incantation du tir plus long
            
        elif action == BossState.REST:
            self.action_timer = self.rest_duration
            
        elif action == BossState.HEAL:
            self.action_timer = self.heal_duration
            
        elif action == BossState.TELEPORT:
            self.action_timer = 400

    def _end_action(self, action: BossState):
        """
        Appelée à la fin d'une action. 
        Ramène le boss en état WALK (Déplacement continu) et déclenche le cooldown.
        """
        self.last_action = action
        self.state = BossState.WALK
        
        self.pause_timer = 800 # 800ms de temps d'arrêt avant de reprendre le mouvement
        
        # Application du Cooldown
        # Si la dernière action était un TP (et qu'on n'est pas en GigaCombo), cooldown de 0 car on force l'attaque ensuite
        if self.force_attack_next and not self.in_giga_combo:
            self.cooldown_timer = 0
        else:
            # Le rythme frénétique du Giga-Combo divise le temps de repos
            modifier = self.giga_combo_modifier if self.in_giga_combo else 1.0
            # On ajoute une légère variance (random) pour rendre le boss moins mécanique
            self.cooldown_timer = (self.base_cooldown * modifier) * random.uniform(0.8, 1.2)

    def _trigger_giga_combo(self):
        """
        Remplit la file d'attente pour le Giga-Combo.
        Règle stricte en boucle : TP -> DASH -> TP -> SHOOT (Répété 3 à 4 fois).
        """
        self.in_giga_combo = True
        nb_cycles = random.randint(3, 4)
        
        self.action_queue.clear()
        for _ in range(nb_cycles):
            self.action_queue.append(BossState.TELEPORT)
            self.action_queue.append(BossState.DASH)
            self.action_queue.append(BossState.TELEPORT)
            self.action_queue.append(BossState.SHOOT)
            
        # Lance immédiatement la première action de la file
        self._pick_next_action()

    def _update_facing_direction(self, vector: pygame.math.Vector2):
        """Met à jour la propriété 'direction' de l'Entity pour les animations."""
        # Utilise la logique existante de ton fichier entity.py
        if abs(vector.x) > abs(vector.y):
            if vector.x > 0:
                self.direction = "right"
            else:
                self.direction = "left"
        else:
            if vector.y > 0:
                self.direction = "down"
            else:
                self.direction = "up"

    def update_animation(self, dt_ms, is_moving, is_attacking):
        """Met à jour l'animation du boss pour le client (appelé par game.py)."""
        self.attacking = is_attacking
        # Ajoute ici la logique de défilement des sprites quand tu en auras.
        self.update_hitbox()

def server_update_boss(mstate, player_states, is_walkable_fn, dt_ms):
    """
    Logique IA du boss exécutée côté serveur.
    Extrait de server.py pour garder le code propre.
    Retourne une liste de dictionnaires pour les joueurs touchés (ex: [{"pid": "1", "damage": 2, ...}]).
    """
    hits = []
    new_projectiles = []
    
    target_pid = None
    min_dist = float('inf')
    for pid, pstate in player_states.items():
        if pstate.get("health", 1) <= 0: continue
        dist_sq = (pstate["pos"][0] - mstate["pos"][0])**2 + (pstate["pos"][1] - mstate["pos"][1])**2
        if dist_sq < min_dist:
            min_dist = dist_sq
            target_pid = pid
            
    target_pos = player_states[target_pid]["pos"] if target_pid else mstate["pos"]
    b_state = mstate.get("state", "WALK")
    mstate["moving"] = False

    def end_boss_action():
        mstate["state"] = "WALK"
        if mstate["force_attack_next"] and not mstate["in_giga_combo"]:
            mstate["cooldown_timer"] = 0
        else:
            mod = 0.3 if mstate["in_giga_combo"] else 1.0
            mstate["cooldown_timer"] = 1000 * mod * random.uniform(0.8, 1.2)
            
        mstate["pause_timer"] = 800 # Arrêt marqué entre les actions (800 ms)

    if b_state == "WALK":
        mstate.setdefault("pause_timer", 0)
        if mstate["pause_timer"] > 0:
            mstate["pause_timer"] -= dt_ms
        elif target_pid:
            dx = target_pos[0] - mstate["pos"][0]
            dy = target_pos[1] - mstate["pos"][1]
            dist = (dx**2 + dy**2)**0.5
            if dist > 0:
                vx = (dx/dist) * mstate["speed"]
                vy = (dy/dist) * mstate["speed"]
                new_x = mstate["pos"][0] + vx
                new_y = mstate["pos"][1] + vy
                if is_walkable_fn(new_x, new_y):
                    mstate["pos"][0] = new_x
                    mstate["pos"][1] = new_y
                    mstate["moving"] = True
                else:
                    if is_walkable_fn(new_x, mstate["pos"][1]): mstate["pos"][0] = new_x
                    if is_walkable_fn(mstate["pos"][0], new_y): mstate["pos"][1] = new_y
                
                if abs(dx) > abs(dy): mstate["dir"] = "right" if dx > 0 else "left"
                else: mstate["dir"] = "down" if dy > 0 else "up"

        if target_pid:
            mstate["cooldown_timer"] -= dt_ms
            if mstate["cooldown_timer"] <= 0:
                if mstate.get("action_queue"):
                    next_act = mstate["action_queue"].pop(0)
                elif mstate["force_attack_next"]:
                    mstate["force_attack_next"] = False
                    next_act = random.choice(["DASH", "SHOOT"])
                else:
                    weights = {"DASH": 30, "SHOOT": 20, "TELEPORT": 25, "REST": 5, "HEAL": 10, "GIGA_COMBO": 10}
                    if mstate["health"] >= mstate["max_health"] * 0.5: weights["HEAL"] = 0
                    if mstate["last_action"] in weights: weights[mstate["last_action"]] *= 2.0
                    acts = list(weights.keys())
                    probs = list(weights.values())
                    chosen = random.choices(acts, weights=probs, k=1)[0]
                    
                    if chosen == "GIGA_COMBO":
                        mstate["in_giga_combo"] = True
                        for _ in range(random.randint(3, 4)):
                            mstate["action_queue"].extend(["TELEPORT", "DASH", "TELEPORT", "SHOOT"])
                        next_act = mstate["action_queue"].pop(0)
                    else:
                        next_act = chosen
                        
                mstate["state"] = next_act
                mstate["last_action"] = next_act
                
                if next_act == "DASH":
                    dx = target_pos[0] - mstate["pos"][0]
                    dy = target_pos[1] - mstate["pos"][1]
                    angle = math.atan2(dy, dx)
                    snap_angle = (round(8 * angle / (2 * math.pi)) % 8) * (math.pi / 4)
                    mstate["move_dir"] = [math.cos(snap_angle), math.sin(snap_angle)]
                    mstate["action_timer"] = random.randint(1000, 1500)
                    mstate["dash_speed"] = random.uniform(18.0, 25.0)
                    mstate["attacking"] = 10
                elif next_act == "SHOOT":
                    mstate["action_timer"] = 400
                    mstate["attacking"] = 10
                    
                    dx = target_pos[0] - mstate["pos"][0]
                    dy = target_pos[1] - mstate["pos"][1]
                    angle = math.atan2(dy, dx)
                    octant = round(8 * angle / (2 * math.pi)) % 8
                    snap_angle = octant * (math.pi / 4)
                    mstate["move_dir"] = [math.cos(snap_angle), math.sin(snap_angle)]
                    
                    speed = 20.0
                    for angle_offset in [-0.6, -0.3, 0, 0.3, 0.6]:
                        a = snap_angle + angle_offset
                        vx = math.cos(a) * speed
                        vy = math.sin(a) * speed
                        new_projectiles.append({
                            "x": mstate["pos"][0], "y": mstate["pos"][1],
                            "vx": vx, "vy": vy,
                            "timer": 2000, "damage": 1
                        })
                elif next_act == "REST": mstate["action_timer"] = 50
                elif next_act == "HEAL": mstate["action_timer"] = 1500
                elif next_act == "TELEPORT":
                    mstate["action_timer"] = 400
                    mstate.pop("tp_target_x", None)
                    mstate.pop("tp_target_y", None)
                    for _ in range(10):
                        angle = random.uniform(0, 2 * math.pi)
                        dist_tp = random.uniform(250, 600)
                        new_x = target_pos[0] + math.cos(angle) * dist_tp
                        new_y = target_pos[1] + math.sin(angle) * dist_tp
                        if is_walkable_fn(new_x, new_y) and int(new_x // 2000) == int(target_pos[0] // 2000) and int(new_y // 2000) == int(target_pos[1] // 2000):
                            mstate["tp_target_x"] = new_x
                            mstate["tp_target_y"] = new_y
                            break
                    if "tp_target_x" not in mstate:
                        mstate["tp_target_x"] = mstate["pos"][0]
                        mstate["tp_target_y"] = mstate["pos"][1]

    elif b_state == "DASH":
        mstate["action_timer"] -= dt_ms
        dash_spd = mstate.get("dash_speed", 40.0)
        new_x = mstate["pos"][0] + mstate["move_dir"][0] * dash_spd
        new_y = mstate["pos"][1] + mstate["move_dir"][1] * dash_spd
        if is_walkable_fn(new_x, new_y):
            mstate["pos"][0] = new_x
            mstate["pos"][1] = new_y
            mstate["moving"] = True
        else:
            if is_walkable_fn(new_x, mstate["pos"][1]): mstate["pos"][0] = new_x
            if is_walkable_fn(mstate["pos"][0], new_y): mstate["pos"][1] = new_y
            
        for pid, pstate in player_states.items():
            if pstate.get("health", 1) <= 0: continue
            dist_hit = ((pstate["pos"][0] - mstate["pos"][0])**2 + (pstate["pos"][1] - mstate["pos"][1])**2)**0.5
            if dist_hit < 150: # Rayon de dégât de l'attaque Dash
                hits.append({"pid": pid, "damage": 1, "x": mstate["pos"][0], "y": mstate["pos"][1]})
                
        if mstate["action_timer"] <= 0: end_boss_action()
    elif b_state == "SHOOT":
        mstate["action_timer"] -= dt_ms
        if mstate["action_timer"] <= 0: end_boss_action()
    elif b_state == "REST":
        mstate["action_timer"] -= dt_ms
        if mstate["action_timer"] <= 0: end_boss_action()
    elif b_state == "HEAL":
        mstate["action_timer"] -= dt_ms
        if mstate["action_timer"] <= 0:
            mstate["health"] = min(mstate["max_health"], mstate["health"] + mstate["max_health"] * 0.15)
            end_boss_action()
    elif b_state == "TELEPORT":
        mstate["action_timer"] -= dt_ms
        if mstate["action_timer"] <= 0:
            mstate["pos"][0] = mstate.get("tp_target_x", mstate["pos"][0])
            mstate["pos"][1] = mstate.get("tp_target_y", mstate["pos"][1])
            mstate["force_attack_next"] = True
            end_boss_action()

    return hits, new_projectiles