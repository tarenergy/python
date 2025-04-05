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
GREEN = (50, 255, 50)   # NEU
PURPLE = (150, 50, 255) # NEU
BLACK = (0, 0, 0)
GRAY = (100, 100, 100) # Farbe für den Hai
DARK_GRAY = (50, 50, 50) # Dunkleres Grau

# --- Boid Klasse ---
class Boid:
    # NIMMT JETZT EIN EINZIGES PARAMETER-DICT ENTGEGEN
    def __init__(self, x, y, color, params):
        self.position = Vector2(x, y)
        max_speed_init = params.get('max_speed', tk.DoubleVar(value=4.0)).get()
        angle = random.uniform(0, 2 * math.pi)
        initial_speed = random.uniform(1, max(1.1, max_speed_init / 2))
        self.velocity = Vector2(math.cos(angle), math.sin(angle)) * initial_speed
        self.acceleration = Vector2(0, 0)
        self.color = color
        self.params = params # Speichert das kombinierte Parameter-Dict
        self.size = 6

    def apply_force(self, force):
        if force and math.isfinite(force.x) and math.isfinite(force.y): self.acceleration += force
    def seek(self, target):
        max_speed=self.params['max_speed'].get(); max_force=self.params['max_force'].get()
        desired = (target - self.position); dist = desired.length()
        if dist > 0:
            desired = desired.normalize() * max_speed; steer = (desired - self.velocity)
            if steer.length() > max_force: steer.scale_to_length(max_force)
            return steer
        return Vector2(0, 0)
    def separate(self, boids):
        steering = Vector2(0, 0); total = 0
        sep_dist = self.params['separation_distance'].get(); max_speed = self.params['max_speed'].get(); max_force = self.params['max_force'].get()
        for other in boids:
            # Nur von Boids der GLEICHEN Farbe trennen
            if self != other and other.color == self.color:
                try: dist_sq = self.position.distance_squared_to(other.position)
                except OverflowError: dist_sq = float('inf')
                if 0 < dist_sq < sep_dist * sep_dist:
                    distance = math.sqrt(dist_sq); diff = self.position - other.position
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
        vis_range = self.params['visual_range'].get(); max_speed = self.params['max_speed'].get(); max_force = self.params['max_force'].get()
        for other in boids:
             # Nur an Boids der GLEICHEN Farbe ausrichten
            if self != other and other.color == self.color:
                try: dist_sq = self.position.distance_squared_to(other.position)
                except OverflowError: dist_sq = float('inf')
                if 0 < dist_sq < vis_range * vis_range:
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
             # Nur mit Boids der GLEICHEN Farbe zusammenrotten
            if self != other and other.color == self.color:
                try: dist_sq = self.position.distance_squared_to(other.position)
                except OverflowError: dist_sq = float('inf')
                if 0 < dist_sq < vis_range * vis_range:
                    center_of_mass += other.position; total += 1
        if total > 0: center_of_mass /= total; return self.seek(center_of_mass)
        return Vector2(0, 0)
    def avoid(self, all_entities): # Renamed parameter for clarity
        steering = Vector2(0, 0); total = 0
        avoid_range = self.params['avoidance_range'].get(); max_speed = self.params['max_speed'].get(); max_force = self.params['max_force'].get()
        for other in all_entities:
             # Allen ANDEREN Farben (andere Schwärme + Haie) ausweichen
            if self != other and other.color != self.color:
                try: dist_sq = self.position.distance_squared_to(other.position)
                except OverflowError: dist_sq = float('inf')
                # Check if the other entity has a position attribute (might be a non-boid)
                if hasattr(other, 'position') and 0 < dist_sq < avoid_range * avoid_range:
                    distance = math.sqrt(dist_sq); diff = self.position - other.position
                    diff /= (distance * distance) if distance > 1 else 1
                    steering += diff; total += 1
        if total > 0:
            steering /= total
            if steering.length() > 0: steering = steering.normalize() * max_speed
            steer = steering - self.velocity
            if steer.length() > max_force: steer.scale_to_length(max_force)
            return steer
        return Vector2(0, 0)

    # Nimmt jetzt all_entities (Boids + Haie)
    def flock(self, all_entities):
        # Separate, Align, Cohere only consider boids of the same color (handled within methods)
        # Avoid considers all entities of different colors (boids + sharks)
        same_color_boids = [b for b in all_entities if isinstance(b, Boid) and b.color == self.color]
        sep = self.separate(same_color_boids) * self.params['separation_factor'].get()
        ali = self.align(same_color_boids) * self.params['alignment_factor'].get()
        coh = self.cohere(same_color_boids) * self.params['cohesion_factor'].get()
        # Avoidance considers ALL other entities (different color boids + sharks)
        avo = self.avoid(all_entities) * self.params['avoidance_factor'].get()
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
        # NUTZT JETZT self.params für Geometrie
        if self.velocity.length_squared() < 0.01:
            try: pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), int(self.size * 0.8))
            except OverflowError: pass; return
        try: heading = self.velocity.normalize()
        except ValueError: heading = Vector2(1, 0)
        try:
            # Holt Geometrie-Parameter direkt aus self.params
            tip_factor = self.params['geom_tip_factor'].get(); mid_offset_factor = self.params['geom_mid_offset_factor'].get()
            width_factor = self.params['geom_width_factor'].get(); tail_offset_factor = self.params['geom_tail_offset_factor'].get()
            tail_width_factor = self.params['geom_tail_width_factor'].get()
            tip = self.position + heading * self.size * tip_factor; perp = Vector2(-heading.y, heading.x)
            mid_base = self.position + heading * self.size * mid_offset_factor; mid_left = mid_base + perp * self.size * width_factor; mid_right = mid_base - perp * self.size * width_factor
            tail_base = self.position - heading * self.size * tail_offset_factor; tail_left = tail_base + perp * self.size * tail_width_factor; tail_right = tail_base - perp * self.size * tail_width_factor
            points_int = [ (int(tip.x), int(tip.y)), (int(mid_left.x), int(mid_left.y)), (int(tail_left.x), int(tail_left.y)), (int(tail_right.x), int(tail_right.y)), (int(mid_right.x), int(mid_right.y)) ]
            pygame.draw.polygon(screen, self.color, points_int)
        except KeyError as e:
             # Fallback, falls Geometrie-Parameter fehlen (sollte nicht passieren)
             # print(f"Warnung: Fehlender Geometrie-Parameter {e} für Farbe {self.color}")
             tip_length_factor = 2.0; base_offset_factor = 0.6; width_factor = 0.4
             tip = self.position + heading * self.size * tip_length_factor; base_point = self.position - heading * self.size * base_offset_factor
             perp_vec = Vector2(-heading.y, heading.x) * self.size * width_factor; base_left = base_point + perp_vec; base_right = base_point - perp_vec
             try: points = [(int(tip.x), int(tip.y)), (int(base_left.x), int(base_left.y)), (int(base_right.x), int(base_right.y))]; pygame.draw.polygon(screen, self.color, points)
             except OverflowError: pass
        except Exception as e:
             print(f"Fehler beim Zeichnen des Boids: {e}")
             try: pygame.draw.circle(screen, self.color, (int(self.position.x), int(self.position.y)), int(self.size))
             except: pass

# --- Shark Klasse ---
class Shark:
    def __init__(self, x, y, params): # Nimmt params entgegen
        self.position = Vector2(x, y); self.velocity = Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() * 2
        self.acceleration = Vector2(0, 0); self.color = DARK_GRAY; self.outline_color = GRAY; self.size = 12
        self.params = params; self.wander_angle = random.uniform(0, 2 * math.pi)
        try:
            current_eat_radius = self.params['shark_eat_radius'].get(); self.eat_radius_sq = current_eat_radius * current_eat_radius
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
    def hunt(self, all_boids): # Nimmt nur Boids entgegen zum Jagen
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
        max_force = self.params['shark_max_force'].get(); self.wander_angle += random.uniform(-0.3, 0.3)
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
    # NIMMT JETZT EIN EINZIGES PARAMETER-DICT ENTGEGEN
    def __init__(self, initial_count, color, params):
        self.color = color
        self.params = params # Speichert das kombinierte Parameter-Dict
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
                # Übergibt das kombinierte Parameter-Dict an Boid
                new_boid = Boid(start_x, start_y, self.color, self.params)
                self.boids.append(new_boid)
            list_changed = True
        elif delta < 0:
             if target_count < current_count:
                 self.boids = self.boids[:target_count]
                 list_changed = True
        return list_changed

    # Nimmt jetzt all_entities (Boids + Haie)
    def run(self, screen, all_entities):
        for boid in self.boids: boid.flock(all_entities) # Übergibt alle Entities für Avoidance
        for boid in self.boids:
            boid.update()
            boid.wrap_borders(SCREEN_WIDTH, SCREEN_HEIGHT)
            boid.draw(screen)


# --- Globale Variablen und Definitionen ---
running = True
screen = None

# Parameter Definitionen für ALLE Slider
slider_definitions = {
    'boid_count': ("Anzahl", 1, 250, 1), # Gekürzt für mehr Platz
    'separation_factor': ("Separation", 0.0, 5.0, 0.1), # Gekürzt
    'alignment_factor': ("Alignment", 0.0, 5.0, 0.1), # Gekürzt
    'cohesion_factor': ("Kohäsion", 0.0, 5.0, 0.1), # Gekürzt
    'visual_range': ("Sichtweite", 10.0, 200.0, 1.0), # Gekürzt
    'separation_distance': ("Min. Abstand", 5.0, 100.0, 1.0), # Gekürzt
    'avoidance_factor': ("Abneigung", 0.0, 10.0, 0.1), # Gekürzt
    'avoidance_range': ("Abn.-Reichw.", 10.0, 250.0, 1.0), # Gekürzt
    'max_speed': ("Max Tempo", 1.0, 10.0, 0.1), # Gekürzt
    'max_force': ("Max Kraft", 0.01, 1.0, 0.01), # Gekürzt

    # Geometrie Parameter (jetzt Teil jeder Schwarm-Def)
    'geom_tip_factor': ("Spitze Länge", 0.5, 4.0, 0.1), # Gekürzt
    'geom_mid_offset_factor': ("Breite Pos", -0.5, 1.0, 0.05), # Gekürzt
    'geom_width_factor': ("Max Breite", 0.1, 1.5, 0.05), # Gekürzt
    'geom_tail_offset_factor': ("Schwanz Pos", 0.1, 2.0, 0.05), # Gekürzt
    'geom_tail_width_factor': ("Schwanz Breite", 0.0, 1.0, 0.05), # Gekürzt

    # Hai Parameter
    'shark_count': ("Anzahl Haie", 0, 10, 1), # NEU
    'shark_max_speed': ("Max Tempo Hai", 1.0, 15.0, 0.1), # Gekürzt
    'shark_max_force': ("Max Kraft Hai", 0.01, 1.5, 0.01), # Gekürzt
    'shark_perception_radius': ("Sichtweite Hai", 50.0, 400.0, 1.0), # Gekürzt
    'shark_eat_radius': ("Fressradius", 5.0, 50.0, 0.5), # Gekürzt
}

# Gemeinsame Geometrie Defaults (als Basis)
default_geometry = {
    'geom_tip_factor': 1.6, 'geom_mid_offset_factor': 0.1, 'geom_width_factor': 0.6,
    'geom_tail_offset_factor': 0.9, 'geom_tail_width_factor': 0.2,
}

# Default Werte (inkl. Geometrie)
default_values_swarm1 = {
    'boid_count': 80, 'separation_factor': 1.8, 'alignment_factor': 1.0, 'cohesion_factor': 1.0,
    'visual_range': 70.0, 'separation_distance': 25.0, 'avoidance_factor': 3.0, 'avoidance_range': 80.0,
    'max_speed': 4.0, 'max_force': 0.2, **default_geometry
}
default_values_swarm2 = {
    'boid_count': 60, 'separation_factor': 1.5, 'alignment_factor': 1.2, 'cohesion_factor': 0.8,
    'visual_range': 50.0, 'separation_distance': 30.0, 'avoidance_factor': 2.5, 'avoidance_range': 90.0,
    'max_speed': 5.0, 'max_force': 0.25, **default_geometry # Fügt Geometrie hinzu
}
default_values_swarm3 = { # NEU
    'boid_count': 70, 'separation_factor': 1.6, 'alignment_factor': 0.8, 'cohesion_factor': 1.2,
    'visual_range': 80.0, 'separation_distance': 28.0, 'avoidance_factor': 3.5, 'avoidance_range': 70.0,
    'max_speed': 4.5, 'max_force': 0.22,
    # Eigene Geometrie für Lila
    'geom_tip_factor': 2.0, 'geom_mid_offset_factor': 0.0, 'geom_width_factor': 0.5,
    'geom_tail_offset_factor': 1.1, 'geom_tail_width_factor': 0.3,
}
default_values_swarm4 = { # NEU
    'boid_count': 50, 'separation_factor': 2.0, 'alignment_factor': 1.1, 'cohesion_factor': 0.9,
    'visual_range': 60.0, 'separation_distance': 22.0, 'avoidance_factor': 2.8, 'avoidance_range': 100.0,
    'max_speed': 3.8, 'max_force': 0.18,
    # Eigene Geometrie für Grün
    'geom_tip_factor': 1.4, 'geom_mid_offset_factor': 0.2, 'geom_width_factor': 0.7,
    'geom_tail_offset_factor': 0.8, 'geom_tail_width_factor': 0.15,
}

default_values_shark = {
    'shark_enabled': True,
    'shark_count': 1, # NEU
    'shark_max_speed': 3.8, 'shark_max_force': 0.35, 'shark_perception_radius': 170.0, 'shark_eat_radius': 13.0,
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

# Angepasste Funktion, akzeptiert start_row und ignoriert keys, die keine Slider sind
def create_sliders(parent_frame, params_dict, default_values, start_row=0):
    row_index = start_row
    # Iteriere über die default_values, da diese alle nötigen Keys enthalten (auch Geometrie)
    for key, default_value in default_values.items():
        # Überspringe Einträge, die nicht im Slider-Definitions-Dictionary sind
        # (z.B. 'shark_enabled', obwohl das hier nicht vorkommen sollte)
        if key not in slider_definitions:
            continue

        label_text, min_val, max_val, resolution = slider_definitions[key]
        row_frame = ttk.Frame(parent_frame)
        row_frame.grid(row=row_index, column=0, columnspan=4, sticky="ew", pady=1)
        row_frame.columnconfigure(1, weight=1) # Slider-Spalte dehnbar machen

        is_count_slider = (key == 'boid_count' or key == 'shark_count')

        if is_count_slider:
            params_dict[key] = tk.IntVar(value=int(default_value))
            var_type = 'int'
        else:
            params_dict[key] = tk.DoubleVar(value=default_value)
            var_type = 'float'

        # Label Breite angepasst für kürzere Texte
        label = ttk.Label(row_frame, text=f"{label_text}:", width=15, anchor="w")
        label.grid(row=0, column=0, sticky="w", padx=(5,0))

        # Slider Breite reduziert, damit mehr Platz ist
        slider = ttk.Scale(row_frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                           variable=params_dict[key], length=120) # Länge reduziert
        slider.grid(row=0, column=1, sticky="ew", padx=5)

        # Wert-Anzeige (Zielwert)
        target_value_label = ttk.Label(row_frame, text="", width=5, anchor="e")
        target_value_label.grid(row=0, column=2, sticky="e", padx=(0, 2))

        # Callback um das Wert-Label neben dem Slider zu aktualisieren
        def make_update_callback(k, var, lbl, vtype):
            def callback(val): # val wird vom Scale-Widget übergeben, ist aber oft ein String
                try:
                    current_val = var.get() # Hol den aktuellen Wert direkt von der Variable
                    if vtype == 'int':
                        lbl.config(text=f"{current_val}")
                    else:
                        lbl.config(text=f"{current_val:.2f}") # Formatiere Float
                except tk.TclError:
                    pass # Fenster könnte geschlossen sein
            return callback

        update_target_label_callback = make_update_callback(key, params_dict[key], target_value_label, var_type)
        slider.config(command=update_target_label_callback) # Setze Callback für den Slider

        # Initialisiere das Label beim Erstellen
        update_target_label_callback(params_dict[key].get())

        # "Aktuell:" Label nur für Zähl-Slider
        if is_count_slider:
            actual_count_label = ttk.Label(row_frame, text="Aktuell: ?", width=10, anchor="w")
            actual_count_label.grid(row=0, column=3, sticky="w", padx=(10, 0))
            # Speichere das Label im Dict, um es später zu aktualisieren
            # Verwende einen eindeutigen Key, z.B. key + '_actual_label'
            params_dict[key + '_actual_label'] = actual_count_label

        row_index += 1
    return row_index # Gibt die nächste freie Zeile zurück


# Funktion zum Auffüllen (jetzt für 4 Schwärme)
def replenish_swarm(params_dict):
    global swarm1, swarm2, swarm3, swarm4, all_boids, sharks # sharks hinzugefügt
    target_swarm = None; swarm_name = "?"
    if params_dict is params1: target_swarm = swarm1; swarm_name = "Schwarm 1 (Blau)"
    elif params_dict is params2: target_swarm = swarm2; swarm_name = "Schwarm 2 (Rot)"
    elif params_dict is params3: target_swarm = swarm3; swarm_name = "Schwarm 3 (Lila)" # NEU
    elif params_dict is params4: target_swarm = swarm4; swarm_name = "Schwarm 4 (Grün)" # NEU

    if target_swarm:
        try:
            target_count = params_dict['boid_count'].get()
            current_count = len(target_swarm.boids)
            # Nur auffüllen, wenn Ziel > Aktuell
            if target_count > current_count:
                if target_swarm.update_boid_count(target_count): # True wenn hinzugefügt wurde
                    # Globale Liste aller Boids neu bauen!
                    all_boids = swarm1.boids + swarm2.boids + swarm3.boids + swarm4.boids
                    print(f"{swarm_name} aufgefüllt auf {len(target_swarm.boids)}. Gesamt Boids: {len(all_boids)}")
                    # Update Actual Label (verwende den neuen Key)
                    if 'boid_count_actual_label' in params_dict:
                        params_dict['boid_count_actual_label'].config(text=f"Aktuell: {len(target_swarm.boids)}")
        except tk.TclError: print("Fehler beim Auffüllen (Tkinter nicht bereit?).")
        except Exception as e: print(f"Fehler beim Auffüllen von {swarm_name}: {e}")
    else: print("Fehler: Unbekanntes Parameter-Dictionary für replenish_swarm.")

# Setup Tkinter Controls Funktion
def setup_tkinter_controls():
    root = tk.Tk()
    root.title("Boid Parameter")
    # Fenster etwas breiter gemacht für 4 Schwärme nebeneinander
    root.geometry("750x850") # Breite angepasst
    root.protocol("WM_DELETE_WINDOW", lambda: close_app(root))
    notebook = ttk.Notebook(root)
    notebook.pack(pady=10, padx=10, expand=True, fill="both")

    # Parameter Dictionaries für 4 Schwärme und Haie
    params_swarm1 = {}; params_swarm2 = {}; params_swarm3 = {}; params_swarm4 = {}
    params_shark = {}

    # --- Tab Schwarm 1 (Blau) ---
    frame1 = ttk.Frame(notebook, padding="10")
    notebook.add(frame1, text='Blau') # Kürzere Tab-Namen
    last_row1 = create_sliders(frame1, params_swarm1, default_values_swarm1)
    button1 = ttk.Button(frame1, text="Auffüllen", command=lambda p=params_swarm1: replenish_swarm(p))
    button1.grid(row=last_row1, column=0, columnspan=4, pady=(10, 0))

    # --- Tab Schwarm 2 (Rot) ---
    frame2 = ttk.Frame(notebook, padding="10")
    notebook.add(frame2, text='Rot')
    last_row2 = create_sliders(frame2, params_swarm2, default_values_swarm2)
    button2 = ttk.Button(frame2, text="Auffüllen", command=lambda p=params_swarm2: replenish_swarm(p))
    button2.grid(row=last_row2, column=0, columnspan=4, pady=(10, 0))

    # --- Tab Schwarm 3 (Lila) --- NEU
    frame3 = ttk.Frame(notebook, padding="10")
    notebook.add(frame3, text='Lila')
    last_row3 = create_sliders(frame3, params_swarm3, default_values_swarm3)
    button3 = ttk.Button(frame3, text="Auffüllen", command=lambda p=params_swarm3: replenish_swarm(p))
    button3.grid(row=last_row3, column=0, columnspan=4, pady=(10, 0))

    # --- Tab Schwarm 4 (Grün) --- NEU
    frame4 = ttk.Frame(notebook, padding="10")
    notebook.add(frame4, text='Grün')
    last_row4 = create_sliders(frame4, params_swarm4, default_values_swarm4)
    button4 = ttk.Button(frame4, text="Auffüllen", command=lambda p=params_swarm4: replenish_swarm(p))
    button4.grid(row=last_row4, column=0, columnspan=4, pady=(10, 0))


    # --- Tab Hai ---
    frame_shark = ttk.Frame(notebook, padding="10")
    notebook.add(frame_shark, text='Haie') # Umbenannt zu Plural

    current_row = 0
    # BooleanVar und Checkbutton für Hai Aktivierung
    params_shark['shark_enabled'] = tk.BooleanVar(value=default_values_shark['shark_enabled'])
    shark_enable_checkbutton = ttk.Checkbutton(frame_shark, text="Haie Aktiviert",
                                               variable=params_shark['shark_enabled'])
    shark_enable_checkbutton.grid(row=current_row, column=0, columnspan=4, sticky="w", pady=(0, 10), padx=5)
    current_row += 1

    # Erstelle die Slider für den Hai (inkl. Anzahl)
    # default_values_shark enthält jetzt 'shark_count'
    last_row_shark = create_sliders(frame_shark, params_shark, default_values_shark, start_row=current_row)

    # Gibt jetzt alle 5 Parameter-Dicts zurück
    return root, params_swarm1, params_swarm2, params_swarm3, params_swarm4, params_shark


# --- Hauptteil ---
if __name__ == "__main__":
    # Hole alle Parameter-Dictionaries
    root, params1, params2, params3, params4, params_shark = setup_tkinter_controls() # << Angepasst
    pygame.init()
    pygame.font.init()

    # Bildschirm Setup
    try:
        display_info = pygame.display.Info(); SCREEN_WIDTH=display_info.current_w; SCREEN_HEIGHT=display_info.current_h
        print(f"Versuche Vollbildmodus: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE)
        print("Vollbildmodus erfolgreich gesetzt.")
    except pygame.error as e:
        print(f"Fehler Vollbild: {e}. Versuche Fenstermodus 1280x720...")
        SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
        try: screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)
        except pygame.error as e2: print(f"Fehler Fenstermodus: {e2}"); close_app(root); exit()
    if not screen: print("Fehler: Pygame Fenster konnte nicht erstellt werden."); close_app(root); exit()

    pygame.display.set_caption("Boids Simulation mit Haien")
    clock = pygame.time.Clock()
    app_font = None
    try: app_font = pygame.font.SysFont(None, 30)
    except Exception as e: print(f"Warnung: Schriftart nicht geladen: {e}")

    # Schwärme erstellen
    try:
        global swarm1, swarm2, swarm3, swarm4 # Für Callbacks
        # Übergibt die kombinierten Param-Dicts an Swarm Konstruktor
        swarm1 = Swarm(0, BLUE, params1); swarm2 = Swarm(0, RED, params2)
        swarm3 = Swarm(0, PURPLE, params3); swarm4 = Swarm(0, GREEN, params4) # NEU
        swarm1.initialize_boids(int(default_values_swarm1['boid_count']))
        swarm2.initialize_boids(int(default_values_swarm2['boid_count']))
        swarm3.initialize_boids(int(default_values_swarm3['boid_count'])) # NEU
        swarm4.initialize_boids(int(default_values_swarm4['boid_count'])) # NEU
        all_boids = swarm1.boids + swarm2.boids + swarm3.boids + swarm4.boids # NEU

        # Haie als Liste erstellen (initial leer, wird in Schleife gefüllt)
        global sharks # Globale Liste für Haie
        sharks = []

        print(f"Init: S1={len(swarm1.boids)}, S2={len(swarm2.boids)}, S3={len(swarm3.boids)}, S4={len(swarm4.boids)}. Haie initial: {len(sharks)}")
    except Exception as e: print(f"Fehler Erstellung: {e}"); close_app(root); exit()


    # --- Hauptschleife (angetrieben durch Tkinter) ---
    def simulation_update():
        global running, all_boids, screen, app_font, sharks # Globale Variablen
        global swarm1, swarm2, swarm3, swarm4
        global params1, params2, params3, params4, params_shark

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

        # === Boid Anzahl anpassen (Slider reduziert) ===
        rebuild_all_boids_due_to_slider = False
        try:
            # Schwarm 1
            target_count1 = params1['boid_count'].get(); current_count1 = len(swarm1.boids)
            if target_count1 < current_count1:
                if swarm1.update_boid_count(target_count1): rebuild_all_boids_due_to_slider = True
            # Schwarm 2
            target_count2 = params2['boid_count'].get(); current_count2 = len(swarm2.boids)
            if target_count2 < current_count2:
                 if swarm2.update_boid_count(target_count2): rebuild_all_boids_due_to_slider = True
            # Schwarm 3 NEU
            target_count3 = params3['boid_count'].get(); current_count3 = len(swarm3.boids)
            if target_count3 < current_count3:
                 if swarm3.update_boid_count(target_count3): rebuild_all_boids_due_to_slider = True
            # Schwarm 4 NEU
            target_count4 = params4['boid_count'].get(); current_count4 = len(swarm4.boids)
            if target_count4 < current_count4:
                 if swarm4.update_boid_count(target_count4): rebuild_all_boids_due_to_slider = True

        except tk.TclError:
             if running: close_app(root); return
        except Exception as e:
             print(f"Fehler Update Boid Anzahl (Slider): {e}");
             if running: close_app(root); return

        # === Hai Anzahl anpassen (Slider) === NEU
        shark_list_changed = False
        try:
            target_shark_count = params_shark['shark_count'].get()
            current_shark_count = len(sharks)
            delta_sharks = target_shark_count - current_shark_count

            if delta_sharks > 0: # Mehr Haie hinzufügen
                for _ in range(delta_sharks):
                    start_x = random.uniform(0, SCREEN_WIDTH) if SCREEN_WIDTH > 0 else 200
                    start_y = random.uniform(0, SCREEN_HEIGHT) if SCREEN_HEIGHT > 0 else 200
                    new_shark = Shark(start_x, start_y, params_shark)
                    sharks.append(new_shark)
                shark_list_changed = True
                # print(f"Haie hinzugefügt. Neu: {len(sharks)}") # Debug
            elif delta_sharks < 0: # Weniger Haie
                sharks = sharks[:target_shark_count] # Liste kürzen
                shark_list_changed = True
                # print(f"Haie entfernt. Neu: {len(sharks)}") # Debug

        except tk.TclError:
            if running: close_app(root); return
        except Exception as e:
            print(f"Fehler Update Hai Anzahl (Slider): {e}")
            if running: close_app(root); return

        # === Globale Boid-Liste neu bauen, falls nötig ===
        if rebuild_all_boids_due_to_slider:
            all_boids = swarm1.boids + swarm2.boids + swarm3.boids + swarm4.boids

        # === Alle Entities für Kollisionsprüfung/Sichtbarkeit ===
        # Fügt die aktuelle Liste der Haie hinzu (wichtig für Boid Avoidance)
        all_entities = all_boids + sharks


        # === Prüfen, ob Haie aktiv sind ===
        shark_is_active = False
        try:
            if 'shark_enabled' in params_shark:
                 shark_is_active = params_shark['shark_enabled'].get()
        except (tk.TclError, KeyError):
             pass # Tkinter oder Variable könnte weg sein, wenn App schließt

        # === Hai Logik (nur ausführen, wenn aktiv und Haie vorhanden) ===
        if shark_is_active and sharks:
            # === Hai Fressradius aktualisieren (nur einmal, da alle Haie dieselben Params haben) ===
            eat_radius_sq = sharks[0].eat_radius_sq # Standardwert holen
            try:
                 if 'shark_eat_radius' in params_shark:
                    current_eat_radius = params_shark['shark_eat_radius'].get()
                    eat_radius_sq = current_eat_radius * current_eat_radius
                    # Radius für alle Hai-Objekte aktualisieren
                    for s in sharks: s.eat_radius_sq = eat_radius_sq
            except tk.TclError: pass
            except KeyError: pass
            except Exception as e: print(f"Fehler Update Hai Radius: {e}")

            # === Haie fressen Fische ===
            eaten_this_frame = set()
            # Wichtig: Iteriere über eine Kopie der Boids zum Prüfen!
            boids_to_check = list(all_boids)
            # Iteriere durch jeden aktiven Hai
            for shark_instance in sharks:
                 # Iteriere durch jeden Boid
                 for boid in boids_to_check:
                    # Ignoriere bereits gefressene Boids in dieser Runde
                    if boid in eaten_this_frame: continue
                    try:
                        dist_sq = shark_instance.position.distance_squared_to(boid.position)
                        if dist_sq < eat_radius_sq: # Verwende den aktualisierten Radius
                            eaten_this_frame.add(boid)
                    except OverflowError: continue
                    except AttributeError: continue
                    except Exception as e: continue

            # === Listen neu aufbauen, wenn etwas gefressen wurde ===
            if eaten_this_frame:
                # print(f"{len(sharks)} Hai(e) haben {len(eaten_this_frame)} Fisch(e) gefressen!") # Debug
                old_s1_count = len(swarm1.boids)
                swarm1.boids = [b for b in swarm1.boids if b not in eaten_this_frame]
                old_s2_count = len(swarm2.boids)
                swarm2.boids = [b for b in swarm2.boids if b not in eaten_this_frame]
                old_s3_count = len(swarm3.boids) # NEU
                swarm3.boids = [b for b in swarm3.boids if b not in eaten_this_frame]
                old_s4_count = len(swarm4.boids) # NEU
                swarm4.boids = [b for b in swarm4.boids if b not in eaten_this_frame]

                # Globale Boid-Liste und Entity-Liste müssen aktualisiert werden!
                all_boids = swarm1.boids + swarm2.boids + swarm3.boids + swarm4.boids
                all_entities = all_boids + sharks # Entity Liste auch!
                # print(f"  Verbleibend all: {len(all_boids)}") # Debug

            # === Hai Simulation (Update, Grenzen, Jagen für jeden Hai) ===
            try:
                for shark_instance in sharks:
                    # Haie jagen nur Boids, nicht andere Haie
                    shark_instance.hunt(all_boids)
                    shark_instance.update()
                    shark_instance.wrap_borders(SCREEN_WIDTH, SCREEN_HEIGHT)
            except Exception as e:
                print(f"Fehler in Hai Simulation: {e}")

        # === Simulation & Rendering ===
        try:
            screen.fill(BLACK) # Hintergrund

            # Schwärme simulieren und zeichnen (übergeben all_entities)
            if len(all_boids) > 0:
                 swarm1.run(screen, all_entities)
                 swarm2.run(screen, all_entities)
                 swarm3.run(screen, all_entities) # NEU
                 swarm4.run(screen, all_entities) # NEU
            elif app_font: # Nachricht wenn alle Fische weg sind
                 # Nachricht nur anzeigen, wenn auch keine Haie (mehr) da sind
                 if not sharks:
                     text = app_font.render("Alles leer!", True, WHITE)
                     text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
                     screen.blit(text, text_rect)
                 elif not all_boids:
                     text = app_font.render("Alle Fische gefressen!", True, WHITE)
                     text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
                     screen.blit(text, text_rect)


            # Haie zeichnen (nur wenn aktiv)
            if shark_is_active and sharks:
                try:
                    for shark_instance in sharks:
                        shark_instance.draw(screen)
                except Exception as e:
                    print(f"Fehler beim Zeichnen der Haie: {e}")

            pygame.display.flip() # Alles anzeigen
            clock.tick(FPS) # Framerate begrenzen
        except pygame.error as e: print(f"Pygame Render/Flip-Fehler: {e}")
        except Exception as e: print(f"Unerwarteter Fehler in Rendering/Simulation: {e}")

        # === Tkinter Update (inkl. aktueller Anzahl) ===
        try:
            if root.winfo_exists():
                # Update der Boid-Anzahl Labels
                actual_count1 = len(swarm1.boids)
                actual_count2 = len(swarm2.boids)
                actual_count3 = len(swarm3.boids) # NEU
                actual_count4 = len(swarm4.boids) # NEU
                actual_sharks = len(sharks)      # NEU

                if 'boid_count_actual_label' in params1: params1['boid_count_actual_label'].config(text=f"Aktuell: {actual_count1}")
                if 'boid_count_actual_label' in params2: params2['boid_count_actual_label'].config(text=f"Aktuell: {actual_count2}")
                if 'boid_count_actual_label' in params3: params3['boid_count_actual_label'].config(text=f"Aktuell: {actual_count3}") # NEU
                if 'boid_count_actual_label' in params4: params4['boid_count_actual_label'].config(text=f"Aktuell: {actual_count4}") # NEU
                # Update Hai-Anzahl Label (verwende den neuen Key)
                if 'shark_count_actual_label' in params_shark: params_shark['shark_count_actual_label'].config(text=f"Aktuell: {actual_sharks}") # NEU

                root.update_idletasks()
            else:
                 if running: print("Tkinter Fenster wurde extern geschlossen (update)."); close_app(root)
                 return # Beende die Schleife, wenn das Fenster weg ist
        except tk.TclError:
             if running: print("Tkinter TclError in update_idletasks."); close_app(root)
             return # Beende die Schleife bei Tkinter Fehlern
        except Exception as e:
             print(f"Fehler beim Aktualisieren der Tkinter Labels: {e}") # Andere Fehler loggen

        # Nächsten Update-Aufruf planen
        if running:
            delay = max(1, int(1000 / FPS - clock.get_time()))
            root.after(delay, simulation_update)


    # Starte die Loops
    print("Starte Simulations-Loop...")
    root.after(50, simulation_update) # Kurze Verzögerung
    print("Starte Tkinter mainloop...")
    root.mainloop()

    # Wird erreicht, wenn mainloop endet
    print("Tkinter mainloop beendet.")
    if running:
        running = False
        pygame.quit()
        print("Pygame final beendet.")