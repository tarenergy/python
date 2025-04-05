import pygame
import sys
import os
from pygame import mixer

# Konstanten
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WALL_COLOR = (100, 100, 100)
PLAYER_COLOR = (255, 215, 0)
GOAL_COLOR = (0, 255, 0)
WALL_THICKNESS = 15
PLAYER_RADIUS = 5

class LabyrintSpiel:
    def __init__(self):
        # Pygame initialisieren
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Labyrinth-Spiel")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        
        # Spielmodus (0 = Entwurfsmodus, 1 = Spielmodus)
        self.mode = 0
        
        # Labyrinth initialisieren
        self.walls = []
        self.create_initial_maze()
        
        # Start- und Zielpunkte festlegen
        self.start_pos = (50, 50)
        self.goal_pos = (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 50)
        self.goal_radius = 20
        
        # Spielstatus
        self.game_over = False
        self.win = False
        
        # Musik initialisieren
        mixer.init()
        if os.path.exists("poster_paster.mp3"):
            self.game_music = mixer.Sound("poster_paster.mp3")
        else:
            # Dummy-Sound wenn die Datei nicht existiert
            self.game_music = pygame.mixer.Sound(buffer=bytearray([]))
            print("Warnung: 'poster_paster.mp3' konnte nicht gefunden werden.")
        
        # Maus unsichtbar machen im Spielmodus
        self.cursor_visible = True
        
        # Variablen für den Entwurfsmodus
        self.drawing = False
        self.start_draw = (0, 0)
        self.current_draw = (0, 0)
        self.erasing = False
    
    def create_initial_maze(self):
        """Einfaches Start-Labyrinth erstellen"""
        # Äußere Wände
        self.walls.append(pygame.Rect(100, 100, WALL_THICKNESS, 400))  # Links
        self.walls.append(pygame.Rect(100, 100, 600, WALL_THICKNESS))  # Oben
        self.walls.append(pygame.Rect(700, 100, WALL_THICKNESS, 400))  # Rechts
        self.walls.append(pygame.Rect(100, 500, 600, WALL_THICKNESS))  # Unten
        
        # Innere Wände
        self.walls.append(pygame.Rect(200, 100, WALL_THICKNESS, 300))
        self.walls.append(pygame.Rect(300, 200, 300, WALL_THICKNESS))
        self.walls.append(pygame.Rect(300, 200, WALL_THICKNESS, 200))
        self.walls.append(pygame.Rect(400, 300, WALL_THICKNESS, 200))
        self.walls.append(pygame.Rect(500, 300, WALL_THICKNESS, 100))
        self.walls.append(pygame.Rect(400, 300, 200, WALL_THICKNESS))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            
            # Tastatureingaben
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit_game()
                elif event.key == pygame.K_SPACE:
                    self.toggle_mode()
                elif event.key == pygame.K_r:
                    self.reset_game()
            
            # Mauseingaben im Entwurfsmodus
            if self.mode == 0:  # Entwurfsmodus
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Linke Maustaste
                        self.drawing = True
                        self.erasing = False
                        self.start_draw = event.pos
                        self.current_draw = event.pos
                    elif event.button == 3:  # Rechte Maustaste
                        self.erasing = True
                        self.drawing = False
                
                elif event.type == pygame.MOUSEMOTION:
                    if self.drawing:
                        self.current_draw = event.pos
                    elif self.erasing:
                        mouse_pos = event.pos
                        self.erase_wall(mouse_pos)
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.drawing:
                        self.add_wall(self.start_draw, event.pos)
                        self.drawing = False
                    elif event.button == 3:
                        self.erasing = False
    
    def toggle_mode(self):
        """Zwischen Entwurfs- und Spielmodus wechseln"""
        self.mode = 1 - self.mode  # Wechseln zwischen 0 und 1
        
        if self.mode == 1:  # Spielmodus
            self.game_over = False
            self.win = False
            pygame.mouse.set_pos(self.start_pos)
            self.cursor_visible = False
            pygame.mouse.set_visible(False)
            
            # Musik starten
            self.game_music.play(-1)  # -1 für Endlosschleife
        else:  # Entwurfsmodus
            self.cursor_visible = True
            pygame.mouse.set_visible(True)
            
            # Musik stoppen
            self.game_music.stop()
    
    def add_wall(self, start, end):
        """Neue Wand zum Labyrinth hinzufügen"""
        x1, y1 = start
        x2, y2 = end
        
        # Horizontale oder vertikale Wand erstellen
        if abs(x2 - x1) > abs(y2 - y1):  # Horizontale Wand
            rect = pygame.Rect(min(x1, x2), min(y1, y2) - WALL_THICKNESS // 2, 
                               abs(x2 - x1), WALL_THICKNESS)
        else:  # Vertikale Wand
            rect = pygame.Rect(min(x1, x2) - WALL_THICKNESS // 2, min(y1, y2), 
                               WALL_THICKNESS, abs(y2 - y1))
        
        self.walls.append(rect)
    
    def erase_wall(self, pos):
        """Wand an der Position entfernen"""
        for i, wall in enumerate(self.walls):
            if wall.collidepoint(pos):
                self.walls.pop(i)
                break
    
    def check_collision(self, pos):
        """Prüfen, ob die Position mit einer Wand kollidiert"""
        x, y = pos
        for wall in self.walls:
            if wall.collidepoint(x, y):
                return True
        return False
    
    def check_win(self, pos):
        """Prüfen, ob der Spieler das Ziel erreicht hat"""
        x, y = pos
        distance = ((x - self.goal_pos[0]) ** 2 + (y - self.goal_pos[1]) ** 2) ** 0.5
        return distance < self.goal_radius
    
    def reset_game(self):
        """Spiel zurücksetzen"""
        self.game_over = False
        self.win = False
        if self.mode == 1:  # Wenn im Spielmodus
            pygame.mouse.set_pos(self.start_pos)
    
    def draw_screen(self):
        """Spielbildschirm zeichnen"""
        self.screen.fill(WHITE)
        
        # Labyrinth zeichnen
        for wall in self.walls:
            pygame.draw.rect(self.screen, WALL_COLOR, wall)
        
        # Ziel zeichnen
        pygame.draw.circle(self.screen, GOAL_COLOR, self.goal_pos, self.goal_radius)
        
        # Start zeichnen
        pygame.draw.circle(self.screen, BLUE, self.start_pos, 10)
        
        # Im Entwurfsmodus: aktuell gezeichnete Wand anzeigen
        if self.mode == 0 and self.drawing:
            if abs(self.current_draw[0] - self.start_draw[0]) > abs(self.current_draw[1] - self.start_draw[1]):
                # Horizontale Vorschau
                pygame.draw.line(self.screen, RED, 
                                 self.start_draw, 
                                 (self.current_draw[0], self.start_draw[1]), 
                                 WALL_THICKNESS)
            else:
                # Vertikale Vorschau
                pygame.draw.line(self.screen, RED, 
                                 self.start_draw, 
                                 (self.start_draw[0], self.current_draw[1]), 
                                 WALL_THICKNESS)
        
        # Spieler im Spielmodus zeichnen
        if self.mode == 1:
            player_pos = pygame.mouse.get_pos()
            pygame.draw.circle(self.screen, PLAYER_COLOR, player_pos, PLAYER_RADIUS)
        
        # Modus-Anzeige
        mode_text = "Entwurfsmodus (SPACE zum Wechseln, R zum Zurücksetzen)" if self.mode == 0 else "Spielmodus"
        text_surface = self.font.render(mode_text, True, BLACK)
        self.screen.blit(text_surface, (10, 10))
        
        # Anweisungen im Entwurfsmodus anzeigen
        if self.mode == 0:
            instructions = "Linksklick: Wand zeichnen, Rechtsklick: Wand löschen"
            instr_surface = self.font.render(instructions, True, BLACK)
            self.screen.blit(instr_surface, (10, SCREEN_HEIGHT - 40))
        
        # Game Over oder Win-Nachricht anzeigen
        if self.game_over:
            text = "Game Over! Drücke R zum Neustarten"
            game_over_surface = self.font.render(text, True, RED)
            text_rect = game_over_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(game_over_surface, text_rect)
        elif self.win:
            text = "Gewonnen! Drücke R zum Neustarten"
            win_surface = self.font.render(text, True, GREEN)
            text_rect = win_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(win_surface, text_rect)
    
    def update_game(self):
        """Spiellogik aktualisieren"""
        if self.mode == 1 and not self.game_over and not self.win:
            player_pos = pygame.mouse.get_pos()
            
            # Kollision mit Wänden prüfen
            if self.check_collision(player_pos):
                self.game_over = True
                self.game_music.stop()
            
            # Sieg prüfen
            if self.check_win(player_pos):
                self.win = True
                self.game_music.stop()
    
    def quit_game(self):
        """Spiel beenden"""
        pygame.quit()
        sys.exit()
    
    def run(self):
        """Hauptspielschleife"""
        while True:
            self.handle_events()
            self.update_game()
            self.draw_screen()
            pygame.display.flip()
            self.clock.tick(60)

# Spiel starten
if __name__ == "__main__":
    game = LabyrintSpiel()
    game.run()