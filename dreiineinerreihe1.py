import pygame
import sys
import math # Import für ceil

# --- Konstanten ---
# Farben (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
LINE_COLOR = BLACK
PLAYER_X_COLOR = RED
PLAYER_O_COLOR = BLUE

# Fenster- und Gitterdimensionen
GRID_SIZE = 3
CELL_SIZE = 100
MARGIN = 20 # Rand um das Gitter
ARROW_AREA_SIZE = 40 # Größe des Bereichs für die Pfeile
INFO_HEIGHT = 60 # Höhe für Statusmeldungen

WIDTH = GRID_SIZE * CELL_SIZE + 2 * MARGIN + 2 * ARROW_AREA_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE + 2 * MARGIN + 2 * ARROW_AREA_SIZE + INFO_HEIGHT
LINE_WIDTH = 5
CIRCLE_RADIUS = CELL_SIZE // 3
CIRCLE_WIDTH = 8
CROSS_WIDTH = 10

# --- Spielvariablen ---
board = [[0] * GRID_SIZE for _ in range(GRID_SIZE)] # 0: Leer, 1: Spieler X, 2: Spieler O
current_player = 1 # 1 für X, 2 für O
game_over = False
winner = 0 # 0: Kein Gewinner, 1: X gewinnt, 2: O gewinnt
message = "Spieler X ist dran"

# --- Pygame Initialisierung ---
pygame.init()
pygame.font.init() # Initialisiere das Font-Modul
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Drei in einer Reihe schieben")
font = pygame.font.SysFont('Arial', 30)
small_font = pygame.font.SysFont('Arial', 20)

# --- Hilfsfunktionen ---

def draw_grid():
    """ Zeichnet das 3x3 Gitter """
    grid_start_x = MARGIN + ARROW_AREA_SIZE
    grid_start_y = MARGIN + ARROW_AREA_SIZE + INFO_HEIGHT
    grid_end_x = grid_start_x + GRID_SIZE * CELL_SIZE
    grid_end_y = grid_start_y + GRID_SIZE * CELL_SIZE

    for i in range(1, GRID_SIZE):
        # Vertikale Linien
        pygame.draw.line(screen, LINE_COLOR,
                         (grid_start_x + i * CELL_SIZE, grid_start_y),
                         (grid_start_x + i * CELL_SIZE, grid_end_y), LINE_WIDTH)
        # Horizontale Linien
        pygame.draw.line(screen, LINE_COLOR,
                         (grid_start_x, grid_start_y + i * CELL_SIZE),
                         (grid_end_x, grid_start_y + i * CELL_SIZE), LINE_WIDTH)

def draw_markers():
    """ Zeichnet die X und O Symbole auf das Brett """
    grid_start_x = MARGIN + ARROW_AREA_SIZE
    grid_start_y = MARGIN + ARROW_AREA_SIZE + INFO_HEIGHT

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            center_x = grid_start_x + col * CELL_SIZE + CELL_SIZE // 2
            center_y = grid_start_y + row * CELL_SIZE + CELL_SIZE // 2

            if board[row][col] == 1: # Spieler X
                # Zeichne X (zwei Linien)
                offset = CELL_SIZE // 4
                pygame.draw.line(screen, PLAYER_X_COLOR, (center_x - offset, center_y - offset),
                                 (center_x + offset, center_y + offset), CROSS_WIDTH)
                pygame.draw.line(screen, PLAYER_X_COLOR, (center_x + offset, center_y - offset),
                                 (center_x - offset, center_y + offset), CROSS_WIDTH)
            elif board[row][col] == 2: # Spieler O
                # Zeichne O (Kreis)
                pygame.draw.circle(screen, PLAYER_O_COLOR, (center_x, center_y), CIRCLE_RADIUS, CIRCLE_WIDTH)

def draw_push_arrows():
    """ Zeichnet die Pfeile/Bereiche zum Schieben """
    grid_start_x = MARGIN + ARROW_AREA_SIZE
    grid_start_y = MARGIN + ARROW_AREA_SIZE + INFO_HEIGHT
    grid_width = GRID_SIZE * CELL_SIZE

    arrow_color = GRAY

    # Obere Pfeile (nach unten schieben)
    for col in range(GRID_SIZE):
        rect = pygame.Rect(grid_start_x + col * CELL_SIZE, MARGIN + INFO_HEIGHT, CELL_SIZE, ARROW_AREA_SIZE)
        pygame.draw.rect(screen, arrow_color, rect)
        pygame.draw.polygon(screen, BLACK, [(rect.centerx, rect.bottom - 5),
                                            (rect.centerx - 10, rect.bottom - 15),
                                            (rect.centerx + 10, rect.bottom - 15)]) # Pfeilspitze

    # Untere Pfeile (nach oben schieben)
    for col in range(GRID_SIZE):
        rect = pygame.Rect(grid_start_x + col * CELL_SIZE, grid_start_y + grid_width, CELL_SIZE, ARROW_AREA_SIZE)
        pygame.draw.rect(screen, arrow_color, rect)
        pygame.draw.polygon(screen, BLACK, [(rect.centerx, rect.top + 5),
                                            (rect.centerx - 10, rect.top + 15),
                                            (rect.centerx + 10, rect.top + 15)]) # Pfeilspitze

    # Linke Pfeile (nach rechts schieben)
    for row in range(GRID_SIZE):
        rect = pygame.Rect(MARGIN, grid_start_y + row * CELL_SIZE, ARROW_AREA_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, arrow_color, rect)
        pygame.draw.polygon(screen, BLACK, [(rect.right - 5, rect.centery),
                                            (rect.right - 15, rect.centery - 10),
                                            (rect.right - 15, rect.centery + 10)]) # Pfeilspitze

    # Rechte Pfeile (nach links schieben)
    for row in range(GRID_SIZE):
        rect = pygame.Rect(grid_start_x + grid_width, grid_start_y + row * CELL_SIZE, ARROW_AREA_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, arrow_color, rect)
        pygame.draw.polygon(screen, BLACK, [(rect.left + 5, rect.centery),
                                            (rect.left + 15, rect.centery - 10),
                                            (rect.left + 15, rect.centery + 10)]) # Pfeilspitze


def get_push_action(pos):
    """ Ermittelt die Schiebeaktion basierend auf der Klickposition """
    x, y = pos
    grid_start_x = MARGIN + ARROW_AREA_SIZE
    grid_start_y = MARGIN + ARROW_AREA_SIZE + INFO_HEIGHT
    grid_width = GRID_SIZE * CELL_SIZE
    grid_height = GRID_SIZE * CELL_SIZE

    # Oberer Bereich (nach unten schieben)
    if MARGIN + INFO_HEIGHT < y < MARGIN + ARROW_AREA_SIZE + INFO_HEIGHT:
        if grid_start_x < x < grid_start_x + grid_width:
            col = (x - grid_start_x) // CELL_SIZE
            return ('down', col)

    # Unterer Bereich (nach oben schieben)
    if grid_start_y + grid_height < y < grid_start_y + grid_height + ARROW_AREA_SIZE:
         if grid_start_x < x < grid_start_x + grid_width:
            col = (x - grid_start_x) // CELL_SIZE
            return ('up', col)

    # Linker Bereich (nach rechts schieben)
    if MARGIN < x < MARGIN + ARROW_AREA_SIZE:
        if grid_start_y < y < grid_start_y + grid_height:
            row = (y - grid_start_y) // CELL_SIZE
            return ('right', row)

    # Rechter Bereich (nach links schieben)
    if grid_start_x + grid_width < x < grid_start_x + grid_width + ARROW_AREA_SIZE:
         if grid_start_y < y < grid_start_y + grid_height:
            row = (y - grid_start_y) // CELL_SIZE
            return ('left', row)

    return None # Kein gültiger Schiebebereich geklickt

def slide_column_down(col, player):
    """ Schiebt eine Spalte nach unten und fügt oben das Spielerzeichen ein """
    global board
    # Letztes Element geht verloren
    for row in range(GRID_SIZE - 1, 0, -1):
        board[row][col] = board[row - 1][col]
    board[0][col] = player

def slide_column_up(col, player):
    """ Schiebt eine Spalte nach oben und fügt unten das Spielerzeichen ein """
    global board
    # Erstes Element geht verloren
    for row in range(0, GRID_SIZE - 1):
        board[row][col] = board[row + 1][col]
    board[GRID_SIZE - 1][col] = player

def slide_row_right(row, player):
    """ Schiebt eine Reihe nach rechts und fügt links das Spielerzeichen ein """
    global board
    # Letztes Element geht verloren
    for col in range(GRID_SIZE - 1, 0, -1):
        board[row][col] = board[row][col - 1]
    board[row][0] = player

def slide_row_left(row, player):
    """ Schiebt eine Reihe nach links und fügt rechts das Spielerzeichen ein """
    global board
    # Erstes Element geht verloren
    for col in range(0, GRID_SIZE - 1):
        board[row][col] = board[row][col + 1]
    board[row][GRID_SIZE - 1] = player


def check_win(player):
    """ Prüft, ob der angegebene Spieler gewonnen hat """
    # Horizontale Prüfung
    for row in range(GRID_SIZE):
        if all(board[row][col] == player for col in range(GRID_SIZE)):
            return True
    # Vertikale Prüfung
    for col in range(GRID_SIZE):
        if all(board[row][col] == player for row in range(GRID_SIZE)):
            return True
    # Diagonale Prüfung (oben links nach unten rechts)
    if all(board[i][i] == player for i in range(GRID_SIZE)):
        return True
    # Diagonale Prüfung (oben rechts nach unten links)
    if all(board[i][GRID_SIZE - 1 - i] == player for i in range(GRID_SIZE)):
        return True

    return False # Kein Gewinn

def reset_game():
    """ Setzt das Spiel zurück """
    global board, current_player, game_over, winner, message
    board = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    current_player = 1
    game_over = False
    winner = 0
    message = "Spieler X ist dran"


# --- Haupt-Spielschleife ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            mouse_pos = pygame.mouse.get_pos()
            action = get_push_action(mouse_pos)

            if action:
                direction, index = action
                if direction == 'down':
                    slide_column_down(index, current_player)
                elif direction == 'up':
                    slide_column_up(index, current_player)
                elif direction == 'right':
                    slide_row_right(index, current_player)
                elif direction == 'left':
                    slide_row_left(index, current_player)

                # Nach dem Zug prüfen, ob der aktuelle Spieler gewonnen hat
                if check_win(current_player):
                    winner = current_player
                    game_over = True
                    message = f"Spieler {'X' if winner == 1 else 'O'} gewinnt! (R = Neustart)"
                else:
                    # Spieler wechseln
                    current_player = 3 - current_player # Wechselt zwischen 1 und 2
                    message = f"Spieler {'X' if current_player == 1 else 'O'} ist dran"

        if event.type == pygame.KEYDOWN:
             if event.key == pygame.K_r: # 'R' Taste für Neustart
                 reset_game()


    # --- Zeichnen ---
    screen.fill(WHITE) # Hintergrund löschen

    # Infobereich zeichnen
    info_rect = pygame.Rect(0, 0, WIDTH, INFO_HEIGHT)
    pygame.draw.rect(screen, GRAY, info_rect)
    msg_surface = font.render(message, True, BLACK)
    msg_rect = msg_surface.get_rect(center=(WIDTH // 2, INFO_HEIGHT // 2))
    screen.blit(msg_surface, msg_rect)

    # Spielbereich zeichnen
    draw_grid()
    draw_markers()
    draw_push_arrows()

    # --- Anzeige aktualisieren ---
    pygame.display.flip()

pygame.quit()