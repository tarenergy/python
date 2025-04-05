import pygame
import sys
import math

# Initialisierung von Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Rollende Kugel in der Parabel")
clock = pygame.time.Clock()

# Parameter für die parabolische Bahn in Bildschirmkoordinaten:
# Wir definieren x relativ zum Mittelpunkt (400) und y = k*x^2 + offset_y.
center_x = 400         # horizontaler Mittelpunkt des Bildschirms
offset_y = 300         # y-Verschiebung, sodass der tiefste Punkt der Bahn hier liegt
k = 0.005              # bestimmt die "Öffnung" der Parabel

# Physikalische Parameter (hier in Pixel/(s^2) bzw. Pixel/s für die Simulation)
g = 9.81               # Erdbeschleunigung (in unseren Einheiten)
# Startbedingungen: x = 0 (Tiefpunkt), v = 0 (keine Anfangsgeschwindigkeit)
x = 0.0                # horizontale Position relativ zum Mittelpunkt
v = 0.0                # Geschwindigkeit dx/dt (in Pixel/s)

# Faktor, um mit den Tasten "+" und "-" die Geschwindigkeit anzupassen
boost = 0.5

running = True
while running:
    # dt in Sekunden (abhängig von 60 FPS)
    dt = clock.tick(60) / 1000.0
    
    # Ereignisbehandlung
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Überprüfe das Tastenevent anhand des eingegebenen Zeichens
            if event.unicode == '+':
                v += boost
            elif event.unicode == '-':
                v -= boost

    # Berechnung der Beschleunigung entlang der Bahn anhand der abgeleiteten Bewegungsgleichung:
    #   d²x/dt² = - (4*k²*x*v² + 2*g*k*x) / (1+4*k²*x²)
    denominator = 1 + 4 * (k ** 2) * (x ** 2)
    a = - (4 * (k ** 2) * x * (v ** 2) + 2 * g * k * x) / denominator

    # Numerische Integration (einfache Euler-Methode)
    v += a * dt
    x += v * dt

    # Berechne die Bildschirmkoordinaten der Kugel
    ball_x = int(center_x + x)
    ball_y = int(k * (x ** 2) + offset_y)

    # Bildschirm löschen
    screen.fill((255, 255, 255))

    # Zeichne die parabolische Bahn (als Linie)
    track_points = []
    for sim_x in range(-400, 401, 5):
        px = center_x + sim_x
        py = k * (sim_x ** 2) + offset_y
        track_points.append((px, int(py)))
    if len(track_points) > 1:
        pygame.draw.lines(screen, (0, 0, 0), False, track_points, 2)

    # Zeichne die Kugel
    pygame.draw.circle(screen, (255, 0, 0), (ball_x, ball_y), 10)

    # Aktualisiere die Anzeige
    pygame.display.flip()

pygame.quit()
sys.exit()
