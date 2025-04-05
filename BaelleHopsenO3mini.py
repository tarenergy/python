import pygame
import random
import math

# Pygame initialisieren
pygame.init()

# Fenstergröße
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bälle hopsen")

clock = pygame.time.Clock()

# Ball-Klasse
class Ball:
    def __init__(self, nummer):
        self.nummer = nummer
        self.radius = random.randint(15, 40)  # zufällige Größe
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = random.randint(self.radius, HEIGHT - self.radius)
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        speed = random.uniform(1, 3)
        angle = random.uniform(0, 2 * math.pi)
        self.dx = speed * math.cos(angle)
        self.dy = speed * math.sin(angle)

    def move(self):
        self.x += self.dx
        self.y += self.dy

        # Kollision mit dem Fensterrahmen
        if self.x - self.radius <= 0 or self.x + self.radius >= WIDTH:
            self.dx = -self.dx
        if self.y - self.radius <= 0 or self.y + self.radius >= HEIGHT:
            self.dy = -self.dy

    def draw(self, surface, font):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # Nummer in der Mitte des Balls zeichnen
        text = font.render(str(self.nummer), True, (0, 0, 0))
        text_rect = text.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(text, text_rect)

# Funktion zur Kollisionserkennung zwischen zwei Bällen
def check_collision(ball1, ball2):
    dx = ball1.x - ball2.x
    dy = ball1.y - ball2.y
    distance = math.hypot(dx, dy)
    return distance < (ball1.radius + ball2.radius)

# Einfache Kollisionsauflösung (elastischer Stoß) zwischen zwei Bällen
def resolve_collision(ball1, ball2):
    # Berechne den Normierungsvektor von ball1 zu ball2
    dx = ball2.x - ball1.x
    dy = ball2.y - ball1.y
    distance = math.hypot(dx, dy)
    if distance == 0:
        distance = 0.1
    nx = dx / distance
    ny = dy / distance

    # Projektion der Geschwindigkeiten auf den Kollisionsvektor
    p1 = ball1.dx * nx + ball1.dy * ny
    p2 = ball2.dx * nx + ball2.dy * ny

    # Austausch der Geschwindigkeitskomponenten entlang des Kollisionsvektors
    ball1.dx += (p2 - p1) * nx
    ball1.dy += (p2 - p1) * ny
    ball2.dx += (p1 - p2) * nx
    ball2.dy += (p1 - p2) * ny

    # Verschiebe die Bälle, sodass sie sich nicht überlappen
    overlap = 0.5 * (ball1.radius + ball2.radius - distance + 1)
    ball1.x -= overlap * nx
    ball1.y -= overlap * ny
    ball2.x += overlap * nx
    ball2.y += overlap * ny

# Erzeuge 20 Bälle
balls = [Ball(i) for i in range(1, 21)]
font = pygame.font.SysFont("Arial", 20)

running = True
while running:
    clock.tick(60)  # 60 FPS

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Bewege die Bälle
    for ball in balls:
        ball.move()

    # Prüfe Kollisionen zwischen den Bällen
    for i in range(len(balls)):
        for j in range(i + 1, len(balls)):
            if check_collision(balls[i], balls[j]):
                resolve_collision(balls[i], balls[j])

    # Zeichne den Hintergrund und die Bälle
    screen.fill((255, 255, 255))
    for ball in balls:
        ball.draw(screen, font)

    pygame.display.flip()

pygame.quit()
