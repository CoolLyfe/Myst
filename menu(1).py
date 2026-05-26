import pygame
import sys
import game
import pyvidplayer
import time
import math
import random

pygame.init()

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

# Palette
NOIR          = (0, 0, 0)
BLANC         = (255, 255, 255)
OR            = (212, 175, 55)
OR_CLAIR      = (255, 215, 80)
OR_SOMBRE     = (140, 110, 20)
ROUGE_FEU     = (200, 60, 10)
AMBRE         = (255, 160, 30)
GRIS_FONCE    = (18, 14, 10)
ROUGE_ERR     = (220, 60, 40)
BLANC_ALPHA   = (255, 255, 255, 200)

# Fonts
try:
    title_font  = pygame.font.SysFont("Chiller",  220, bold=True)
    button_font = pygame.font.SysFont("Chiller",   62, bold=False)
    sub_font    = pygame.font.SysFont("Chiller",   38)
    hint_font   = pygame.font.SysFont("Garamond",  28, italic=True)
except:
    title_font  = pygame.font.SysFont(None, 220, bold=True)
    button_font = pygame.font.SysFont(None,  62)
    sub_font    = pygame.font.SysFont(None,  38)
    hint_font   = pygame.font.SysFont(None,  28)

# Dimensions boutons
BTN_W  = 480
BTN_H  = 72
GAP    = 18
BLOC_Y = HAUTEUR // 2 + 20   # point de départ vertical des boutons

# --- Définition des boutons ---
def make_btn(label, row):
    x = LARGEUR // 2 - BTN_W // 2
    y = BLOC_Y + row * (BTN_H + GAP)
    return {"label": label, "rect": pygame.Rect(x, y, BTN_W, BTN_H)}

def make_btn_half(label, row, side):
    half_w = BTN_W // 2 - 8
    x = (LARGEUR // 2 - BTN_W // 2) if side == "left" else (LARGEUR // 2 + 8)
    y = BLOC_Y + row * (BTN_H + GAP)
    return {"label": label, "rect": pygame.Rect(x, y, half_w, BTN_H)}

boutons = [
    make_btn("Solo",         0),
    make_btn("En ligne",     1),
    make_btn_half("Notre équipe", 2, "left"),
    make_btn_half("Paramètres",   2, "right"),
    make_btn("Quitter",      3),
]

online_buttons = [
    make_btn("Host",      0),
    make_btn("Rejoindre", 1),
    make_btn("Retour",    3),
]

# --- Particules de braises ---
class Ember:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x   = random.uniform(0, LARGEUR)
        self.y   = random.uniform(HAUTEUR * 0.4, HAUTEUR + 20)
        self.vx  = random.uniform(-0.6, 0.6)
        self.vy  = random.uniform(-1.8, -0.5)
        self.life = random.uniform(0.4, 1.0)
        self.decay = random.uniform(0.003, 0.007)
        self.r   = random.uniform(1.5, 3.5)
        self.col = random.choice([
            (255, 140, 0), (255, 80, 0), (255, 200, 50), (200, 50, 10)
        ])

    def update(self):
        self.x   += self.vx + math.sin(self.y * 0.01) * 0.3
        self.y   += self.vy
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

# --- Overlay sombre dégradé vertical ---
def make_vignette():
    surf = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
    # Bande sombre en haut et en bas pour encadrer
    for i in range(HAUTEUR):
        t_top    = max(0, 1 - i / (HAUTEUR * 0.45))
        t_bottom = max(0, (i - HAUTEUR * 0.55) / (HAUTEUR * 0.45))
        alpha    = int(min(1.0, t_top * 1.4 + t_bottom * 1.2) * 200)
        if alpha > 0:
            pygame.draw.line(surf, (0, 0, 0, alpha), (0, i), (LARGEUR, i))
    return surf

vignette_surf = make_vignette()

# --- Séparateur doré ---
def draw_gold_line(surf, y, alpha=160):
    line_surf = pygame.Surface((BTN_W, 2), pygame.SRCALPHA)
    cx = BTN_W // 2
    for px in range(BTN_W):
        t = 1 - abs(px - cx) / cx
        a = int(t * alpha)
        pygame.draw.line(line_surf, (*OR, a), (px, 0), (px, 1))
    surf.blit(line_surf, (LARGEUR // 2 - BTN_W // 2, y))

# --- Dessin d'un bouton ---
def draw_button(surf, btn, hovered=False, clicked=False, alpha_mult=1.0):
    rect   = btn["rect"]
    label  = btn["label"]

    # Fond semi-transparent
    if clicked:
        bg_alpha = int(200 * alpha_mult)
        bg_color = (180, 130, 30, bg_alpha)
        border_col = OR_CLAIR
        border_w   = 3
    elif hovered:
        bg_alpha = int(160 * alpha_mult)
        bg_color = (60, 40, 10, bg_alpha)
        border_col = OR
        border_w   = 2
    else:
        bg_alpha = int(100 * alpha_mult)
        bg_color = (20, 14, 8, bg_alpha)
        border_col = OR_SOMBRE
        border_w   = 1

    btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(btn_surf, bg_color, btn_surf.get_rect(), border_radius=6)
    # Bord supérieur OR plus lumineux
    pygame.draw.rect(btn_surf, (*border_col, 220), btn_surf.get_rect(), border_w, border_radius=6)

    # Reflet subtil en haut
    if hovered or clicked:
        shine = pygame.Surface((rect.width - 4, rect.height // 3), pygame.SRCALPHA)
        shine.fill((255, 200, 80, 18))
        btn_surf.blit(shine, (2, 2))

    surf.blit(btn_surf, rect.topleft)

    # Texte
    text_col = OR_CLAIR if (hovered or clicked) else (210, 200, 180)
    lbl_surf = button_font.render(label, True, text_col)

    # Ombre légère
    shadow_surf = button_font.render(label, True, (10, 5, 0))
    lbl_rect    = lbl_surf.get_rect(center=rect.center)
    surf.blit(shadow_surf, (lbl_rect.x + 2, lbl_rect.y + 2))
    surf.blit(lbl_surf,     lbl_rect)

    # Lueur dorée au hover
    if hovered:
        glow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for offset in range(1, 5):
            pygame.draw.rect(glow, (*OR, max(0, 30 - offset * 7)),
                             pygame.Rect(-offset, -offset, rect.width + offset*2, rect.height + offset*2),
                             border_radius=6 + offset)
        surf.blit(glow, rect.topleft)

# --- Titre avec ombre et reflet ---
def draw_title(surf, alpha=255):
    title_surf = title_font.render("Myst", True, BLANC)
    # Ombre profonde
    shadow     = title_font.render("Myst", True, (80, 20, 0))
    sx = LARGEUR // 2 - title_surf.get_width() // 2
    sy = int(HAUTEUR * 0.18)

    shadow_layer = shadow.copy()
    shadow_layer.set_alpha(int(alpha * 0.6))
    surf.blit(shadow_layer, (sx + 5, sy + 8))

    # Titre principal
    t = title_surf.copy()
    t.set_alpha(alpha)
    surf.blit(t, (sx, sy))

    # Reflet OR sous le titre
    draw_gold_line(surf, sy + title_surf.get_height() + 6, alpha=int(alpha * 0.7))
    draw_gold_line(surf, sy + title_surf.get_height() + 10, alpha=int(alpha * 0.35))

    # Sous-titre mystérieux
    hint = hint_font.render("Plongez dans les ténèbres…", True, (180, 150, 80))
    hint.set_alpha(int(alpha * 0.75))
    surf.blit(hint, (LARGEUR // 2 - hint.get_width() // 2, sy + title_surf.get_height() + 20))

# --- Champ de saisie ---
def draw_input_field(surf, input_text, menu_state, alpha=255):
    prompt = "Nom de la salle à REJOINDRE" if menu_state == "join" else "Nom de la salle à HÉBERGER"

    # Label
    lbl = sub_font.render(prompt, True, OR)
    lbl.set_alpha(alpha)
    surf.blit(lbl, (LARGEUR // 2 - lbl.get_width() // 2, HAUTEUR // 2 - 90))

    hint = hint_font.render("Appuyez sur ENTRÉE pour confirmer  •  ÉCHAP pour revenir", True, (140, 120, 80))
    hint.set_alpha(int(alpha * 0.7))
    surf.blit(hint, (LARGEUR // 2 - hint.get_width() // 2, HAUTEUR // 2 - 48))

    # Champ
    field_rect = pygame.Rect(LARGEUR // 2 - 300, HAUTEUR // 2 - 6, 600, 62)
    field_surf = pygame.Surface((field_rect.width, field_rect.height), pygame.SRCALPHA)
    field_surf.fill((20, 14, 8, int(alpha * 0.85)))
    pygame.draw.rect(field_surf, (*OR, int(alpha * 0.9)), field_surf.get_rect(), 2, border_radius=5)
    surf.blit(field_surf, field_rect.topleft)

    txt = button_font.render(input_text + "|", True, OR_CLAIR)
    txt.set_alpha(alpha)
    surf.blit(txt, (field_rect.x + 18, field_rect.y + 10))

# État
menu_state         = "main"
input_text         = ""
error_msg          = ""
error_timer        = 0
click_feedback_btn = None
click_feedback_timer = 0
transition_alpha   = 255   # pour les fondus
prev_state         = None

def draw_menu():
    global error_msg, error_timer, click_feedback_btn, click_feedback_timer

    screen.fill(GRIS_FONCE)

    # Vidéo de fond
    if not video.active:
        video.restart()
    video.draw(screen, (0, 0))

    # Vignette sombre
    screen.blit(vignette_surf, (0, 0))

    # Braises
    for ember in EMBERS:
        ember.update()
        ember.draw(screen)

    # Titre
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
        btn = online_buttons[2]  # Retour
        hovered = btn["rect"].collidepoint(mouse_pos)
        clicked = (click_feedback_btn == btn and current_time < click_feedback_timer)
        draw_button(screen, btn, hovered=hovered, clicked=clicked)

    # Message d'erreur / info
    if error_msg and time.time() < error_timer:
        col = AMBRE if "Searching" in error_msg else ROUGE_ERR
        err_surf = sub_font.render(error_msg, True, col)
        # Fond semi-transparent derrière le message
        pad = 14
        bg  = pygame.Surface((err_surf.get_width() + pad * 2, err_surf.get_height() + pad), pygame.SRCALPHA)
        bg.fill((10, 5, 0, 160))
        screen.blit(bg, (LARGEUR // 2 - bg.get_width() // 2, HAUTEUR // 2 + 230))
        screen.blit(err_surf, (LARGEUR // 2 - err_surf.get_width() // 2, HAUTEUR // 2 + 238))
    elif error_msg:
        error_msg = ""

    pygame.display.flip()


def main():
    clock = pygame.time.Clock()
    global menu_state, input_text, error_msg, error_timer, click_feedback_btn, click_feedback_timer

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quitgame()

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
                            elif btn["label"] == "En ligne":
                                menu_state = "online"
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

                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    menu_state = "online"
                else:
                    if event.unicode.isalnum() or event.unicode in "_- ":
                        input_text += event.unicode

        draw_menu()
        clock.tick(60)

if __name__ == "__main__":
    main()
