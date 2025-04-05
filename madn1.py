import pygame
import random

pygame.init()

# Spielkonstanten
WIDTH, HEIGHT = 800, 800
GRID_SIZE = 60
FPS = 30

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Fenster initialisieren
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mensch ärgere dich nicht")
clock = pygame.time.Clock()

# Startpositionen und Pfade
start_positions = {
    "Mensch": [(100, 700), (160, 700), (100, 760), (160, 760)],
    "Bot 1": [(640, 100), (700, 100), (640, 160), (700, 160)],
    "Bot 2": [(100, 100), (160, 100), (100, 160), (160, 160)],
    "Bot 3": [(640, 700), (700, 700), (640, 760), (700, 760)]
}

path = [(400, 760), (400, 700), (400, 640), (400, 580), (400, 520),
        (340, 460), (280, 460), (220, 460), (160, 460), (100, 460),
        (100, 400), (100, 340), (100, 280), (100, 220), (100, 160),
        (160, 160), (220, 160), (280, 160), (340, 160), (400, 160),
        (460, 160), (520, 160), (580, 160), (640, 160), (700, 160),
        (700, 220), (700, 280), (700, 340), (700, 400), (700, 460),
        (640, 460), (580, 460), (520, 460), (460, 460), (400, 520),
        (400, 580), (400, 640), (400, 700), (400, 760)]

# Spielfiguren
pawns = {player: [pygame.Rect(pos[0], pos[1], 50, 50) for pos in start_positions[player]] for player in start_positions}

# Spielvariablen
players = ["Mensch", "Bot 1", "Bot 2", "Bot 3"]
current_player = 0
dice_result = None
turn_active = False
selected_pawn = None

running = True
while running:
    screen.fill(WHITE)
    
    # Spielfeld zeichnen
    for i in range(15):
        for j in range(15):
            if (i, j) not in [(7, 0), (7, 1), (7, 13), (7, 14), (0, 7), (1, 7), (13, 7), (14, 7)]:
                x, y = 100 + i * 40, 100 + j * 40
                pygame.draw.rect(screen, BLACK, (x, y, GRID_SIZE, GRID_SIZE), 1)
    
    # Spielfiguren zeichnen
    for player, pawn_list in pawns.items():
        color = RED if player == "Mensch" else BLUE
        for pawn in pawn_list:
            pygame.draw.ellipse(screen, color, pawn)
    
    # Ereignisse verarbeiten
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not turn_active:
                dice_result = random.randint(1, 6)
                print(f"{players[current_player]} würfelt eine {dice_result}")
                turn_active = True
        elif event.type == pygame.MOUSEBUTTONDOWN and turn_active and players[current_player] == "Mensch":
            mouse_pos = pygame.mouse.get_pos()
            for pawn in pawns["Mensch"]:
                if pawn.collidepoint(mouse_pos):
                    selected_pawn = pawn
        elif event.type == pygame.KEYDOWN and turn_active and selected_pawn:
            if event.key == pygame.K_RETURN:
                index = path.index((selected_pawn.x + 25, selected_pawn.y + 25)) if (selected_pawn.x + 25, selected_pawn.y + 25) in path else -1
                if index != -1 and index + dice_result < len(path):
                    selected_pawn.x, selected_pawn.y = path[index + dice_result][0] - 25, path[index + dice_result][1] - 25
                selected_pawn = None
                turn_active = False
                current_player = (current_player + 1) % 4
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
