import tkinter as tk
from tkinter import ttk
import pyaudio
import numpy as np
import threading, time, math

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

class AudioGenerator:
    def __init__(self):
        self.fs = 44100
        self.chunk = 1024
        self.running = False
        self.phase = 0.0
        self.start_time = time.perf_counter()
        self.param_lock = threading.Lock()
        self.params = {
            'waveform': 'Sinus',        # Options: Sinus, Rechteck, Dreieck, Weiss, Rosa_BP, Rosa_Voss, Rosa_iFFT
            'mode': 'wobbeln',          # Options: Festfrequenz, wobbeln, Frequenzsprung
            'freq_start': 200.0,
            'freq_end': 1000.0,
            'wobble_speed': 1.0,        # in seconds
            'freq_var': 'linear',       # or "logarithmisch"
            'left_volume': 0.5,
            'right_volume': 0.5,
            'phase_shift': 0.0,         # in degrees
        }
        self.stream = None
        self.pa = pyaudio.PyAudio()
        # State for Voss-McCartney pink noise
        self.voss_rows = 16
        self.voss_vals = np.random.randn(self.voss_rows)
        self.voss_counter = 0

    def start(self):
        if not self.running:
            self.running = True
            self.start_time = time.perf_counter()
            self.phase = 0.0
            self.voss_counter = 0
            self.voss_vals = np.random.randn(self.voss_rows)
            self.stream = self.pa.open(format=pyaudio.paFloat32,
                                       channels=2,
                                       rate=self.fs,
                                       output=True,
                                       frames_per_buffer=self.chunk,
                                       stream_callback=self.callback)
            self.stream.start_stream()

    def stop(self):
        if self.running:
            self.running = False
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
            self.stream = None

    def update_params(self, new_params):
        with self.param_lock:
            self.params.update(new_params)

    def get_params(self):
        with self.param_lock:
            return self.params.copy()

    def callback(self, in_data, frame_count, time_info, status):
        params = self.get_params()
        dt = 1.0 / self.fs

        # Rosa Rauschen inverse FFT
        if params['waveform'] == 'Rosa_iFFT':
            pink_block = generate_pink_noise(frame_count, self.fs, params['freq_start'], params['freq_end'])
            samples_left = pink_block * params['left_volume']
            samples_right = pink_block * params['right_volume']
            interleaved = np.empty(frame_count * 2, dtype=np.float32)
            interleaved[0::2] = samples_left
            interleaved[1::2] = samples_right
            return (interleaved.tobytes(), pyaudio.paContinue if self.running else pyaudio.paComplete)

        samples_left = np.zeros(frame_count, dtype=np.float32)
        samples_right = np.zeros(frame_count, dtype=np.float32)
        for i in range(frame_count):
            current_time = time.perf_counter() - self.start_time
            if params['mode'] == 'Festfrequenz':
                f = params['freq_start']
            elif params['mode'] == 'wobbeln':
                T = params['wobble_speed']
                mod = (current_time % T) / T
                factor = (2 * mod) if mod < 0.5 else (2 - 2 * mod)
                if params['freq_var'] == 'linear':
                    f = params['freq_start'] + (params['freq_end'] - params['freq_start']) * factor
                else:
                    log_start = math.log(params['freq_start'])
                    log_end = math.log(params['freq_end'])
                    f = math.exp(log_start + (log_end - log_start) * factor)
            elif params['mode'] == 'Frequenzsprung':
                T = params['wobble_speed']
                f = params['freq_start'] if int(current_time / T) % 2 == 0 else params['freq_end']
            else:
                f = params['freq_start']
            phase_inc = 2 * math.pi * f * dt
            self.phase += phase_inc
            if self.phase > 2 * math.pi:
                self.phase -= 2 * math.pi

            sample = 0.0
            wave = params['waveform']
            if wave == 'Sinus':
                sample = math.sin(self.phase)
            elif wave == 'Rechteck':
                sample = 1.0 if math.sin(self.phase) >= 0 else -1.0
            elif wave == 'Dreieck':
                sample = 2.0 * abs(2.0 * (self.phase / (2 * math.pi) - math.floor(self.phase / (2 * math.pi) + 0.5))) - 1.0
            elif wave == 'Weiss':
                sample = np.random.uniform(-1, 1)
            elif wave == 'Rosa_Voss':
                if self.voss_counter % 2 == 0:
                    row = np.random.randint(0, self.voss_rows)
                    self.voss_vals[row] = np.random.uniform(-1, 1)
                sample = np.mean(self.voss_vals)
                self.voss_counter += 1
            elif wave == 'Rosa_BP':
                sample = np.random.uniform(-1, 1)
            samples_left[i] = sample * params['left_volume']
            phase_shift_rad = math.radians(params['phase_shift'])
            if wave in ['Sinus', 'Rechteck', 'Dreieck']:
                samples_right[i] = math.sin(self.phase + phase_shift_rad) * params['right_volume']
            else:
                samples_right[i] = sample * params['right_volume']

        interleaved = np.empty(frame_count * 2, dtype=np.float32)
        interleaved[0::2] = samples_left
        interleaved[1::2] = samples_right
        return (interleaved.tobytes(), pyaudio.paContinue if self.running else pyaudio.paComplete)

class App:
    def __init__(self, root):
        self.root = root
        root.title("Universal-Funktionsgenerator")
        self.audio_gen = AudioGenerator()
        self.create_widgets()
        self.update_entries_from_scales()

    def create_widgets(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=10, pady=10)

        tk.Label(self.frame, text="Wellenform:").grid(row=0, column=0, sticky="w")
        self.waveform_var = tk.StringVar(value="Sinus")
        self.waveform_menu = ttk.Combobox(self.frame, textvariable=self.waveform_var, 
                                          values=["Sinus", "Rechteck", "Dreieck", "Weiss", "Rosa_BP", "Rosa_Voss", "Rosa_iFFT"], 
                                          state="readonly")
        self.waveform_menu.grid(row=0, column=1)

        tk.Label(self.frame, text="Modus:").grid(row=1, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="wobbeln")
        modes = [("Festfrequenz", "Festfrequenz"), ("wobbeln", "wobbeln"), ("Frequenzsprung", "Frequenzsprung")]
        col = 1
        for text, mode in modes:
            rb = tk.Radiobutton(self.frame, text=text, variable=self.mode_var, value=mode)
            rb.grid(row=1, column=col, sticky="w")
            col += 1

        tk.Label(self.frame, text="Frequenzverstellung:").grid(row=2, column=0, sticky="w")
        self.freq_var_var = tk.StringVar(value="linear")
        rb_linear = tk.Radiobutton(self.frame, text="linear", variable=self.freq_var_var, value="linear")
        rb_log = tk.Radiobutton(self.frame, text="logarithmisch", variable=self.freq_var_var, value="logarithmisch")
        rb_linear.grid(row=2, column=1, sticky="w")
        rb_log.grid(row=2, column=2, sticky="w")

        tk.Label(self.frame, text="Startfrequenz (Hz):").grid(row=3, column=0, sticky="w")
        self.start_freq_scale = tk.Scale(self.frame, from_=math.log10(10), to=math.log10(10000),
                                         resolution=0.0001, orient="horizontal", command=self.update_start_entry)
        self.start_freq_scale.set(math.log10(200))
        self.start_freq_scale.grid(row=3, column=1, columnspan=2, sticky="we")
        self.start_freq_entry = tk.Entry(self.frame, width=10)
        self.start_freq_entry.insert(0, "200.0000")
        self.start_freq_entry.grid(row=3, column=3)
        self.start_freq_entry.bind("<Return>", self.on_start_freq_entry)

        tk.Label(self.frame, text="Endfrequenz (Hz):").grid(row=4, column=0, sticky="w")
        self.end_freq_scale = tk.Scale(self.frame, from_=math.log10(10), to=math.log10(10000),
                                       resolution=0.0001, orient="horizontal", command=self.update_end_entry)
        self.end_freq_scale.set(math.log10(1000))
        self.end_freq_scale.grid(row=4, column=1, columnspan=2, sticky="we")
        self.end_freq_entry = tk.Entry(self.frame, width=10)
        self.end_freq_entry.insert(0, "1000.0000")
        self.end_freq_entry.grid(row=4, column=3)
        self.end_freq_entry.bind("<Return>", self.on_end_freq_entry)

        tk.Label(self.frame, text="Wobbelgeschwindigkeit (Sec):").grid(row=5, column=0, sticky="w")
        self.wobble_scale = tk.Scale(self.frame, from_=math.log10(0.1), to=math.log10(100),
                                     resolution=0.0001, orient="horizontal", command=self.update_wobble_entry)
        self.wobble_scale.set(math.log10(1))
        self.wobble_scale.grid(row=5, column=1, columnspan=2, sticky="we")
        self.wobble_entry = tk.Entry(self.frame, width=10)
        self.wobble_entry.insert(0, "1.0000")
        self.wobble_entry.grid(row=5, column=3)
        self.wobble_entry.bind("<Return>", self.on_wobble_entry)

        tk.Label(self.frame, text="Lautstärke links:").grid(row=6, column=0, sticky="w")
        self.left_vol_scale = tk.Scale(self.frame, from_=0, to=1, resolution=0.01, orient="horizontal")
        self.left_vol_scale.set(0.5)
        self.left_vol_scale.grid(row=6, column=1, columnspan=2, sticky="we")

        tk.Label(self.frame, text="Lautstärke rechts:").grid(row=7, column=0, sticky="w")
        self.right_vol_scale = tk.Scale(self.frame, from_=0, to=1, resolution=0.01, orient="horizontal")
        self.right_vol_scale.set(0.5)
        self.right_vol_scale.grid(row=7, column=1, columnspan=2, sticky="we")

        tk.Label(self.frame, text="Phasenverschiebung (Grad):").grid(row=8, column=0, sticky="w")
        self.phase_scale = tk.Scale(self.frame, from_=-180, to=180, resolution=1, orient="horizontal")
        self.phase_scale.set(0)
        self.phase_scale.grid(row=8, column=1, columnspan=2, sticky="we")

        self.start_stop_button = tk.Button(self.frame, text="Start", command=self.toggle_audio)
        self.start_stop_button.grid(row=9, column=0, columnspan=4, sticky="we")

    def update_start_entry(self, val):
        # Nur aktualisieren, wenn das Entry nicht fokussiert ist
        if self.root.focus_get() != self.start_freq_entry:
            freq = 10 ** float(val)
            self.start_freq_entry.delete(0, tk.END)
            self.start_freq_entry.insert(0, f"{freq:.4f}")

    def update_end_entry(self, val):
        if self.root.focus_get() != self.end_freq_entry:
            freq = 10 ** float(val)
            self.end_freq_entry.delete(0, tk.END)
            self.end_freq_entry.insert(0, f"{freq:.4f}")

    def update_wobble_entry(self, val):
        if self.root.focus_get() != self.wobble_entry:
            speed = 10 ** float(val)
            self.wobble_entry.delete(0, tk.END)
            self.wobble_entry.insert(0, f"{speed:.4f}")

    def update_entries_from_scales(self):
        # Aktualisiere die Einträge nur, wenn sie nicht fokussiert sind
        if self.root.focus_get() != self.start_freq_entry:
            self.update_start_entry(self.start_freq_scale.get())
        if self.root.focus_get() != self.end_freq_entry:
            self.update_end_entry(self.end_freq_scale.get())
        if self.root.focus_get() != self.wobble_entry:
            self.update_wobble_entry(self.wobble_scale.get())
        self.root.after(100, self.update_entries_from_scales)

    def on_start_freq_entry(self, event):
        try:
            val = float(self.start_freq_entry.get())
            if val < 10: val = 10
            if val > 10000: val = 10000
            self.start_freq_scale.set(math.log10(val))
        except ValueError:
            pass

    def on_end_freq_entry(self, event):
        try:
            val = float(self.end_freq_entry.get())
            if val < 10: val = 10
            if val > 10000: val = 10000
            self.end_freq_scale.set(math.log10(val))
        except ValueError:
            pass

    def on_wobble_entry(self, event):
        try:
            val = float(self.wobble_entry.get())
            if val < 0.1: val = 0.1
            if val > 100: val = 100
            self.wobble_scale.set(math.log10(val))
        except ValueError:
            pass

    def periodic_update(self):
        try:
            freq_start = float(self.start_freq_entry.get())
        except:
            freq_start = 200.0
        try:
            freq_end = float(self.end_freq_entry.get())
        except:
            freq_end = 1000.0
        try:
            wobble_speed = float(self.wobble_entry.get())
        except:
            wobble_speed = 1.0
        new_params = {
            'waveform': self.waveform_var.get(),
            'mode': self.mode_var.get(),
            'freq_start': freq_start,
            'freq_end': freq_end,
            'wobble_speed': wobble_speed,
            'freq_var': self.freq_var_var.get(),
            'left_volume': self.left_vol_scale.get(),
            'right_volume': self.right_vol_scale.get(),
            'phase_shift': self.phase_scale.get(),
        }
        self.audio_gen.update_params(new_params)
        self.root.after(50, self.periodic_update)

    def toggle_audio(self):
        if self.audio_gen.running:
            self.audio_gen.stop()
            self.start_stop_button.config(text="Start")
        else:
            self.audio_gen.start()
            self.start_stop_button.config(text="Stop")
        self.periodic_update()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.audio_gen.stop(), root.destroy()))
    root.mainloop()
