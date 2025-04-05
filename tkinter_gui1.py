import tkinter as tk

def toggle_status(action):
    current_color = status_labels[action]["bg"]
    new_color = "green" if current_color == "red" else "red"
    status_labels[action].config(bg=new_color)
    print(f"Button {action} clicked")
    
    if action == "vor":
        arrow_label.config(text="→", font=("Arial", 50, "bold"))
    elif action == "zurück":
        arrow_label.config(text="←", font=("Arial", 50, "bold"))

def validate_float(action, var):
    try:
        value = float(var.get())
        print(f"{action}: {value}")
    except ValueError:
        print(f"Ungültige Eingabe für {action}")
        var.set("")

def on_enter(event, action, var):
    validate_float(action, var)

def save_data():
    print("Daten gespeichert")

def quit_app():
    root.quit()

# Hauptfenster erstellen
root = tk.Tk()
root.title("Steuerung")
root.geometry("500x300")

# Menü erstellen
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Save", command=save_data)
file_menu.add_command(label="Quit", command=quit_app)
menu_bar.add_cascade(label="File", menu=file_menu)

# Buttons, Eingabefelder und Statuslampen erstellen
frame = tk.Frame(root)
frame.pack()

buttons = [
    ("An", "an"),
    ("Aus", "aus"),
    ("Vor", "vor"),
    ("Zurück", "zurück")
]

status_labels = {}
entry_vars = {}

for text, action in buttons:
    row_frame = tk.Frame(frame)
    row_frame.pack(fill="x", pady=5)
    
    var = tk.StringVar()
    entry_vars[action] = var
    
    entry = tk.Entry(row_frame, width=10, textvariable=var)
    entry.pack(side="left", padx=5)
    entry.bind("<Return>", lambda event, a=action, v=var: on_enter(event, a, v))
    
    button = tk.Button(row_frame, text=text, command=lambda a=action: toggle_status(a), width=10, height=2)
    button.pack(side="left", padx=5)
    
    status_label = tk.Label(row_frame, width=2, height=1, bg="red")
    status_label.pack(side="right", padx=5)
    
    status_labels[action] = status_label

# Pfeil anzeigen
arrow_label = tk.Label(root, text="", font=("Arial", 50, "bold"))
arrow_label.pack(pady=20)

# Hauptloop starten
root.mainloop()
