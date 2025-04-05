import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.stats import chisquare

class DiceSimulationApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.attributes("-zoomed", True)
        self.title("Würfelsimulation")
        
        # Rahmen für die Parameter
        param_frame = tk.Frame(self)
        param_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Anzahl der Würfel
        tk.Label(param_frame, text="Anzahl der Würfel:").grid(row=0, column=0, sticky="e")
        self.dice_entry = tk.Entry(param_frame, width=10)
        self.dice_entry.grid(row=0, column=1)
        self.dice_entry.insert(0, "2")
        
        # Anzahl der Würfe
        tk.Label(param_frame, text="Anzahl der Würfe:").grid(row=1, column=0, sticky="e")
        self.throws_entry = tk.Entry(param_frame, width=10)
        self.throws_entry.grid(row=1, column=1)
        self.throws_entry.insert(0, "1000")
        
        # Vertrauensbereich (Konfidenzniveau)
        tk.Label(param_frame, text="Vertrauensbereich (%):").grid(row=2, column=0, sticky="e")
        self.confidence_entry = tk.Entry(param_frame, width=10)
        self.confidence_entry.grid(row=2, column=1)
        self.confidence_entry.insert(0, "95")
        
        # Zusätzliche Wahrscheinlichkeit für die 6 in Prozent
        tk.Label(param_frame, text="Erhöhung für 6 (%):").grid(row=3, column=0, sticky="e")
        self.loaded_entry = tk.Entry(param_frame, width=10)
        self.loaded_entry.grid(row=3, column=1)
        self.loaded_entry.insert(0, "0")
        
        # Button zum Starten eines neuen Versuchs
        self.simulate_button = tk.Button(param_frame, text="Neuer Versuch", command=self.simulate)
        self.simulate_button.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Matplotlib-Figur in tkinter einbetten
        self.figure = plt.Figure(figsize=(6, 4))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Label zur Anzeige des Testergebnisses
        self.result_label = tk.Label(self, text="", font=("Arial", 12))
        self.result_label.pack(side=tk.TOP, pady=5)
        
    def simulate(self):
        # Einlesen der Parameter
        try:
            n_dice = int(self.dice_entry.get())
            n_throws = int(self.throws_entry.get())
            confidence = float(self.confidence_entry.get())
            loaded_percent = float(self.loaded_entry.get())
        except ValueError:
            self.result_label.config(text="Ungültige Eingabe!")
            return
        
        # Vertrauensbereich prüfen
        if not (50 <= confidence <= 99.9):
            self.result_label.config(text="Vertrauensbereich muss zwischen 50 und 99,9 liegen!")
            return
        
        # Berechne die manipulierten Einzelwürfelwahrscheinlichkeiten
        # Normalfall: alle Seiten gleichwahrscheinlich (1/6)
        # Bei Manipulation: die 6 ist um loaded_percent% wahrscheinlicher.
        p = loaded_percent / 100.0
        # Wahrscheinlichkeit für Seiten 1-5: 1/(6+p), für Seite 6: (1+p)/(6+p)
        prob = [1/(6+p)] * 5 + [(1+p)/(6+p)]
        
        # Simuliere n_throws Würfe mit n_dice Würfeln (vektorisierte Simulation)
        # Jede Zeile in 'rolls' enthält die Ergebnisse eines Wurfes
        rolls = np.random.choice(np.arange(1, 7), size=(n_throws, n_dice), p=prob)
        sums = np.sum(rolls, axis=1)
        
        # Bestimme die Häufigkeitsverteilung der Wurfsummen
        min_sum = n_dice
        max_sum = 6 * n_dice
        bins = np.arange(min_sum, max_sum + 2) - 0.5  # für zentrierte Balken
        observed_counts, _ = np.histogram(sums, bins=bins)
        sum_values = np.arange(min_sum, max_sum + 1)
        
        # Berechne die theoretische Verteilung für manipulierte Würfel
        loaded_dist = np.array(prob)
        for _ in range(n_dice - 1):
            loaded_dist = np.convolve(loaded_dist, prob)
        expected_loaded_counts = loaded_dist * n_throws
        
        # Berechne die theoretische Verteilung für faire Würfel (jeder Seite 1/6)
        fair_prob = [1/6] * 6
        fair_dist = np.array(fair_prob)
        for _ in range(n_dice - 1):
            fair_dist = np.convolve(fair_dist, fair_prob)
        expected_fair_counts = fair_dist * n_throws
        
        # Chi-Quadrat-Test: Nullhypothese H0: Würfel sind fair
        chi2_stat, p_value = chisquare(f_obs=observed_counts, f_exp=expected_fair_counts)
        alpha = 1 - (confidence / 100)  # z.B. 0.05 bei 95%
        if p_value < alpha:
            test_result = "Ablehnung der H0: Würfel sind manipuliert!"
        else:
            test_result = "H0 kann nicht abgelehnt werden: Keine Manipulation festgestellt."
        
        # Aktualisiere das Diagramm
        self.ax.clear()
        # Balkendiagramm für beobachtete Häufigkeiten
        self.ax.bar(sum_values, observed_counts, width=0.8, label="Beobachtet")
        # Darstellung der erwarteten Häufigkeiten (manipuliert) als gestrichelte Linie mit Punkten
        self.ax.plot(sum_values, expected_loaded_counts, "r--", label="Erwartet (manipuliert)")
        self.ax.set_xlabel("Wurfsumme")
        self.ax.set_ylabel("Häufigkeit")
        self.ax.legend()
        self.ax.set_title(f"Chi² p-Wert: {p_value:.4f}\n{test_result}")
        self.canvas.draw()
        
        # Zeige das Testergebnis
        self.result_label.config(text=test_result)

if __name__ == "__main__":
    app = DiceSimulationApp()
    app.mainloop()
