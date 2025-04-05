import tkinter as tk
from tkinter import messagebox
import numpy as np
import pyaudio

def generate_sine_wave(frequency, duration, sample_rate=44100):
    """Erzeugt einen Sinuston als numpy-Array."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    return (wave * 32767).astype(np.int16)

def play_sound():
    """Spielt den Sinuston ab und vermeidet Knackser durch blockweise Wiedergabe."""
    try:
        frequency = float(freq_entry.get())
        duration = float(dur_entry.get())
        if frequency <= 0 or duration <= 0:
            raise ValueError("Frequenz und Dauer müssen positive Werte sein.")
        
        sample_rate = 5000
        chunk_size = 1024  # Größe der Audioblöcke
        wave = generate_sine_wave(frequency, duration, sample_rate)
        
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, output=True)
        
        # Blockweise Wiedergabe
        for i in range(0, len(wave), chunk_size):
            stream.write(wave[i:i+chunk_size].tobytes())

        stream.stop_stream()
        stream.close()
        p.terminate()
    except ValueError as e:
        messagebox.showerror("Eingabefehler", str(e))

# GUI erstellen
root = tk.Tk()
root.title("Sinusgenerator")
root.geometry("300x200")

tk.Label(root, text="Frequenz (Hz):").pack()
freq_entry = tk.Entry(root)
freq_entry.pack()

tk.Label(root, text="Dauer (s):").pack()
dur_entry = tk.Entry(root)
dur_entry.pack()

tk.Button(root, text="Ton abspielen", command=play_sound).pack()

root.mainloop()
