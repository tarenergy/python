import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

def roll_dice(num_dice, num_rolls):
    rolls = np.random.randint(1, 7, size=(num_rolls, num_dice))
    sums = np.sum(rolls, axis=1)
    return sums

def theoretical_distribution(num_dice, num_rolls):
    # Mögliche Summen
    min_sum = num_dice
    max_sum = num_dice * 6
    
    # Array für die Wahrscheinlichkeiten
    x = np.arange(min_sum, max_sum + 1)
    
    # Berechnung der exakten Verteilung durch dynamische Programmierung
    # Start mit einem Würfel
    probs = np.ones(6) / 6
    
    # Für jeden weiteren Würfel
    for _ in range(num_dice - 1):
        new_probs = np.zeros(len(probs) + 5)  # Platz für neue maximale Summe
        for i in range(1, 7):  # Für jede Würfelseite
            new_probs[i-1:i-1+len(probs)] += probs / 6
        probs = new_probs
    
    # Skaliere auf Anzahl der Würfe
    return x, probs * num_rolls

def update_plot():
    try:
        num_dice = int(dice_entry.get())
        num_rolls = int(rolls_entry.get())
        
        if num_dice <= 0 or num_rolls <= 0:
            raise ValueError("Bitte positive Zahlen eingeben")
        
        # Simulierte Würfe
        sums = roll_dice(num_dice, num_rolls)
        
        # Theoretische Verteilung
        x_theo, y_theo = theoretical_distribution(num_dice, num_rolls)
        
        # Histogramm der simulierten Würfe
        hist, bins = np.histogram(sums, bins=range(num_dice, num_dice*6 + 2), density=False)
        
        # Plot aktualisieren
        ax.clear()
        ax.bar(bins[:-1], hist, alpha=0.7, label='Simulierte Würfe', color='blue')
        ax.plot(x_theo, y_theo, 'r-', label='Theoretische Verteilung', linewidth=2)
        
        ax.set_xlabel('Summe')
        ax.set_ylabel('Häufigkeit')
        ax.set_title(f'Würfelsimulation: {num_dice} Würfel, {num_rolls} Würfe')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        canvas.draw()
        
    except ValueError as e:
        status_label.config(text=f"Fehler: {str(e)}")

# GUI Setup
root = tk.Tk()
root.title("Würfelsimulation")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(frame, text="Anzahl Würfel:").grid(row=0, column=0, padx=5, pady=5)
dice_entry = ttk.Entry(frame)
dice_entry.grid(row=0, column=1, padx=5, pady=5)
dice_entry.insert(0, "2")

ttk.Label(frame, text="Anzahl Würfe:").grid(row=1, column=0, padx=5, pady=5)
rolls_entry = ttk.Entry(frame)
rolls_entry.grid(row=1, column=1, padx=5, pady=5)
rolls_entry.insert(0, "1000")

ttk.Button(frame, text="Simulation starten", command=update_plot).grid(row=2, column=0, columnspan=2, pady=10)

status_label = ttk.Label(frame, text="")
status_label.grid(row=3, column=0, columnspan=2)

fig, ax = plt.subplots(figsize=(10, 6))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=1, column=0, padx=10, pady=10)

update_plot()

root.mainloop()