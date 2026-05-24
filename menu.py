import pygame
import sys
import game
import pyvidplayer
import time

pygame.init()
def quitgame():
    pygame.quit()
    if 'video' in globals() and video is not None:
        video.close()
    sys.exit()

video = pyvidplayer.Video("assets/fire_background.mp4")
video.set_size((1920, 1080))
LARGEUR, HAUTEUR = 1920, 1080
screen = pygame.display.set_mode((LARGEUR, HAUTEUR), pygame.FULLSCREEN)
pygame.display.set_caption("Myst")

GRIS = (100, 100, 100)
NOIR = (0, 0, 0)
BLANC = (255, 255, 255)
ROUGE = (200, 50, 50)

title_font = pygame.font.SysFont("Chiller", 1500, bold=True, italic=True)
button_font = pygame.font.SysFont("Chiller", 50)

boutons = [
    {"label": "Solo", "rect": pygame.Rect(LARGEUR // 2 - LARGEUR // 6, HAUTEUR // 2, LARGEUR // 3, HAUTEUR // 8)},
    {"label": "En ligne", "rect": pygame.Rect(LARGEUR // 2 - LARGEUR // 6, (HAUTEUR // 4) * 3 - 5, LARGEUR // 3, HAUTEUR // 12)},
    {"label": "Notre équipe", "rect": pygame.Rect(LARGEUR // 4 - LARGEUR // 16, (HAUTEUR // 4) * 3, LARGEUR // 8, HAUTEUR // 12)},
    {"label": "Paramètres", "rect": pygame.Rect((LARGEUR // 4)*3 - LARGEUR // 16, (HAUTEUR // 4) * 3, LARGEUR // 8, HAUTEUR // 12)},
    {"label": "Quitter", "rect": pygame.Rect(LARGEUR // 2 - LARGEUR // 16, (HAUTEUR // 8) * 7, LARGEUR // 8, HAUTEUR // 12)},
]

online_buttons = [
    {"label": "Host", "rect": pygame.Rect(LARGEUR // 2 - LARGEUR // 6, HAUTEUR // 2 - HAUTEUR // 12, LARGEUR // 3, HAUTEUR // 10)},
    {"label": "Rejoindre", "rect": pygame.Rect(LARGEUR // 2 - LARGEUR // 6, HAUTEUR // 2 + HAUTEUR // 12, LARGEUR // 3, HAUTEUR // 10)},
    {"label": "Retour", "rect": pygame.Rect(LARGEUR // 2 - LARGEUR // 8, (HAUTEUR // 8) * 7, LARGEUR // 4, HAUTEUR // 12)},
]

menu_state = "main"
input_text = ""
error_msg = ""
error_timer = 0

def draw_menu():
    global error_msg, error_timer
    video.draw(screen, (0, 0))

    title_surf = title_font.render("Myst", True, BLANC)
    title_scaled = pygame.transform.scale(title_surf, (LARGEUR // 3, HAUTEUR // 5))
    screen.blit(title_scaled, (LARGEUR // 2 - title_scaled.get_width() // 2, HAUTEUR // 4 - title_scaled.get_height() // 2))

    if menu_state == "main":
        for btn in boutons:
            pygame.draw.rect(screen, NOIR, btn["rect"])
            label_surf = button_font.render(btn["label"], True, BLANC)
            label_rect = label_surf.get_rect(center=btn["rect"].center)
            screen.blit(label_surf, label_rect)
    elif menu_state == "online":
        for btn in online_buttons:
            pygame.draw.rect(screen, NOIR, btn["rect"])
            label_surf = button_font.render(btn["label"], True, BLANC)
            label_rect = label_surf.get_rect(center=btn["rect"].center)
            screen.blit(label_surf, label_rect)
    elif menu_state in ["join", "host_setup"]:
        input_rect = pygame.Rect(LARGEUR // 2 - 300, HAUTEUR // 2 - 25, 600, 60)
        pygame.draw.rect(screen, NOIR, input_rect)
        pygame.draw.rect(screen, BLANC, input_rect, 2)
        
        txt_surf = button_font.render(input_text, True, BLANC)
        screen.blit(txt_surf, (input_rect.x + 20, input_rect.y + 10))
        
        prompt = "Enter Room Name to JOIN" if menu_state == "join" else "Enter Room Name to HOST"
        instr_surf = button_font.render(f"{prompt} and press ENTER", True, BLANC)
        screen.blit(instr_surf, (LARGEUR // 2 - instr_surf.get_width() // 2, HAUTEUR // 2 - 100))

        btn = online_buttons[2] # Retour
        pygame.draw.rect(screen, NOIR, btn["rect"])
        label_surf = button_font.render(btn["label"], True, BLANC)
        label_rect = label_surf.get_rect(center=btn["rect"].center)
        screen.blit(label_surf, label_rect)

    # Error message display
    if error_msg and time.time() < error_timer:
        err_surf = button_font.render(error_msg, True, ROUGE)
        screen.blit(err_surf, (LARGEUR // 2 - err_surf.get_width() // 2, HAUTEUR // 2 + 215))
    elif error_msg:
        error_msg = ""

    pygame.display.flip()

def main():
    clock = pygame.time.Clock()
    global menu_state, input_text, error_msg, error_timer

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if menu_state == "main":
                    for btn in boutons:
                        if btn["rect"].collidepoint(pos):
                            if btn["label"] == "Solo":
                                game.game(is_host=True, is_solo=True)
                                pygame.display.set_mode((LARGEUR, HAUTEUR), pygame.FULLSCREEN)
                            elif btn["label"] == "En ligne":
                                menu_state = "online"
                            elif btn["label"] == "Quitter":
                                quitgame()
                elif menu_state == "online":
                    for btn in online_buttons:
                        if btn["rect"].collidepoint(pos):
                            if btn["label"] == "Host":
                                input_text = ""
                                menu_state = "host_setup"
                            elif btn["label"] == "Rejoindre":
                                input_text = ""
                                menu_state = "join"
                            elif btn["label"] == "Retour":
                                menu_state = "main"
                elif menu_state in ["join", "host_setup"]:
                    if online_buttons[2]["rect"].collidepoint(pos):
                        menu_state = "online"
            
            elif event.type == pygame.KEYDOWN and menu_state in ["join", "host_setup"]:
                if event.key == pygame.K_RETURN:
                    if input_text.strip():
                        success = True
                        if menu_state == "host_setup":
                            game.game(is_host=True, is_solo=False, room_name=input_text)
                        else:
                            # Show "Searching..." feedback?
                            error_msg = "Searching for room..."
                            error_timer = time.time() + 10 # Temporary message
                            draw_menu() # Force update
                            
                            res = game.game(is_host=False, room_name=input_text)
                            if res is False:
                                error_msg = f"Error: Room '{input_text}' not found!"
                                error_timer = time.time() + 3.0
                                success = False
                        
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
