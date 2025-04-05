import pygame
import sys
import time
import random
import math
import os

# Initialisierung von Pygame
pygame.init()
pygame.mixer.init()  # Sound-System initialisieren

# Sound für den Audio-Modus erstellen
try:
    # Versuche, einen Piepton zu erzeugen
    buffer = bytearray()
    for i in range(4410):  # Ca. 0.1 Sekunden bei 44100 Hz
        value = 128 + int(127 * math.sin(i * 0.1))  # Einfacher Sinus-Ton
        buffer.append(value)
    beep_sound = pygame.mixer.Sound(bytes(buffer))
    beep_sound.set_volume(0.5)  # Lautstärke auf 50%
except:
    # Fallback, falls das nicht funktioniert
    beep_sound = pygame.mixer.Sound(bytes([128]*4410))

# Fenstergröße
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Reaktionstest mit Statistik")

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (100, 100, 100)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

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

# Spielmodus
VISUAL_MODE = 0
AUDIO_MODE = 1

# Spielvariablen
game_state = WAITING
game_mode = VISUAL_MODE  # Standardmäßig visueller Modus
circle_radius = 25
target_time = 0
reaction_time = 0
wait_start_time = 0
auto_restart_time = 0
mode_selection_active = True  # Für die anfängliche Modusauswahl

# Statistikvariablen
all_times = []
visual_times = []  # Zeiten im visuellen Modus
audio_times = []   # Zeiten im Audio-Modus
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
    global game_state, wait_start_time, mode_selection_active
    game_state = WAITING
    mode_selection_active = False  # Modusauswahl deaktivieren
    # Zufällige Wartezeit zwischen 2 und 5 Sekunden
    wait_start_time = time.time()

def display_target():
    """Ziel anzeigen oder Sound abspielen"""
    global game_state, target_time
    game_state = DISPLAY
    target_time = time.time()
    
    # Wenn im Audio-Modus, Piepton abspielen
    if game_mode == AUDIO_MODE:
        beep_sound.play()

def show_result():
    """Ergebnis anzeigen und Statistiken aktualisieren"""
    global game_state, reaction_time, attempts_count, auto_restart_time
    game_state = RESULT
    reaction_time = time.time() - target_time
    
    # Reaktionszeit zur Liste hinzufügen und Statistiken aktualisieren
    all_times.append(reaction_time)
    attempts_count += 1
    
    # Reaktionszeit auch in die modusspezifische Liste eintragen
    if game_mode == VISUAL_MODE:
        visual_times.append(reaction_time)
    else:
        audio_times.append(reaction_time)
    
    update_stats()
    
    # Zeit für automatischen Neustart setzen
    auto_restart_time = time.time()

def draw_stats():
    """Statistiken auf der rechten Seite anzeigen"""
    # Hintergrund für Statistikbereich
    pygame.draw.rect(screen, GRAY, stats_area_rect)
    
    # Titel
    draw_text("STATISTIK", font, WHITE, GAME_AREA_WIDTH + (WIDTH - GAME_AREA_WIDTH) // 2, 40)
    
    # Aktueller Modus anzeigen
    mode_text = "VISUELL" if game_mode == VISUAL_MODE else "AUDIO"
    mode_color = RED if game_mode == VISUAL_MODE else BLUE
    draw_text(f"Modus: {mode_text}", font, mode_color, GAME_AREA_WIDTH + (WIDTH - GAME_AREA_WIDTH) // 2, 70)
    
    # Stats anzeigen
    stats_x = GAME_AREA_WIDTH + 20
    stats_y = 120
    stats_spacing = 40
    
    # Gesamtversuche
    draw_text_left(f"Versuche gesamt: {attempts_count}", font, WHITE, stats_x, stats_y)
    stats_y += stats_spacing
    
    # Modus-spezifische Versuche
    visual_count = len(visual_times)
    audio_count = len(audio_times)
    draw_text_left(f"Visuell: {visual_count}", font, RED, stats_x, stats_y)
    stats_y += stats_spacing
    draw_text_left(f"Audio: {audio_count}", font, BLUE, stats_x, stats_y)
    stats_y += stats_spacing
    
    # Allgemeine Statistiken nur anzeigen, wenn Daten vorhanden sind
    if attempts_count > 0:
        stats_y += stats_spacing // 2  # Extra Abstand
        
        draw_text_left(f"Minimum: {min_time:.3f} s", font, WHITE, stats_x, stats_y)
        stats_y += stats_spacing
        
        draw_text_left(f"Maximum: {max_time:.3f} s", font, WHITE, stats_x, stats_y)
        stats_y += stats_spacing
        
        draw_text_left(f"Mittelwert: {avg_time:.3f} s", font, WHITE, stats_x, stats_y)
        stats_y += stats_spacing
        
        draw_text_left(f"Std.Abw.: {std_dev:.3f} s", font, WHITE, stats_x, stats_y)
        
        # Modus-spezifische Durchschnitte anzeigen
        stats_y += stats_spacing
        if visual_count > 0:
            visual_avg = sum(visual_times) / visual_count
            draw_text_left(f"Visuell Ø: {visual_avg:.3f} s", font, RED, stats_x, stats_y)
            stats_y += stats_spacing
        
        if audio_count > 0:
            audio_avg = sum(audio_times) / audio_count
            draw_text_left(f"Audio Ø: {audio_avg:.3f} s", font, BLUE, stats_x, stats_y)

# Funktion für Modusauswahl
def draw_mode_selection():
    """Zeichnet die Modusauswahl-Oberfläche"""
    screen.fill(BLACK)
    
    # Titel
    draw_text("REAKTIONSTEST", big_font, WHITE, WIDTH // 2, 100)
    draw_text("Wähle deinen Modus:", font, WHITE, WIDTH // 2, 200)
    
    # Auswahl-Buttons
    visual_rect = pygame.Rect(WIDTH // 4 - 100, 250, 200, 60)
    audio_rect = pygame.Rect(WIDTH * 3 // 4 - 100, 250, 200, 60)
    
    pygame.draw.rect(screen, RED, visual_rect)
    pygame.draw.rect(screen, BLUE, audio_rect)
    
    draw_text("VISUELL", font, WHITE, WIDTH // 4, 280)
    draw_text("AUDIO", font, WHITE, WIDTH * 3 // 4, 280)
    
    # Beschreibungen
    draw_text("Klicke, wenn der rote Kreis erscheint", font, WHITE, WIDTH // 4, 350)
    draw_text("Klicke, wenn du den Piepton hörst", font, WHITE, WIDTH * 3 // 4, 350)
    
    return visual_rect, audio_rect

# Hauptschleife
clock = pygame.time.Clock()
# Nicht direkt start_wait() aufrufen, sondern mit der Modusauswahl beginnen

while True:
    current_time = time.time()
    
    # Event-Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Modusauswahl-Handling
            if mode_selection_active:
                visual_rect, audio_rect = draw_mode_selection()
                
                if visual_rect.collidepoint(mouse_pos):
                    game_mode = VISUAL_MODE
                    start_wait()
                elif audio_rect.collidepoint(mouse_pos):
                    game_mode = AUDIO_MODE
                    start_wait()
            
            # Reaktionstest-Handling
            elif not mode_selection_active:
                # Moduswechsel-Button in der Statistik-Leiste
                mode_switch_rect = pygame.Rect(GAME_AREA_WIDTH + 20, HEIGHT - 60, WIDTH - GAME_AREA_WIDTH - 40, 40)
                if mode_switch_rect.collidepoint(mouse_pos):
                    mode_selection_active = True
                # Nur im Spielbereich auf Klicks reagieren, nicht im Statistikbereich
                elif mouse_pos[0] < GAME_AREA_WIDTH:
                    if game_state == DISPLAY:
                        # Auf Klick reagieren
                        show_result()
    
    # Modusauswahl anzeigen, wenn aktiv
    if mode_selection_active:
        visual_rect, audio_rect = draw_mode_selection()
    else:
        # Normale Spiellogik
        
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
        
        # Modus-Wechsel-Button
        mode_switch_rect = pygame.Rect(GAME_AREA_WIDTH + 20, HEIGHT - 60, WIDTH - GAME_AREA_WIDTH - 40, 40)
        pygame.draw.rect(screen, GREEN, mode_switch_rect)
        draw_text("Modus wechseln", font, BLACK, GAME_AREA_WIDTH + (WIDTH - GAME_AREA_WIDTH) // 2, HEIGHT - 40)
        
        # Spielinhalte zeichnen
        if game_state == DISPLAY:
            if game_mode == VISUAL_MODE:
                # Visuelles Ziel unter dem Mauszeiger zeichnen
                mouse_pos = pygame.mouse.get_pos()
                # Stelle sicher, dass der Kreis im Spielbereich bleibt
                x = min(mouse_pos[0], GAME_AREA_WIDTH - circle_radius)
                pygame.draw.circle(screen, RED, (x, mouse_pos[1]), circle_radius)
            # Bei Audio-Modus wird kein Kreis gezeichnet, nur der Ton abgespielt
        
        elif game_state == RESULT:
            # Ergebnis anzeigen
            draw_text(f"{reaction_time:.3f} s", big_font, WHITE, GAME_AREA_WIDTH // 2, HEIGHT // 2)
        
        elif game_state == WAITING:
            # Anweisungen während des Wartens, je nach Modus
            if game_mode == VISUAL_MODE:
                draw_text("Warte auf den roten Kreis und klicke, sobald er erscheint", 
                          font, WHITE, GAME_AREA_WIDTH // 2, HEIGHT // 2)
            else:
                draw_text("Warte auf den Piepton und klicke, sobald du ihn hörst", 
                          font, WHITE, GAME_AREA_WIDTH // 2, HEIGHT // 2)
    
    # Bildschirm aktualisieren
    pygame.display.flip()
    clock.tick(200)  # 60 FPS