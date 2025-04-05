import tkinter as tk
from tkinter import messagebox
import numpy as np
import pyaudio
import threading

running = True  # Variable zur Steuerung der Schleife

def generate_waveform(wave_type, freqs, sample_rate):
    """Erzeugt eine Wellenform basierend auf dem ausgewählten Typ."""
    t = np.linspace(0, len(freqs) / sample_rate, len(freqs), False)
    if wave_type == "Sinus":
        wave = 0.5 * np.sin(2 * np.pi * freqs * t)
    elif wave_type == "Rechteck":
        wave = 0.5 * np.sign(np.sin(2 * np.pi * freqs * t))
    elif wave_type == "Dreieck":
        wave = 0.5 * 2 * np.abs(2 * (t * freqs - np.floor(0.5 + t * freqs))) - 1
    elif wave_type == "Impuls":
        wave = (np.random.rand(len(freqs)) > 0.95).astype(float) * 0.5
    elif wave_type == "Rosa Rauschen":
        wave = generate_pink_noise(len(freqs), sample_rate, freqs.min(), freqs.max())
    else:
        wave = np.zeros_like(t)
    return (wave * 32767).astype(np.int16)

def generate_pink_noise(samples, sample_rate, min_freq, max_freq):
    """Erzeugt rosa Rauschen im Frequenzbereich zwischen min_freq und max_freq."""
    noise = np.random.randn(samples)
    fft_noise = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(samples, 1 / sample_rate)
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    fft_noise[~mask] = 0  # Frequenzen außerhalb des Bereichs entfernen
    pink_noise = np.fft.irfft(fft_noise)
    pink_noise /= np.max(np.abs(pink_noise))  # Normalisieren
    return pink_noise * 0.5

def generate_wobble_wave(start_freq, end_freq, duration, wave_type, sample_rate=44100):
    """Erzeugt einen Wobble-Ton mit periodischer Frequenzmodulation (hoch und runter)."""
    total_samples = int(sample_rate * duration)
    t = np.linspace(0, 1, total_samples, False)
    wobble_freq = np.sin(2 * np.pi * t)  # Sinusförmiges Hoch- und Runterwobbeln
    freqs = start_freq + (end_freq - start_freq) * (wobble_freq + 1) / 2
    return generate_waveform(wave_type, freqs, sample_rate)

def play_sound():
    """Spielt den Wobble-Ton in einer Schleife ab."""
    global running
    try:
        start_freq = float(start_freq_entry.get())
        end_freq = float(end_freq_entry.get())
        duration = float(dur_entry.get())
        wave_type = wave_type_var.get()
        if start_freq <= 0 or end_freq <= 0 or duration <= 0:
            raise ValueError("Frequenzen und Dauer müssen positive Werte sein.")
        
        sample_rate = 44100
        chunk_size = 256  # Größe der Audioblöcke
        
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, output=True)
        
        while running:
            wave = generate_wobble_wave(start_freq, end_freq, duration, wave_type, sample_rate)
            for i in range(0, len(wave), chunk_size):
                if not running:
                    break
                stream.write(wave[i:i+chunk_size].tobytes())

        stream.stop_stream()
        stream.close()
        p.terminate()
    except ValueError as e:
        messagebox.showerror("Eingabefehler", str(e))

def start_wobble():
    global running
    running = True
    threading.Thread(target=play_sound, daemon=True).start()

def stop_wobble(event=None):
    global running
    running = False

# GUI erstellen
root = tk.Tk()
root.title("Wobbelgenerator")
root.geometry("300x300")

root.bind("x", stop_wobble)  # Taste 'x' stoppt den Ton

tk.Label(root, text="Startfrequenz (Hz):").pack()
start_freq_entry = tk.Entry(root)
start_freq_entry.pack()

tk.Label(root, text="Endfrequenz (Hz):").pack()
end_freq_entry = tk.Entry(root)
end_freq_entry.pack()

tk.Label(root, text="Dauer (s):").pack()
dur_entry = tk.Entry(root)
dur_entry.pack()

tk.Label(root, text="Wellenform:").pack()
wave_type_var = tk.StringVar(value="Sinus")
tk.OptionMenu(root, wave_type_var, "Sinus", "Rechteck", "Dreieck", "Impuls", "Rosa Rauschen").pack()

tk.Button(root, text="Start Wobbeln", command=start_wobble).pack()
tk.Button(root, text="Stop", command=stop_wobble).pack()

root.mainloop()