import tkinter as tk
from tkinter import ttk
import numpy as np
import pyaudio

# Globale Parameter für Audio
SAMPLE_RATE = 44100  # Samplingrate in Hz
DURATION = 2.0       # Dauer des Tons in Sekunden

# Definition der Skalenintervalle in Halbtonschritten
major_scale = [0, 2, 4, 5, 7, 9, 11]
minor_scale = [0, 2, 3, 5, 7, 8, 10]

def play_chord(mode, chord_degree):
    """
    Erzeugt und spielt einen Dreiklang basierend auf dem ausgewählten Modus (Dur/Moll)
    und dem Akkordgrad (I bis VII).

    mode: "Dur" oder "Moll"
    chord_degree: z. B. "I", "II", ..., "VII"
    """
    # Mapping: Akkordgrad in Index (0-indexiert)
    chord_index = {"I": 0, "II": 1, "III": 2, "IV": 3, "V": 4, "VI": 5, "VII": 6}[chord_degree]

    # Für Dur nehmen wir standardmäßig C-Dur (C4 ~ 261,63 Hz) und für Moll A-Moll (A3 ~ 220 Hz)
    if mode == "Dur":
        base_freq = 261.63  # C4
        scale = major_scale
    else:
        base_freq = 220.00  # A3
        scale = minor_scale

    # Erzeuge den Dreiklang: Grundton, Terz und Quinte (entsprechend den Skalenstufen 0, 2 und 4)
    freqs = []
    for offset in [0, 2, 4]:
        idx = chord_index + offset
        octave_adjust = 0
        if idx >= len(scale):
            idx -= len(scale)
            octave_adjust = 12  # Eine Oktave höher, wenn die Stufe über die Skala hinausgeht
        semitone = scale[idx] + octave_adjust
        freq = base_freq * (2 ** (semitone / 12.0))
        freqs.append(freq)

    # Erzeuge den Zeitvektor
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
    chord_wave = np.zeros_like(t)
    
    # Addiere die Sinuswellen der einzelnen Noten
    for freq in freqs:
        chord_wave += np.sin(2 * np.pi * freq * t)
    
    # Normiere die Amplitude, um Clipping zu vermeiden
    chord_wave = chord_wave / np.max(np.abs(chord_wave))
    chord_wave = chord_wave.astype(np.float32)
    
    # Initialisiere PyAudio und spiele den erzeugten Ton
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=SAMPLE_RATE,
                    output=True)
    stream.write(chord_wave.tobytes())
    stream.stop_stream()
    stream.close()
    p.terminate()

def on_play():
    mode = mode_var.get()
    chord = chord_var.get()
    play_chord(mode, chord)

# Erzeuge die grafische Oberfläche
root = tk.Tk()
root.title("Musik-Akkordgenerator")

# Tkinter-Variablen
mode_var = tk.StringVar(value="Dur")
chord_var = tk.StringVar(value="I")

# Auswahlfeld für die Tonart
tk.Label(root, text="Tonart:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
mode_menu = ttk.OptionMenu(root, mode_var, "Dur", "Dur", "Moll")
mode_menu.grid(row=0, column=1, padx=5, pady=5)

# Auswahlfeld für den Akkordgrad
tk.Label(root, text="Akkord:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
chord_menu = ttk.OptionMenu(root, chord_var, "I", "I", "II", "III", "IV", "V", "VI", "VII")
chord_menu.grid(row=1, column=1, padx=5, pady=5)

# Button zum Abspielen des Akkords
play_button = ttk.Button(root, text="Akkord spielen", command=on_play)
play_button.grid(row=2, column=0, columnspan=2, padx=5, pady=10)

root.mainloop()
