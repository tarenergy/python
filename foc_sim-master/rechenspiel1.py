import tkinter as tk
import random

class RechenSpiel:
    def __init__(self, root):
        self.root = root
        self.root.title("Rechenspiel")
        self.punkte = 0
        
        self.label_aufgabe = tk.Label(root, text="", font=("Arial", 20))
        self.label_aufgabe.pack(pady=20)
        
        self.entry_antwort = tk.Entry(root, font=("Arial", 20))
        self.entry_antwort.pack()
        self.entry_antwort.bind("<Return>", self.pruefe_antwort)
        
        self.label_ergebnis = tk.Label(root, text="", font=("Arial", 16))
        self.label_ergebnis.pack(pady=10)
        
        self.label_punkte = tk.Label(root, text=f"Punkte: {self.punkte}", font=("Arial", 16))
        self.label_punkte.pack(pady=10)
        
        self.neue_aufgabe()
    
    def neue_aufgabe(self):
        self.zahl1 = random.randint(1, 20)
        self.zahl2 = random.randint(1, 20)
        self.operator = random.choice(["+", "-"])
        self.loesung = eval(f"{self.zahl1} {self.operator} {self.zahl2}")
        
        self.label_aufgabe.config(text=f"{self.zahl1} {self.operator} {self.zahl2} = ?")
        self.entry_antwort.delete(0, tk.END)
        self.label_ergebnis.config(text="")
    
    def pruefe_antwort(self, event=None):
        try:
            antwort = int(self.entry_antwort.get())
            if antwort == self.loesung:
                self.punkte += 1
                self.label_ergebnis.config(text="Richtig!", fg="green")
            else:
                self.punkte -= 1
                self.label_ergebnis.config(text=f"Falsch! Richtige Antwort: {self.loesung}", fg="red")
        except ValueError:
            self.label_ergebnis.config(text="Bitte eine Zahl eingeben!", fg="orange")
        
        self.label_punkte.config(text=f"Punkte: {self.punkte}")
        self.neue_aufgabe()

if __name__ == "__main__":
    root = tk.Tk()
    app = RechenSpiel(root)
    root.mainloop()