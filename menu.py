import pygame
import sys

pygame.init()

LARGEUR, HAUTEUR = 600, 450
screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Myst")

GRIS = (100, 100, 100)
NOIR = (0, 0, 0)
BLANC = (255, 255, 255)

title_font = pygame.font.SysFont("Chiller", 64, bold=True, italic=True)
button_font = pygame.font.SysFont("Chiller", 28)

boutons = [{"label": "Solo", "rect": pygame.Rect(175, 150, 250, 55)},
    {"label": "En ligne", "rect": pygame.Rect(175, 230, 250, 55)},
    {"label": "Notre équipe", "rect": pygame.Rect(60,  320, 160, 45)},
    {"label": "Paramètres", "rect": pygame.Rect(380, 320, 160, 45)},]

def draw_menu():
    screen.fill(GRIS)

    title_surf = title_font.render("Myst", True, NOIR)
    title_rect = title_surf.get_rect(center=(LARGEUR // 2, 75))
    screen.blit(title_surf, title_rect)

    for btn in boutons:
        pygame.draw.rect(screen, NOIR, btn["rect"])
        label_surf = button_font.render(btn["label"], True, BLANC)
        label_rect = label_surf.get_rect(center=btn["rect"].center)
        screen.blit(label_surf, label_rect)

    pygame.display.flip()

def main():
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                for btn in boutons:
                    if btn["rect"].collidepoint(pos):
                        print(f"Clicked: {btn['label']}")
        draw_menu()
        clock.tick(60)

if __name__ == "__main__":
    main()
