import pygame
import sys
import time
import random
import math

# Initialisierung von Pygame
pygame.init()

# Fenstergröße
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Reaktionstest mit Statistik")

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (100, 100, 100)

# Schriftarten
font = pygame.font.SysFont(None, 30)
big_font = pygame.font.SysFont(None, 60)

# Spielbereich und Statistikbereich
GAME_AREA_WIDTH = 700
stats_area_rect = pygame.Rect(GAME_AREA_WIDTH, 0, WIDTH - GAME_AREA_WIDTH, HEIGHT)

# Spielstatus
WAITING = 0     # Warten auf Erscheinen des Kreises
DISPLAY = 1     # Kreis wird angezeigt
RESULT = 2      # Ergebnis wird angezeigt

# Spielvariablen
game_state = WAITING
circle_radius = 25
target_time = 0
reaction_time = 0
wait_start_time = 0
auto_restart_time = 0

# Statistikvariablen
all_times = []
attempts_count = 0
min_time = float('inf')
max_time = 0
avg_time = 0
std_dev = 0

def draw_text(text, font, color, x, y):
    """Text auf dem Bildschirm zeichnen"""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

def draw_text_left(text, font, color, x, y):
    """Text auf dem Bildschirm zeichnen (linksbündig)"""
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def update_stats():
    """Statistiken aktualisieren"""
    global min_time, max_time, avg_time, std_dev
    
    if all_times:
        min_time = min(all_times)
        max_time = max(all_times)
        avg_time = sum(all_times) / len(all_times)
        
        # Standardabweichung berechnen
        variance = sum((t - avg_time) ** 2 for t in all_times) / len(all_times)
        std_dev = math.sqrt(variance)

def start_wait():
    """Startphase, in der der Bildschirm leer ist"""
    global game_state, wait_start_time
    game_state = WAITING
    # Zufällige Wartezeit zwischen 2 und 5 Sekunden
    wait_start_time = time.time()

def display_target():
    """Ziel anzeigen"""
    global game_state, target_time
    game_state = DISPLAY
    target_time = time.time()

def show_result():
    """Ergebnis anzeigen und Statistiken aktualisieren"""
    global game_state, reaction_time, attempts_count, auto_restart_time
    game_state = RESULT
    reaction_time = time.time() - target_time
    
    # Reaktionszeit zur Liste hinzufügen und Statistiken aktualisieren
    all_times.append(reaction_time)
    attempts_count += 1
    update_stats()
    
    # Zeit für automatischen Neustart setzen
    auto_restart_time = time.time()

def draw_stats():
    """Statistiken auf der rechten Seite anzeigen"""
    # Hintergrund für Statistikbereich
    pygame.draw.rect(screen, GRAY, stats_area_rect)
    
    # Titel
    draw_text("STATISTIK", font, WHITE, GAME_AREA_WIDTH + (WIDTH - GAME_AREA_WIDTH) // 2, 40)
    
    # Stats anzeigen
    stats_x = GAME_AREA_WIDTH + 20
    stats_y = 100
    stats_spacing = 40
    
    draw_text_left(f"Versuche: {attempts_count}", font, WHITE, stats_x, stats_y)
    stats_y += stats_spacing
    
    if attempts_count > 0:
        draw_text_left(f"Minimum: {min_time:.3f} s", font, WHITE, stats_x, stats_y)
        stats_y += stats_spacing
        
        draw_text_left(f"Maximum: {max_time:.3f} s", font, WHITE, stats_x, stats_y)
        stats_y += stats_spacing
        
        draw_text_left(f"Mittelwert: {avg_time:.3f} s", font, WHITE, stats_x, stats_y)
        stats_y += stats_spacing
        
        draw_text_left(f"Std.Abw.: {std_dev:.3f} s", font, WHITE, stats_x, stats_y)

# Hauptschleife
clock = pygame.time.Clock()
start_wait()

while True:
    current_time = time.time()
    
    # Event-Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Nur im Spielbereich auf Klicks reagieren, nicht im Statistikbereich
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0] < GAME_AREA_WIDTH:
                if game_state == DISPLAY:
                    # Auf Klick reagieren
                    show_result()
    
    # Zustandslogik
    if game_state == WAITING:
        # Nach zufälliger Zeit das Ziel anzeigen
        wait_time = random.uniform(2.0, 5.0)
        if current_time - wait_start_time > wait_time:
            display_target()
    
    elif game_state == RESULT:
        # Automatischer Neustart nach 2 Sekunden
        if current_time - auto_restart_time > 2.0:
            start_wait()
    
    # Bildschirm löschen
    screen.fill(BLACK, pygame.Rect(0, 0, GAME_AREA_WIDTH, HEIGHT))  # Nur den Spielbereich löschen
    
    # Statistiken zeichnen
    draw_stats()
    
    # Spielinhalte zeichnen
    if game_state == DISPLAY:
        # Ziel unter dem Mauszeiger zeichnen
        mouse_pos = pygame.mouse.get_pos()
        # Stelle sicher, dass der Kreis im Spielbereich bleibt
        x = min(mouse_pos[0], GAME_AREA_WIDTH - circle_radius)
        pygame.draw.circle(screen, RED, (x, mouse_pos[1]), circle_radius)
    
    elif game_state == RESULT:
        # Ergebnis anzeigen
        draw_text(f"{reaction_time:.3f} s", big_font, WHITE, GAME_AREA_WIDTH // 2, HEIGHT // 2)
    
    elif game_state == WAITING:
        # Anweisungen während des Wartens
        draw_text("Warte auf den roten Kreis und klicke, sobald er erscheint", 
                  font, WHITE, GAME_AREA_WIDTH // 2, HEIGHT // 2)
    
    # Bildschirm aktualisieren
    pygame.display.flip()
    clock.tick(60)  # 60 FPS