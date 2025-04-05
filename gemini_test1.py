import tkinter as tk
from tkinter import ttk

class App:
    def __init__(self, master):
        self.master = master
        master.title("Tkinter Demo")

        self.label = ttk.Label(master, text="Hello, Tkinter!")
        self.label.pack(pady=10)

        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(master, textvariable=self.entry_var)
        self.entry.pack(pady=5)

        self.button = ttk.Button(master, text="Click Me!", command=self.greet)
        self.button.pack(pady=5)

        self.checkbox_var = tk.BooleanVar()
        self.checkbox = ttk.Checkbutton(master, text="Check Me", variable=self.checkbox_var)
        self.checkbox.pack(pady=5)

        self.radio_var = tk.StringVar()
        self.radio1 = ttk.Radiobutton(master, text="Option 1", variable=self.radio_var, value="Option 1")
        self.radio1.pack(pady=2)
        self.radio2 = ttk.Radiobutton(master, text="Option 2", variable=self.radio_var, value="Option 2")
        self.radio2.pack(pady=2)

        self.combobox_var = tk.StringVar()
        self.combobox = ttk.Combobox(master, textvariable=self.combobox_var, values=["Value 1", "Value 2", "Value 3"])
        self.combobox.pack(pady=5)
        self.combobox.current(0)

        self.scale_var = tk.DoubleVar()
        self.scale = ttk.Scale(master, from_=0, to=100, variable=self.scale_var, orient=tk.HORIZONTAL)
        self.scale.pack(pady=5)

        self.progress_var = tk.DoubleVar()
        self.progressbar = ttk.Progressbar(master, variable=self.progress_var, maximum=100)
        self.progressbar.pack(pady=5)
        self.progress_var.set(50)       

    def greet(self):
        print("Greetings!")
        print(f"Entry: {self.entry_var.get()}")
        print(f"Checkbox: {self.checkbox_var.get()}")
        print(f"Radiobutton: {self.radio_var.get()}")
        print(f"Combobox: {self.combobox_var.get()}")
        print(f"Scale: {self.scale_var.get()}")


root = tk.Tk()
app = App(root)
root.mainloop()
