import tkinter as tk
from tkinter import ttk
import pygame
import random
import math
import os
from pygame.math import Vector2 # Pygame's Vector2 ist sehr praktisch

# --- Pygame Fenster Setup ---
# Wird dynamisch auf Vollbildgröße gesetzt
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0
FPS = 60

# --- Farben ---
WHITE = (255, 255, 255)
RED = (255, 50, 50)
BLUE = (50, 50, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)

# --- Boid Klasse ---
class Boid:
    def __init__(self, x, y, color, params):
        self.position = Vector2(x, y)
        max_speed_init = params.get('max_speed', tk.DoubleVar(value=4.0)).get()
        angle = random.uniform(0, 2 * math.pi)
        # Starte mit einer zufälligen Geschwindigkeit, aber nicht Null
        initial_speed = random.uniform(1, max(1.1, max_speed_init / 2))
        self.velocity = Vector2(math.cos(angle), math.sin(angle)) * initial_speed
        self.acceleration = Vector2(0, 0)
        self.color = color
        self.params = params
        self.size = 6 # Größe etwas angepasst für bessere Sichtbarkeit

    def apply_force(self, force):
        self.acceleration += force

    def seek(self, target):
        max_speed = self.params['max_speed'].get()
        max_force = self.params['max_force'].get()
        desired = (target - self.position)
        dist = desired.length()

        if dist > 0:
            desired = desired.normalize() * max_speed
            steer = (desired - self.velocity)
            if steer.length() > max_force:
                steer.scale_to_length(max_force)
            return steer
        return Vector2(0, 0)

    # --- Boids Regeln (unverändert) ---
    def separate(self, boids):
        steering = Vector2(0, 0)
        total = 0
        sep_dist = self.params['separation_distance'].get()
        max_speed = self.params['max_speed'].get()
        max_force = self.params['max_force'].get()

        for other in boids:
            try:
                distance = self.position.distance_to(other.position)
            except OverflowError: # Kann bei extremen Werten auftreten
                distance = float('inf')

            if self != other and 0 < distance < sep_dist and other.color == self.color:
                diff = self.position - other.position
                diff /= (distance * distance) if distance > 1 else 1
                steering += diff
                total += 1
        if total > 0:
            steering /= total
            if steering.length() > 0:
                steering = steering.normalize() * max_speed
            steer = steering - self.velocity
            if steer.length() > max_force:
                steer.scale_to_length(max_force)
            return steer
        return Vector2(0, 0)

    def align(self, boids):
        steering = Vector2(0, 0)
        total = 0
        vis_range = self.params['visual_range'].get()
        max_speed = self.params['max_speed'].get()
        max_force = self.params['max_force'].get()

        for other in boids:
            try:
                distance = self.position.distance_to(other.position)
            except OverflowError:
                 distance = float('inf')

            if self != other and 0 < distance < vis_range and other.color == self.color:
                 # Prüfe ob other.velocity nicht None oder Zero ist (kann beim Start passieren)
                 if other.velocity and other.velocity.length_squared() > 0:
                    steering += other.velocity
                    total += 1
        if total > 0:
            steering /= total
            if steering.length() > 0:
                steering = steering.normalize() * max_speed
            steer = steering - self.velocity
            if steer.length() > max_force:
                steer.scale_to_length(max_force)
            return steer
        return Vector2(0, 0)

    def cohere(self, boids):
        center_of_mass = Vector2(0, 0)
        total = 0
        vis_range = self.params['visual_range'].get()

        for other in boids:
            try:
                distance = self.position.distance_to(other.position)
            except OverflowError:
                 distance = float('inf')

            if self != other and 0 < distance < vis_range and other.color == self.color:
                center_of_mass += other.position
                total += 1
        if total > 0:
            center_of_mass /= total
            return self.seek(center_of_mass)
        return Vector2(0, 0)

    # --- Verhalten anwenden (unverändert) ---
    def flock(self, all_boids):
        sep = self.separate(all_boids) * self.params['separation_factor'].get()
        ali = self.align(all_boids) * self.params['alignment_factor'].get()
        coh = self.cohere(all_boids) * self.params['cohesion_factor'].get()

        self.apply_force(sep)
        self.apply_force(ali)
        self.apply_force(coh)

    # --- Update (unverändert) ---
    def update(self):
        max_speed = self.params['max_speed'].get()
        self.velocity += self.acceleration
        # Stelle sicher, dass die Geschwindigkeit nicht Null wird (oder sehr klein)
        # Dies verhindert Probleme bei der Normalisierung oder Richtungsberechnung
        if self.velocity.length_squared() < 0.001:
            angle = random.uniform(0, 2 * math.pi)
            self.velocity = Vector2(math.cos(angle), math.sin(angle)) * 0.1 # Minimale Geschwindigkeit
        elif self.velocity.length() > max_speed:
            self.velocity.scale_to_length(max_speed)

        self.position += self.velocity
        self.acceleration *= 0

    # --- Wrap Borders (unverändert) ---
    def wrap_borders(self, width, height):
        if self.position.x < -self.size: self.position.x = width + self.size
        if self.position.y < -self.size: self.position.y = height + self.size
        if self.position.x > width + self.size: self.position.x = -self.size
        if self.position.y > height + self.size: self.position.y = -self.size

    # --- Draw (MODIFIZIERT) ---
# --- Draw (MODIFIZIERT für längere/spitzere Dreiecke) ---
    def draw(self, screen):
        # Verwende die aktuelle Geschwindigkeit, um die Ausrichtung zu bestimmen
        # Behandle den Fall, dass die Geschwindigkeit (fast) Null ist
        if self.velocity.length_squared() < 0.01: # Kleiner Schwellenwert statt exakt 0
            try:
                draw_pos = (int(self.position.x), int(self.position.y))
                pygame.draw.circle(screen, self.color, draw_pos, int(self.size * 0.8))
            except OverflowError:
                 pass
            return

        # Normierter Richtungsvektor (zeigt in Bewegungsrichtung)
        try:
            heading = self.velocity.normalize()
        except ValueError:
             heading = Vector2(1, 0) # Fallback auf rechts

        # === PARAMETER ZUM ANPASSEN DER FORM ===
        tip_length_factor = 4.0   # >> Erhöhen für längere Spitze (war 1.0)
        base_offset_factor = 0.6  # >> Anpassen, wie weit Basis hinter Mitte (war 0.8)
        width_factor = 0.6        # >> Verringern für schmalere Basis/spitzer (war 0.7)
        # =======================================

        # 1. Punkt: Die Spitze des Dreiecks
        tip = self.position + heading * self.size * tip_length_factor

        # 2. & 3. Punkt: Die Basis des Dreiecks
        base_point = self.position - heading * self.size * base_offset_factor
        perp_vec = Vector2(-heading.y, heading.x) * self.size * width_factor # Schmalere Basis
        base_left = base_point + perp_vec
        base_right = base_point - perp_vec

        # Konvertiere Punkte zu Integer-Tupeln für pygame.draw.polygon
        try:
            points = [
                (int(tip.x), int(tip.y)),
                (int(base_left.x), int(base_left.y)),
                (int(base_right.x), int(base_right.y))
            ]
            # Zeichne das Polygon
            pygame.draw.polygon(screen, self.color, points)
        except OverflowError:
            pass # Koordinaten außerhalb des gültigen Bereichs
# --- Schwarm Klasse (unverändert) ---
class Swarm:
    def __init__(self, initial_count, color, params):
        self.color = color
        self.params = params
        self.boids = []
        self.update_boid_count(initial_count)

    def update_boid_count(self, target_count):
        current_count = len(self.boids)
        delta = target_count - current_count
        global SCREEN_WIDTH, SCREEN_HEIGHT # Zugriff auf globale Bildschirmgröße

        if delta > 0:
            for _ in range(delta):
                # Sicherstellen, dass wir gültige Startpositionen haben
                start_x = random.uniform(0, SCREEN_WIDTH) if SCREEN_WIDTH > 0 else 100
                start_y = random.uniform(0, SCREEN_HEIGHT) if SCREEN_HEIGHT > 0 else 100
                new_boid = Boid(start_x, start_y, self.color, self.params)
                self.boids.append(new_boid)
        elif delta < 0:
            self.boids = self.boids[:target_count]
        return delta != 0

    def run(self, screen, all_boids):
        for boid in self.boids:
            boid.flock(all_boids)
            boid.update()
            boid.wrap_borders(SCREEN_WIDTH, SCREEN_HEIGHT) # Verwende globale Bildschirmgröße
            boid.draw(screen)

# --- Tkinter Setup (unverändert) ---
def setup_tkinter_controls():
    root = tk.Tk()
    root.title("Boid Parameter")
    root.geometry("400x650")
    root.protocol("WM_DELETE_WINDOW", lambda: close_app(root))

    notebook = ttk.Notebook(root)
    notebook.pack(pady=10, padx=10, expand=True, fill="both")

    params_swarm1 = {}
    params_swarm2 = {}

    frame1 = ttk.Frame(notebook, padding="10")
    notebook.add(frame1, text='Schwarm 1 (Blau)')
    create_sliders(frame1, params_swarm1, default_values_swarm1)

    frame2 = ttk.Frame(notebook, padding="10")
    notebook.add(frame2, text='Schwarm 2 (Rot)')
    create_sliders(frame2, params_swarm2, default_values_swarm2)

    return root, params_swarm1, params_swarm2

# --- Create Sliders (unverändert) ---
def create_sliders(parent_frame, params_dict, default_values):
    row_index = 0
    if 'boid_count' not in slider_definitions:
         slider_definitions['boid_count'] = ("Anzahl Fische", 1, 200, 1)

    for key in slider_definitions:
        if key not in default_values: continue

        label_text, min_val, max_val, resolution = slider_definitions[key]

        if key == 'boid_count':
            params_dict[key] = tk.IntVar(value=int(default_values[key]))
            var_type = 'int'
        else:
            params_dict[key] = tk.DoubleVar(value=default_values[key])
            var_type = 'float'

        label = ttk.Label(parent_frame, text=f"{label_text}:")
        label.grid(row=row_index, column=0, sticky="w", padx=5, pady=2)

        value_label = ttk.Label(parent_frame, text="")
        value_label.grid(row=row_index, column=2, sticky="e", padx=5)

        def make_update_callback(k, var, lbl, vtype):
            def callback(val): # val ist der String-Wert vom Slider
                try:
                    current_val = var.get() # Hole den tatsächlichen Wert aus der tk Variable
                    if vtype == 'int':
                        lbl.config(text=f"{current_val}")
                    else:
                        lbl.config(text=f"{current_val:.2f}")
                except tk.TclError: # Kann auftreten, wenn Fenster geschlossen wird
                    pass
            return callback

        update_label_callback = make_update_callback(key, params_dict[key], value_label, var_type)

        slider = ttk.Scale(parent_frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                           variable=params_dict[key], length=200,
                           command=update_label_callback)

        update_label_callback(params_dict[key].get())

        slider.grid(row=row_index, column=1, sticky="ew", padx=5)
        parent_frame.grid_columnconfigure(1, weight=1)
        row_index += 1


# --- Globale Variablen und Definitionen (unverändert) ---
running = True
screen = None

def close_app(root):
    global running
    running = False
    try:
        root.quit()
        root.destroy()
    except tk.TclError:
        pass
    pygame.quit()

slider_definitions = {
    'boid_count': ("Anzahl Fische", 1, 200, 1),
    'separation_factor': ("Separation Stärke", 0.0, 5.0, 0.1),
    'alignment_factor': ("Alignment Stärke", 0.0, 5.0, 0.1),
    'cohesion_factor': ("Kohäsion Stärke", 0.0, 5.0, 0.1),
    'visual_range': ("Sichtweite", 10.0, 200.0, 1.0),
    'separation_distance': ("Min. Abstand", 5.0, 100.0, 1.0),
    'max_speed': ("Max. Tempo", 1.0, 10.0, 0.1),
    'max_force': ("Max. Lenkkraft", 0.01, 1.0, 0.01),
}

default_values_swarm1 = {
    'boid_count': 70,
    'separation_factor': 1.8,
    'alignment_factor': 1.0,
    'cohesion_factor': 1.0,
    'visual_range': 70.0,
    'separation_distance': 25.0,
    'max_speed': 4.0,
    'max_force': 0.2,
}

default_values_swarm2 = {
    'boid_count': 50,
    'separation_factor': 1.5,
    'alignment_factor': 1.2,
    'cohesion_factor': 0.8,
    'visual_range': 50.0,
    'separation_distance': 30.0,
    'max_speed': 5.0,
    'max_force': 0.25,
}

# --- Hauptteil (unverändert bis auf Fehlerbehandlung beim Zeichnen) ---
if __name__ == "__main__":
    root, params1, params2 = setup_tkinter_controls()
    pygame.init()

    try:
        display_info = pygame.display.Info()
        SCREEN_WIDTH = display_info.current_w
        SCREEN_HEIGHT = display_info.current_h
        print(f"Starte im Vollbildmodus: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF) # Double Buffering aktivieren
    except pygame.error as e:
        print(f"Fehler beim Setzen des Vollbildmodus: {e}")
        print("Versuche Fenstermodus 1280x720...")
        SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
        try:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)
        except pygame.error as e2:
             print(f"Fehler beim Setzen des Fenstermodus: {e2}")
             close_app(root)
             exit()


    if not screen:
        print("Fehler: Pygame-Fenster konnte nicht erstellt werden.")
        close_app(root)
        exit()

    pygame.display.set_caption("Boids Simulation")
    clock = pygame.time.Clock()

    # Schwärme erstellen
    try:
        swarm1 = Swarm(int(default_values_swarm1['boid_count']), BLUE, params1)
        swarm2 = Swarm(int(default_values_swarm2['boid_count']), RED, params2)
        all_boids = swarm1.boids + swarm2.boids
    except Exception as e:
        print(f"Fehler beim Erstellen der Schwärme: {e}")
        close_app(root)
        exit()


    # --- Hauptschleife (unverändert) ---
    def simulation_update():
        global running, all_boids, screen

        if not running or screen is None:
            return

        # === Event Handling (Pygame) ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close_app(root)
                return
            if event.type == pygame.KEYDOWN:
                 if event.key == pygame.K_ESCAPE:
                    close_app(root)
                    return
            # Optional: Handle window resize if not fullscreen
            # if event.type == pygame.VIDEORESIZE and not (screen.get_flags() & pygame.FULLSCREEN):
            #     SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
            #     screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)


        # === Boid Anzahl anpassen ===
        needs_rebuild = False
        try:
            target_count1 = params1['boid_count'].get()
            if swarm1.update_boid_count(target_count1):
                needs_rebuild = True

            target_count2 = params2['boid_count'].get()
            if swarm2.update_boid_count(target_count2):
                needs_rebuild = True
        except tk.TclError: # Fenster könnte geschlossen sein
             if running: close_app(root)
             return
        except Exception as e: # Andere Fehler beim Zugriff auf Tk Variablen
             print(f"Fehler beim Update der Boid-Anzahl: {e}")
             if running: close_app(root)
             return


        if needs_rebuild:
            all_boids = swarm1.boids + swarm2.boids

        # === Simulation & Rendering ===
        try:
            screen.fill(BLACK)

            if len(all_boids) > 0:
                 swarm1.run(screen, all_boids)
                 swarm2.run(screen, all_boids)
            else:
                 # Nachricht anzeigen, wenn keine Boids da sind
                 try:
                     font = pygame.font.SysFont(None, 30)
                     text = font.render("Keine Fische zum Anzeigen!", True, WHITE)
                     text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
                     screen.blit(text, text_rect)
                 except Exception as e: # Fehler beim Font-Rendering abfangen
                     print(f"Fehler beim Font Rendering: {e}")


            pygame.display.flip()
            clock.tick(FPS)
        except pygame.error as e:
             print(f"Pygame Render-Fehler: {e}")
             # Optional: Versuchen, weiterzumachen oder App beenden
             # close_app(root)
             # return
        except Exception as e:
             print(f"Unerwarteter Fehler in Rendering/Simulation: {e}")
             # close_app(root) # Im Zweifel beenden
             # return


        # === Tkinter Update (minimal) ===
        try:
            root.update_idletasks()
        except tk.TclError:
             if running:
                 print("Tkinter Fenster wurde extern geschlossen.")
                 close_app(root)
             return

        # Nächsten Update-Aufruf planen (rekursiv)
        if running:
            root.after(max(1, 1000 // FPS), simulation_update) # Mindestens 1ms Verzögerung


    root.after(50, simulation_update)
    root.mainloop()

    print("Tkinter mainloop beendet.")