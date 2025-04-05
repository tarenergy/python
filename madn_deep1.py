import pygame
import random
import sys

# Initialisierung von Pygame
pygame.init()

# Bildschirmgröße
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mensch ärgere dich nicht")

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Spielerfarben
PLAYER_COLORS = [RED, GREEN, BLUE, YELLOW]

# Spielbrett
BOARD_SIZE = 4
SQUARE_SIZE = WIDTH // BOARD_SIZE

# Spieler
NUM_PLAYERS = 4
PLAYER_POSITIONS = [0] * NUM_PLAYERS

# Würfel
DICE_SIZE = 50
DICE_POS = (WIDTH // 2 - DICE_SIZE // 2, HEIGHT // 2 - DICE_SIZE // 2)

# Spielzustand
current_player = 0
dice_result = 0

def draw_board():
    screen.fill(WHITE)
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            rect = pygame.Rect(j * SQUARE_SIZE, i * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(screen, BLACK, rect, 1)

def draw_players():
    for i, pos in enumerate(PLAYER_POSITIONS):
        x = (pos % BOARD_SIZE) * SQUARE_SIZE + SQUARE_SIZE // 2
        y = (pos // BOARD_SIZE) * SQUARE_SIZE + SQUARE_SIZE // 2
        pygame.draw.circle(screen, PLAYER_COLORS[i], (x, y), SQUARE_SIZE // 4)

def roll_dice():
    return random.randint(1, 6)

def draw_dice():
    pygame.draw.rect(screen, BLACK, (*DICE_POS, DICE_SIZE, DICE_SIZE))
    font = pygame.font.Font(None, 36)
    text = font.render(str(dice_result), True, WHITE)
    screen.blit(text, (DICE_POS[0] + DICE_SIZE // 3, DICE_POS[1] + DICE_SIZE // 3))

def handle_events():
    global current_player, dice_result
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                dice_result = roll_dice()
                PLAYER_POSITIONS[current_player] = (PLAYER_POSITIONS[current_player] + dice_result) % (BOARD_SIZE * BOARD_SIZE)
                current_player = (current_player + 1) % NUM_PLAYERS

def main():
    global dice_result
    clock = pygame.time.Clock()
    while True:
        handle_events()
        draw_board()
        draw_players()
        draw_dice()
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()