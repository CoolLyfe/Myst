import pygame
import sys
import game
import pyvidplayer
import time
import math
import random
import json
import os

pygame.init()

KEYBINDS_FILE = "keybinds.json"

DEFAULT_KEYBINDS = {
    "haut":    pygame.K_z,
    "bas":     pygame.K_s,
    "gauche":  pygame.K_q,
    "droite":  pygame.K_d,
    "attaque": pygame.K_SPACE,
    "potion":  pygame.K_e,
    "sprint":  pygame.K_LSHIFT,
}

ACTION_LABELS = {
    "haut":    "Aller en haut",
    "bas":     "Aller en bas",
    "gauche":  "Aller à gauche",
    "droite":  "Aller à droite",
    "attaque": "Attaquer",
    "potion":  "Utiliser potion",
    "sprint":  "Sprinter",
}

def load_keybinds():
    if os.path.exists(KEYBINDS_FILE):
        try:
            with open(KEYBINDS_FILE, "r") as f:
                raw = json.load(f)
            return {k: int(v) for k, v in raw.items()}
        except:
            pass
    return DEFAULT_KEYBINDS.copy()

def save_keybinds(binds):
    with open(KEYBINDS_FILE, "w") as f:
        json.dump({k: int(v) for k, v in binds.items()}, f)

def quitgame():
    if 'video' in globals() and video is not None:
        video.close()
    pygame.quit()
    sys.exit()

video = pyvidplayer.Video("assets/fire_background.mp4")
video.set_size((1920, 1080))
LARGEUR, HAUTEUR = 1920, 1080
screen = pygame.display.set_mode((LARGEUR, HAUTEUR), pygame.FULLSCREEN)
pygame.display.set_caption("Myst")

# Palette gris-bleu pour aller avec la brume
NOIR          = (0, 0, 0)
BLANC         = (255, 255, 255)
ACCENT        = (140, 170, 200)
ACCENT_CLAIR  = (190, 215, 235)
ACCENT_SOMBRE = (70,  95,  120)
GRIS_FONCE    = (18,  14,  10)
ROUGE_ERR     = (220, 60,  40)
AMBRE         = (200, 180, 140)
JAUNE         = (210, 230, 255)

try:
    title_font  = pygame.font.SysFont("Chiller", 220, bold=True)
    button_font = pygame.font.SysFont("Chiller",  62, bold=False)
    sub_font    = pygame.font.SysFont("Chiller",  38)
    hint_font   = pygame.font.SysFont("Garamond", 28, italic=True)
    small_font  = pygame.font.SysFont("Chiller",  34)
    tiny_font   = pygame.font.SysFont("Chiller",  26)
except:
    title_font  = pygame.font.SysFont(None, 220, bold=True)
    button_font = pygame.font.SysFont(None,  62)
    sub_font    = pygame.font.SysFont(None,  38)
    hint_font   = pygame.font.SysFont(None,  28)
    small_font  = pygame.font.SysFont(None,  34)
    tiny_font   = pygame.font.SysFont(None,  26)

BTN_W  = 480
BTN_H  = 72
GAP    = 18
BLOC_Y = HAUTEUR // 2 + 20

def make_btn(label, row):
    x = LARGEUR // 2 - BTN_W // 2
    y = BLOC_Y + row * (BTN_H + GAP)
    return {"label": label, "rect": pygame.Rect(x, y, BTN_W, BTN_H)}

# 4 boutons bien centrés, sans "Notre équipe"
boutons = [
    make_btn("Solo",       0),
    make_btn("En ligne",   1),
    make_btn("Paramètres", 2),
    make_btn("Quitter",    3),
]

online_buttons = [
    make_btn("Host",      0),
    make_btn("Rejoindre", 1),
    make_btn("Retour",    3),
]


class Ember:
    """Petite braise qui monte et se disperse — effet purement visuel."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.x     = random.uniform(0, LARGEUR)
        self.y     = random.uniform(HAUTEUR * 0.4, HAUTEUR + 20)
        self.vx    = random.uniform(-0.6, 0.6)
        self.vy    = random.uniform(-1.8, -0.5)
        self.life  = random.uniform(0.4, 1.0)
        self.decay = random.uniform(0.003, 0.007)
        self.r     = random.uniform(1.5, 3.5)
        self.col   = random.choice([
            (100, 140, 190), (80, 120, 170), (130, 160, 200), (60, 100, 150)
        ])

    def update(self):
        self.x    += self.vx + math.sin(self.y * 0.01) * 0.3
        self.y    += self.vy
        self.life -= self.decay
        if self.life <= 0 or self.y < -10:
            self.reset()

    def draw(self, surf):
        alpha = max(0, min(255, int(self.life * 255)))
        r, g, b = self.col
        tmp = pygame.Surface((int(self.r * 2 + 2), int(self.r * 2 + 2)), pygame.SRCALPHA)
        pygame.draw.circle(tmp, (r, g, b, alpha), (int(self.r + 1), int(self.r + 1)), int(self.r))
        surf.blit(tmp, (int(self.x - self.r), int(self.y - self.r)))


EMBERS = [Ember() for _ in range(120)]


def make_vignette():
    surf = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
    for i in range(HAUTEUR):
        t_top    = max(0, 1 - i / (HAUTEUR * 0.45))
        t_bottom = max(0, (i - HAUTEUR * 0.55) / (HAUTEUR * 0.45))
        alpha    = int(min(1.0, t_top * 1.4 + t_bottom * 1.2) * 200)
        if alpha > 0:
            pygame.draw.line(surf, (0, 0, 0, alpha), (0, i), (LARGEUR, i))
    return surf

vignette_surf = make_vignette()


def draw_accent_line(surf, y, alpha=160):
    """Ligne decorative dégradée en gris-bleu sous le titre."""
    line_surf = pygame.Surface((BTN_W, 2), pygame.SRCALPHA)
    cx = BTN_W // 2
    for px in range(BTN_W):
        t = 1 - abs(px - cx) / cx
        a = int(t * alpha)
        pygame.draw.line(line_surf, (*ACCENT, a), (px, 0), (px, 1))
    surf.blit(line_surf, (LARGEUR // 2 - BTN_W // 2, y))


def draw_button(surf, btn, hovered=False, clicked=False, alpha_mult=1.0):
    rect  = btn["rect"]
    label = btn["label"]

    if clicked:
        bg_alpha   = int(200 * alpha_mult)
        bg_color   = (40, 60, 85, bg_alpha)
        border_col = ACCENT_CLAIR
        border_w   = 3
    elif hovered:
        bg_alpha   = int(160 * alpha_mult)
        bg_color   = (25, 40, 58, bg_alpha)
        border_col = ACCENT
        border_w   = 2
    else:
        bg_alpha   = int(100 * alpha_mult)
        bg_color   = (12, 18, 26, bg_alpha)
        border_col = ACCENT_SOMBRE
        border_w   = 1

    btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(btn_surf, bg_color, btn_surf.get_rect(), border_radius=6)
    pygame.draw.rect(btn_surf, (*border_col, 220), btn_surf.get_rect(), border_w, border_radius=6)

    if hovered or clicked:
        shine = pygame.Surface((rect.width - 4, rect.height // 3), pygame.SRCALPHA)
        shine.fill((140, 180, 220, 14))
        btn_surf.blit(shine, (2, 2))

    surf.blit(btn_surf, rect.topleft)

    # Cascade de tailles : button_font → small_font → tiny_font selon l'espace dispo
    text_col = ACCENT_CLAIR if (hovered or clicked) else (180, 200, 215)
    marge    = 12
    for f in (button_font, small_font, tiny_font):
        lbl_surf = f.render(label, True, text_col)
        if lbl_surf.get_width() <= rect.width - marge:
            break
    shadow_s = f.render(label, True, (5, 8, 12))
    lbl_rect = lbl_surf.get_rect(center=rect.center)
    # Clip au rect du bouton pour qu'aucun texte ne déborde jamais
    old_clip = surf.get_clip()
    surf.set_clip(rect)
    surf.blit(shadow_s, shadow_s.get_rect(center=(rect.centerx + 2, rect.centery + 2)))
    surf.blit(lbl_surf, lbl_rect)
    surf.set_clip(old_clip)

    if hovered:
        glow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for offset in range(1, 5):
            pygame.draw.rect(glow, (*ACCENT, max(0, 30 - offset * 7)),
                             pygame.Rect(-offset, -offset, rect.width + offset * 2, rect.height + offset * 2),
                             border_radius=6 + offset)
        surf.blit(glow, rect.topleft)


def draw_title(surf, alpha=255):
    title_surf = title_font.render("Myst", True, BLANC)
    shadow     = title_font.render("Myst", True, (30, 50, 80))
    sx = LARGEUR // 2 - title_surf.get_width() // 2
    sy = int(HAUTEUR * 0.18)

    shadow_layer = shadow.copy()
    shadow_layer.set_alpha(int(alpha * 0.6))
    surf.blit(shadow_layer, (sx + 5, sy + 8))

    t = title_surf.copy()
    t.set_alpha(alpha)
    surf.blit(t, (sx, sy))

    draw_accent_line(surf, sy + title_surf.get_height() + 6,  alpha=int(alpha * 0.7))
    draw_accent_line(surf, sy + title_surf.get_height() + 10, alpha=int(alpha * 0.35))

    hint = hint_font.render("Plongez dans les ténèbres…", True, (130, 160, 190))
    hint.set_alpha(int(alpha * 0.75))
    surf.blit(hint, (LARGEUR // 2 - hint.get_width() // 2, sy + title_surf.get_height() + 20))


def draw_input_field(surf, input_text, menu_state, alpha=255):
    prompt = "Nom de la salle à REJOINDRE" if menu_state == "join" else "Nom de la salle à HÉBERGER"

    lbl = sub_font.render(prompt, True, ACCENT)
    lbl.set_alpha(alpha)
    surf.blit(lbl, (LARGEUR // 2 - lbl.get_width() // 2, HAUTEUR // 2 - 90))

    hint = hint_font.render("Appuyez sur ENTRÉE pour confirmer  •  ÉCHAP pour revenir", True, (110, 140, 170))
    hint.set_alpha(int(alpha * 0.7))
    surf.blit(hint, (LARGEUR // 2 - hint.get_width() // 2, HAUTEUR // 2 - 48))

    field_rect = pygame.Rect(LARGEUR // 2 - 300, HAUTEUR // 2 - 6, 600, 62)
    field_surf = pygame.Surface((field_rect.width, field_rect.height), pygame.SRCALPHA)
    field_surf.fill((10, 16, 24, int(alpha * 0.88)))
    pygame.draw.rect(field_surf, (*ACCENT, int(alpha * 0.9)), field_surf.get_rect(), 2, border_radius=5)
    surf.blit(field_surf, field_rect.topleft)

    txt = button_font.render(input_text + "|", True, ACCENT_CLAIR)
    txt.set_alpha(alpha)
    surf.blit(txt, (field_rect.x + 18, field_rect.y + 10))


# Stockage des rects du panneau paramétres pour que le clic et l'affichage restent synchrones
_param_rows   = []
_param_retour = None
_param_reset  = None


def draw_parametres(surf, keybinds, waiting_for_key, mouse_pos):
    """Panneau paramétres : touches + volume musique et effets."""
    global _param_rows, _param_retour, _param_reset

    actions   = list(ACTION_LABELS.keys())
    panel_w   = 740
    panel_x   = LARGEUR // 2 - panel_w // 2
    row_h     = 68
    nb_rows   = len(actions)
    SLIDER_W  = 240          # réduit pour laisser la place au % à droite
    SLIDER_H  = 10
    SLIDER_X  = panel_x + panel_w - SLIDER_W - 60  # 60px de marge pour le %
    panel_h   = nb_rows * row_h + 230
    panel_y   = HAUTEUR // 2 - panel_h // 2 - 20

    # Fond du panel
    panel_surf = pygame.Surface((panel_w + 60, panel_h), pygame.SRCALPHA)
    panel_surf.fill((10, 16, 24, 225))
    pygame.draw.rect(panel_surf, (*ACCENT_SOMBRE, 200), panel_surf.get_rect(), 2, border_radius=10)
    surf.blit(panel_surf, (panel_x - 30, panel_y))
    draw_accent_line(surf, panel_y + 8, alpha=100)

    titre = sub_font.render("— Paramètres —", True, ACCENT_CLAIR)
    surf.blit(titre, (LARGEUR // 2 - titre.get_width() // 2, panel_y + 18))

    # ---- Section touches ----
    start_y  = panel_y + 70
    new_rows = []
    for i, action in enumerate(actions):
        y        = start_y + i * row_h
        key_rect = pygame.Rect(panel_x + panel_w - 210, y + 8, 190, 50)

        lbl = sub_font.render(ACTION_LABELS[action], True, (180, 200, 215))
        surf.blit(lbl, (panel_x + 10, y + 14))

        if waiting_for_key == action:
            box_col = (20, 40, 65)
            txt_col = JAUNE
            key_lbl = "Appuye sur une touche…"
        else:
            hov      = key_rect.collidepoint(mouse_pos)
            box_col  = (30, 50, 72) if hov else (12, 20, 30)
            txt_col  = ACCENT_CLAIR
            key_lbl  = pygame.key.name(keybinds.get(action, 0)).upper()

        ks = pygame.Surface((key_rect.width, key_rect.height), pygame.SRCALPHA)
        ks.fill((*box_col, 220))
        pygame.draw.rect(ks, (*ACCENT_SOMBRE, 220), ks.get_rect(), 1, border_radius=4)
        surf.blit(ks, key_rect.topleft)
        k_surf = small_font.render(key_lbl, True, txt_col)
        # Clip pour que le texte ne déborde pas du cadre de touche
        old_clip = surf.get_clip()
        surf.set_clip(key_rect)
        surf.blit(k_surf, k_surf.get_rect(center=key_rect.center))
        surf.set_clip(old_clip)

        new_rows.append({"action": action, "key_rect": key_rect})

    # ---- Section son ----
    sep_y = start_y + nb_rows * row_h + 10
    draw_accent_line(surf, sep_y, alpha=60)
    son_titre = small_font.render("— Son —", True, ACCENT_CLAIR)
    surf.blit(son_titre, (LARGEUR // 2 - son_titre.get_width() // 2, sep_y + 6))

    mus_y = sep_y + 44
    surf.blit(sub_font.render("Musique", True, (180, 200, 215)), (panel_x + 10, mus_y))
    _draw_slider(surf, SLIDER_X, mus_y + 14, SLIDER_W, SLIDER_H, volume_musique, mouse_pos)
    new_rows.append({
        "action":      "__vol_musique__",
        "key_rect":    None,
        "slider_rect": pygame.Rect(SLIDER_X - 5, mus_y + 4, SLIDER_W + 10, SLIDER_H + 20),
        "slider_x":    SLIDER_X, "slider_w": SLIDER_W, "slider_y": mus_y + 14
    })

    sfx_y = mus_y + 52
    surf.blit(sub_font.render("Effets sonores", True, (180, 200, 215)), (panel_x + 10, sfx_y))
    _draw_slider(surf, SLIDER_X, sfx_y + 14, SLIDER_W, SLIDER_H, volume_effets, mouse_pos)
    new_rows.append({
        "action":      "__vol_effets__",
        "key_rect":    None,
        "slider_rect": pygame.Rect(SLIDER_X - 5, sfx_y + 4, SLIDER_W + 10, SLIDER_H + 20),
        "slider_x":    SLIDER_X, "slider_w": SLIDER_W, "slider_y": sfx_y + 14
    })

    # Boutons juste en dessous du panel, pas dedans
    btns_y  = panel_y + panel_h + 10
    btn_x0  = panel_x
    btn_tot = panel_w
    demi    = btn_tot // 2 - 6
    retour_btn = {"label": "Retour",  "rect": pygame.Rect(btn_x0,             btns_y, demi, BTN_H)}
    reset_btn  = {"label": "Réinit.", "rect": pygame.Rect(btn_x0 + demi + 12, btns_y, demi, BTN_H)}

    draw_button(surf, retour_btn, hovered=retour_btn["rect"].collidepoint(mouse_pos))
    draw_button(surf, reset_btn,  hovered=reset_btn["rect"].collidepoint(mouse_pos))

    # Mise à jour des globaux en une seule fois à la fin
    _param_rows   = new_rows
    _param_retour = retour_btn
    _param_reset  = reset_btn

    return new_rows, retour_btn, reset_btn


def _draw_slider(surf, x, y, w, h, valeur, mouse_pos):
    """Dessine un slider horizontal avec la valeur entre 0 et 1."""
    # Fond
    pygame.draw.rect(surf, (12, 20, 30), (x, y, w, h), border_radius=4)
    pygame.draw.rect(surf, ACCENT_SOMBRE, (x, y, w, h), 1, border_radius=4)
    # Rempli
    fill_w = int(w * valeur)
    if fill_w > 0:
        pygame.draw.rect(surf, ACCENT, (x, y, fill_w, h), border_radius=4)
    # Curseur
    cx = x + fill_w
    cy = y + h // 2
    pygame.draw.circle(surf, ACCENT_CLAIR, (cx, cy), h + 2)
    pygame.draw.circle(surf, (5, 8, 12), (cx, cy), h + 2, 1)
    # Valeur en %
    pct  = small_font.render(f"{int(valeur * 100)}%", True, ACCENT_CLAIR)
    surf.blit(pct, (x + w + 10, y - 4))


menu_state           = "main"
input_text           = ""
error_msg            = ""
error_timer          = 0
click_feedback_btn   = None
click_feedback_timer = 0
keybinds             = load_keybinds()
waiting_for_key      = None

# Volumes : musique (0.0 - 1.0) et effets sonores
volume_musique = 0.15
volume_effets  = 0.5

def apply_volumes():
    try:
        pygame.mixer.music.set_volume(volume_musique)
    except: pass

def save_settings():
    try:
        data = load_keybinds()
        with open(KEYBINDS_FILE, "r") as f:
            existing = json.load(f)
    except:
        existing = {}
    existing.update({k: int(v) for k, v in keybinds.items()})
    existing["vol_musique"] = volume_musique
    existing["vol_effets"]  = volume_effets
    with open(KEYBINDS_FILE, "w") as f:
        json.dump(existing, f)

def load_settings():
    global volume_musique, volume_effets
    if os.path.exists(KEYBINDS_FILE):
        try:
            with open(KEYBINDS_FILE, "r") as f:
                data = json.load(f)
            volume_musique = float(data.get("vol_musique", 0.15))
            volume_effets  = float(data.get("vol_effets",  0.5))
        except:
            pass


def play_menu_music():
    try:
        pygame.mixer.music.load("assets/sound/music_menu.mp3")
        pygame.mixer.music.set_volume(volume_musique)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"[MENU] Erreur chargement musique : {e}")


def draw_menu():
    global error_msg, error_timer, click_feedback_btn, click_feedback_timer

    screen.fill(GRIS_FONCE)
    if not video.active:
        video.restart()
    video.draw(screen, (0, 0))
    screen.blit(vignette_surf, (0, 0))

    for ember in EMBERS:
        ember.update()
        ember.draw(screen)

    # Le titre n'est affiché que sur les écrans principaux, pas dans les paramétres
    if menu_state != "parametres":
        draw_title(screen)

    current_time = time.time()
    mouse_pos    = pygame.mouse.get_pos()

    if menu_state == "main":
        for btn in boutons:
            hovered = btn["rect"].collidepoint(mouse_pos)
            clicked = (click_feedback_btn == btn and current_time < click_feedback_timer)
            draw_button(screen, btn, hovered=hovered, clicked=clicked)

    elif menu_state == "online":
        for btn in online_buttons:
            hovered = btn["rect"].collidepoint(mouse_pos)
            clicked = (click_feedback_btn == btn and current_time < click_feedback_timer)
            draw_button(screen, btn, hovered=hovered, clicked=clicked)

    elif menu_state in ["join", "host_setup"]:
        draw_input_field(screen, input_text, menu_state)
        btn     = online_buttons[2]
        hovered = btn["rect"].collidepoint(mouse_pos)
        clicked = (click_feedback_btn == btn and current_time < click_feedback_timer)
        draw_button(screen, btn, hovered=hovered, clicked=clicked)

    elif menu_state == "parametres":
        draw_parametres(screen, keybinds, waiting_for_key, mouse_pos)

    if error_msg and time.time() < error_timer:
        col      = AMBRE if "Recherche" in error_msg else ROUGE_ERR
        err_surf = sub_font.render(error_msg, True, col)
        pad      = 14
        bg       = pygame.Surface((err_surf.get_width() + pad * 2, err_surf.get_height() + pad), pygame.SRCALPHA)
        bg.fill((8, 12, 18, 180))
        screen.blit(bg,       (LARGEUR // 2 - bg.get_width()       // 2, HAUTEUR // 2 + 230))
        screen.blit(err_surf, (LARGEUR // 2 - err_surf.get_width() // 2, HAUTEUR // 2 + 238))
    elif error_msg:
        error_msg = ""

    pygame.display.flip()


def main():
    clock = pygame.time.Clock()
    global menu_state, input_text, error_msg, error_timer
    global click_feedback_btn, click_feedback_timer, keybinds, waiting_for_key
    global volume_musique, volume_effets

    load_settings()
    play_menu_music()

    dragging_slider = None  # "__vol_musique__" ou "__vol_effets__"

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitgame()

            # Relachement slider
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging_slider:
                    save_settings()
                    dragging_slider = None

            # Glissement slider en cours
            if event.type == pygame.MOUSEMOTION and dragging_slider:
                for row in _param_rows:
                    if row.get("action") == dragging_slider:
                        sx  = row["slider_x"]
                        sw  = row["slider_w"]
                        val = max(0.0, min(1.0, (event.pos[0] - sx) / sw))
                        if dragging_slider == "__vol_musique__":
                            volume_musique = round(val, 2)
                            apply_volumes()
                        else:
                            volume_effets = round(val, 2)
                        break

            # Capture d'une nouvelle touche dans les paramétres
            elif event.type == pygame.KEYDOWN and menu_state == "parametres" and waiting_for_key:
                if event.key == pygame.K_ESCAPE:
                    waiting_for_key = None
                else:
                    keybinds[waiting_for_key] = event.key
                    save_keybinds(keybinds)
                    waiting_for_key = None
                continue

            elif event.type == pygame.KEYDOWN and menu_state in ["join", "host_setup"]:
                if event.key == pygame.K_RETURN:
                    if input_text.strip():
                        success = True
                        if menu_state == "host_setup":
                            res = game.game(is_host=True, is_solo=False, room_name=input_text)
                            while res == "retry":
                                time.sleep(0.5)
                                res = game.game(is_host=True, is_solo=False, room_name=input_text)
                        else:
                            error_msg   = "Recherche de la salle en cours…"
                            error_timer = time.time() + 10
                            draw_menu()
                            res         = game.game(is_host=False, room_name=input_text)
                            retry_count = 0
                            while res == "retry" or (res is False and retry_count < 10):
                                time.sleep(1.0)
                                res = game.game(is_host=False, room_name=input_text)
                                if res is not False and res != "retry":
                                    break
                                retry_count += 1
                            if res is False:
                                error_msg   = f"Salle introuvable : « {input_text} »"
                                error_timer = time.time() + 3.5
                                success     = False
                        if success:
                            pygame.display.set_mode((LARGEUR, HAUTEUR), pygame.FULLSCREEN)
                            play_menu_music()
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    menu_state = "online"
                else:
                    if event.unicode.isalnum() or event.unicode in "_- ":
                        input_text += event.unicode

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if menu_state == "main":
                    for btn in boutons:
                        if btn["rect"].collidepoint(pos):
                            click_feedback_btn   = btn
                            click_feedback_timer = time.time() + 0.12
                            draw_menu()
                            pygame.display.flip()
                            time.sleep(0.05)
                            if btn["label"] == "Solo":
                                res = game.game(is_host=True, is_solo=True)
                                while res == "retry":
                                    time.sleep(0.5)
                                    res = game.game(is_host=True, is_solo=True)
                                pygame.display.set_mode((LARGEUR, HAUTEUR), pygame.FULLSCREEN)
                                play_menu_music()
                            elif btn["label"] == "En ligne":
                                menu_state = "online"
                            elif btn["label"] == "Paramètres":
                                menu_state      = "parametres"
                                waiting_for_key = None
                            elif btn["label"] == "Quitter":
                                quitgame()

                elif menu_state == "online":
                    for btn in online_buttons:
                        if btn["rect"].collidepoint(pos):
                            click_feedback_btn   = btn
                            click_feedback_timer = time.time() + 0.12
                            draw_menu()
                            pygame.display.flip()
                            time.sleep(0.05)
                            if btn["label"] == "Host":
                                input_text = ""
                                menu_state = "host_setup"
                            elif btn["label"] == "Rejoindre":
                                input_text = ""
                                menu_state = "join"
                            elif btn["label"] == "Retour":
                                menu_state = "main"

                elif menu_state in ["join", "host_setup"]:
                    btn = online_buttons[2]
                    if btn["rect"].collidepoint(pos):
                        click_feedback_btn   = btn
                        click_feedback_timer = time.time() + 0.12
                        draw_menu()
                        pygame.display.flip()
                        time.sleep(0.05)
                        menu_state = "online"

                elif menu_state == "parametres":
                    clicked_row = False
                    for row in _param_rows:
                        action = row.get("action", "")
                        # Clic sur un slider de volume
                        if action in ("__vol_musique__", "__vol_effets__"):
                            sr = row.get("slider_rect")
                            if sr and sr.collidepoint(pos):
                                dragging_slider = action
                                sx  = row["slider_x"]
                                sw  = row["slider_w"]
                                val = max(0.0, min(1.0, (pos[0] - sx) / sw))
                                if action == "__vol_musique__":
                                    volume_musique = round(val, 2)
                                    apply_volumes()
                                else:
                                    volume_effets = round(val, 2)
                                clicked_row = True
                                break
                        # Clic sur une touche
                        elif row.get("key_rect") and row["key_rect"].collidepoint(pos):
                            waiting_for_key = action
                            clicked_row     = True
                            break

                    if not clicked_row:
                        if _param_retour and _param_retour["rect"].collidepoint(pos):
                            waiting_for_key = None
                            menu_state      = "main"
                            save_settings()
                        elif _param_reset and _param_reset["rect"].collidepoint(pos):
                            keybinds       = DEFAULT_KEYBINDS.copy()
                            volume_musique = 0.15
                            volume_effets  = 0.5
                            save_keybinds(keybinds)
                            save_settings()
                            apply_volumes()
                            waiting_for_key = None

        draw_menu()
        clock.tick(60)


if __name__ == "__main__":
    main()
