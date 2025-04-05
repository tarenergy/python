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
        aufgaben_typ = random.choice(["rechnung", "text"])
        
        if aufgaben_typ == "rechnung":
            self.operator = random.choice(["+", "-", "*", "/"])
            
            if self.operator in ["+", "-"]:
                self.zahl1 = random.randint(1, 100)
                self.zahl2 = random.randint(1, 100)
            elif self.operator == "*":
                self.zahl1 = random.randint(1, 10)
                self.zahl2 = random.randint(1, 10)
            else:  # Division mit ganzzahligem Ergebnis
                self.zahl2 = random.randint(1, 10)
                self.zahl1 = self.zahl2 * random.randint(1, 10)
            
            self.loesung = eval(f"{self.zahl1} {self.operator} {self.zahl2}")
            self.label_aufgabe.config(text=f"{self.zahl1} {self.operator} {self.zahl2} = ?")
        else:
            texte = ["Haus", "Baum", "Katze", "Hund", "Blume", "Sonne"]
            self.loesung = random.choice(texte)
            self.label_aufgabe.config(text=f"Schreibe richtig: {self.loesung}")
        
        self.entry_antwort.delete(0, tk.END)
        self.label_ergebnis.config(text="")
    
    def pruefe_antwort(self, event=None):
        eingabe = self.entry_antwort.get().strip()
        
        try:
            if str(eingabe) == str(self.loesung):
                self.punkte += 1
                self.label_ergebnis.config(text="Richtig!", fg="green")
            else:
                self.punkte -= 1
                self.label_ergebnis.config(text=f"Bist du dumm oder was? Richtige Antwort: {self.loesung}", fg="red")
        except ValueError:
            self.label_ergebnis.config(text="Bitte eine gültige Eingabe machen!", fg="orange")
        
        self.label_punkte.config(text=f"Punkte: {self.punkte}")
        
        # Verzögerung, bevor die nächste Aufgabe geladen wird
        self.root.after(2000, self.neue_aufgabe)

if __name__ == "__main__":
    root = tk.Tk()
    app = RechenSpiel(root)
    root.mainloop()
