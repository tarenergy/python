import pygame
import random

# Konstanten
WIDTH, HEIGHT = 600, 500  # Noch größeres Spielfeld
TILE_SIZE = 20  # Kleinere Kacheln für schmalere Gänge
ROWS, COLS = HEIGHT // TILE_SIZE, WIDTH // TILE_SIZE
WHITE, BLACK, GREEN, RED = (255, 255, 255), (0, 0, 0), (0, 255, 0), (255, 0, 0)

# Labyrinth-Generierung (Rekursiver Backtracking-Algorithmus mit noch mehr Verzweigungen)
def generate_maze(rows, cols):
    maze = [[1 for _ in range(cols)] for _ in range(rows)]
    stack = [(1, 1)]
    maze[1][1] = 0
    directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
    
    while stack:
        x, y = stack[-1]
        random.shuffle(directions)
        valid_moves = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 1 <= nx < rows - 1 and 1 <= ny < cols - 1 and maze[nx][ny] == 1:
                valid_moves.append((dx, dy))
        
        if valid_moves:
            dx, dy = random.choice(valid_moves)
            nx, ny = x + dx, y + dy
            maze[nx][ny] = 0
            maze[x + dx // 2][y + dy // 2] = 0
            stack.append((nx, ny))
        else:
            stack.pop()
    
    # Zufällige Extra-Gänge erzeugen
    for _ in range(rows * cols // 5):
        x, y = random.randint(1, rows - 2), random.randint(1, cols - 2)
        maze[x][y] = 0
    
    return maze

# Spielerklasse
class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
    
    def move(self, dx, dy, maze):
        if maze[self.y + dy][self.x + dx] == 0:
            self.x += dx
            self.y += dy
    
    def draw(self, screen):
        pygame.draw.rect(screen, GREEN, (self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

# Hauptfunktion
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    maze = generate_maze(ROWS, COLS)
    player = Player(1, 1)
    goal = (COLS - 2, ROWS - 2)
    
    running = True
    while running:
        screen.fill(WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    player.move(0, -1, maze)
                elif event.key == pygame.K_DOWN:
                    player.move(0, 1, maze)
                elif event.key == pygame.K_LEFT:
                    player.move(-1, 0, maze)
                elif event.key == pygame.K_RIGHT:
                    player.move(1, 0, maze)
        
        # Zeichne das Labyrinth
        for row in range(ROWS):
            for col in range(COLS):
                if maze[row][col] == 1:
                    pygame.draw.rect(screen, BLACK, (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        
        # Zeichne das Ziel
        pygame.draw.rect(screen, RED, (goal[0] * TILE_SIZE, goal[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        
        # Zeichne den Spieler
        player.draw(screen)
        
        # Überprüfe, ob das Ziel erreicht wurde
        if (player.x, player.y) == goal:
            print("Gewonnen!")
            running = False
        
        pygame.display.flip()
        clock.tick(30)
    
    pygame.quit()

if __name__ == "__main__":
    main()
