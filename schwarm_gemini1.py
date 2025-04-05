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

# --- Boid Klasse (weitgehend unverändert) ---
class Boid:
    def __init__(self, x, y, color, params):
        self.position = Vector2(x, y)
        # Verwende max_speed aus params beim Initialisieren
        max_speed_init = params.get('max_speed', tk.DoubleVar(value=4.0)).get() # Standardwert falls nicht bereit
        angle = random.uniform(0, 2 * math.pi)
        self.velocity = Vector2(math.cos(angle), math.sin(angle)) * random.uniform(1, max_speed_init / 2)
        self.acceleration = Vector2(0, 0)
        self.color = color
        self.params = params # Referenz auf die Tkinter Variablen des Schwarms
        self.size = 5 # Größe des Boid-Dreiecks

    def apply_force(self, force):
        self.acceleration += force

    def seek(self, target):
        max_speed = self.params['max_speed'].get()
        max_force = self.params['max_force'].get()
        desired = (target - self.position)
        dist = desired.length()

        if dist > 0:
            # Skaliere die gewünschte Geschwindigkeit basierend auf der Distanz (optional, für sanfteres Ankommen)
            # speed = max_speed if dist > 100 else max_speed * (dist / 100.0)
            # desired = desired.normalize() * speed
            desired = desired.normalize() * max_speed

            steer = (desired - self.velocity)
            if steer.length() > max_force:
                steer.scale_to_length(max_force)
            return steer
        return Vector2(0, 0)

    # --- Boids Regeln ---
    def separate(self, boids):
        steering = Vector2(0, 0)
        total = 0
        sep_dist = self.params['separation_distance'].get()
        max_speed = self.params['max_speed'].get()
        max_force = self.params['max_force'].get()

        for other in boids:
            distance = self.position.distance_to(other.position)
            # Nur nahe Boids des *eigenen* Schwarms berücksichtigen
            if self != other and 0 < distance < sep_dist and other.color == self.color:
                diff = self.position - other.position
                # Stärker abstoßen, je näher sie sind
                diff /= (distance * distance) if distance > 1 else 1 # Vermeide Division durch 0
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
            distance = self.position.distance_to(other.position)
            if self != other and 0 < distance < vis_range and other.color == self.color:
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
            distance = self.position.distance_to(other.position)
            if self != other and 0 < distance < vis_range and other.color == self.color:
                center_of_mass += other.position
                total += 1
        if total > 0:
            center_of_mass /= total
            return self.seek(center_of_mass)
        return Vector2(0, 0)

    # --- Verhalten anwenden ---
    def flock(self, all_boids):
        sep = self.separate(all_boids) * self.params['separation_factor'].get()
        ali = self.align(all_boids) * self.params['alignment_factor'].get()
        coh = self.cohere(all_boids) * self.params['cohesion_factor'].get()

        self.apply_force(sep)
        self.apply_force(ali)
        self.apply_force(coh)

    # --- Update und Zeichnen ---
    def update(self):
        max_speed = self.params['max_speed'].get()
        # Geschwindigkeit aktualisieren und begrenzen
        self.velocity += self.acceleration
        if self.velocity.length() > max_speed:
            self.velocity.scale_to_length(max_speed)

        self.position += self.velocity
        self.acceleration *= 0 # Beschleunigung für nächsten Frame zurücksetzen

    def wrap_borders(self, width, height):
        if self.position.x < -self.size: self.position.x = width + self.size
        if self.position.y < -self.size: self.position.y = height + self.size
        if self.position.x > width + self.size: self.position.x = -self.size
        if self.position.y > height + self.size: self.position.y = -self.size

    def draw(self, screen):
        angle = self.velocity.angle_to(Vector2(1, 0)) # Winkel zur x-Achse
        p1 = self.position + Vector2(self.size * 1.5, 0).rotate(angle)
        p2 = self.position + Vector2(-self.size * 0.75, self.size * 0.75).rotate(angle)
        p3 = self.position + Vector2(-self.size * 0.75, -self.size * 0.75).rotate(angle)
        pygame.draw.polygon(screen, self.color, [p1, p2, p3])


# --- Schwarm Klasse ---
class Swarm:
    def __init__(self, initial_count, color, params):
        self.color = color
        self.params = params
        # Boids werden jetzt basierend auf dem initialen Slider-Wert erstellt
        self.boids = []
        self.update_boid_count(initial_count) # Erstellt die initialen Boids

    def update_boid_count(self, target_count):
        current_count = len(self.boids)
        delta = target_count - current_count

        if delta > 0: # Boids hinzufügen
            for _ in range(delta):
                # Füge neue Boids an zufälligen Positionen hinzu
                new_boid = Boid(random.uniform(0, SCREEN_WIDTH),
                                random.uniform(0, SCREEN_HEIGHT),
                                self.color, self.params)
                self.boids.append(new_boid)
        elif delta < 0: # Boids entfernen
             # Entferne Boids vom Ende der Liste
            self.boids = self.boids[:target_count]

        # Gibt zurück, ob sich die Anzahl geändert hat
        return delta != 0

    def run(self, screen, all_boids):
        for boid in self.boids:
            boid.flock(all_boids)
            boid.update()
            boid.wrap_borders(SCREEN_WIDTH, SCREEN_HEIGHT)
            boid.draw(screen)

# --- Tkinter Setup für Parameter ---
def setup_tkinter_controls():
    root = tk.Tk()
    root.title("Boid Parameter")
    root.geometry("400x650") # Etwas breiter/höher für die neuen Slider
    root.protocol("WM_DELETE_WINDOW", lambda: close_app(root))

    notebook = ttk.Notebook(root)
    notebook.pack(pady=10, padx=10, expand=True, fill="both")

    params_swarm1 = {}
    params_swarm2 = {}

    # Frame und Slider für Schwarm 1 (Blau)
    frame1 = ttk.Frame(notebook, padding="10")
    notebook.add(frame1, text='Schwarm 1 (Blau)')
    create_sliders(frame1, params_swarm1, default_values_swarm1)

    # Frame und Slider für Schwarm 2 (Rot)
    frame2 = ttk.Frame(notebook, padding="10")
    notebook.add(frame2, text='Schwarm 2 (Rot)')
    create_sliders(frame2, params_swarm2, default_values_swarm2)

    # Kein Pygame Frame mehr hier, da Pygame im eigenen Fenster läuft
    return root, params_swarm1, params_swarm2

def create_sliders(parent_frame, params_dict, default_values):
    row_index = 0
    # Füge 'boid_count' zu den Slider-Definitionen hinzu, falls nicht schon geschehen
    if 'boid_count' not in slider_definitions:
         slider_definitions['boid_count'] = ("Anzahl Fische", 1, 200, 1) # Min 1, Max 200

    # Verwende die Reihenfolge aus slider_definitions
    for key in slider_definitions:
        if key not in default_values: continue # Überspringe, wenn kein Default-Wert existiert

        label_text, min_val, max_val, resolution = slider_definitions[key]

        # Unterscheide zwischen Integer (Anzahl) und Float (andere Parameter)
        if key == 'boid_count':
            params_dict[key] = tk.IntVar(value=int(default_values[key]))
            var_type = 'int'
        else:
            params_dict[key] = tk.DoubleVar(value=default_values[key])
            var_type = 'float'

        label = ttk.Label(parent_frame, text=f"{label_text}:")
        label.grid(row=row_index, column=0, sticky="w", padx=5, pady=2)

        # Wertanzeige-Label
        value_label = ttk.Label(parent_frame, text="") # Wird unten initialisiert
        value_label.grid(row=row_index, column=2, sticky="e", padx=5)

        # Callback zum Aktualisieren des Wertanzeige-Labels
        def make_update_callback(k, var, lbl, vtype):
            def callback(val):
                if vtype == 'int':
                    lbl.config(text=f"{var.get()}") # Keine Dezimalstellen für int
                else:
                    lbl.config(text=f"{var.get():.2f}") # 2 Dezimalstellen für float
            return callback

        update_label_callback = make_update_callback(key, params_dict[key], value_label, var_type)

        slider = ttk.Scale(parent_frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                           variable=params_dict[key], length=200, # Slider etwas länger
                           command=update_label_callback)

        # Initialwert im Label anzeigen
        update_label_callback(params_dict[key].get())

        slider.grid(row=row_index, column=1, sticky="ew", padx=5)
        parent_frame.grid_columnconfigure(1, weight=1)
        row_index += 1

# --- Globale Variablen und Definitionen ---
running = True
screen = None # Globale Variable für den Pygame Screen

def close_app(root):
    global running
    running = False
    # Beende zuerst Tkinter, falls es noch läuft
    try:
        root.quit()
        root.destroy()
    except tk.TclError: # Fenster könnte schon zerstört sein
        pass
    # Beende Pygame
    pygame.quit()


# Slider Definitionen: key: (Label, Min, Max, Auflösung - nicht direkt genutzt)
slider_definitions = {
    # NEU: Slider für Anzahl
    'boid_count': ("Anzahl Fische", 1, 200, 1),
    # Bisherige Parameter
    'separation_factor': ("Separation Stärke", 0.0, 5.0, 0.1),
    'alignment_factor': ("Alignment Stärke", 0.0, 5.0, 0.1),
    'cohesion_factor': ("Kohäsion Stärke", 0.0, 5.0, 0.1),
    'visual_range': ("Sichtweite", 10.0, 200.0, 1.0),
    'separation_distance': ("Min. Abstand", 5.0, 100.0, 1.0),
    'max_speed': ("Max. Tempo", 1.0, 10.0, 0.1),
    'max_force': ("Max. Lenkkraft", 0.01, 1.0, 0.01),
}

# Standardwerte für die Schwärme (inkl. Anzahl)
default_values_swarm1 = {
    'boid_count': 200, # Startanzahl
    'separation_factor': 1.8,
    'alignment_factor': 1.0,
    'cohesion_factor': 1.0,
    'visual_range': 70.0,
    'separation_distance': 25.0,
    'max_speed': 4.0,
    'max_force': 0.2,
}

default_values_swarm2 = {
    'boid_count': 300, # Startanzahl
    'separation_factor': 1.5,
    'alignment_factor': 1.2,
    'cohesion_factor': 0.8,
    'visual_range': 50.0,
    'separation_distance': 30.0,
    'max_speed': 5.0,
    'max_force': 0.25,
}

# --- Hauptteil ---
if __name__ == "__main__":
    # Tkinter zuerst initialisieren (läuft in separatem Fenster)
    root, params1, params2 = setup_tkinter_controls()

    # Pygame initialisieren
    pygame.init()

    # Bildschirmgröße für Vollbild ermitteln
    display_info = pygame.display.Info()
    SCREEN_WIDTH = display_info.current_w
    SCREEN_HEIGHT = display_info.current_h
    print(f"Starte im Vollbildmodus: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")

    # Pygame im Vollbildmodus starten (eigenes Fenster)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    if not screen:
        print("Fehler: Pygame-Fenster konnte nicht erstellt werden.")
        close_app(root)
        exit()

    pygame.display.set_caption("Boids Simulation (Fullscreen)")
    clock = pygame.time.Clock()

    # Schwärme erstellen (mit initialer Anzahl aus den Defaults)
    swarm1 = Swarm(int(default_values_swarm1['boid_count']), BLUE, params1)
    swarm2 = Swarm(int(default_values_swarm2['boid_count']), RED, params2)
    all_boids = swarm1.boids + swarm2.boids # Initiale Gesamtliste

    # --- Hauptschleife (angetrieben durch Tkinter) ---
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
                 if event.key == pygame.K_ESCAPE: # ESC beendet den Vollbildmodus/App
                    close_app(root)
                    return

        # === Boid Anzahl anpassen ===
        needs_rebuild = False
        target_count1 = params1['boid_count'].get()
        if swarm1.update_boid_count(target_count1):
            needs_rebuild = True

        target_count2 = params2['boid_count'].get()
        if swarm2.update_boid_count(target_count2):
            needs_rebuild = True

        # Wenn Boids hinzugefügt/entfernt wurden, Gesamtliste neu erstellen
        if needs_rebuild:
            all_boids = swarm1.boids + swarm2.boids
            # print(f"Anzahl aktualisiert: S1={len(swarm1.boids)}, S2={len(swarm2.boids)}")

        # === Simulation & Rendering ===
        screen.fill(BLACK)

        # Schwärme ausführen und zeichnen
        if len(all_boids) > 0: # Nur simulieren, wenn Boids vorhanden sind
             swarm1.run(screen, all_boids)
             swarm2.run(screen, all_boids)
        else:
            # Optional: Nachricht anzeigen, wenn keine Boids da sind
             font = pygame.font.SysFont(None, 30)
             text = font.render("Keine Fische zum Anzeigen!", True, WHITE)
             text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
             screen.blit(text, text_rect)


        pygame.display.flip() # Pygame Anzeige aktualisieren
        clock.tick(FPS) # Framerate begrenzen

        # === Tkinter Update (minimal) ===
        try:
            root.update_idletasks() # Nur Idle-Tasks verarbeiten (weniger CPU-intensiv)
            # root.update() # Vollständiges Update (kann mehr CPU kosten)
        except tk.TclError: # Fenster könnte geschlossen worden sein
             if running: # Nur wenn nicht schon beendet
                 print("Tkinter Fenster wurde extern geschlossen.")
                 close_app(root) # App sauber beenden
             return # Schleife verlassen

        # Nächsten Update-Aufruf planen (rekursiv)
        root.after(1000 // FPS, simulation_update)


    # Starte die Simulationsschleife über Tkinter's after Methode
    root.after(50, simulation_update) # Kurze Startverzögerung

    # Starte die Tkinter Hauptschleife (blockierend)
    root.mainloop()

    # Wird erreicht, nachdem root.quit() aufgerufen wurde
    print("Tkinter mainloop beendet.")
    # Pygame quit wird in close_app() aufgerufen