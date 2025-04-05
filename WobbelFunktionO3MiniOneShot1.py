import tkinter as tk
from tkinter import ttk
import numpy as np
import pyaudio
import threading
import time
import math

# Audio generation functions

def get_frequency_array(t0, block_size, sr, params):
    t = t0 + np.arange(block_size) / sr
    mode = params['mode']
    start = params['start_freq']
    end = params['end_freq']
    T = params['wobble_speed']
    scaling = params['scaling']
    if mode == "fixed":
        return np.full(block_size, start)
    elif mode == "wobble":
        m = (np.sin(2 * np.pi * t / T) + 1) / 2
        if scaling == "linear":
            return start + m * (end - start)
        else:
            return 10 ** (np.log10(start) + m * (np.log10(end) - np.log10(start)))
    elif mode == "jump":
        phases = np.floor(t / T) % 2
        return np.where(phases == 0, start, end)
    else:
        return np.full(block_size, start)

def generate_oscillator(block_size, sr, t_global, phase, params, waveform, phase_offset=0):
    freqs = get_frequency_array(t_global, block_size, sr, params)
    dphi = 2 * np.pi * freqs / sr
    phases = phase + np.cumsum(dphi)
    new_phase = phases[-1] % (2 * np.pi)
    if waveform == 'Sinus':
        wave = np.sin(phases + phase_offset)
    elif waveform == 'Rechteck':
        wave = np.sign(np.sin(phases + phase_offset))
    elif waveform == 'Dreieck':
        wave = (2 / np.pi) * np.arcsin(np.sin(phases + phase_offset))
    else:
        wave = np.zeros(block_size)
    return wave, new_phase

def generate_white_noise(block_size):
    return np.random.uniform(-1, 1, block_size)

def generate_pink_bandpass(block_size, sr, params):
    start = params['start_freq']
    end = params['end_freq']
    white = np.random.normal(0, 1, block_size)
    spectrum = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(block_size, 1/sr)
    mask = (freqs >= start) & (freqs <= end)
    weighting = np.ones_like(freqs)
    weighting[1:] = 1 / np.sqrt(np.maximum(freqs[1:], 1e-10))
    filter_response = np.where(mask, weighting, 0)
    filtered_spectrum = spectrum * filter_response
    result = np.fft.irfft(filtered_spectrum, n=block_size)
    max_val = np.max(np.abs(result))
    if max_val != 0:
        result /= max_val
    return result

def generate_pink_ifft(block_size, sr, params):
    start = params['start_freq']
    end = params['end_freq']
    freqs = np.fft.rfftfreq(block_size, 1/sr)
    amplitude = np.zeros_like(freqs)
    mask = (freqs >= start) & (freqs <= end)
    amplitude[mask] = 1 / np.sqrt(np.maximum(freqs[mask], 1e-10))
    phase = np.random.uniform(0, 2 * np.pi, len(freqs))
    spectrum = amplitude * np.exp(1j * phase)
    output = np.fft.irfft(spectrum, n=block_size)
    max_val = np.max(np.abs(output))
    if max_val != 0:
        output /= max_val
    return output

def generate_pink_voss(block_size, sr, params, voss_state):
    num_rows = 16
    if 'counter' not in voss_state:
        voss_state['counter'] = 0
        voss_state['rows'] = np.random.uniform(-1, 1, num_rows)
    output = np.zeros(block_size)
    for i in range(block_size):
        for r in range(num_rows):
            if (voss_state['counter'] % (2 ** r)) == 0:
                voss_state['rows'][r] = np.random.uniform(-1, 1)
        output[i] = np.sum(voss_state['rows'])
        voss_state['counter'] += 1
    max_val = np.max(np.abs(output))
    if max_val != 0:
        output /= max_val
    # Apply bandpass filter
    start = params['start_freq']
    end = params['end_freq']
    spectrum = np.fft.rfft(output)
    freqs = np.fft.rfftfreq(block_size, 1/sr)
    mask = (freqs >= start) & (freqs <= end)
    spectrum = spectrum * np.where(mask, 1, 0)
    output = np.fft.irfft(spectrum, n=block_size)
    max_val = np.max(np.abs(output))
    if max_val != 0:
        output /= max_val
    return output

# Audio generator thread

class AudioGenerator(threading.Thread):
    def __init__(self, params):
        super().__init__()
        self.params = params
        self.running = False
        self.sample_rate = 44100
        self.block_size = 1024
        self.phase = 0.0
        self.voss_state = {}
        self.start_time = time.perf_counter()
        self.lock = threading.Lock()
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32,
                                  channels=2,
                                  rate=self.sample_rate,
                                  output=True)
    def run(self):
        t_global = time.perf_counter() - self.start_time
        while self.running:
            with self.lock:
                current_params = self.params.copy()
            waveform = current_params['waveform']
            # Oscillator waveforms
            if waveform in ['Sinus', 'Rechteck', 'Dreieck']:
                left, self.phase = generate_oscillator(self.block_size, self.sample_rate, t_global, self.phase, current_params, waveform, phase_offset=0)
                phase_shift_rad = np.deg2rad(current_params['phase_shift'])
                right, _ = generate_oscillator(self.block_size, self.sample_rate, t_global, self.phase, current_params, waveform, phase_offset=phase_shift_rad)
            elif waveform == 'weißes Rauschen':
                left = generate_white_noise(self.block_size)
                shift = int((current_params['phase_shift'] / 360.0) * self.block_size)
                right = np.roll(left, shift)
            elif waveform == 'rosa Rauschen mit steilflankigem Bandpassfilter':
                left = generate_pink_bandpass(self.block_size, self.sample_rate, current_params)
                shift = int((current_params['phase_shift'] / 360.0) * self.block_size)
                right = np.roll(left, shift)
            elif waveform == 'rosa Rauschen mit Voss-McCartney-Algorithmus':
                left = generate_pink_voss(self.block_size, self.sample_rate, current_params, self.voss_state)
                shift = int((current_params['phase_shift'] / 360.0) * self.block_size)
                right = np.roll(left, shift)
            elif waveform == 'rosa Rauschen mit inverser FFT':
                left = generate_pink_ifft(self.block_size, self.sample_rate, current_params)
                shift = int((current_params['phase_shift'] / 360.0) * self.block_size)
                right = np.roll(left, shift)
            else:
                left = np.zeros(self.block_size)
                right = np.zeros(self.block_size)
            # Apply volumes
            left *= current_params['vol_left']
            right *= current_params['vol_right']
            # Interleave channels
            stereo = np.empty((self.block_size, 2), dtype=np.float32)
            stereo[:, 0] = left
            stereo[:, 1] = right
            data = stereo.flatten().tobytes()
            try:
                self.stream.write(data)
            except Exception as e:
                print("Stream write error:", e)
                break
            t_global += self.block_size / self.sample_rate
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    def stop(self):
        self.running = False

# GUI

class WobbelGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Wobbel-Funktionsgenerator")
        self.params = {
            'waveform': 'Sinus',
            'mode': 'fixed',
            'scaling': 'linear',
            'start_freq': 10.0,
            'end_freq': 10000.0,
            'wobble_speed': 1.0,
            'vol_left': 1.0,
            'vol_right': 1.0,
            'phase_shift': 0.0,
        }
        self.audio_gen = None

        mainframe = ttk.Frame(root, padding="10")
        mainframe.grid(row=0, column=0, sticky="NSEW")

        # Waveform selection
        ttk.Label(mainframe, text="Wellenform:").grid(row=0, column=0, sticky="W")
        self.waveform_var = tk.StringVar(value="Sinus")
        waveforms = ['Sinus', 'Rechteck', 'Dreieck', 'weißes Rauschen',
                     'rosa Rauschen mit steilflankigem Bandpassfilter',
                     'rosa Rauschen mit Voss-McCartney-Algorithmus',
                     'rosa Rauschen mit inverser FFT']
        self.waveform_menu = ttk.OptionMenu(mainframe, self.waveform_var, waveforms[0], *waveforms, command=self.update_waveform)
        self.waveform_menu.grid(row=0, column=1, sticky="EW")

        # Frequenzmodus
        ttk.Label(mainframe, text="Frequenzmodus:").grid(row=1, column=0, sticky="W")
        self.mode_var = tk.StringVar(value="fixed")
        modes = [("Festfrequenz", "fixed"), ("wobbeln", "wobble"), ("Frequenzsprung", "jump")]
        col = 1
        for text, mode in modes:
            rb = ttk.Radiobutton(mainframe, text=text, variable=self.mode_var, value=mode, command=self.update_mode)
            rb.grid(row=1, column=col, sticky="W")
            col += 1

        # Frequenzverstellung (linear/logarithmisch)
        ttk.Label(mainframe, text="Frequenzverstellung:").grid(row=2, column=0, sticky="W")
        self.scaling_var = tk.StringVar(value="linear")
        for i, (text, val) in enumerate([("linear", "linear"), ("logarithmisch", "log")]):
            rb = ttk.Radiobutton(mainframe, text=text, variable=self.scaling_var, value=val, command=self.update_scaling)
            rb.grid(row=2, column=1 + i, sticky="W")

        # Logarithmische Schieberegler für Startfrequenz, Endfrequenz und Wobbelgeschwindigkeit
        # Intern: Slider values in log10, aber Anzeige in Hz oder sec.
        ttk.Label(mainframe, text="Startfrequenz (Hz):").grid(row=3, column=0, sticky="W")
        self.start_freq_slider = tk.Scale(mainframe, from_=1, to=4, resolution=0.0001, orient="horizontal", command=self.start_freq_slider_update)
        self.start_freq_slider.set(np.log10(self.params['start_freq']))
        self.start_freq_slider.grid(row=3, column=1, sticky="EW")
        self.start_freq_entry = ttk.Entry(mainframe, width=10)
        self.start_freq_entry.insert(0, str(self.params['start_freq']))
        self.start_freq_entry.grid(row=3, column=2, sticky="W")
        self.start_freq_entry.bind("<Return>", self.start_freq_entry_update)

        ttk.Label(mainframe, text="Endfrequenz (Hz):").grid(row=4, column=0, sticky="W")
        self.end_freq_slider = tk.Scale(mainframe, from_=1, to=4, resolution=0.0001, orient="horizontal", command=self.end_freq_slider_update)
        self.end_freq_slider.set(np.log10(self.params['end_freq']))
        self.end_freq_slider.grid(row=4, column=1, sticky="EW")
        self.end_freq_entry = ttk.Entry(mainframe, width=10)
        self.end_freq_entry.insert(0, str(self.params['end_freq']))
        self.end_freq_entry.grid(row=4, column=2, sticky="W")
        self.end_freq_entry.bind("<Return>", self.end_freq_entry_update)

        ttk.Label(mainframe, text="Wobbelgeschwindigkeit (Sec):").grid(row=5, column=0, sticky="W")
        self.wobble_slider = tk.Scale(mainframe, from_=-1, to=2, resolution=0.0001, orient="horizontal", command=self.wobble_slider_update)
        self.wobble_slider.set(np.log10(self.params['wobble_speed']))
        self.wobble_slider.grid(row=5, column=1, sticky="EW")
        self.wobble_entry = ttk.Entry(mainframe, width=10)
        self.wobble_entry.insert(0, str(self.params['wobble_speed']))
        self.wobble_entry.grid(row=5, column=2, sticky="W")
        self.wobble_entry.bind("<Return>", self.wobble_entry_update)

        # Lautstärke Regler für linken und rechten Kanal
        ttk.Label(mainframe, text="Lautstärke links:").grid(row=6, column=0, sticky="W")
        self.vol_left_slider = tk.Scale(mainframe, from_=0, to=1, resolution=0.01, orient="horizontal", command=self.vol_left_update)
        self.vol_left_slider.set(self.params['vol_left'])
        self.vol_left_slider.grid(row=6, column=1, sticky="EW")

        ttk.Label(mainframe, text="Lautstärke rechts:").grid(row=7, column=0, sticky="W")
        self.vol_right_slider = tk.Scale(mainframe, from_=0, to=1, resolution=0.01, orient="horizontal", command=self.vol_right_update)
        self.vol_right_slider.set(self.params['vol_right'])
        self.vol_right_slider.grid(row=7, column=1, sticky="EW")

        # Phasenverschiebung Regler
        ttk.Label(mainframe, text="Phasenverschiebung (°):").grid(row=8, column=0, sticky="W")
        self.phase_slider = tk.Scale(mainframe, from_=-180, to=180, resolution=1, orient="horizontal", command=self.phase_update)
        self.phase_slider.set(self.params['phase_shift'])
        self.phase_slider.grid(row=8, column=1, sticky="EW")

        # Start/Stop Button
        self.start_stop_button = ttk.Button(mainframe, text="Start", command=self.toggle_audio)
        self.start_stop_button.grid(row=9, column=0, columnspan=2, pady=10)

        # Configure grid weights
        for i in range(10):
            mainframe.rowconfigure(i, weight=1)
        mainframe.columnconfigure(1, weight=1)

    def update_waveform(self, value):
        self.params['waveform'] = value

    def update_mode(self):
        self.params['mode'] = self.mode_var.get()

    def update_scaling(self):
        self.params['scaling'] = self.scaling_var.get()

    def start_freq_slider_update(self, val):
        freq = 10 ** float(val)
        self.params['start_freq'] = freq
        self.start_freq_entry.delete(0, tk.END)
        self.start_freq_entry.insert(0, f"{freq:.4f}")

    def start_freq_entry_update(self, event):
        try:
            freq = float(self.start_freq_entry.get())
            if 10 <= freq <= 10000:
                self.params['start_freq'] = freq
                self.start_freq_slider.set(np.log10(freq))
        except:
            pass

    def end_freq_slider_update(self, val):
        freq = 10 ** float(val)
        self.params['end_freq'] = freq
        self.end_freq_entry.delete(0, tk.END)
        self.end_freq_entry.insert(0, f"{freq:.4f}")

    def end_freq_entry_update(self, event):
        try:
            freq = float(self.end_freq_entry.get())
            if 10 <= freq <= 10000:
                self.params['end_freq'] = freq
                self.end_freq_slider.set(np.log10(freq))
        except:
            pass

    def wobble_slider_update(self, val):
        speed = 10 ** float(val)
        self.params['wobble_speed'] = speed
        self.wobble_entry.delete(0, tk.END)
        self.wobble_entry.insert(0, f"{speed:.4f}")

    def wobble_entry_update(self, event):
        try:
            speed = float(self.wobble_entry.get())
            if 0.1 <= speed <= 100:
                self.params['wobble_speed'] = speed
                self.wobble_slider.set(np.log10(speed))
        except:
            pass

    def vol_left_update(self, val):
        self.params['vol_left'] = float(val)

    def vol_right_update(self, val):
        self.params['vol_right'] = float(val)

    def phase_update(self, val):
        self.params['phase_shift'] = float(val)

    def toggle_audio(self):
        if self.audio_gen is None or not self.audio_gen.running:
            self.start_audio()
            self.start_stop_button.config(text="Stop")
        else:
            self.stop_audio()
            self.start_stop_button.config(text="Start")

    def start_audio(self):
        self.audio_gen = AudioGenerator(self.params)
        self.audio_gen.running = True
        self.audio_gen.start()

    def stop_audio(self):
        if self.audio_gen:
            self.audio_gen.stop()
            self.audio_gen.join()
            self.audio_gen = None

if __name__ == "__main__":
    root = tk.Tk()
    app = WobbelGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_audio(), root.destroy()))
    root.mainloop()
