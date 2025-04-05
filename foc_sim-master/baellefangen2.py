import pygame
import random

# Initialisierung von Pygame
pygame.init()

# Bildschirmgröße
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bälle fangen mit einer Schüssel")

# Farben
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Spieler (Schüssel) Einstellungen
bowl_width = 120
bowl_height = 30
bowl_x = WIDTH // 2 - bowl_width // 2
bowl_y = HEIGHT - 50
bowl_speed = 10

# Ball-Einstellungen
ball_radius = 10
ball_speed = 5
balls = []
ball_colors = {RED: 1, BLUE: 2, GREEN: 3, YELLOW: 5}  # Punkte je Farbe

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
    if keys[pygame.K_LEFT] and bowl_x > 0:
        bowl_x -= bowl_speed
    if keys[pygame.K_RIGHT] and bowl_x < WIDTH - bowl_width:
        bowl_x += bowl_speed
    
    # Neue Bälle erzeugen
    if random.randint(1, 20) == 1:
        color = random.choice(list(ball_colors.keys()))
        balls.append([random.randint(0, WIDTH), 0, color])
    
    # Bälle bewegen und Kollision prüfen
    new_balls = []
    for ball in balls:
        ball[1] += ball_speed
        if ball[1] > HEIGHT:
            continue
        if bowl_y < ball[1] + ball_radius < bowl_y + bowl_height and bowl_x < ball[0] < bowl_x + bowl_width:
            score += ball_colors[ball[2]]
            continue
        new_balls.append(ball)
    balls = new_balls
    
    # Spieler (Schüssel) zeichnen
    pygame.draw.ellipse(screen, BLUE, (bowl_x, bowl_y, bowl_width, bowl_height))
    
    # Bälle zeichnen
    for ball in balls:
        pygame.draw.circle(screen, ball[2], (ball[0], ball[1]), ball_radius)
    
    # Punktestand anzeigen
    text = font.render(f"Score: {score}", True, (0, 0, 0))
    screen.blit(text, (10, 10))
    
    # Bildschirm aktualisieren
    pygame.display.flip()
    clock.tick(30)

pygame.quit()