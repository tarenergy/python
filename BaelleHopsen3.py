import pygame
import random
import math

# Pygame initialisieren
pygame.init()
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h

# Konstanten definieren
BALL_COUNT = 10
BALL_RADIUS = 20
BIG_BALL_RADIUS = BALL_RADIUS * 2

# Farben generieren
def random_color():
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

# Ball-Klasse definieren
class Ball:
    def __init__(self, big=False, number=1):
        self.radius = random.randint(10, 40) if not big else BIG_BALL_RADIUS
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = random.randint(self.radius, HEIGHT - self.radius)
        self.vx = random.uniform(-10, 10)
        self.vy = random.uniform(-10, 10)
        self.color = random_color()
        self.number = number
        self.big = big

    def move(self):
        self.x += self.vx
        self.y += self.vy
        
        # Kollision mit den Wänden
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx *= -1
        elif self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vx *= -1
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy *= -1
        elif self.y + self.radius > HEIGHT:
            self.y = HEIGHT - self.radius
            self.vy *= -1

    def draw(self, screen):
        font = pygame.font.Font(None, 24)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        text = font.render(str(self.number), True, (255, 255, 255))
        text_rect = text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(text, text_rect)
        if self.big:
            for _ in range(5):  # Zeichne bunte Punkte auf den großen Ball
                px = int(self.x + random.uniform(-self.radius, self.radius))
                py = int(self.y + random.uniform(-self.radius, self.radius))
                pygame.draw.circle(screen, random_color(), (px, py), 5)

# Prüft Kollision zwischen zwei Bällen
def check_collision(ball1, ball2):
    dx = ball1.x - ball2.x
    dy = ball1.y - ball2.y
    distance = math.sqrt(dx ** 2 + dy ** 2)
    return distance < (ball1.radius + ball2.radius)

# Bewegt Bälle voneinander weg nach einer Kollision
def resolve_collision(ball1, ball2):
    dx = ball1.x - ball2.x
    dy = ball1.y - ball2.y
    distance = math.sqrt(dx ** 2 + dy ** 2)
    if distance == 0:
        return  # Verhindert Division durch Null
    
    overlap = (ball1.radius + ball2.radius) - distance
    move_x = (dx / distance) * (overlap / 2)
    move_y = (dy / distance) * (overlap / 2)
    
    ball1.x += move_x
    ball1.y += move_y
    ball2.x -= move_x
    ball2.y -= move_y
    
    # Geschwindigkeiten tauschen (einfaches Elastizitätsmodell)
    ball1.vx, ball2.vx = ball2.vx, ball1.vx
    ball1.vy, ball2.vy = ball2.vy, ball1.vy

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Bälle hopsen")
clock = pygame.time.Clock()

# Liste der Bälle erstellen, ein großer Ball und die restlichen normal
balls = [Ball(big=True, number=1)] + [Ball(number=i+2) for i in range(BALL_COUNT - 1)]

running = True
paused = False
while running:
    screen.fill((0, 0, 0))
    
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            paused = not paused
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_x:
            running = False
    
    # Bälle bewegen und zeichnen
    if not paused:
        for ball in balls:
            ball.move()
    
    for ball in balls:
        ball.draw(screen)
    
    # Kollisionen zwischen Bällen prüfen
    for i in range(BALL_COUNT):
        for j in range(i + 1, BALL_COUNT):
            if check_collision(balls[i], balls[j]):
                resolve_collision(balls[i], balls[j])

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

