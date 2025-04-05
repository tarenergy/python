import pygame
import random

# Initialisierung von Pygame
pygame.init()

# Bildschirmgröße
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bälle fangen")

# Farben
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Spieler-Einstellungen
player_width = 100
player_height = 20
player_x = WIDTH // 2 - player_width // 2
player_y = HEIGHT - 40
player_speed = 10

# Ball-Einstellungen
ball_radius = 10
ball_speed = 5
balls = []

# Punkte
score = 0
font = pygame.font.Font(None, 36)

# Spiel-Loop
running = True
clock = pygame.time.Clock()
while running:
    screen.fill(WHITE)
    
    # Ereignisse verarbeiten
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Spielerbewegung
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player_x > 0:
        player_x -= player_speed
    if keys[pygame.K_RIGHT] and player_x < WIDTH - player_width:
        player_x += player_speed
    
    # Neue Bälle erzeugen
    if random.randint(1, 30) == 1:
        balls.append([random.randint(0, WIDTH), 0])
    
    # Bälle bewegen und Kollision prüfen
    new_balls = []
    for ball in balls:
        ball[1] += ball_speed
        if ball[1] > HEIGHT:
            continue
        if player_y < ball[1] + ball_radius < player_y + player_height and player_x < ball[0] < player_x + player_width:
            score += 1
            continue
        new_balls.append(ball)
    balls = new_balls
    
    # Spieler zeichnen
    pygame.draw.rect(screen, BLUE, (player_x, player_y, player_width, player_height))
    
    # Bälle zeichnen
    for ball in balls:
        pygame.draw.circle(screen, RED, (ball[0], ball[1]), ball_radius)
    
    # Punktestand anzeigen
    text = font.render(f"Score: {score}", True, (0, 0, 0))
    screen.blit(text, (10, 10))
    
    # Bildschirm aktualisieren
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
