import tkinter as tk
import threading
import numpy as np
import pyaudio
import time
import scipy.signal

fs = 44100
block_size = 1024
running = False
osc_phase = 0.0
pink_filter_zi = None

# Paul Kellet pink noise state variables
p_b0 = p_b1 = p_b2 = p_b3 = p_b4 = p_b5 = p_b6 = 0.0

params_lock = threading.Lock()
params = {
    'waveform': 'Sinus',
    'start_freq': 200.0,    # in Hz (set via logarithmic slider: 10^(slider_value) with slider_value in [0,4])
    'end_freq': 800.0,      # in Hz
    'wobble_period': 1.0,   # in seconds (set via logarithmic slider: 10^(slider_value) with slider_value in [-1,2])
    'volume': 0.5,          # 0.0 to 1.0
    'wobble_interp_log': True  # True for logarithmic interpolation, False for linear
}

def generate_oscillator_block(n, t0):
    global osc_phase
    with params_lock:
        start_freq = params['start_freq']
        end_freq = params['end_freq']
        wobble_period = params['wobble_period']
        volume = params['volume']
        waveform = params['waveform']
        interp_log = params['wobble_interp_log']
    t = np.arange(n) / fs + t0
    # LFO: frequency of LFO is 1/wobble_period
    lfo = 0.5 * (1 + np.sin(2 * np.pi * (1.0 / wobble_period) * t))
    if interp_log:
        freq = np.exp(np.log(start_freq) + lfo * (np.log(end_freq) - np.log(start_freq)))
    else:
        freq = start_freq + lfo * (end_freq - start_freq)
    dphase = 2 * np.pi * freq / fs
    phases = osc_phase + np.cumsum(dphase)
    osc_phase = phases[-1] % (2 * np.pi)
    if waveform == 'Sinus':
        samples = np.sin(phases)
    elif waveform == 'Rechteck':
        samples = np.where(np.sin(phases) >= 0, 1.0, -1.0)
    elif waveform == 'Dreieck':
        samples = scipy.signal.sawtooth(phases, width=0.5)
    else:
        samples = np.zeros(n)
    return (volume * samples).astype(np.float32), t[-1]

def generate_pink_block(n):
    global p_b0, p_b1, p_b2, p_b3, p_b4, p_b5, p_b6, pink_filter_zi
    block = np.empty(n, dtype=np.float32)
    for i in range(n):
        white = np.random.uniform(-1, 1)
        p_b0 = 0.99886 * p_b0 + white * 0.0555179
        p_b1 = 0.99332 * p_b1 + white * 0.0750759
        p_b2 = 0.96900 * p_b2 + white * 0.1538520
        p_b3 = 0.86650 * p_b3 + white * 0.3104856
        p_b4 = 0.55000 * p_b4 + white * 0.5329522
        p_b5 = -0.7616 * p_b5 - white * 0.0168980
        pink = p_b0 + p_b1 + p_b2 + p_b3 + p_b4 + p_b5 + p_b6 + white * 0.5362
        p_b6 = white * 0.115926
        block[i] = pink * 0.11
    with params_lock:
        start_freq = params['start_freq']
        end_freq = params['end_freq']
        volume = params['volume']
    low = min(start_freq, end_freq)
    high = max(start_freq, end_freq)
    nyq = 0.5 * fs
    low_norm = low / nyq
    high_norm = high / nyq
    if high_norm >= 1:
        high_norm = 0.999
    b, a = scipy.signal.butter(4, [low_norm, high_norm], btype='band')
    global pink_filter_zi
    if pink_filter_zi is None or pink_filter_zi.shape[0] != len(a):
        pink_filter_zi = scipy.signal.lfilter_zi(b, a) * block[0]
    filtered_block, pink_filter_zi = scipy.signal.lfilter(b, a, block, zi=pink_filter_zi)
    return (volume * filtered_block).astype(np.float32), None

def generate_pink_noise(samples, sample_rate, min_freq, max_freq):
    noise = np.random.randn(samples)
    fft_noise = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(samples, 1 / sample_rate)
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    fft_noise[~mask] = 0
    pink_noise = np.fft.irfft(fft_noise)
    pink_noise /= np.max(np.abs(pink_noise))
    return pink_noise * 0.5

def generate_pink2_block(n):
    with params_lock:
        start_freq = params['start_freq']
        end_freq = params['end_freq']
        volume = params['volume']
    low = min(start_freq, end_freq)
    high = max(start_freq, end_freq)
    samples = generate_pink_noise(n, fs, low, high)
    return (volume * samples).astype(np.float32), None

def audio_thread():
    global running, osc_phase
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=fs,
                    output=True,
                    frames_per_buffer=block_size)
    current_time = 0.0
    while running:
        with params_lock:
            wf = params['waveform']
        if wf == 'rosa Rauschen':
            samples, new_time = generate_pink_block(block_size)
        elif wf == 'rosa2':
            samples, new_time = generate_pink2_block(block_size)
        else:
            samples, new_time = generate_oscillator_block(block_size, current_time)
            current_time = new_time
        stream.write(samples.tobytes())
    stream.stop_stream()
    stream.close()
    p.terminate()

def start_audio():
    global running
    if not running:
        running = True
        threading.Thread(target=audio_thread, daemon=True).start()

def stop_audio():
    global running
    running = False

root = tk.Tk()
root.title("Wobbel-Funktionsgenerator")

def update_waveform(val):
    with params_lock:
        params['waveform'] = waveform_var.get()

def update_start_freq(val):
    with params_lock:
        params['start_freq'] = 10 ** float(val)

def update_end_freq(val):
    with params_lock:
        params['end_freq'] = 10 ** float(val)

def update_wobble_speed(val):
    with params_lock:
        params['wobble_period'] = 10 ** float(val)

def update_interp_mode():
    with params_lock:
        params['wobble_interp_log'] = bool(interp_var.get())

waveform_var = tk.StringVar(root)
waveform_var.set("Sinus")
waveform_menu = tk.OptionMenu(root, waveform_var, "Sinus", "Rechteck", "Dreieck", "rosa Rauschen", "rosa2", command=update_waveform)
waveform_menu.grid(row=0, column=0, columnspan=2, pady=5)

tk.Label(root, text="Startfrequenz (1Hz bis 10kHz)").grid(row=1, column=0, sticky="w")
start_freq_scale = tk.Scale(root, from_=0, to=4, resolution=0.01, orient=tk.HORIZONTAL, command=update_start_freq)
start_freq_scale.set(np.log10(200))
start_freq_scale.grid(row=1, column=1)

tk.Label(root, text="Endfrequenz (1Hz bis 10kHz)").grid(row=2, column=0, sticky="w")
end_freq_scale = tk.Scale(root, from_=0, to=4, resolution=0.01, orient=tk.HORIZONTAL, command=update_end_freq)
end_freq_scale.set(np.log10(800))
end_freq_scale.grid(row=2, column=1)

tk.Label(root, text="Wobbelperiode (0,1s bis 100s)").grid(row=3, column=0, sticky="w")
wobble_speed_scale = tk.Scale(root, from_=-1, to=2, resolution=0.01, orient=tk.HORIZONTAL, command=update_wobble_speed)
wobble_speed_scale.set(0)  # 10^0 = 1s
wobble_speed_scale.grid(row=3, column=1)

interp_var = tk.IntVar()
interp_var.set(1)  # 1 for logarithmic interpolation, 0 for linear
interp_check = tk.Checkbutton(root, text="Logarithmische Wobbelfrequenzverstellung", variable=interp_var, command=update_interp_mode)
interp_check.grid(row=4, column=0, columnspan=2, pady=5)

tk.Label(root, text="Lautstärke").grid(row=5, column=0, sticky="w")
volume_scale = tk.Scale(root, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=lambda val: params.update({'volume': float(val)}))
volume_scale.set(0.5)
volume_scale.grid(row=5, column=1)

start_button = tk.Button(root, text="Start", command=start_audio)
start_button.grid(row=6, column=0, pady=5)

stop_button = tk.Button(root, text="Stop", command=stop_audio)
stop_button.grid(row=6, column=1, pady=5)

root.protocol("WM_DELETE_WINDOW", lambda: (stop_audio(), root.destroy()))
root.mainloop()

