import pygame
import math

# Initialisierung von pygame
pygame.init()

# Bildschirmgröße und Einstellungen
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Parabel-Kugel-Spiel")
clock = pygame.time.Clock()

# Physikalische Konstanten
g = 0.1  # Erdbeschleunigung
k = 0.002  # Skalierungsfaktor für die Parabel (reduziert für realistischere Bewegung)
friction = 1.0  # Reibung (leicht erhöht)

# Kugel-Parameter
ball_radius = 15
ball_x = -WIDTH // 2  # Position entlang der x-Achse (startet links)
ball_vx = 0  # Anfangsgeschwindigkeit auf null setzen

# Hauptspiel-Schleife
running = True
while running:
    screen.fill((255, 255, 255))
    
    # Event-Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
                ball_vx += 0.5  # Geschwindigkeit leicht erhöhen
            elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                ball_vx -= 0.5  # Geschwindigkeit leicht verringern
    
    # Berechnung der Beschleunigung
    acceleration = -k * ball_x * g  # Hangneigung beachten, kleinerer Faktor für realistische Bewegung
    ball_vx += acceleration
    ball_vx *= friction  # Reibung anwenden
    ball_x += ball_vx  # Position aktualisieren
    
    # Begrenzung der Bewegung
    if ball_x < -WIDTH // 2:
        ball_x = -WIDTH // 2
        ball_vx = -ball_vx * 0.7  # Rückstoß mit Dämpfung bei Wandkontakt
    elif ball_x > WIDTH // 2:
        ball_x = WIDTH // 2
        ball_vx = -ball_vx * 0.7  # Rückstoß mit Dämpfung bei Wandkontakt
    
    # Berechnung der y-Position aus der umgedrehten Parabelgleichung
    ball_y = -k * ball_x ** 2
    
    # Umrechnung der Koordinaten ins Bildschirmformat
    screen_x = WIDTH // 2 + int(ball_x)
    screen_y = HEIGHT // 2 + int(ball_y)
    
    # Zeichnen der umgedrehten Parabel
    for x in range(-WIDTH // 2, WIDTH // 2, 5):
        y = -k * x ** 2
        pygame.draw.circle(screen, (0, 0, 0), (WIDTH // 2 + x, HEIGHT // 2 + int(y)), 1)
    
    # Zeichnen der Kugel
    pygame.draw.circle(screen, (255, 0, 0), (screen_x, screen_y), ball_radius)
    
    # Bildschirm aktualisieren
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
