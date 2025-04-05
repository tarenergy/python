# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import pygame
import random
import math
import os
from pygame.math import Vector2 # Pygame's Vector2 ist sehr praktisch
import time # Für wanderndes Verhalten

# --- Pygame Fenster Setup ---
SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0
FPS = 60

# --- Farben ---
WHITE = (255, 255, 255)
RED = (255, 50, 50)
BLUE = (50, 50, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100) # Farbe für den Hai
DARK_GRAY = (50, 50, 50) # Dunkleres Grau

# --- Boid Klasse ---
class Boid:
    def __init__(self, x, y, color, params):
        self.position = Vector2(x, y)
        max_speed_init = params.get('max_speed', tk.DoubleVar(value=4.0)).get()
        angle = random.uniform(0, 2 * math.pi)
        initial_speed = random.uniform(1, max(1.1, max_speed_init / 2))
        self.velocity = Vector2(math.cos(angle), math.sin(angle)) * initial_speed
        self.acceleration = Vector2(0, 0)
        self.color = color
        self.params = params
        self.size = 6

    def apply_force(self, force):
        if force and math.isfinite(force.x) and math.isfinite(force.y):
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

    def separate(self, boids):
        steering = Vector2(0, 0); total = 0
        sep_dist = self.params['separation_distance'].get()
        max_speed = self.params['max_speed'].get(); max_force = self.params['max_force'].get()
        for other in boids:
            try: dist_sq = self.position.distance_squared_to(other.position)
            except OverflowError: dist_sq = float('inf')
            if self != other and 0 < dist_sq < sep_dist * sep_dist and other.color == self.color:
                distance = math.sqrt(dist_sq)
                diff = self.position - other.position
                diff /= (distance * distance) if distance > 1 else 1
                steering += diff; total += 1
        if total > 0:
            steering /= total
            if steering.length() > 0: steering = steering.normalize() * max_speed
            steer = steering - self.velocity
            if steer.length() > max_force: steer.scale_to_length(max_force)
            return steer
        return Vector2(0, 0)

    def align(self, boids):
        steering = Vector2(0, 0); total = 0
        vis_range = self.params['visual_range'].get()
        max_speed = self.params['max_speed'].get(); max_force = self.params['max_force'].get()
        for other in boids:
            try: dist_sq = self.position.distance_squared_to(other.position)
            except OverflowError: dist_sq = float('inf')
            if self != other and 0 < dist_sq < vis_range * vis_range and other.color == self.color:
                 if other.velocity and other.velocity.length_squared() > 0: steering += other.velocity; total += 1
        if total > 0:
            steering /= total
            if steering.length() > 0: steering = steering.normalize() * max_speed
            steer = steering - self.velocity
            if steer.length() > max_force: steer.scale_to_length(max_force)
            return steer
        return Vector2(0, 0)

    def cohere(self, boids):
        center_of_mass = Vector2(0, 0); total = 0
        vis_range = self.params['visual_range'].get()
        for other in boids:
            try: dist_sq = self.position.distance_squared_to(other.position)
            except OverflowError: dist_sq = float('inf')
            if self != other and 0 < dist_sq < vis_range * vis_range and other.color == self.color:
                center_of_mass += other.position; total += 1
        if total > 0: center_of_mass /= total; return self.seek(center_of_mass)
        return Vector2(0, 0)

    def avoid(self, boids):
        steering = Vector2(0, 0); total = 0
        avoid_range = self.params['avoidance_range'].get()
        max_speed = self.params['max_speed'].get(); max_force = self.params['max_force'].get()
        for other in boids:
            try: dist_sq = self.position.distance_squared_to(other.position)
            except OverflowError: dist_sq = float('inf')
            if self != other and 0 < dist_sq < avoid_range * avoid_range and other.color != self.color:
                distance = math.sqrt(dist_sq)
                diff = self.position - other.position
                diff /= (distance * distance) if distance > 1 else 1
                steering += diff; total += 1
        if total > 0:
            steering /= total
            if steering.length() > 0: steering = steering.normalize() * max_speed
            steer = steering - self.velocity
            if steer.length() > max_force: steer.scale_to_length(max_force)
            return steer
        return Vector2(0, 0)

    def flock(self, all_boids):
        sep = self.separate(all_boids) * self.params['separation_factor'].get()
        ali = self.align(all_boids) * self.params['alignment_factor'].get()
        coh = self.cohere(all_boids) * self.params['cohesion_factor'].get()
        avo = self.avoid(all_boids) * self.params['avoidance_factor'].get()
        self.apply_force(sep); self.apply_force(ali); self.apply_force(coh); self.apply_force(avo)

    def update(self):
        max_speed = self.params['max_speed'].get(); self.velocity += self.acceleration
        vel_len_sq = self.velocity.length_squared()
        if vel_len_sq < 0.001:
            angle = random.uniform(0, 2 * math.pi); self.velocity = Vector2(math.cos(angle), math.sin(angle)) * 0.1
        elif vel_len_sq > max_speed * max_speed: self.velocity.scale_to_length(max_speed)
        self.position += self.velocity; self.acceleration *= 0

    def wrap_borders(self, width, height):
        buffer = self.size * 2
        if self.position.x < -buffer: self.position.x = width + buffer
        if self.position.y < -buffer: self.position.y = height + buffer
        if self.position.x > width + buffer: self.position.x = -buffer
        if self.position.y > height + buffer: self.position.y = -buffer

    def draw(self, screen):
        if self.velocity.length_squared() < 0.01:
            try: pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), int(self.size * 0.8))
            except OverflowError: pass; return
        try: heading = self.velocity.normalize()
        except ValueError: heading = Vector2(1, 0)
        tip_length_factor = 2.0; base_offset_factor = 0.6; width_factor = 0.4
        tip = self.position + heading * self.size * tip_length_factor
        base_point = self.position - heading * self.size * base_offset_factor
        perp_vec = Vector2(-heading.y, heading.x) * self.size * width_factor
        base_left = base_point + perp_vec; base_right = base_point - perp_vec
        try:
            points = [(int(tip.x), int(tip.y)), (int(base_left.x), int(base_left.y)), (int(base_right.x), int(base_right.y))]
            pygame.draw.polygon(screen, self.color, points)
        except OverflowError: pass

# --- Shark Klasse ---
class Shark:
    def __init__(self, x, y, params): # Nimmt params entgegen
        self.position = Vector2(x, y)
        self.velocity = Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 2
        self.acceleration = Vector2(0, 0)
        self.color = DARK_GRAY
        self.outline_color = GRAY
        self.size = 12
        self.params = params # Referenz auf Hai-Parameter (tk.Vars)
        self.wander_angle = random.uniform(0, 2 * math.pi)
        # Initialisiere eat_radius_sq
        try:
            current_eat_radius = self.params['shark_eat_radius'].get()
            self.eat_radius_sq = current_eat_radius * current_eat_radius
        except KeyError: eat_radius_fallback = 13.0; self.eat_radius_sq = eat_radius_fallback * eat_radius_fallback
    def apply_force(self, force):
         if force and math.isfinite(force.x) and math.isfinite(force.y): self.acceleration += force
    def seek(self, target_pos):
        max_speed=self.params['shark_max_speed'].get(); max_force=self.params['shark_max_force'].get()
        desired = (target_pos - self.position); dist = desired.length()
        if dist > 0:
            desired = desired.normalize() * max_speed; steer = (desired - self.velocity)
            if steer.length() > max_force: steer.scale_to_length(max_force)
            return steer
        return Vector2(0, 0)
    def hunt(self, all_boids):
        closest_boid = None; perception_radius = self.params['shark_perception_radius'].get()
        min_dist_sq = perception_radius * perception_radius
        for boid in all_boids:
            try:
                dist_sq = self.position.distance_squared_to(boid.position)
                if dist_sq < min_dist_sq: min_dist_sq = dist_sq; closest_boid = boid
            except OverflowError: continue
            except AttributeError: continue
        if closest_boid: seek_force = self.seek(closest_boid.position); self.apply_force(seek_force); return True
        else: self.wander(); return False
    def wander(self):
        max_force = self.params['shark_max_force'].get()
        self.wander_angle += random.uniform(-0.3, 0.3)
        wander_target_direction = Vector2(math.cos(self.wander_angle), math.sin(self.wander_angle))
        wander_force = wander_target_direction * max_force * 0.5; self.apply_force(wander_force)
    def update(self):
        max_speed = self.params['shark_max_speed'].get(); self.velocity += self.acceleration
        vel_len_sq = self.velocity.length_squared(); max_speed_sq = max_speed * max_speed
        if vel_len_sq > max_speed_sq: self.velocity.scale_to_length(max_speed)
        self.position += self.velocity; self.acceleration *= 0
    def wrap_borders(self, width, height):
        max_speed=self.params['shark_max_speed'].get(); max_force=self.params['shark_max_force'].get()
        buffer = self.size * 2; steer = Vector2()
        if self.position.x < buffer: desired = Vector2(max_speed, self.velocity.y); steer = desired - self.velocity
        elif self.position.x > width - buffer: desired = Vector2(-max_speed, self.velocity.y); steer = desired - self.velocity
        if self.position.y < buffer: desired = Vector2(self.velocity.x, max_speed); steer = desired - self.velocity
        elif self.position.y > height - buffer: desired = Vector2(self.velocity.x, -max_speed); steer = desired - self.velocity
        if steer.length_squared() > 0:
             if steer.length() > max_force * 2: steer.scale_to_length(max_force * 2)
             self.apply_force(steer)
    def draw(self, screen):
        if self.velocity.length_squared() < 0.01: heading = Vector2(1, 0)
        else:
            try: heading = self.velocity.normalize()
            except ValueError: heading = Vector2(1, 0)
        tip_length_factor = 2.5; base_offset_factor = 0.8; width_factor = 0.5
        tip = self.position + heading * self.size * tip_length_factor
        base_point = self.position - heading * self.size * base_offset_factor
        perp_vec = Vector2(-heading.y, heading.x) * self.size * width_factor
        base_left = base_point + perp_vec; base_right = base_point - perp_vec
        try:
            points = [(int(tip.x), int(tip.y)), (int(base_left.x), int(base_left.y)), (int(base_right.x), int(base_right.y))]
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, self.outline_color, points, 2)
        except OverflowError: pass


# --- Schwarm Klasse ---
class Swarm:
    def __init__(self, initial_count, color, params):
        self.color = color
        self.params = params
        self.boids = []

    def initialize_boids(self, initial_count):
         self.update_boid_count(initial_count)

    def update_boid_count(self, target_count):
        target_count = int(target_count)
        current_count = len(self.boids)
        delta = target_count - current_count
        global SCREEN_WIDTH, SCREEN_HEIGHT
        list_changed = False
        if delta > 0:
            for _ in range(delta):
                start_x = random.uniform(0, SCREEN_WIDTH) if SCREEN_WIDTH > 0 else 100
                start_y = random.uniform(0, SCREEN_HEIGHT) if SCREEN_HEIGHT > 0 else 100
                new_boid = Boid(start_x, start_y, self.color, self.params)
                self.boids.append(new_boid)
            list_changed = True
        elif delta < 0:
             if target_count < current_count:
                 self.boids = self.boids[:target_count]
                 list_changed = True
        return list_changed

    def run(self, screen, all_boids):
        for boid in self.boids: boid.flock(all_boids)
        for boid in self.boids:
            boid.update()
            boid.wrap_borders(SCREEN_WIDTH, SCREEN_HEIGHT)
            boid.draw(screen)


# --- Globale Variablen und Definitionen ---
running = True
screen = None

slider_definitions = {
    'boid_count': ("Anzahl Fische", 1, 250, 1),
    'separation_factor': ("Separation Stärke", 0.0, 5.0, 0.1),
    'alignment_factor': ("Alignment Stärke", 0.0, 5.0, 0.1),
    'cohesion_factor': ("Kohäsion Stärke", 0.0, 5.0, 0.1),
    'visual_range': ("Sichtweite (Gruppe)", 10.0, 200.0, 1.0),
    'separation_distance': ("Min. Abstand (Gruppe)", 5.0, 100.0, 1.0),
    'avoidance_factor': ("Abneigungs-Stärke", 0.0, 10.0, 0.1),
    'avoidance_range': ("Abneigungs-Reichweite", 10.0, 250.0, 1.0),
    'max_speed': ("Max. Tempo (Fisch)", 1.0, 10.0, 0.1),
    'max_force': ("Max. Lenkkraft (Fisch)", 0.01, 1.0, 0.01),
    'shark_max_speed': ("Max. Tempo (Hai)", 1.0, 15.0, 0.1),
    'shark_max_force': ("Max. Lenkkraft (Hai)", 0.01, 1.5, 0.01),
    'shark_perception_radius': ("Sichtweite (Hai)", 50.0, 400.0, 1.0),
    'shark_eat_radius': ("Fressradius (Hai)", 5.0, 50.0, 0.5),
}
default_values_swarm1 = {
    'boid_count': 80,
    'separation_factor': 1.8, 'alignment_factor': 1.0, 'cohesion_factor': 1.0,
    'visual_range': 70.0, 'separation_distance': 25.0,
    'avoidance_factor': 3.0, 'avoidance_range': 80.0,
    'max_speed': 4.0, 'max_force': 0.2,
}
default_values_swarm2 = {
    'boid_count': 60,
    'separation_factor': 1.5, 'alignment_factor': 1.2, 'cohesion_factor': 0.8,
    'visual_range': 50.0, 'separation_distance': 30.0,
    'avoidance_factor': 2.5, 'avoidance_range': 90.0,
    'max_speed': 5.0, 'max_force': 0.25,
}
default_values_shark = {
    'shark_max_speed': 3.8, 'shark_max_force': 0.35,
    'shark_perception_radius': 170.0, 'shark_eat_radius': 13.0,
}


# --- Tkinter Hilfsfunktionen ---
def close_app(root):
    global running
    if not running: return
    running = False
    print("Beende Anwendung...")
    try: root.destroy(); print("Tkinter beendet.")
    except tk.TclError: print("Tkinter bereits beendet oder Fehler.")
    except Exception as e: print(f"Anderer Fehler beim Beenden von Tkinter: {e}")
    pygame.quit(); print("Pygame beendet.")

def create_sliders(parent_frame, params_dict, default_values):
    row_index = 0
    for key in default_values.keys():
        if key not in slider_definitions: continue
        label_text, min_val, max_val, resolution = slider_definitions[key]
        row_frame = ttk.Frame(parent_frame)
        row_frame.grid(row=row_index, column=0, columnspan=4, sticky="ew", pady=1)
        row_frame.columnconfigure(1, weight=1)
        if key == 'boid_count':
            params_dict[key] = tk.IntVar(value=int(default_values[key]))
            var_type = 'int'
        else:
            params_dict[key] = tk.DoubleVar(value=default_values[key])
            var_type = 'float'
        label = ttk.Label(row_frame, text=f"{label_text}:", width=22, anchor="w")
        label.grid(row=0, column=0, sticky="w", padx=5)
        target_value_label = ttk.Label(row_frame, text="", width=5, anchor="e")
        target_value_label.grid(row=0, column=2, sticky="e", padx=2)
        if key == 'boid_count':
            actual_count_label = ttk.Label(row_frame, text="Aktuell: ?", width=10, anchor="w")
            actual_count_label.grid(row=0, column=3, sticky="w", padx=(10, 0))
            params_dict['boid_count_actual_label'] = actual_count_label
        def make_update_callback(k, var, lbl, vtype):
            def callback(val):
                try:
                    current_val = var.get()
                    if vtype == 'int': lbl.config(text=f"{current_val}")
                    else: lbl.config(text=f"{current_val:.2f}")
                except tk.TclError: pass
            return callback
        update_target_label_callback = make_update_callback(key, params_dict[key], target_value_label, var_type)
        slider = ttk.Scale(row_frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                           variable=params_dict[key], length=150,
                           command=update_target_label_callback)
        update_target_label_callback(params_dict[key].get())
        slider.grid(row=0, column=1, sticky="ew", padx=5)
        row_index += 1
    return row_index # Gebe nächste Zeilennummer zurück

# Funktion zum Auffüllen (jetzt global)
def replenish_swarm(params_dict):
    """Füllt den entsprechenden Schwarm auf den Slider-Zielwert auf."""
    global swarm1, swarm2, all_boids, SCREEN_WIDTH, SCREEN_HEIGHT

    target_swarm = None
    swarm_name = "?"
    if params_dict is params1: target_swarm = swarm1; swarm_name = "Schwarm 1 (Blau)"
    elif params_dict is params2: target_swarm = swarm2; swarm_name = "Schwarm 2 (Rot)"

    if target_swarm:
        try:
            target_count = params_dict['boid_count'].get()
            current_count = len(target_swarm.boids)
            diff = target_count - current_count

            if diff > 0:
                print(f"Fülle {swarm_name} um {diff} Boids auf...")
                # Rufe die Methode auf, die hinzufügen kann
                target_swarm.update_boid_count(target_count)
                all_boids = swarm1.boids + swarm2.boids # Globale Liste neu bauen!
                print(f"Auffüllen fertig. Neue Anzahl: {len(target_swarm.boids)}. Gesamt: {len(all_boids)}")
                if 'boid_count_actual_label' in params_dict:
                    params_dict['boid_count_actual_label'].config(text=f"Aktuell: {len(target_swarm.boids)}")
            else: print("Keine Boids zum Auffüllen benötigt.")
        except tk.TclError: print("Fehler beim Auffüllen (Tkinter nicht bereit?).")
        except Exception as e: print(f"Fehler beim Auffüllen von {swarm_name}: {e}")
    else: print("Fehler: Unbekanntes Parameter-Dictionary für replenish_swarm.")

# Setup Tkinter Controls Funktion (fügt Buttons hinzu)
def setup_tkinter_controls():
    root = tk.Tk()
    root.title("Boid Parameter")
    root.geometry("550x750")
    root.protocol("WM_DELETE_WINDOW", lambda: close_app(root))
    notebook = ttk.Notebook(root)
    notebook.pack(pady=10, padx=10, expand=True, fill="both")
    params_swarm1 = {}; params_swarm2 = {}; params_shark = {}

    # --- Tab Schwarm 1 ---
    frame1 = ttk.Frame(notebook, padding="10")
    notebook.add(frame1, text='Schwarm 1 (Blau)')
    last_row1 = create_sliders(frame1, params_swarm1, default_values_swarm1)
    button1 = ttk.Button(frame1, text="Schwarm 1 Auffüllen",
                         # KORREKTUR: Verwende params_swarm1
                         command=lambda p=params_swarm1: replenish_swarm(p))
    button1.grid(row=last_row1, column=0, columnspan=4, pady=(10, 0))

    # --- Tab Schwarm 2 ---
    frame2 = ttk.Frame(notebook, padding="10")
    notebook.add(frame2, text='Schwarm 2 (Rot)')
    last_row2 = create_sliders(frame2, params_swarm2, default_values_swarm2)
    button2 = ttk.Button(frame2, text="Schwarm 2 Auffüllen",
                         # KORREKTUR: Verwende params_swarm2
                         command=lambda p=params_swarm2: replenish_swarm(p))
    button2.grid(row=last_row2, column=0, columnspan=4, pady=(10, 0))

    # --- Tab Hai ---
    frame_shark = ttk.Frame(notebook, padding="10")
    notebook.add(frame_shark, text='Hai Parameter')
    create_sliders(frame_shark, params_shark, default_values_shark)

    return root, params_swarm1, params_swarm2, params_shark


# --- Hauptteil ---
if __name__ == "__main__":
    root, params1, params2, params_shark = setup_tkinter_controls()
    pygame.init()
    pygame.font.init()

    # Bildschirm Setup
    try:
        display_info = pygame.display.Info()
        SCREEN_WIDTH = display_info.current_w; SCREEN_HEIGHT = display_info.current_h
        print(f"Versuche Vollbildmodus: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        print("Vollbildmodus erfolgreich gesetzt.")
    except pygame.error as e:
        print(f"Fehler Vollbild: {e}. Versuche Fenstermodus 1280x720...")
        SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
        try: screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)
        except pygame.error as e2: print(f"Fehler Fenstermodus: {e2}"); close_app(root); exit()
    if not screen: print("Fehler: Pygame Fenster konnte nicht erstellt werden."); close_app(root); exit()

    pygame.display.set_caption("Boids Simulation mit Hai")
    clock = pygame.time.Clock()
    app_font = None
    try: app_font = pygame.font.SysFont(None, 30)
    except Exception as e: print(f"Warnung: Schriftart nicht geladen: {e}")

    # Schwärme und Hai erstellen
    try:
        # Deklariere swarm1 und swarm2 hier als global für replenish_swarm
        global swarm1, swarm2
        swarm1 = Swarm(0, BLUE, params1); swarm2 = Swarm(0, RED, params2)
        swarm1.initialize_boids(int(default_values_swarm1['boid_count']))
        swarm2.initialize_boids(int(default_values_swarm2['boid_count']))
        all_boids = swarm1.boids + swarm2.boids
        shark = Shark(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, params_shark) # Übergebe Hai-Params
        print(f"Init: S1={len(swarm1.boids)}, S2={len(swarm2.boids)}. Hai erstellt.")
    except Exception as e: print(f"Fehler Erstellung: {e}"); close_app(root); exit()


    # --- Hauptschleife (angetrieben durch Tkinter) ---
    def simulation_update():
        global running, all_boids, screen, app_font, shark, swarm1, swarm2, params1, params2, params_shark

        if not running or screen is None: return

        # === Event Handling (Pygame) ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT: close_app(root); return
            if event.type == pygame.KEYDOWN:
                 if event.key == pygame.K_ESCAPE: close_app(root); return
            if event.type == pygame.VIDEORESIZE and not (screen.get_flags() & pygame.FULLSCREEN):
                 global SCREEN_WIDTH, SCREEN_HEIGHT
                 SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                 try: screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)
                 except pygame.error as e: print(f"Fehler Resize: {e}")

        # === Boid Anzahl anpassen (Slider reduziert nur noch) ===
        rebuild_all_boids_due_to_slider = False
        try:
            target_count1 = params1['boid_count'].get(); current_count1 = len(swarm1.boids)
            if target_count1 < current_count1:
                if swarm1.update_boid_count(target_count1): rebuild_all_boids_due_to_slider = True
            target_count2 = params2['boid_count'].get(); current_count2 = len(swarm2.boids)
            if target_count2 < current_count2:
                 if swarm2.update_boid_count(target_count2): rebuild_all_boids_due_to_slider = True
        except tk.TclError:
             if running: close_app(root); return
        except Exception as e:
             print(f"Fehler Update Boid Anzahl (Slider): {e}");
             if running: close_app(root); return

        # Baue globale Liste nur neu auf, wenn Slider Fische *entfernt* hat
        if rebuild_all_boids_due_to_slider:
            all_boids = swarm1.boids + swarm2.boids

        # === Hai Fressradius aktualisieren ===
        eat_radius_sq = shark.eat_radius_sq
        try:
             current_eat_radius = params_shark['shark_eat_radius'].get()
             eat_radius_sq = current_eat_radius * current_eat_radius
             shark.eat_radius_sq = eat_radius_sq # Aktualisiere internen Wert
        except tk.TclError: pass
        except KeyError: pass
        except Exception as e: print(f"Fehler Update Hai Radius: {e}")

        # === Hai frisst Fische ===
        eaten_this_frame = set()
        boids_to_check = list(all_boids)

        for boid in boids_to_check:
            try:
                dist_sq = shark.position.distance_squared_to(boid.position)
                if dist_sq < eat_radius_sq: # Verwende aktualisierten Wert
                    eaten_this_frame.add(boid)
            except Exception: continue

        # === Listen neu aufbauen, wenn etwas gefressen wurde ===
        if eaten_this_frame:
            # print(f"Hai hat {len(eaten_this_frame)} Fisch(e) gefressen!") # Debug
            old_s1_count = len(swarm1.boids)
            swarm1.boids = [b for b in swarm1.boids if b not in eaten_this_frame]
            removed_s1 = old_s1_count - len(swarm1.boids)
            old_s2_count = len(swarm2.boids)
            swarm2.boids = [b for b in swarm2.boids if b not in eaten_this_frame]
            removed_s2 = old_s2_count - len(swarm2.boids)
            all_boids = swarm1.boids + swarm2.boids # Globale Liste neu bauen!
            # print(f"  Removed: {removed_s1} from S1, {removed_s2} from S2. Verbleibend all: {len(all_boids)}, S1: {len(swarm1.boids)}, S2: {len(swarm2.boids)}") # Debug


        # === Simulation & Rendering ===
        try:
            screen.fill(BLACK)
            if len(all_boids) > 0:
                 swarm1.run(screen, all_boids)
                 swarm2.run(screen, all_boids)
            elif app_font:
                 text = app_font.render("Alle Fische gefressen!", True, WHITE)
                 text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
                 screen.blit(text, text_rect)

            shark.hunt(all_boids)
            shark.update()
            shark.wrap_borders(SCREEN_WIDTH, SCREEN_HEIGHT)
            shark.draw(screen)

            pygame.display.flip()
            clock.tick(FPS)
        except pygame.error as e: print(f"Pygame Render/Flip-Fehler: {e}")
        except Exception as e: print(f"Unerwarteter Fehler in Rendering/Simulation: {e}")

        # === Tkinter Update (inkl. aktueller Anzahl) ===
        try:
            if root.winfo_exists():
                actual_count1 = len(swarm1.boids)
                actual_count2 = len(swarm2.boids)
                if 'boid_count_actual_label' in params1:
                    params1['boid_count_actual_label'].config(text=f"Aktuell: {actual_count1}")
                if 'boid_count_actual_label' in params2:
                    params2['boid_count_actual_label'].config(text=f"Aktuell: {actual_count2}")
                root.update_idletasks()
            else:
                 if running: print("Tkinter Fenster wurde extern geschlossen (update)."); close_app(root)
                 return
        except tk.TclError:
             if running: print("Tkinter TclError in update_idletasks."); close_app(root)
             return
        except Exception as e:
             print(f"Fehler beim Aktualisieren der Tkinter Labels: {e}")

        # Nächsten Update-Aufruf planen
        if running:
            root.after(max(1, 1000 // FPS), simulation_update)


    # Starte die Loops
    print("Starte Simulations-Loop...")
    root.after(100, simulation_update)
    print("Starte Tkinter mainloop...")
    root.mainloop()