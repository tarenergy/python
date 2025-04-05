import tkinter as tk
from tkinter import ttk, messagebox
import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import Counter
from scipy.stats import chisquare
import math
from itertools import product

# --- Kernfunktionen ---

def calculate_single_die_probabilities(bias_percent):
    """
    Berechnet die Wahrscheinlichkeiten für jede Seite eines einzelnen Würfels,
    wobei die 6 um einen bestimmten Prozentsatz wahrscheinlicher sein kann.
    """
    if bias_percent < 0:
        bias_percent = 0 # Negativer Bias ist nicht vorgesehen

    # Normale Wahrscheinlichkeit für jede Seite (1-5)
    # p = Wahrscheinlichkeit für 1, 2, 3, 4, 5
    # p6 = Wahrscheinlichkeit für 6
    # p6 = p * (1 + bias_percent / 100)
    # 5*p + p6 = 1
    # 5*p + p * (1 + bias_percent / 100) = 1
    # p * (5 + 1 + bias_percent / 100) = 1
    # p * (6 + bias_percent / 100) = 1
    # p = 1 / (6 + bias_percent / 100)

    denominator = 6 + bias_percent / 100.0
    if denominator == 0: # Sollte nicht passieren, aber sicher ist sicher
         return [1/6] * 6

    prob_1_to_5 = 1.0 / denominator
    prob_6 = prob_1_to_5 * (1 + bias_percent / 100.0)

    probabilities = [prob_1_to_5] * 5 + [prob_6]

    # Rundungsfehler korrigieren, damit die Summe exakt 1 ist
    probabilities = np.array(probabilities)
    probabilities /= probabilities.sum()

    return probabilities.tolist()

def simulate_dice_rolls(num_dice, num_rolls, bias_percent):
    """
    Simuliert das Würfeln von 'num_dice' Würfeln für 'num_rolls' Würfe.
    Berücksichtigt einen möglichen Bias für die Zahl 6.
    Gibt eine Liste der Summen der Augenzahlen pro Wurf zurück.
    """
    if num_dice <= 0 or num_rolls <= 0:
        return []

    dice_faces = list(range(1, 7))
    probabilities = calculate_single_die_probabilities(bias_percent)

    roll_sums = []
    for _ in range(num_rolls):
        current_roll_sum = 0
        # Würfle jeden Würfel einzeln
        rolls = np.random.choice(dice_faces, size=num_dice, p=probabilities)
        current_roll_sum = np.sum(rolls)
        roll_sums.append(current_roll_sum)

    return roll_sums

def calculate_theoretical_distribution(num_dice):
    """
    Berechnet die theoretische Wahrscheinlichkeitsverteilung der Summen
    beim Wurf von 'num_dice' fairen Würfeln.
    Gibt ein Dictionary zurück: {Summe: Wahrscheinlichkeit}
    und den möglichen Summenbereich (min_sum, max_sum).
    """
    if num_dice <= 0:
        return {}, (0, 0)

    min_sum = num_dice
    max_sum = num_dice * 6
    total_outcomes = 6**num_dice
    sum_counts = Counter()

    # Generiere alle möglichen Wurfkombinationen
    possible_rolls = product(range(1, 7), repeat=num_dice)

    for roll in possible_rolls:
        sum_counts[sum(roll)] += 1

    theoretical_probs = {s: count / total_outcomes for s, count in sum_counts.items()}

    # Stelle sicher, dass alle möglichen Summen im Dictionary sind (auch wenn Prob=0, was hier nicht vorkommt)
    for s in range(min_sum, max_sum + 1):
        if s not in theoretical_probs:
             theoretical_probs[s] = 0.0 # Sollte bei fairen Würfeln nicht passieren

    return theoretical_probs, (min_sum, max_sum)

def perform_significance_test(observed_sums, theoretical_probs, num_rolls, min_sum, max_sum):
    """
    Führt einen Chi-Quadrat-Anpassungstest durch.
    Vergleicht die beobachteten Häufigkeiten mit den erwarteten Häufigkeiten.
    Gibt den Chi-Quadrat-Wert und den p-Wert zurück.
    """
    if not observed_sums or not theoretical_probs or num_rolls == 0:
        return None, None

    observed_counts = Counter(observed_sums)

    # Erstelle Listen für beobachtete und erwartete Häufigkeiten,
    # die auf die gleiche Summenachse ausgerichtet sind.
    sums_range = list(range(min_sum, max_sum + 1))
    f_obs = [observed_counts.get(s, 0) for s in sums_range]
    f_exp = [theoretical_probs.get(s, 0) * num_rolls for s in sums_range]

    # Wichtig: Chi-Quadrat-Test erfordert erwartete Häufigkeiten > 0.
    # Entferne Kategorien (Summen), bei denen die erwartete Häufigkeit 0 ist.
    # (Sollte bei fairen Würfeln nicht vorkommen, aber zur Sicherheit)
    valid_indices = [i for i, exp_count in enumerate(f_exp) if exp_count > 0]
    f_obs_valid = [f_obs[i] for i in valid_indices]
    f_exp_valid = [f_exp[i] for i in valid_indices]

    # Prüfe, ob genügend Daten für den Test vorhanden sind
    if len(f_obs_valid) < 2 or sum(f_obs_valid) == 0:
         messagebox.showwarning("Chi-Quadrat-Test Warnung",
                                "Nicht genügend Daten oder Kategorien für den Chi-Quadrat-Test vorhanden.\n"
                                "Stellen Sie sicher, dass die Anzahl der Würfe ausreichend ist.")
         return None, None

    # Prüfe auf geringe erwartete Häufigkeiten (oft als < 5 angesehen)
    low_expected = sum(1 for count in f_exp_valid if count < 5)
    if low_expected > 0:
        print(f"Warnung: {low_expected} Kategorien haben eine erwartete Häufigkeit < 5. "
              "Der Chi-Quadrat-Test könnte ungenau sein.")
        # Hier könnte man optional Kategorien zusammenfassen, aber das macht die Interpretation komplexer.

    try:
        chisq_stat, p_value = chisquare(f_obs=f_obs_valid, f_exp=f_exp_valid)
        return chisq_stat, p_value
    except ValueError as e:
        messagebox.showerror("Chi-Quadrat-Test Fehler", f"Fehler bei der Berechnung: {e}")
        return None, None


# --- GUI Klasse ---

class DiceSimulatorApp:
    def __init__(self, master):
        self.master = master
        master.title("Würfelsimulator mit Analyse")
        master.geometry("800x700") # Fenstergröße anpassen

        # --- Eingabefelder ---
        input_frame = ttk.Frame(master, padding="10")
        input_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(input_frame, text="Anzahl Würfel:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.num_dice_var = tk.IntVar(value=2)
        ttk.Entry(input_frame, textvariable=self.num_dice_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Anzahl Würfe:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.num_rolls_var = tk.IntVar(value=1000)
        ttk.Entry(input_frame, textvariable=self.num_rolls_var, width=10).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Bias für 6 (% mehr):").grid(row=0, column=2, padx=15, pady=5, sticky=tk.W)
        self.bias_percent_var = tk.DoubleVar(value=0.0)
        ttk.Entry(input_frame, textvariable=self.bias_percent_var, width=10).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="Konfidenzniveau (%):").grid(row=1, column=2, padx=15, pady=5, sticky=tk.W)
        self.confidence_level_var = tk.DoubleVar(value=95.0)
        # Eingabefeld mit Validierung für Konfidenzniveau
        confidence_entry = ttk.Entry(input_frame, textvariable=self.confidence_level_var, width=10)
        confidence_entry.grid(row=1, column=3, padx=5, pady=5)
        # Tooltip hinzufügen
        # self.create_tooltip(confidence_entry, "Werte zwischen 50.0 und 99.9 erlaubt")


        # --- Button ---
        self.run_button = ttk.Button(input_frame, text="Simulation starten / Neuer Versuch", command=self.run_simulation)
        self.run_button.grid(row=2, column=0, columnspan=4, pady=10)

        # --- Plot Bereich ---
        plot_frame = ttk.Frame(master)
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(7, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
        self.ax.set_title("Häufigkeitsverteilung der Wurfsummen")
        self.ax.set_xlabel("Summe der Augenzahlen")
        self.ax.set_ylabel("Häufigkeit")

        # --- Ergebnis Bereich ---
        result_frame = ttk.Frame(master, padding="10")
        result_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.result_label_var = tk.StringVar(value="Ergebnisse des Signifikanztests werden hier angezeigt.")
        result_label = ttk.Label(result_frame, textvariable=self.result_label_var, wraplength=750, justify=tk.LEFT)
        result_label.pack(fill=tk.X)

        # Initialen leeren Plot zeichnen
        self.canvas.draw()

    # def create_tooltip(self, widget, text):
    #      # Einfache Tooltip-Implementierung (optional, erfordert ggf. externe Bibliothek für schönere Darstellung)
    #      def enter(event):
    #          tooltip_window = tk.Toplevel(widget)
    #          tooltip_window.wm_overrideredirect(True)
    #          tooltip_window.wm_geometry(f"+{event.x_root+15}+{event.y_root+10}")
    #          label = tk.Label(tooltip_window, text=text, background="#ffffe0", relief=tk.SOLID, borderwidth=1)
    #          label.pack()
    #          widget.tooltip_window = tooltip_window
    #      def leave(event):
    #          if hasattr(widget, 'tooltip_window'):
    #              widget.tooltip_window.destroy()
    #      widget.bind("<Enter>", enter)
    #      widget.bind("<Leave>", leave)


    def run_simulation(self):
        """Führt die Simulation aus, aktualisiert den Plot und zeigt Testergebnisse an."""
        try:
            num_dice = self.num_dice_var.get()
            num_rolls = self.num_rolls_var.get()
            bias_percent = self.bias_percent_var.get()
            confidence_level = self.confidence_level_var.get()

            # --- Eingabevalidierung ---
            if not (1 <= num_dice):
                 messagebox.showerror("Ungültige Eingabe", "Anzahl der Würfel muss mindestens 1 sein.")
                 return
            if not (num_rolls > 0):
                 messagebox.showerror("Ungültige Eingabe", "Anzahl der Würfe muss größer als 0 sein.")
                 return
            if not (50.0 <= confidence_level <= 99.9):
                 messagebox.showerror("Ungültige Eingabe", "Konfidenzniveau muss zwischen 50.0 und 99.9 liegen.")
                 return
            if bias_percent < 0:
                 messagebox.showwarning("Ungültige Eingabe", "Bias-Prozentsatz wird auf 0 gesetzt (kein negativer Bias).")
                 bias_percent = 0.0
                 self.bias_percent_var.set(0.0)


            # Signifikanzniveau alpha berechnen
            alpha = 1.0 - (confidence_level / 100.0)

            # --- Simulation durchführen ---
            observed_sums = simulate_dice_rolls(num_dice, num_rolls, bias_percent)
            if not observed_sums: # Falls Simulation fehlschlägt (z.B. 0 Würfe)
                self.ax.clear()
                self.ax.set_title("Häufigkeitsverteilung der Wurfsummen")
                self.ax.set_xlabel("Summe der Augenzahlen")
                self.ax.set_ylabel("Häufigkeit")
                self.canvas.draw()
                self.result_label_var.set("Simulation fehlgeschlagen (ungültige Parameter?).")
                return

            observed_counts = Counter(observed_sums)

            # --- Theoretische Verteilung berechnen ---
            # Wichtig: Die theoretische Verteilung basiert auf FAIREN Würfeln für den Test!
            theoretical_probs, (min_sum, max_sum) = calculate_theoretical_distribution(num_dice)
            theoretical_counts = {s: p * num_rolls for s, p in theoretical_probs.items()}

            # --- Plot aktualisieren ---
            self.ax.clear()
            sums_range = list(range(min_sum, max_sum + 1))

            # Beobachtete Häufigkeiten (Balkendiagramm)
            observed_freq = [observed_counts.get(s, 0) for s in sums_range]
            bar_width = 0.4
            bars = self.ax.bar([s - bar_width/2 for s in sums_range], observed_freq, bar_width,
                              label=f'Beobachtet ({num_rolls} Würfe)', color='blue', alpha=0.7)

            # Theoretisch erwartete Häufigkeiten (Linie oder Punkte)
            expected_freq = [theoretical_counts.get(s, 0) for s in sums_range]
            self.ax.plot(sums_range, expected_freq, 'ro-', # Rote Punkte mit Linie
                         label='Theoretisch erwartet (faire Würfel)', linewidth=2, markersize=4)
            # Alternative: Zweites Balkendiagramm
            # self.ax.bar([s + bar_width/2 for s in sums_range], expected_freq, bar_width,
            #                   label='Theoretisch erwartet (faire Würfel)', color='red', alpha=0.6)


            # Achsen und Titel
            self.ax.set_xlabel("Summe der Augenzahlen")
            self.ax.set_ylabel("Häufigkeit")
            self.ax.set_title(f"Vergleich: Beobachtete vs. Theoretische Häufigkeiten ({num_dice} Würfel)")
            self.ax.set_xticks(sums_range) # Stellt sicher, dass alle Summen auf der x-Achse sind
            self.ax.legend()
            self.ax.grid(axis='y', linestyle='--', alpha=0.7)

            # Füge die genauen Werte über die Balken hinzu (optional, kann bei vielen Balken unübersichtlich werden)
            # for bar in bars:
            #     yval = bar.get_height()
            #     if yval > 0: # Nur anzeigen, wenn Häufigkeit > 0
            #         plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.01 * max(observed_freq),
            #                  int(yval), va='bottom', ha='center', fontsize=8)


            self.canvas.draw()

            # --- Signifikanztest durchführen ---
            chisq_stat, p_value = perform_significance_test(observed_sums, theoretical_probs, num_rolls, min_sum, max_sum)

            # --- Ergebnisse anzeigen ---
            if chisq_stat is not None and p_value is not None:
                test_result_text = f"Chi²-Test (Vergleich mit fairen Würfeln):\n"
                test_result_text += f"Chi²-Statistik = {chisq_stat:.4f}, p-Wert = {p_value:.4f}\n"
                test_result_text += f"Signifikanzniveau (alpha) = {alpha:.3f} (für {confidence_level:.1f}% Konfidenz)\n\n"

                if p_value < alpha:
                    test_result_text += f"Ergebnis: Der Test ist signifikant (p < alpha).\n"
                    test_result_text += f"Die Nullhypothese ('die Würfel sind fair') wird verworfen.\n"
                    test_result_text += f"Es gibt statistische Evidenz dafür, dass die Würfel manipuliert sein könnten (oder der Zufall war sehr unwahrscheinlich)."
                    if bias_percent > 0:
                         test_result_text += f"\n(Ein Bias von {bias_percent:.1f}% wurde für die 6 eingestellt.)"
                else:
                    test_result_text += f"Ergebnis: Der Test ist NICHT signifikant (p >= alpha).\n"
                    test_result_text += f"Die Nullhypothese ('die Würfel sind fair') kann nicht verworfen werden.\n"
                    test_result_text += f"Es gibt keine ausreichende statistische Evidenz, um eine Manipulation der Würfel anzunehmen."
                    if bias_percent > 0:
                        test_result_text += f"\n(Obwohl ein Bias von {bias_percent:.1f}% eingestellt wurde, war er bei {num_rolls} Würfen nicht signifikant nachweisbar.)"

                self.result_label_var.set(test_result_text)
            else:
                self.result_label_var.set("Chi-Quadrat-Test konnte nicht durchgeführt werden (siehe Konsole/Warnungen).")

        except ValueError:
             messagebox.showerror("Eingabefehler", "Bitte geben Sie gültige Zahlen für alle Parameter ein.")
        except Exception as e:
             messagebox.showerror("Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {e}")
             # Optional: Log the full traceback
             # import traceback
             # print(traceback.format_exc())


# --- Hauptprogramm ---
if __name__ == "__main__":
    root = tk.Tk()
    app = DiceSimulatorApp(root)
    root.mainloop()