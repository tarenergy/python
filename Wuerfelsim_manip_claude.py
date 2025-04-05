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

        # Mittlere Reihe für Manipulationsparameter
        ttk.Label(control_frame, text="Sechs-Bonus (%):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.six_bias_var = tk.DoubleVar(value=0.0)
        six_bias_spinbox = ttk.Spinbox(control_frame, from_=0.0, to=500.0, increment=5.0, textvariable=self.six_bias_var, width=5)
        six_bias_spinbox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Tooltips für Erklärungen
        ttk.Label(control_frame, text="(0% = fair, 100% = doppelt so wahrscheinlich)").grid(row=1, column=2, columnspan=3, padx=5, pady=5, sticky=tk.W)

        # Untere Reihe für den Vertrauensbereich
        ttk.Label(control_frame, text="Vertrauensniveau (%):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.confidence_var = tk.DoubleVar(value=95.0)
        confidence_spinbox = ttk.Spinbox(control_frame, from_=80.0, to=99.9, increment=0.1, textvariable=self.confidence_var, width=5)
        confidence_spinbox.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Ergebnis des Signifikanztests
        self.significance_label = ttk.Label(control_frame, text="", font=("Arial", 10, "bold"))
        self.significance_label.grid(row=2, column=2, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
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
        six_bias = self.six_bias_var.get() / 100.0  # Umwandlung in Dezimalzahl
        
        # Deaktiviere den Button während der Simulation
        self.sim_button.configure(state="disabled")
        self.root.update()
        
        # Würfelwahrscheinlichkeiten berechnen
        # Bei six_bias = 0 sind alle Zahlen gleich wahrscheinlich (1/6)
        # Bei six_bias = 1 ist die 6 doppelt so wahrscheinlich wie die anderen Zahlen
        if six_bias == 0:
            # Faire Würfel
            face_probs = np.ones(6) / 6
        else:
            # Manipulierte Würfel, bei denen die 6 um six_bias % wahrscheinlicher ist
            # Die Wahrscheinlichkeit für die anderen Zahlen muss entsprechend reduziert werden,
            # damit die Summe aller Wahrscheinlichkeiten 1 ergibt
            extra_prob_for_six = six_bias / 6
            prob_rest = (1 - extra_prob_for_six) / 6
            face_probs = np.ones(6) * prob_rest
            face_probs[5] = prob_rest + extra_prob_for_six
        
        # Würfelwürfe simulieren mit den manipulierten Wahrscheinlichkeiten
        rolls = np.zeros((num_rolls, num_dice), dtype=int)
        
        for i in range(num_rolls):
            for j in range(num_dice):
                # Gewichtete Zufallsauswahl (1-6) basierend auf den berechneten Wahrscheinlichkeiten
                rolls[i, j] = np.random.choice(np.arange(1, 7), p=face_probs)
        
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
        
        # Theoretische Wahrscheinlichkeiten berechnen (immer für faire Würfel als Vergleichsgrundlage)
        theoretical_probs_fair = self.calculate_theoretical_probabilities(num_dice)
        theoretical_counts_fair = theoretical_probs_fair * num_rolls
        
        # Zusätzlich auch theoretische Wahrscheinlichkeiten für manipulierte Würfel berechnen (zur Anzeige)
        if six_bias > 0:
            theoretical_probs_biased = self.calculate_theoretical_probabilities_biased(num_dice, face_probs)
            theoretical_counts_biased = theoretical_probs_biased * num_rolls
        else:
            theoretical_counts_biased = theoretical_counts_fair
        
        # Berechne die Abweichung der experimentellen von der theoretischen Verteilung (fairer Würfel)
        abs_diff = np.abs(experimental_counts - theoretical_counts_fair)
        rel_diff = np.sum(abs_diff) / np.sum(theoretical_counts_fair) * 100
        
        # Führe Signifikanztest durch (Vergleich mit fairen Würfeln)
        chi2_stat, p_value = self.perform_significance_test(experimental_counts, theoretical_counts_fair)
        
        # Bestimme, ob die Würfel manipuliert erscheinen
        alpha = 1 - confidence_level
        is_manipulated = p_value < alpha
        
        # Plotten der Ergebnisse
        self.plot_results(possible_sums, experimental_counts, theoretical_counts_fair, 
                          theoretical_counts_biased, rel_diff, p_value, is_manipulated, 
                          confidence_level, six_bias)
        
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
    
    def calculate_theoretical_probabilities_biased(self, num_dice, face_probs):
        """Berechnet die theoretischen Wahrscheinlichkeiten für die Summen beim Würfeln mit manipulierten Würfeln."""
        min_sum = num_dice
        max_sum = num_dice * 6
        possible_sums = list(range(min_sum, max_sum + 1))
        
        # Für die theoretischen Wahrscheinlichkeiten bei manipulierten Würfeln
        # starten wir mit der Wahrscheinlichkeitsverteilung für einen Würfel
        probs = {i+1: face_probs[i] for i in range(6)}
        
        # Rekursiv für jeden weiteren Würfel die Verteilung aktualisieren
        for _ in range(1, num_dice):
            new_probs = {}
            for old_sum, old_prob in probs.items():
                for face in range(1, 7):
                    new_sum = old_sum + face
                    new_probs[new_sum] = new_probs.get(new_sum, 0) + old_prob * face_probs[face-1]
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
    
    def plot_results(self, possible_sums, experimental_counts, theoretical_counts_fair, 
                    theoretical_counts_biased, rel_diff, p_value, is_manipulated, 
                    confidence_level, six_bias):
        """Plottet die experimentelle und theoretische Häufigkeitsverteilung und zeigt das Ergebnis des Signifikanztests an."""
        self.ax.clear()
        
        # Balkenbreite berechnen
        bar_width = 0.3
        index = np.arange(len(possible_sums))
        
        # Experimentelle Häufigkeiten plotten
        exp_bars = self.ax.bar(index - bar_width, experimental_counts, bar_width, 
                              alpha=0.7, color='blue', label='Experimentell')
        
        # Theoretische Häufigkeiten für faire Würfel plotten
        fair_bars = self.ax.bar(index, theoretical_counts_fair, bar_width, 
                               alpha=0.7, color='green', label='Theoretisch (fair)')
        
        # Wenn manipulierte Würfel vorliegen, auch theoretische Häufigkeiten für manipulierte Würfel plotten
        if six_bias > 0 and not np.array_equal(theoretical_counts_fair, theoretical_counts_biased):
            biased_bars = self.ax.bar(index + bar_width, theoretical_counts_biased, bar_width, 
                                     alpha=0.7, color='red', label='Theoretisch (manipuliert)')
        
        # Labels und Legende hinzufügen
        self.ax.set_xlabel('Summe der Augenzahlen')
        self.ax.set_ylabel('Häufigkeit')
        
        title = f'Häufigkeitsverteilung der Würfelsumme ({self.dice_var.get()} Würfel, {self.rolls_var.get()} Würfe)'
        if six_bias > 0:
            title += f', Sechs-Bonus: {six_bias*100:.2f}%'
        
        self.ax.set_title(title)
        self.ax.set_xticks(index)
        self.ax.set_xticklabels(possible_sums)
        self.ax.legend()
        
        # Y-Achse bei 0 beginnen lassen
        self.ax.set_ylim(bottom=0)
        
        # Statistik Label aktualisieren
        self.stats_label.config(text=f"Relative Abweichung zu fairen Würfeln: {rel_diff:.2f}% | "
                                     f"Anzahl Würfel: {self.dice_var.get()} | "
                                     f"Anzahl Würfe: {self.rolls_var.get()} | "
                                     f"p-Wert: {p_value:.4f}")
        
        # Signifikanz-Label aktualisieren
        if six_bias > 0:
            # Bei absichtlich manipulierten Würfeln
            if is_manipulated:
                result_text = f"ERGEBNIS: Manipulation erkannt! (p < {1-confidence_level:.4f})"
                self.significance_label.config(text=result_text, foreground="red")
            else:
                result_text = f"ERGEBNIS: Manipulation nicht erkannt. (p ≥ {1-confidence_level:.4f})"
                self.significance_label.config(text=result_text, foreground="orange")
        else:
            # Bei fairen Würfeln
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