import pygame
import tkinter as tk
from tkinter import ttk
import random
import math
# threading wird nicht mehr benötigt für die GUI
import time
import sys # Für sys.exit bei Fehlern

# --- Globale Konfiguration & Parameter (werden von GUI überschrieben) ---
CONFIG = {
    "screen_width": 1000,
    "screen_height": 250,
    "num_lanes": 3,
    "lane_width": 50,
    "car_width": 20,
    "car_height": 40,
    "total_cars": 50, # Startwert, wird von GUI überschrieben wenn geändert
    "fps": 60,
    "safe_distance_factor": 1.8, # Faktor der eigenen Länge als Sicherheitsabstand
    "base_max_speed_slow": 40,  # Blau
    "base_max_speed_medium": 70, # Grün
    "base_max_speed_fast": 100, # Rot
    "acceleration": 15,        # Beschleunigung (Pixel/s^2)
    "braking_deceleration": 40, # Normale Bremsverzögerung
    "hard_braking_deceleration": 100, # Starke Bremsverzögerung
    "lane_change_speed": 40,    # Geschwindigkeit des Spurwechsels (Pixel/s in Y-Richtung)
    "speed_variance": 0.1,      # +/- 10% Varianz in max. Geschwindigkeit
    "overtake_speed_diff": 10,  # Mind. Geschw.-Unterschied zum Vordermann für Überholwunsch
    "min_gap_overtake": 50,     # Mindestlücke (Pixel) zum Überholen (vorne & hinten)
    "min_gap_move_right": 40,   # Mindestlücke (Pixel) zum Rechts rüberziehen
    "slow_car_lane_change_prob": 0.001 # Wahrscheinlichkeit pro Frame, dass ein langsames Auto überholt
}

# --- Farbdefinitionen ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
ROAD_GRAY = (50, 50, 50)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# --- Auto Klasse ---
class Car:
    def __init__(self, car_id, lane, car_type, x_pos=None):
        self.id = car_id
        self.width = CONFIG["car_width"]
        self.height = CONFIG["car_height"]
        self.lane = lane
        self.target_lane = lane
        self.type = car_type # 'slow', 'medium', 'fast'

        # Geschwindigkeit und Farbe basierend auf Typ
        speed_variance = random.uniform(1 - CONFIG["speed_variance"], 1 + CONFIG["speed_variance"])
        if self.type == 'slow':
            self.max_speed = CONFIG["base_max_speed_slow"] * speed_variance
            self.color = BLUE
        elif self.type == 'medium':
            self.max_speed = CONFIG["base_max_speed_medium"] * speed_variance
            self.color = GREEN
        else: # fast
            self.max_speed = CONFIG["base_max_speed_fast"] * speed_variance
            self.color = RED

        # Sicherstellen, dass max_speed nicht negativ ist (durch extreme Varianz)
        self.max_speed = max(1, self.max_speed) # Mindestgeschwindigkeit > 0

        self.speed = self.max_speed * 0.8 # Start mit 80% der max. Geschwindigkeit
        self.desired_speed = self.max_speed

        road_height = CONFIG["num_lanes"] * CONFIG["lane_width"]
        road_top_y = (CONFIG["screen_height"] - road_height) // 2

        # Position
        self.y = road_top_y + (self.lane * CONFIG["lane_width"]) + (CONFIG["lane_width"] / 2) - (self.height / 2)
        self.x = x_pos if x_pos is not None else random.uniform(-CONFIG["screen_width"] * 0.5, 0) # Start vor dem Bildschirm

        # Spurwechsel-Status
        self.is_changing_lane = False
        self.lane_change_direction = 0 # -1 für rechts, 1 für links

    def get_lane_center_y(self, lane_index):
        road_height = CONFIG["num_lanes"] * CONFIG["lane_width"]
        road_top_y = (CONFIG["screen_height"] - road_height) // 2
        return road_top_y + (lane_index * CONFIG["lane_width"]) + (CONFIG["lane_width"] / 2) - (self.height / 2)

    def update(self, dt, all_cars):
        """Aktualisiert die Position und den Zustand des Autos."""
        if self.is_changing_lane:
            self.perform_lane_change(dt, all_cars)
        else:
            # 1. Fahrspurlogik (Überholen / Rechts fahren)
            self.decide_lane(all_cars)

            # 2. Geschwindigkeitsanpassung basierend auf Vordermann
            self.adjust_speed(dt, all_cars)

        # 3. Bewegung
        self.x += self.speed * dt

        # Auto zurücksetzen, wenn es weit aus dem Bild ist
        if self.x > CONFIG["screen_width"] + self.width * 5: # Etwas mehr Puffer
           self.reset_position(all_cars)
        elif self.x < -CONFIG["screen_width"] * 1.6: # Auch wenn es weit zurückfällt
            self.reset_position(all_cars)


    def adjust_speed(self, dt, all_cars):
        """Passt die Geschwindigkeit an, um Kollisionen zu vermeiden und max. Speed zu erreichen."""
        if self.is_changing_lane: # Während Spurwechsel Geschwindigkeit halten (oder leicht reduzieren)
            # self.speed *= 0.999 # Optional leichte Verlangsamung
            return

        car_ahead = self.find_car_ahead(all_cars)
        # Dynamischer Sicherheitsabstand: Basis + Geschwindigkeitsabhängiger Teil (vereinfachter Bremsweg)
        base_safe_dist = self.height * CONFIG["safe_distance_factor"]
        # Vermeide Division durch ~0 bei niedriger Bremsverzögerung
        braking_term = CONFIG["braking_deceleration"] * 0.5 + 1
        speed_dependent_dist = (self.speed * self.speed) / (2 * braking_term)
        safe_dist = base_safe_dist + speed_dependent_dist

        if car_ahead:
            # Abstand von eigener Front zur Heck des Vordermanns
            distance_to_ahead = car_ahead.x - (self.x + self.width)

            if distance_to_ahead < safe_dist:
                # Stärker bremsen, je näher und je schneller die Annäherung
                gap_deficit = safe_dist - distance_to_ahead
                speed_diff = self.speed - car_ahead.speed # Positive Differenz = wir sind schneller

                if distance_to_ahead < base_safe_dist * 0.5: # Sehr nah dran
                     deceleration = CONFIG["hard_braking_deceleration"]
                elif distance_to_ahead < base_safe_dist: # Ziemlich nah
                    deceleration = CONFIG["braking_deceleration"] * 1.8
                else: # Im normalen Bremsbereich
                    deceleration = CONFIG["braking_deceleration"]

                # Zusätzliches Bremsen basierend auf Geschwindigkeitsdifferenz und Abstandsmangel
                adaptive_brake = (gap_deficit * 0.8) + max(0, speed_diff * 0.5)
                brake_force = deceleration + adaptive_brake # Kombinierte Bremskraft

                brake_amount = brake_force * dt
                # Nicht mehr bremsen als die aktuelle Geschwindigkeit und nicht negativ bremsen
                brake = max(0, min(self.speed, brake_amount))

                self.speed -= brake
                self.desired_speed = self.speed # Wunsch anpassen, da wir folgen müssen

            else:
                # Genug Abstand, versuchen Maximalgeschwindigkeit zu erreichen
                self.desired_speed = self.max_speed
                self.accelerate(dt)
        else:
            # Freie Bahn, beschleunigen
            self.desired_speed = self.max_speed
            self.accelerate(dt)

        # Geschwindigkeit darf nicht negativ werden
        self.speed = max(0, self.speed)

    def accelerate(self, dt):
        """Beschleunigt das Auto in Richtung desired_speed."""
        if self.speed < self.desired_speed:
            self.speed = min(self.desired_speed, self.speed + CONFIG["acceleration"] * dt)
        elif self.speed > self.desired_speed: # Sanftes Bremsen wenn über Ziel (selten nötig hier)
            self.speed = max(self.desired_speed, self.speed - CONFIG["braking_deceleration"] * 0.5 * dt)


    def decide_lane(self, all_cars):
        """Entscheidet, ob ein Spurwechsel nötig oder möglich ist."""
        if self.is_changing_lane:
            return

        car_ahead = self.find_car_ahead(all_cars)
        is_blocked = False
        if car_ahead:
            distance_to_ahead = car_ahead.x - (self.x + self.width)
            decision_safe_dist = self.height * CONFIG["safe_distance_factor"] * 1.8 + (self.speed**2) / (2*CONFIG["braking_deceleration"] + 1)
            # Blockiert, wenn zu nah UND deutlich langsamer als max. Speed UND Vordermann relevant langsamer
            if (distance_to_ahead < decision_safe_dist and
                self.speed < self.max_speed * 0.9 and # Wir fahren langsamer als wir wollen
                car_ahead.speed < self.speed - CONFIG["overtake_speed_diff"]): # Vordermann ist merklich langsamer
                 is_blocked = True

        # --- 1. Überholwunsch prüfen (nach links) ---
        wants_to_overtake = is_blocked or (self.type == 'slow' and random.random() < CONFIG["slow_car_lane_change_prob"])

        if wants_to_overtake and self.lane < CONFIG["num_lanes"] - 1:
            target_lane_idx = self.lane + 1
            if self.can_change_to_lane(target_lane_idx, all_cars, CONFIG["min_gap_overtake"], 'left'):
                self.initiate_lane_change(1) # Nach links
                return # Entscheidung getroffen

        # --- 2. Rechtsfahrgebot prüfen (nach rechts) ---
        # Nur prüfen, wenn wir nicht gerade überholen wollten/mussten
        if not wants_to_overtake and self.lane > 0:
            target_lane_idx = self.lane - 1
            # Prüfen, ob rechte Spur frei ist
            if self.can_change_to_lane(target_lane_idx, all_cars, CONFIG["min_gap_move_right"], 'right'):
                 should_move_right = True
                 # Verhindern, dass schnelle Autos unnötig nach rechts ziehen, wenn sie schnell fahren
                 if self.type == 'fast' and self.speed > CONFIG["base_max_speed_medium"] * 1.1:
                     should_move_right = False # Schnelle Autos bleiben eher links/mitte wenn schnell
                 elif self.type == 'medium' and target_lane_idx == 0 and self.speed > CONFIG["base_max_speed_slow"] * 1.2:
                      should_move_right = False # Mittlere nicht ganz nach rechts wenn sie flott sind

                 if should_move_right:
                     self.initiate_lane_change(-1) # Nach rechts
                     return # Entscheidung getroffen


    def can_change_to_lane(self, target_lane_idx, all_cars, min_gap, direction):
        """Prüft, ob in der Zielspur vorne und hinten genug Platz ist."""
        # Lücke nach hinten: Muss größer sein, besonders beim Überholen (nach links)
        # Lücke nach vorne: Muss groß genug sein, um nicht direkt bremsen zu müssen
        time_gap_back = 1.2 if direction == 'left' else 1.0 # Sekunden
        time_gap_front = 0.8 # Sekunden

        safe_gap_back = min_gap + (self.speed * time_gap_back)
        safe_gap_front = min_gap + (self.speed * time_gap_front)

        for other in all_cars:
            is_relevant_lane = (other.lane == target_lane_idx or
                                (other.is_changing_lane and other.target_lane == target_lane_idx))

            if other.id == self.id or not is_relevant_lane:
                 continue

            # Abstand von unserem Heck zum Vordermann-Heck (für hinteres Auto)
            dist_to_other_behind = (self.x - other.x) if other.x < self.x else float('inf')
            # Abstand von unserer Front zum Vordermann-Heck (für vorderes Auto)
            dist_to_other_ahead = (other.x - (self.x + self.width)) if other.x > self.x else float('inf')

            # Check car behind in target lane
            if other.x < self.x: # Anderes Auto ist hinter uns
                 actual_gap_back = self.x - (other.x + other.width) # Unser Heck zu dessen Front
                 required_gap_back = min_gap + (other.speed * time_gap_back) # Benötigter Abstand basierend auf Geschwindigkeit des HINTEREN

                 if actual_gap_back < required_gap_back:
                    # print(f"Car {self.id}: Cannot change {direction} to {target_lane_idx}, car {other.id} too close behind ({actual_gap_back:.1f} < {required_gap_back:.1f})")
                    return False

            # Check car ahead in target lane
            if other.x > self.x: # Anderes Auto ist vor uns
                 actual_gap_front = other.x - (self.x + self.width) # Unsere Front zu dessen Heck
                 required_gap_front = min_gap + (self.speed * time_gap_front) # Benötigter Abstand basierend auf UNSERER Geschwindigkeit

                 if actual_gap_front < required_gap_front:
                    # print(f"Car {self.id}: Cannot change {direction} to {target_lane_idx}, car {other.id} too close ahead ({actual_gap_front:.1f} < {required_gap_front:.1f})")
                    return False

        return True

    def initiate_lane_change(self, direction):
        """Startet den Spurwechselvorgang."""
        if not self.is_changing_lane:
            # Zusätzliche Prüfung: Nicht direkt nach Abschluss eines Wechsels wieder wechseln
            # if hasattr(self, 'last_lane_change_time') and time.time() - self.last_lane_change_time < 1.0:
            #    return # Kurze Pause nach Spurwechsel
            self.is_changing_lane = True
            self.lane_change_direction = direction
            self.target_lane = self.lane + direction


    def perform_lane_change(self, dt, all_cars):
        """Führt den Spurwechsel schrittweise durch."""
        target_y = self.get_lane_center_y(self.target_lane)
        current_center_y = self.y + self.height / 2
        target_center_y = target_y + self.height / 2

        delta_y = target_center_y - current_center_y
        move_y_abs = CONFIG["lane_change_speed"] * dt
        move_y = move_y_abs * self.lane_change_direction

        if abs(delta_y) <= move_y_abs:
            self.y = target_y
            self.lane = self.target_lane
            self.is_changing_lane = False
            self.lane_change_direction = 0
            # self.last_lane_change_time = time.time() # Zeitstempel für Pause
            self.adjust_speed(dt, all_cars) # Geschwindigkeit an neue Spur anpassen
        else:
            self.y += move_y
            # Leichte Geschwindigkeitsreduktion während des Wechsels (optional)
            self.speed *= 0.998


    def find_car_ahead(self, all_cars):
        """Findet das nächste Auto in der gleichen Spur (oder Zielspur bei Wechsel)."""
        current_lane_to_check = self.target_lane if self.is_changing_lane else self.lane

        min_dist = float('inf')
        car_ahead = None
        for other in all_cars:
             is_in_relevant_lane = (other.lane == current_lane_to_check or
                                   (other.is_changing_lane and other.target_lane == current_lane_to_check))

             if other.id != self.id and is_in_relevant_lane and other.x > self.x:
                dist = other.x - self.x # Abstand Front zu Front
                if dist < min_dist:
                    min_dist = dist
                    car_ahead = other
        return car_ahead

    def draw(self, screen):
        """Zeichnet das Auto."""
        # Stelle sicher, dass Positionen Integer sind für Pygame Rect
        car_rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        pygame.draw.rect(screen, self.color, car_rect)


    def reset_position(self, all_cars):
        """Setzt das Auto an den Anfang zurück."""
        if self.type == 'slow':
             self.lane = 0
        elif self.type == 'medium':
             self.lane = random.choice([0,1]) if CONFIG["num_lanes"] > 1 else 0
        else: # fast
             self.lane = random.choice([max(0, CONFIG["num_lanes"] - 2), CONFIG["num_lanes"] - 1]) if CONFIG["num_lanes"] > 0 else 0

        self.target_lane = self.lane
        self.is_changing_lane = False

        road_height = CONFIG["num_lanes"] * CONFIG["lane_width"]
        road_top_y = (CONFIG["screen_height"] - road_height) // 2
        self.y = road_top_y + (self.lane * CONFIG["lane_width"]) + (CONFIG["lane_width"] / 2) - (self.height / 2)

        min_reset_x = -CONFIG["screen_width"] * 1.8
        max_reset_x = -CONFIG["car_width"] * 10
        self.x = random.uniform(min_reset_x, max_reset_x)

        # Kollisionsprüfung beim Reset (vereinfacht)
        placed = False
        attempts = 0
        min_dist = CONFIG["car_height"] * CONFIG["safe_distance_factor"] * 2.5 # Größerer Abstand beim Reset

        while not placed and attempts < 50:
             collision = False
             for other in all_cars:
                 is_relevant_lane = (other.lane == self.lane or
                                     (other.is_changing_lane and other.target_lane == self.lane))
                 if other.id != self.id and is_relevant_lane:
                      if abs(self.x - other.x) < min_dist:
                           collision = True
                           self.x -= min_dist # Weiter nach links
                           if self.x < min_reset_x - CONFIG["screen_width"]:
                               break
                           break
             if not collision or self.x < min_reset_x - CONFIG["screen_width"]:
                 placed = True
             attempts += 1

        self.speed = self.max_speed * random.uniform(0.5, 0.7) # Mit etwas variabler Geschwindigkeit starten


# --- GUI Klasse ---
class ControlGUI:
    def __init__(self, master, config, restart_callback):
        self.master = master
        self.config = config
        self.restart_callback = restart_callback
        self.master.title("Simulation Control")

        self.vars = {}
        self.labels = {} # Zum Speichern der Wert-Labels

        frame = ttk.Frame(master, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(frame, text="Simulation Parameters").grid(column=0, row=0, columnspan=3, pady=5)

        row_idx = 1

        param_defs = [
            ("total_cars", "Total Cars", 1, 150, 1),
            ("base_max_speed_slow", "Max Speed Slow (Blue)", 10, 100, 5),
            ("base_max_speed_medium", "Max Speed Medium (Green)", 30, 150, 5),
            ("base_max_speed_fast", "Max Speed Fast (Red)", 50, 200, 5),
            ("safe_distance_factor", "Safe Distance Factor", 1.0, 5.0, 0.1),
            ("acceleration", "Acceleration", 5, 50, 1),
            ("braking_deceleration", "Braking Deceleration", 10, 100, 5),
            ("hard_braking_deceleration", "Hard Braking", 50, 200, 10),
            ("slow_car_lane_change_prob", "Slow Car Overtake Prob", 0.0, 0.01, 0.0005),
            ("min_gap_overtake", "Min Overtake Gap (px)", 10, 150, 5),
            ("min_gap_move_right", "Min Move Right Gap (px)", 10, 150, 5),
            ("lane_change_speed", "Lane Change Speed (px/s)", 10, 100, 5),
        ]

        for key, text, min_val, max_val, res in param_defs:
            ttk.Label(frame, text=text).grid(column=0, row=row_idx, sticky=tk.W, padx=5, pady=2)
            var = tk.DoubleVar(value=self.config[key])
            self.vars[key] = var
            scale = ttk.Scale(frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL, variable=var, length=200)
            scale.grid(column=1, row=row_idx, sticky=(tk.W, tk.E), padx=5, pady=2)
            val_label = ttk.Label(frame, text="", width=7)
            val_label.grid(column=2, row=row_idx, sticky=tk.W, padx=5)
            self.labels[key] = val_label # Label speichern

            # Binden der Events zur Aktualisierung und Rundung
            def scale_changed(event, k=key, s=scale, r=res, v=var):
                raw_value = s.get()
                snapped_value = round(raw_value / r) * r
                snapped_value = float(f"{snapped_value:.6f}") # Rundungsfehler vermeiden
                if k == "total_cars":
                    snapped_value = int(snapped_value)
                # Nur setzen, wenn Wert sich geändert hat, um unnötige traces zu vermeiden
                if v.get() != snapped_value:
                    v.set(snapped_value)

            scale.bind("<B1-Motion>", scale_changed)
            scale.bind("<ButtonRelease-1>", scale_changed)

            # Trace zur Aktualisierung des Labels
            var.trace_add("write", lambda name, index, mode, k=key, v=var: self.update_label_text(k, v))

            # Initialwert im Label anzeigen
            self.update_label_text(key, var)

            row_idx += 1

        # Neustart-Button
        restart_button = ttk.Button(frame, text="Apply & Restart Simulation", command=self.apply_and_restart)
        restart_button.grid(column=0, row=row_idx, columnspan=3, pady=15)

        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def update_label_text(self, key, var):
        """Aktualisiert den Text des Labels für einen Parameter."""
        label_widget = self.labels.get(key)
        if not label_widget: return
        try:
            value = var.get()
            if key == "total_cars":
                text = f"{int(value)}"
            elif abs(value) < 0.01 and abs(value) > 0:
                 text = f"{value:.4f}"
            elif abs(value) < 1:
                 text = f"{value:.3f}"
            else:
                 text = f"{value:.1f}"
            label_widget.config(text=text)
        except (ValueError, tk.TclError): # TclError fängt Fehler ab, wenn Widget zerstört wird
            label_widget.config(text="N/A")

    def apply_and_restart(self):
        """Aktualisiert die globale CONFIG und ruft den Callback auf."""
        print("--- Applying new config ---")
        for key, var in self.vars.items():
            try:
                value = var.get()
                if key == "total_cars":
                     value = int(value)
                self.config[key] = value
                print(f"  {key}: {value}")
            except tk.TclError:
                 print(f"  Error reading value for {key} (window likely closing).")
        print("---------------------------")
        if self.restart_callback:
            self.restart_callback()

# --- Globale Variablen für Pygame und Simulation ---
screen = None
clock = None
cars = []
running = True
simulation_needs_restart = False
gui_root = None # Globale Referenz auf Tkinter-Root

# --- Pygame Initialisierung und Hauptschleife ---
def initialize_simulation():
    """Initialisiert oder reinitialisiert die Pygame-Simulation."""
    global screen, clock, cars
    if not pygame.get_init(): # Nur initialisieren, wenn nicht schon geschehen
        print("Initializing Pygame...")
        pygame.init()
        # Font-Modul explizit initialisieren, falls nötig
        if not pygame.font.get_init():
            pygame.font.init()
            print("Pygame font module initialized.")

    # Prüfen, ob die Anzeige bereits initialisiert ist
    if screen is None:
        print("Creating Pygame screen...")
        try:
            screen = pygame.display.set_mode((CONFIG["screen_width"], CONFIG["screen_height"]))
            pygame.display.set_caption("Traffic Simulation")
        except pygame.error as e:
            print(f"Fatal: Could not set display mode: {e}")
            sys.exit(1) # Beenden, wenn Bildschirm nicht erstellt werden kann
    if clock is None:
        clock = pygame.time.Clock()
        print("Pygame clock created.")

    # Autos erstellen (alte Liste leeren)
    cars.clear()
    total_cars_to_create = CONFIG.get("total_cars", 0) # Sicherer Zugriff
    if total_cars_to_create <= 0:
        print("Warning: total_cars is zero or less. No cars will be created.")
        return

    # Aufteilung etc. wie zuvor...
    num_slow = max(0, int(total_cars_to_create * 0.4))
    num_medium = max(0, int(total_cars_to_create * 0.4))
    num_fast = max(0, total_cars_to_create - num_slow - num_medium)
    current_total = num_slow + num_medium + num_fast
    if current_total < total_cars_to_create:
        num_medium += (total_cars_to_create - current_total)
    elif current_total > total_cars_to_create:
         diff = current_total - total_cars_to_create
         removed_slow = min(diff, num_slow)
         num_slow -= removed_slow
         diff -= removed_slow
         if diff > 0: num_medium = max(0, num_medium - diff)

    car_counts = {'slow': num_slow, 'medium': num_medium, 'fast': num_fast}
    car_types_dist = []
    for type, count in car_counts.items(): car_types_dist.extend([type] * count)
    random.shuffle(car_types_dist)

    print(f"Creating {total_cars_to_create} cars: {num_slow} slow, {num_medium} medium, {num_fast} fast")
    lane_occupancy = {i: [] for i in range(CONFIG["num_lanes"])}
    current_car_id = 0
    cars_created = 0
    min_initial_spacing = CONFIG["car_height"] * CONFIG["safe_distance_factor"] * 1.5

    def find_free_spot_for_car(lane_idx, car_width, min_spacing):
        # (Implementierung wie zuvor)
        attempts = 0
        max_attempts = 200
        min_x = -CONFIG["screen_width"] * 1.5
        max_x = -car_width # Nur links vom Bildschirm starten
        while attempts < max_attempts:
            x_start = random.uniform(min_x, max_x)
            x_end = x_start + car_width
            is_free = True
            for occupied_start, occupied_end in lane_occupancy[lane_idx]:
                if max(x_start, occupied_start) < min(x_end, occupied_end) + min_spacing:
                    is_free = False
                    break
            if is_free:
                lane_occupancy[lane_idx].append((x_start, x_end))
                return x_start
            attempts += 1
        # Fallback
        fallback_x = min_x - len(lane_occupancy[lane_idx]) * (car_width + min_spacing)
        lane_occupancy[lane_idx].append((fallback_x, fallback_x + car_width))
        return fallback_x

    for car_type in car_types_dist:
         if CONFIG["num_lanes"] <= 0: continue # Keine Spuren -> keine Autos
         if car_type == 'slow':
             preferred_lane = 0
         elif car_type == 'medium':
             preferred_lane = random.choice([0, 1]) if CONFIG["num_lanes"] > 1 else 0
         else:
             preferred_lane = random.choice([max(0, CONFIG["num_lanes"] - 2), CONFIG["num_lanes"] - 1]) if CONFIG["num_lanes"] > 0 else 0

         # Stelle sicher, dass die Spur existiert
         preferred_lane = min(preferred_lane, CONFIG["num_lanes"] - 1)

         start_x = find_free_spot_for_car(preferred_lane, CONFIG["car_width"], min_initial_spacing)
         cars.append(Car(current_car_id, preferred_lane, car_type, start_x))
         current_car_id += 1
         cars_created += 1

    print(f"Simulation initialized with {cars_created} cars.")


def draw_road():
    """Zeichnet die Straße und die Spuren."""
    if screen is None: return
    screen.fill(GRAY)
    road_height = CONFIG["num_lanes"] * CONFIG["lane_width"]
    road_top_y = (CONFIG["screen_height"] - road_height) // 2
    road_rect = pygame.Rect(0, road_top_y, CONFIG["screen_width"], road_height)
    pygame.draw.rect(screen, ROAD_GRAY, road_rect)

    for i in range(1, CONFIG["num_lanes"]):
        line_y = road_top_y + i * CONFIG["lane_width"]
        dash_length = 15
        gap_length = 10
        start_x = 0
        for x in range(start_x, CONFIG["screen_width"], dash_length + gap_length):
            start_pos = (x, line_y)
            end_pos = (x + dash_length, line_y)
            if end_pos[0] > 0 and start_pos[0] < CONFIG["screen_width"]:
                 pygame.draw.line(screen, WHITE, start_pos, end_pos, 2)

def run_simulation():
    """Führt die Hauptschleife von Pygame aus und integriert Tkinter-Updates."""
    global running, simulation_needs_restart, gui_root

    try:
        initialize_simulation() # Erste Initialisierung
    except Exception as e:
        print(f"Error during initial simulation setup: {e}")
        running = False

    while running:
        # --- Tkinter Updates & Event Handling ---
        if gui_root:
            try:
                # Verarbeitet Tkinter Events und aktualisiert die GUI
                gui_root.update()
            except tk.TclError as e:
                # Fehler tritt auf, wenn das Fenster zerstört wurde, während wir updaten
                if "application has been destroyed" in str(e):
                    print("Tkinter window was closed.")
                    gui_root = None # Verhindert weitere Updates
                    running = False # Beende auch Pygame
                else:
                    print(f"Tkinter error during update: {e}")
                    # running = False # Optional: Bei anderen Tk-Fehlern auch beenden
            except Exception as e:
                 print(f"Unexpected error during gui_root.update(): {e}")
                 running = False


        if simulation_needs_restart:
            print("Restarting simulation...")
            try:
                initialize_simulation() # Reinitialisieren mit neuen Parametern
                simulation_needs_restart = False
            except Exception as e:
                print(f"Error during simulation restart: {e}")
                running = False # Kritischer Fehler -> Stopp

        # --- Pygame Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Pygame QUIT event received.")
                running = False

        if not running: # Erneut prüfen, falls Tkinter-Update oder Event running geändert hat
            break

        # Delta Time berechnen
        dt = min(clock.tick(CONFIG["fps"]) / 1000.0, 0.1)

        # --- Update Schritt ---
        for car in cars:
            try:
                car.update(dt, cars)
            except Exception as e:
                print(f"Error updating car {car.id}: {e}")


        # --- Draw Schritt ---
        try:
            draw_road()
            for car in cars:
                car.draw(screen)
            pygame.display.flip()
        except Exception as e:
             print(f"Error during drawing: {e}")
             # running = False # Optional stoppen

    # --- Aufräumen nach der Schleife ---
    print("Exiting simulation loop.")
    if gui_root:
        try:
            print("Destroying Tkinter window...")
            gui_root.destroy()
            gui_root = None
        except (tk.TclError, Exception) as e:
            print(f"Note: Error destroying Tkinter window (may already be closed): {e}")

    if pygame.get_init():
        print("Quitting Pygame...")
        pygame.quit()


def signal_restart():
    """Setzt das Flag, dass die Simulation neu gestartet werden muss."""
    global simulation_needs_restart
    if not simulation_needs_restart:
        print("Restart signaled.")
        simulation_needs_restart = True

# --- Callback für Tkinter Fenster-Schließbutton ---
def on_tkinter_close():
    """Wird aufgerufen, wenn das Tkinter-Fenster geschlossen wird."""
    global running, gui_root
    print("Tkinter window close button pressed.")
    running = False # Signalisiert der Pygame-Schleife zu stoppen
    # Zerstören nicht hier, wird im Cleanup nach der Schleife gemacht


# --- Hauptprogramm ---
if __name__ == "__main__":
    # Tkinter-Root-Fenster erstellen (aber noch nicht mainloop starten)
    gui_root = tk.Tk()
    # Verhindern, dass das leere Hauptfenster kurz aufblitzt
    gui_root.withdraw() # Zuerst verstecken

    # GUI-Inhalt erstellen
    gui_app = ControlGUI(gui_root, CONFIG, signal_restart)

    # Schließ-Callback für Tkinter-Fenster setzen
    gui_root.protocol("WM_DELETE_WINDOW", on_tkinter_close)

    # Tkinter-Fenster jetzt anzeigen
    gui_root.deiconify()

    # Pygame starten und Hauptschleife ausführen (diese Funktion blockiert bis zum Ende)
    run_simulation()

    print("Program finished.")
    # sys.exit(0) # Expliziter Exit-Code (optional)