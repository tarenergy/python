import tkinter as tk
from tkinter import messagebox
import math

def on_click(button_text):
    if button_text == "=":
        try:
            result = eval(entry_var.get())
            entry_var.set(result)
        except Exception as e:
            messagebox.showerror("Fehler", "Ungültige Eingabe")
    elif button_text == "C":
        entry_var.set("")
    elif button_text == "sin":
        try:
            result = math.sin(math.radians(float(entry_var.get())))
            entry_var.set(result)
        except Exception as e:
            messagebox.showerror("Fehler", "Ungültige Eingabe")
    elif button_text == "cos":
        try:
            result = math.cos(math.radians(float(entry_var.get())))
            entry_var.set(result)
        except Exception as e:
            messagebox.showerror("Fehler", "Ungültige Eingabe")
    elif button_text == "√":
        try:
            result = math.sqrt(float(entry_var.get()))
            entry_var.set(result)
        except Exception as e:
            messagebox.showerror("Fehler", "Ungültige Eingabe")
    elif button_text == "x²":
        try:
            result = float(entry_var.get()) ** 2
            entry_var.set(result)
        except Exception as e:
            messagebox.showerror("Fehler", "Ungültige Eingabe")
    else:
        entry_var.set(entry_var.get() + button_text)

# Hauptfenster erstellen
root = tk.Tk()
root.title("Taschenrechner")
root.geometry("400x400")

entry_var = tk.StringVar()
entry = tk.Entry(root, textvariable=entry_var, font=("Arial", 18), justify='right', bd=10)
entry.grid(row=0, column=0, columnspan=4, ipadx=8, ipady=8)

buttons = [
    ('7', '8', '9', '/'),
    ('4', '5', '6', '*'),
    ('1', '2', '3', '-'),
    ('C', '0', '=', '+'),
    ('sin', 'cos', '√', 'x²')
]

for row_index, row in enumerate(buttons):
    for col_index, text in enumerate(row):
        button = tk.Button(root, text=text, font=("Arial", 16), padx=25, pady=20,
                           command=lambda t=text: on_click(t))
        button.grid(row=row_index+1, column=col_index, sticky='nsew')

root.mainloop()
