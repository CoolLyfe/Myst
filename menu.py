import pygame
import sys
import game
import pyvidplayer

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
# Definition des dimensions du menu + affichage  du nom

GRIS = (100, 100, 100)
NOIR = (0, 0, 0)
BLANC = (255, 255, 255)
# Definition des couleurs pour le menu ( Ajouter en plus si besoin )

title_font = pygame.font.SysFont("Chiller", 1500, bold=True, italic=True)
button_font = pygame.font.SysFont("Chiller", 50)
# Definition de la police pour le text des bouttons ( Police,  taille, gras, italique)


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
# Caracteristiques des boutons ( label = texte, rect = position + taille, (x, y, largeur, hauteur) )


def draw_menu():
    video.draw(screen, (0, 0))
    # Def fonction qui affiche le menu + remplissage du fond en gris ( jcrois on peut mettre un .png pour le fond a la  place du gris )

    title_surf = title_font.render("Myst", True, BLANC)
    title_scaled = pygame.transform.scale(title_surf, (LARGEUR // 3, HAUTEUR // 5))
    screen.blit(title_scaled, (LARGEUR // 2 - title_scaled.get_width() // 2, HAUTEUR // 4 - title_scaled.get_height() // 2))
    # Apparition du Titre ( creation, centrer au milieu de la page, afficher le titre )

    if menu_state == "main":
        active_buttons = boutons
    else:
        active_buttons = online_buttons

    for btn in active_buttons:
        pygame.draw.rect(screen, NOIR, btn["rect"])
        label_surf = button_font.render(btn["label"], True, BLANC)
        label_rect = label_surf.get_rect(center=btn["rect"].center)
        screen.blit(label_surf, label_rect)
        # Apparition de chaque bouton en fonction des coordonees definis avant

    pygame.display.flip()

def main():
    # Fonction principale pour faire tourner  le menu en boucle et recuperer les cliques
    clock = pygame.time.Clock()
    #  Setup d'un FPS cap pour le menu

    global menu_state

    while True:
        for event in pygame.event.get():
            # Recupere tous les cliques/touches appuyer
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                # Ferme le menu/jeu si on clique sur la croix/quitter
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                # Recupere la position du clique pour verifier si il est sur un bouton
                if menu_state == "main":
                    active_buttons = boutons
                else:
                    active_buttons = online_buttons

                for btn in active_buttons:
                    if btn["rect"].collidepoint(pos):
                        print(f"Clicked: {btn['label']}")
                        if menu_state == "main":
                            if btn["label"] == "Solo":
                                game.game(is_host=True, is_solo=True)
                                # We need to restore the menu screen after game returns
                                pygame.display.set_mode((LARGEUR, HAUTEUR), pygame.FULLSCREEN)
                            elif btn["label"] == "En ligne":
                                menu_state = "online"
                            elif btn["label"] == "Quitter":
                                quitgame()
                        else:
                            if btn["label"] == "Host":
                                game.game(is_host=True, is_solo=False)
                                pygame.display.set_mode((LARGEUR, HAUTEUR), pygame.FULLSCREEN)
                            elif btn["label"] == "Rejoindre":
                                ip = input("Enter Server IP (default 127.0.0.1): ") or "127.0.0.1"
                                game.game(is_host=False, server_ip=ip)
                                pygame.display.set_mode((LARGEUR, HAUTEUR), pygame.FULLSCREEN)
                            elif btn["label"] == "Retour":
                                menu_state = "main"
        draw_menu()
        clock.tick(60)
        # Fait tourner le menu a 60 fps


if __name__ == "__main__":
    main()
