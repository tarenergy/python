import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.stats import multinomial, chisquare

class DiceSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Würfelsimulation")
        self.root.geometry("800x600")
        self.root.configure(padx=10, pady=10)
        
        # Erstelle die UI-Elemente
        self.create_widgets()
        
        # Erstelle die Matplotlib-Figur
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Führe die erste Simulation durch
        self.run_simulation()
    
    def create_widgets(self):
        # Steuerungsframe (oben)
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Obere Reihe
        # Anzahl der Würfel
        ttk.Label(control_frame, text="Anzahl der Würfel:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.dice_var = tk.IntVar(value=2)
        dice_spinbox = ttk.Spinbox(control_frame, from_=1, to=10, textvariable=self.dice_var, width=5)
        dice_spinbox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Anzahl der Würfe
        ttk.Label(control_frame, text="Anzahl der Würfe:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.rolls_var = tk.IntVar(value=1000)
        rolls_spinbox = ttk.Spinbox(control_frame, from_=100, to=100000, textvariable=self.rolls_var, width=8)
        rolls_spinbox.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Neuer Versuch Button
        self.sim_button = ttk.Button(control_frame, text="Neuen Versuch starten", command=self.run_simulation)
        self.sim_button.grid(row=0, column=4, padx=20, pady=5)

        # Untere Reihe für den Vertrauensbereich
        ttk.Label(control_frame, text="Vertrauensniveau (%):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.confidence_var = tk.DoubleVar(value=95.0)
        confidence_spinbox = ttk.Spinbox(control_frame, from_=80.0, to=99.9, increment=0.1, textvariable=self.confidence_var, width=5)
        confidence_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Ergebnis des Signifikanztests
        self.significance_label = ttk.Label(control_frame, text="", font=("Arial", 10, "bold"))
        self.significance_label.grid(row=1, column=2, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # Graph-Frame (unten)
        self.plot_frame = ttk.Frame(self.root)
        self.plot_frame.pack(fill=tk.BOTH, expand=True)
        
        # Statistik-Label
        self.stats_label = ttk.Label(self.root, text="", font=("Arial", 10))
        self.stats_label.pack(fill=tk.X, pady=(10, 0))
    
    def run_simulation(self):
        # Parameter der Simulation setzen
        num_dice = self.dice_var.get()
        num_rolls = self.rolls_var.get()
        confidence_level = self.confidence_var.get() / 100.0  # Umwandlung in Dezimalzahl
        
        # Deaktiviere den Button während der Simulation
        self.sim_button.configure(state="disabled")
        self.root.update()
        
        # Wurfsumme simulieren
        rolls = np.random.randint(1, 7, size=(num_rolls, num_dice))
        roll_sums = np.sum(rolls, axis=1)
        
        # Berechne die Häufigkeitsverteilung
        min_sum = num_dice
        max_sum = num_dice * 6
        possible_sums = list(range(min_sum, max_sum + 1))
        
        # Experimentelle Häufigkeiten
        experimental_counts = np.zeros(max_sum - min_sum + 1)
        for i, s in enumerate(possible_sums):
            experimental_counts[i] = np.sum(roll_sums == s)
        
        experimental_probs = experimental_counts / num_rolls
        
        # Theoretische Wahrscheinlichkeiten berechnen
        theoretical_probs = self.calculate_theoretical_probabilities(num_dice)
        theoretical_counts = theoretical_probs * num_rolls
        
        # Berechne die Abweichung der experimentellen von der theoretischen Verteilung
        abs_diff = np.abs(experimental_counts - theoretical_counts)
        rel_diff = np.sum(abs_diff) / np.sum(theoretical_counts) * 100
        
        # Führe Signifikanztest durch
        chi2_stat, p_value = self.perform_significance_test(experimental_counts, theoretical_counts)
        
        # Bestimme, ob die Würfel manipuliert erscheinen
        alpha = 1 - confidence_level
        is_manipulated = p_value < alpha
        
        # Plotten der Ergebnisse
        self.plot_results(possible_sums, experimental_counts, theoretical_counts, rel_diff, p_value, is_manipulated, confidence_level)
        
        # Aktiviere den Button wieder
        self.sim_button.configure(state="normal")
    
    def calculate_theoretical_probabilities(self, num_dice):
        """Berechnet die theoretischen Wahrscheinlichkeiten für die Summen beim Würfeln."""
        min_sum = num_dice
        max_sum = num_dice * 6
        possible_sums = list(range(min_sum, max_sum + 1))
        
        # Für die theoretischen Wahrscheinlichkeiten nutzen wir einen rekursiven Ansatz
        # Beginnen mit einer Wahrscheinlichkeitsverteilung für einen Würfel
        probs = {i: 1/6 for i in range(1, 7)}
        
        # Rekursiv für jeden weiteren Würfel die Verteilung aktualisieren
        for _ in range(1, num_dice):
            new_probs = {}
            for old_sum, old_prob in probs.items():
                for face in range(1, 7):
                    new_sum = old_sum + face
                    new_probs[new_sum] = new_probs.get(new_sum, 0) + old_prob / 6
            probs = new_probs
        
        # Sortierte Wahrscheinlichkeiten für alle möglichen Summen
        theoretical_probs = np.array([probs.get(s, 0) for s in possible_sums])
        
        return theoretical_probs
    
    def perform_significance_test(self, observed, expected):
        """Führt einen Chi-Quadrat-Test durch, um zu prüfen, ob die beobachteten Werte
        von den erwarteten Werten signifikant abweichen."""
        # Wir brauchen mindestens 5 erwartete Beobachtungen pro Kategorie für den Chi-Quadrat-Test
        # Daher kombinieren wir Kategorien mit zu wenigen erwarteten Beobachtungen
        min_expected = 5
        
        valid_obs = []
        valid_exp = []
        
        i = 0
        while i < len(observed):
            curr_obs = observed[i]
            curr_exp = expected[i]
            
            # Wenn die erwartete Häufigkeit zu niedrig ist, kombiniere mit der nächsten Kategorie
            while i < len(observed) - 1 and curr_exp < min_expected:
                i += 1
                curr_obs += observed[i]
                curr_exp += expected[i]
            
            valid_obs.append(curr_obs)
            valid_exp.append(curr_exp)
            i += 1
        
        # Führe den Chi-Quadrat-Test durch
        chi2_stat, p_value = chisquare(valid_obs, valid_exp)
        
        return chi2_stat, p_value
    
    def plot_results(self, possible_sums, experimental_counts, theoretical_counts, rel_diff, p_value, is_manipulated, confidence_level):
        """Plottet die experimentelle und theoretische Häufigkeitsverteilung und zeigt das Ergebnis des Signifikanztests an."""
        self.ax.clear()
        
        # Balkenbreite berechnen
        bar_width = 0.35
        index = np.arange(len(possible_sums))
        
        # Experimentelle Häufigkeiten plotten
        exp_bars = self.ax.bar(index - bar_width/2, experimental_counts, bar_width, 
                              alpha=0.7, color='blue', label='Experimentell')
        
        # Theoretische Häufigkeiten plotten
        theo_bars = self.ax.bar(index + bar_width/2, theoretical_counts, bar_width, 
                               alpha=0.7, color='red', label='Theoretisch')
        
        # Labels und Legende hinzufügen
        self.ax.set_xlabel('Summe der Augenzahlen')
        self.ax.set_ylabel('Häufigkeit')
        title = f'Häufigkeitsverteilung der Würfelsumme ({self.dice_var.get()} Würfel, {self.rolls_var.get()} Würfe)'
        self.ax.set_title(title)
        self.ax.set_xticks(index)
        self.ax.set_xticklabels(possible_sums)
        self.ax.legend()
        
        # Y-Achse bei 0 beginnen lassen
        self.ax.set_ylim(bottom=0)
        
        # Statistik Label aktualisieren
        self.stats_label.config(text=f"Relative Abweichung: {rel_diff:.2f}% | "
                                     f"Anzahl Würfel: {self.dice_var.get()} | "
                                     f"Anzahl Würfe: {self.rolls_var.get()} | "
                                     f"p-Wert: {p_value:.4f}")
        
        # Signifikanz-Label aktualisieren
        if is_manipulated:
            result_text = f"ERGEBNIS: Die Würfel scheinen manipuliert zu sein! (p < {1-confidence_level:.4f})"
            self.significance_label.config(text=result_text, foreground="red")
        else:
            result_text = f"ERGEBNIS: Die Würfel scheinen nicht manipuliert zu sein. (p ≥ {1-confidence_level:.4f})"
            self.significance_label.config(text=result_text, foreground="green")
        
        # Canvas aktualisieren
        self.fig.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = DiceSimulator(root)
    root.mainloop()