import pygame
import sys

pygame.init()

LARGEUR, HAUTEUR = 600, 450
screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Myst")
# Definition des dimensions du menu + affichage  du nom

GRIS = (100, 100, 100)
NOIR = (0, 0, 0)
BLANC = (255, 255, 255)
# Definition des couleurs pour le menu ( Ajouter en plus si besoin )

title_font = pygame.font.SysFont("Chiller", 64, bold=True, italic=True)
button_font = pygame.font.SysFont("Chiller", 28)
# Definition de la police pour le text des bouttons ( Police,  taille, gras, italique)

boutons = [{"label": "Solo", "rect": pygame.Rect(175, 150, 250, 55)},
    {"label": "En ligne", "rect": pygame.Rect(175, 230, 250, 55)},
    {"label": "Notre équipe", "rect": pygame.Rect(60,  320, 160, 45)},
    {"label": "Paramètres", "rect": pygame.Rect(380, 320, 160, 45)},
    {"label": "Quitter", "rect": pygame.Rect(220, 380, 160, 45)},]
# Caracteristiques des boutons ( label = texte, rect = position + taille, (x, y, largeur, hauteur) )

def draw_menu():
    screen.fill(GRIS)
    # Def fonction qui affiche le menu + remplissage du fond en gris ( jcrois on peut mettre un .png pour le fond a la  place du gris )

    title_surf = title_font.render("Myst", True, NOIR)
    title_rect = title_surf.get_rect(center=(LARGEUR // 2, 75))
    screen.blit(title_surf, title_rect)
    # Apparition du Titre ( creation, centrer au milieu de la page, afficher le titre )

    for btn in boutons:
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

    while True:
        for event in pygame.event.get():
            # Recupere tous les cliques/touches appuyer
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                # Ferme le menu/jeu si on clique sur la croix/quitter

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                # Recupere la position du clique pour verifier si il est sur un bouton
                for btn in boutons:
                    if btn["rect"].collidepoint(pos):
                        print(f"Clicked: {btn['label']}")
                        # Verifie si le clique correspond aux coordonees d'un bouton
                        # Ajouter un "return FONCTION" a la place  du "{btn['label']}" pour lancer des fonctions avec les boutons
                        if btn["label"] == "Quitter":
                            pygame.quit()
                            sys.exit()
        draw_menu()
        clock.tick(60)
        # Fait tourner le menu a 60 fps

if __name__ == "__main__":
    main()
