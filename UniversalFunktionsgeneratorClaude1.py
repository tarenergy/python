import tkinter as tk
from tkinter import ttk
import pyaudio
import numpy as np
import time
import threading
import math
from scipy import signal
import random

class AudioFunctionGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal-Funktionsgenerator")
        self.root.geometry("800x600")
        
        # Audio-Parameter
        self.sample_rate = 44100  # Hz
        self.chunk_size = 1024
        self.channels = 2
        self.running = False
        self.thread = None
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Signal-Parameter
        self.signal_type = "Sinus"  # Standard: Sinus
        self.start_freq = 200.0  # Hz
        self.end_freq = 1000.0  # Hz
        self.wobble_time = 1.0  # Sekunden
        self.wobble_mode = "Festfrequenz"  # Festfrequenz, Wobbeln, Frequenzsprung
        self.freq_scale = "Logarithmisch"  # Linear oder Logarithmisch
        self.current_freq = self.start_freq
        self.phase_shift = 0.0  # Phase zwischen linkem und rechtem Kanal (-180 bis +180 Grad)
        self.volume_left = 1.0  # Lautstärke linker Kanal (0-1)
        self.volume_right = 1.0  # Lautstärke rechter Kanal (0-1)
        self.phase = 0.0  # Interne Phase für Signalerzeugung
        self.last_update_time = time.time()
        
        # GUI erstellen
        self.create_widgets()
        
    def create_widgets(self):
        # Hauptframe
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Signal-Typ Auswahl
        signal_frame = ttk.LabelFrame(main_frame, text="Signalform", padding="10")
        signal_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.signal_var = tk.StringVar(value=self.signal_type)
        signals = ["Sinus", "Rechteck", "Dreieck", "Doppelton", "Weißes Rauschen", 
                  "Rosa Rauschen (Bandpass)", "Rosa Rauschen (Voss-McCartney)", 
                  "Rosa Rauschen (Inverse FFT)"]
        
        for i, signal_name in enumerate(signals):
            ttk.Radiobutton(signal_frame, text=signal_name, value=signal_name, 
                           variable=self.signal_var, command=self.update_params).grid(
                           row=i//2, column=i%2, sticky="w", padx=5, pady=2)
        
        # Modus-Auswahl
        mode_frame = ttk.LabelFrame(main_frame, text="Frequenzmodus", padding="10")
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mode_var = tk.StringVar(value=self.wobble_mode)
        modes = ["Festfrequenz", "Wobbeln", "Frequenzsprung"]
        
        for i, mode in enumerate(modes):
            ttk.Radiobutton(mode_frame, text=mode, value=mode, 
                           variable=self.mode_var, command=self.update_params).pack(
                           side=tk.LEFT, padx=20, pady=2)
        
        # Frequenzskalierung
        scale_frame = ttk.Frame(mode_frame)
        scale_frame.pack(side=tk.RIGHT, padx=20)
        
        self.scale_var = tk.StringVar(value=self.freq_scale)
        scales = ["Linear", "Logarithmisch"]
        
        ttk.Label(scale_frame, text="Skalierung:").pack(side=tk.LEFT)
        for scale in scales:
            ttk.Radiobutton(scale_frame, text=scale, value=scale, 
                           variable=self.scale_var, command=self.update_params).pack(
                           side=tk.LEFT, padx=5)
        
        # Frequenz-Einstellungen
        freq_frame = ttk.LabelFrame(main_frame, text="Frequenzeinstellungen", padding="10")
        freq_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Startfrequenz
        ttk.Label(freq_frame, text="Startfrequenz (Hz):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        self.start_freq_var = tk.StringVar(value=str(self.start_freq))
        self.start_freq_entry = ttk.Entry(freq_frame, textvariable=self.start_freq_var, width=10)
        self.start_freq_entry.grid(row=0, column=1, padx=5, pady=5)
        self.start_freq_entry.bind("<Return>", self.update_from_entry)
        
        ttk.Label(freq_frame, text="10").grid(row=1, column=0, padx=5)
        self.start_freq_scale = ttk.Scale(freq_frame, from_=1, to=4, length=300, 
                                         command=self.update_start_freq)
        self.start_freq_scale.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5)
        self.start_freq_scale.set(math.log10(self.start_freq/10))
        ttk.Label(freq_frame, text="10000").grid(row=1, column=3, padx=5)
        
        # Endfrequenz
        ttk.Label(freq_frame, text="Endfrequenz (Hz):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        self.end_freq_var = tk.StringVar(value=str(self.end_freq))
        self.end_freq_entry = ttk.Entry(freq_frame, textvariable=self.end_freq_var, width=10)
        self.end_freq_entry.grid(row=2, column=1, padx=5, pady=5)
        self.end_freq_entry.bind("<Return>", self.update_from_entry)
        
        ttk.Label(freq_frame, text="10").grid(row=3, column=0, padx=5)
        self.end_freq_scale = ttk.Scale(freq_frame, from_=1, to=4, length=300, 
                                       command=self.update_end_freq)
        self.end_freq_scale.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5)
        self.end_freq_scale.set(math.log10(self.end_freq/10))
        ttk.Label(freq_frame, text="10000").grid(row=3, column=3, padx=5)
        
        # Wobbelzeit
        ttk.Label(freq_frame, text="Wobbelzeit (Sek):").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        
        self.wobble_time_var = tk.StringVar(value=str(self.wobble_time))
        self.wobble_time_entry = ttk.Entry(freq_frame, textvariable=self.wobble_time_var, width=10)
        self.wobble_time_entry.grid(row=4, column=1, padx=5, pady=5)
        self.wobble_time_entry.bind("<Return>", self.update_from_entry)
        
        ttk.Label(freq_frame, text="0.1").grid(row=5, column=0, padx=5)
        self.wobble_time_scale = ttk.Scale(freq_frame, from_=-1, to=2, length=300, 
                                          command=self.update_wobble_time)
        self.wobble_time_scale.grid(row=5, column=1, columnspan=2, sticky="ew", padx=5)
        self.wobble_time_scale.set(math.log10(self.wobble_time))
        ttk.Label(freq_frame, text="100").grid(row=5, column=3, padx=5)
        
        # Lautstärke und Phase
        vol_frame = ttk.LabelFrame(main_frame, text="Lautstärke und Phase", padding="10")
        vol_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Lautstärke links
        ttk.Label(vol_frame, text="Lautstärke Links:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.vol_left_scale = ttk.Scale(vol_frame, from_=0, to=1, length=300, 
                                       command=self.update_vol_left)
        self.vol_left_scale.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5)
        self.vol_left_scale.set(self.volume_left)
        
        # Lautstärke rechts
        ttk.Label(vol_frame, text="Lautstärke Rechts:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.vol_right_scale = ttk.Scale(vol_frame, from_=0, to=1, length=300, 
                                        command=self.update_vol_right)
        self.vol_right_scale.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5)
        self.vol_right_scale.set(self.volume_right)
        
        # Phasenverschiebung
        ttk.Label(vol_frame, text="Phasenverschiebung:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(vol_frame, text="-180°").grid(row=2, column=1, sticky="w")
        self.phase_scale = ttk.Scale(vol_frame, from_=-180, to=180, length=300, 
                                    command=self.update_phase)
        self.phase_scale.grid(row=2, column=2, sticky="ew", padx=5)
        self.phase_scale.set(self.phase_shift)
        ttk.Label(vol_frame, text="+180°").grid(row=2, column=3, sticky="e")
        
        # Start/Stop Button
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_stop_text = tk.StringVar(value="Start")
        self.start_stop_button = ttk.Button(control_frame, textvariable=self.start_stop_text, 
                                           command=self.toggle_audio, width=20)
        self.start_stop_button.pack(side=tk.LEFT, padx=5)
        
        # Statusanzeige
        self.status_var = tk.StringVar(value="Bereit")
        status_label = ttk.Label(control_frame, textvariable=self.status_var, font=("Arial", 10, "italic"))
        status_label.pack(side=tk.RIGHT, padx=5)
    
    def update_start_freq(self, value):
        # Logarithmischer Schieberegler für Startfrequenz
        log_value = float(value)
        freq = 10 * 10**log_value
        # Auf 4 Nachkommastellen runden
        freq = round(freq, 4)
        self.start_freq = freq
        self.start_freq_var.set(f"{freq:.4f}")
        if self.wobble_mode == "Festfrequenz":
            self.current_freq = self.start_freq
    
    def update_end_freq(self, value):
        # Logarithmischer Schieberegler für Endfrequenz
        log_value = float(value)
        freq = 10 * 10**log_value
        # Auf 4 Nachkommastellen runden
        freq = round(freq, 4)
        self.end_freq = freq
        self.end_freq_var.set(f"{freq:.4f}")
    
    def update_wobble_time(self, value):
        # Logarithmischer Schieberegler für Wobbelzeit
        log_value = float(value)
        time_value = 10**log_value
        # Auf 4 Nachkommastellen runden
        time_value = round(time_value, 4)
        self.wobble_time = time_value
        self.wobble_time_var.set(f"{time_value:.4f}")
    
    def update_vol_left(self, value):
        self.volume_left = float(value)
    
    def update_vol_right(self, value):
        self.volume_right = float(value)
    
    def update_phase(self, value):
        self.phase_shift = float(value)
    
    def update_from_entry(self, event=None):
        # Aktualisiert die Werte, wenn sie in die Eingabefelder eingegeben werden
        try:
            self.start_freq = float(self.start_freq_var.get())
            if self.start_freq < 10:
                self.start_freq = 10
            elif self.start_freq > 10000:
                self.start_freq = 10000
            
            self.start_freq_scale.set(math.log10(self.start_freq/10))
            self.start_freq_var.set(f"{self.start_freq:.4f}")
            
            if self.wobble_mode == "Festfrequenz":
                self.current_freq = self.start_freq
        except ValueError:
            self.start_freq_var.set(f"{self.start_freq:.4f}")
        
        try:
            self.end_freq = float(self.end_freq_var.get())
            if self.end_freq < 10:
                self.end_freq = 10
            elif self.end_freq > 10000:
                self.end_freq = 10000
            
            self.end_freq_scale.set(math.log10(self.end_freq/10))
            self.end_freq_var.set(f"{self.end_freq:.4f}")
        except ValueError:
            self.end_freq_var.set(f"{self.end_freq:.4f}")
        
        try:
            self.wobble_time = float(self.wobble_time_var.get())
            if self.wobble_time < 0.1:
                self.wobble_time = 0.1
            elif self.wobble_time > 100:
                self.wobble_time = 100
            
            self.wobble_time_scale.set(math.log10(self.wobble_time))
            self.wobble_time_var.set(f"{self.wobble_time:.4f}")
        except ValueError:
            self.wobble_time_var.set(f"{self.wobble_time:.4f}")
    
    def update_params(self):
        # Aktualisiert Parameter, wenn Radiobuttons geändert werden
        self.signal_type = self.signal_var.get()
        self.wobble_mode = self.mode_var.get()
        self.freq_scale = self.scale_var.get()
        
        if self.wobble_mode == "Festfrequenz":
            self.current_freq = self.start_freq
        
        self.status_var.set(f"Signaltyp: {self.signal_type}, Modus: {self.wobble_mode}")
    
    def toggle_audio(self):
        if not self.running:
            self.start_audio()
        else:
            self.stop_audio()
    
    def start_audio(self):
        self.running = True
        self.start_stop_text.set("Stop")
        self.status_var.set("Signalausgabe läuft...")
        
        # Audio-Stream starten
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self.audio_callback
        )
        
        # Phase zurücksetzen
        self.phase = 0.0
        self.last_update_time = time.time()
    
    def stop_audio(self):
        self.running = False
        self.start_stop_text.set("Start")
        self.status_var.set("Bereit")
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        # Signalberechnung für den aktuellen Buffer
        output_buffer = np.zeros((frame_count, self.channels), dtype=np.float32)
        
        # Zeitpunkt und aktuelle Frequenz berechnen
        current_time = time.time()
        time_delta = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Frequenzmodulation bei aktivem Wobbeln
        if self.wobble_mode == "Wobbeln":
            # Aktuellen Zeitpunkt im Wobbelzyklus berechnen
            cycle_position = (current_time % self.wobble_time) / self.wobble_time
            
            # Linear oder logarithmisch interpolieren
            if self.freq_scale == "Linear":
                self.current_freq = self.start_freq + cycle_position * (self.end_freq - self.start_freq)
            else:  # Logarithmisch
                log_start = math.log(self.start_freq)
                log_end = math.log(self.end_freq)
                self.current_freq = math.exp(log_start + cycle_position * (log_end - log_start))
        
        # Frequenzsprung
        elif self.wobble_mode == "Frequenzsprung":
            cycle_position = (current_time % self.wobble_time) / self.wobble_time
            if cycle_position < 0.5:
                self.current_freq = self.start_freq
            else:
                self.current_freq = self.end_freq
        
        # Für jeden Sample im Buffer das Signal berechnen
        time_values = np.arange(frame_count) / self.sample_rate
        
        # Signal je nach Typ erzeugen
        if self.signal_type == "Sinus":
            signal_left = self.generate_sine(time_values, 0)
            signal_right = self.generate_sine(time_values, self.phase_shift)
        
        elif self.signal_type == "Rechteck":
            signal_left = self.generate_square(time_values, 0)
            signal_right = self.generate_square(time_values, self.phase_shift)
        
        elif self.signal_type == "Dreieck":
            signal_left = self.generate_triangle(time_values, 0)
            signal_right = self.generate_triangle(time_values, self.phase_shift)
        
        elif self.signal_type == "Doppelton":
            signal_left = self.generate_dual_tone(time_values, 0)
            signal_right = self.generate_dual_tone(time_values, self.phase_shift)
        
        elif self.signal_type == "Weißes Rauschen":
            signal_left = self.generate_white_noise(frame_count)
            signal_right = self.generate_white_noise(frame_count)
        
        elif self.signal_type == "Rosa Rauschen (Bandpass)":
            signal_left = self.generate_pink_noise_bandpass(frame_count)
            signal_right = self.generate_pink_noise_bandpass(frame_count)
        
        elif self.signal_type == "Rosa Rauschen (Voss-McCartney)":
            signal_left = self.generate_pink_noise_voss(frame_count)
            signal_right = self.generate_pink_noise_voss(frame_count)
        
        elif self.signal_type == "Rosa Rauschen (Inverse FFT)":
            signal_left = self.generate_pink_noise_ifft(frame_count)
            signal_right = self.generate_pink_noise_ifft(frame_count)
        
        # Lautstärke anwenden
        output_buffer[:, 0] = signal_left * self.volume_left
        output_buffer[:, 1] = signal_right * self.volume_right
        
        # Phase für nächsten Buffer aktualisieren
        self.phase += 2 * np.pi * self.current_freq * frame_count / self.sample_rate
        self.phase %= 2 * np.pi
        
        # Buffer zurückgeben
        return output_buffer.tobytes(), pyaudio.paContinue
    
    def generate_sine(self, time_values, phase_shift_degrees):
        # Sinus-Signal erzeugen
        phase_shift_rad = phase_shift_degrees * np.pi / 180.0
        return np.sin(2 * np.pi * self.current_freq * time_values + self.phase + phase_shift_rad)
    
    def generate_square(self, time_values, phase_shift_degrees):
        # Rechteck-Signal erzeugen
        phase_shift_rad = phase_shift_degrees * np.pi / 180.0
        return np.sign(np.sin(2 * np.pi * self.current_freq * time_values + self.phase + phase_shift_rad))
    
    def generate_triangle(self, time_values, phase_shift_degrees):
        # Dreieck-Signal erzeugen
        phase_shift_rad = phase_shift_degrees * np.pi / 180.0
        return 2 * np.abs(2 * ((self.current_freq * time_values + (self.phase + phase_shift_rad) / (2 * np.pi)) % 1) - 1) - 1
    
    def generate_dual_tone(self, time_values, phase_shift_degrees):
        # Doppelton (Start- und Endfrequenz gleichzeitig)
        phase_shift_rad = phase_shift_degrees * np.pi / 180.0
        tone1 = 0.5 * np.sin(2 * np.pi * self.start_freq * time_values + self.phase + phase_shift_rad)
        tone2 = 0.5 * np.sin(2 * np.pi * self.end_freq * time_values + self.phase + phase_shift_rad)
        return tone1 + tone2
    
    def generate_white_noise(self, length):
        # Weißes Rauschen erzeugen
        return np.random.uniform(-1, 1, length)
    
    def generate_pink_noise_bandpass(self, length):
        # Rosa Rauschen mit Bandpassfilter
        # Zuerst weißes Rauschen erzeugen
        white = np.random.uniform(-1, 1, length)
        
        # Bandpassfilter anwenden
        nyquist = self.sample_rate / 2.0
        low = self.start_freq / nyquist
        high = self.end_freq / nyquist
        
        # Steilflankiger Bandpassfilter
        b, a = signal.butter(8, [low, high], btype='band')
        filtered = signal.lfilter(b, a, white)
        
        # 1/f Spektrum (rosa Rauschen) durch Filterung
        b_pink = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
        a_pink = [1, -2.494956002, 2.017265875, -0.522189400]
        pink_filtered = signal.lfilter(b_pink, a_pink, filtered)
        
        # Normalisieren
        return pink_filtered / np.max(np.abs(pink_filtered))
    
    def generate_pink_noise_voss(self, length):
        # Rosa Rauschen mit Voss-McCartney Algorithmus
        # Implementierung basierend auf dem Voss-McCartney Algorithmus
        max_key = 14
        white_values = np.random.uniform(-1, 1, length)
        pink = np.zeros(length)
        
        # Array für Speicherung der letzten Werte
        key_values = np.zeros(max_key)
        
        # Laufvariablen
        key = 0
        last_key = 0
        
        # Voss Algorithmus durchführen
        for i in range(length):
            # Nächsten Wert bestimmen
            total = 0
            key = (last_key + 1) & ((1 << max_key) - 1)
            diff = last_key ^ key
            
            # Für jeden geänderten Bit ein neues Zufallssignal generieren
            for j in range(max_key):
                if (diff >> j) & 1:
                    key_values[j] = white_values[i]
            
            # Alle Werte addieren
            for j in range(max_key):
                total += key_values[j]
            
            # Signal aktualisieren
            pink[i] = total / max_key
            last_key = key
        
        # Bandpass anwenden, um die gewünschten Frequenzen zu erhalten
        nyquist = self.sample_rate / 2.0
        low = self.start_freq / nyquist
        high = self.end_freq / nyquist
        
        b, a = signal.butter(4, [low, high], btype='band')
        filtered = signal.lfilter(b, a, pink)
        
        # Normalisieren
        return filtered / np.max(np.abs(filtered))
    
    def generate_pink_noise_ifft(self, length):
        # Rosa Rauschen mit inverser FFT
        # Erstelle ein Spektrum mit 1/f Charakteristik
        L = length
        X = np.random.randn(L//2 + 1) + 1j * np.random.randn(L//2 + 1)
        S = np.zeros(L//2 + 1)
        
        # Frequenzbereichsgrenzen in Bins umrechnen
        start_bin = int(self.start_freq * L / self.sample_rate)
        end_bin = int(self.end_freq * L / self.sample_rate)
        
        # Clip to valid range
        start_bin = max(1, start_bin)  # Avoid DC component
        end_bin = min(end_bin, L//2)
        
        # 1/f Spektrum im gewünschten Frequenzbereich
        for i in range(start_bin, end_bin + 1):
            S[i] = 1.0 / np.sqrt(i)
        
        # Spektrum mit Zufallsphase multiplizieren
        X = X * S
        
        # Symmetrische komplexe Konjugation für reelles Signal
        full_X = np.concatenate([X, np.conj(X[1:-1][::-1])])
        
        # Inverse FFT durchführen
        x = np.real(np.fft.ifft(full_X))
        
        # Normalisieren
        return x / np.max(np.abs(x))

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioFunctionGenerator(root)
    root.mainloop()