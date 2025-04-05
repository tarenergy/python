import tkinter as tk
from tkinter import messagebox

def on_button_click(event):
    text = event.widget.cget("text")
    if text == "=":
        try:
            result = eval(str(entry_var.get()))
            entry_var.set(result)
        except Exception as e:
            messagebox.showerror("Fehler", "Ungültige Eingabe")
            entry_var.set("")
    elif text == "C":
        entry_var.set("")
    else:
        entry_var.set(entry_var.get() + text)

# Hauptfenster
root = tk.Tk()
root.title("Taschenrechner")
root.geometry("300x400")

entry_var = tk.StringVar()
entry = tk.Entry(root, textvar=entry_var, font="Arial 20 bold", justify="right")
entry.pack(fill="both", ipadx=8, ipady=8, padx=10, pady=10)

buttons = [
    ["7", "8", "9", "/"],
    ["4", "5", "6", "*"],
    ["1", "2", "3", "-"],
    ["0", "C", "=", "+"]
]

frame = tk.Frame(root)
frame.pack()

for row in buttons:
    button_row = tk.Frame(frame)
    button_row.pack()
    for btn_text in row:
        btn = tk.Button(button_row, text=btn_text, font="Arial 15", width=5, height=2)
        btn.pack(side="left", padx=5, pady=5)
        btn.bind("<Button-1>", on_button_click)

root.mainloop()
