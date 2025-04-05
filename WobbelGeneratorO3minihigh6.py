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

# Globale Variablen für den Frequenzsprung-Modus
freq_jump = None
next_jump_time = 0.0

# Paul Kellet pink noise state variables
p_b0 = p_b1 = p_b2 = p_b3 = p_b4 = p_b5 = p_b6 = 0.0

params_lock = threading.Lock()
params = {
    'waveform': 'Sinus',
    'start_freq': 200.0,         # in Hz
    'end_freq': 800.0,           # in Hz
    'wobble_period': 1.0,        # in Sekunden
    'volume_left': 0.5,          # 0.0 bis 1.0
    'volume_right': 0.5,         # 0.0 bis 1.0
    'phase_shift': 0.0,          # in Grad (für Sinus)
    'wobble_interp_log': True,   # logarithmische Interpolation
    'output_mode': 'Audioausgang',  # "Audioausgang" oder "Bluetooth"
    'bluetooth_device_index': None, # Ausgewähltes Bluetooth-Gerät (Geräteindex)
    'frequency_mode': 'wobbeln'      # "Festfrequenz", "wobbeln", "Frequenzsprung"
}

def scan_bluetooth_devices():
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        name = info.get('name', "")
        name_lower = name.lower()
        if info.get('maxOutputChannels', 0) > 0 and (
            "bluetooth" in name_lower or "blue" in name_lower or "a2dp" in name_lower or "vhm-338" in name_lower):
            devices.append((i, name))
    p.terminate()
    return devices

def generate_oscillator_stereo_block(n, t0):
    global osc_phase, freq_jump, next_jump_time
    with params_lock:
        start_freq = params['start_freq']
        end_freq = params['end_freq']
        wobble_period = params['wobble_period']
        volume_left = params['volume_left']
        volume_right = params['volume_right']
        waveform = params['waveform']
        interp_log = params['wobble_interp_log']
        phase_shift_deg = params['phase_shift']
        frequency_mode = params['frequency_mode']
    t = np.arange(n) / fs + t0
    # Frequenzberechnung je nach gewähltem Modus
    if frequency_mode == "wobbeln":
        lfo = 0.5 * (1 + np.sin(2 * np.pi * (1.0 / wobble_period) * t))
        if interp_log:
            freq = np.exp(np.log(start_freq) + lfo * (np.log(end_freq) - np.log(start_freq)))
        else:
            freq = start_freq + lfo * (end_freq - start_freq)
    elif frequency_mode == "Festfrequenz":
        freq = np.full(n, start_freq)
    elif frequency_mode == "Frequenzsprung":
        # Nutze die wobble_period als Intervall für Sprünge
        if freq_jump is None:
            freq_jump = start_freq
            next_jump_time = t0 + wobble_period
        freq = np.empty(n)
        for i, sample_time in enumerate(t):
            if sample_time >= next_jump_time:
                freq_jump = np.random.choice([start_freq, end_freq])
                next_jump_time = sample_time + wobble_period
            freq[i] = freq_jump
    else:
        freq = np.full(n, start_freq)
    dphase = 2 * np.pi * freq / fs
    phases = osc_phase + np.cumsum(dphase)
    new_time = t[-1]
    osc_phase = phases[-1] % (2 * np.pi)
    if waveform == 'Sinus':
        left_channel = np.sin(phases)
        phase_shift_rad = np.deg2rad(phase_shift_deg)
        right_channel = np.sin(phases + phase_shift_rad)
    elif waveform == 'Rechteck':
        sample = np.where(np.sin(phases) >= 0, 1.0, -1.0)
        left_channel = sample
        right_channel = sample
    elif waveform == 'Dreieck':
        sample = scipy.signal.sawtooth(phases, width=0.5)
        left_channel = sample
        right_channel = sample
    else:
        left_channel = np.zeros(n)
        right_channel = np.zeros(n)
    left_channel *= volume_left
    right_channel *= volume_right
    stereo = np.column_stack((left_channel, right_channel))
    return stereo, new_time

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
        volume_left = params['volume_left']
        volume_right = params['volume_right']
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
    mono = filtered_block
    left_channel = volume_left * mono
    right_channel = volume_right * mono
    stereo = np.column_stack((left_channel, right_channel))
    return stereo, None

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
        volume_left = params['volume_left']
        volume_right = params['volume_right']
    low = min(start_freq, end_freq)
    high = max(start_freq, end_freq)
    mono = generate_pink_noise(n, fs, low, high)
    left_channel = volume_left * mono
    right_channel = volume_right * mono
    stereo = np.column_stack((left_channel, right_channel))
    return stereo, None

def audio_thread():
    global running, osc_phase
    p = pyaudio.PyAudio()
    with params_lock:
        output_mode = params['output_mode']
        bt_index = params['bluetooth_device_index']
    device_index = bt_index if output_mode == "Bluetooth" else None
    stream = p.open(format=pyaudio.paFloat32,
                    channels=2,
                    rate=fs,
                    output=True,
                    frames_per_buffer=block_size,
                    output_device_index=device_index)
    current_time = 0.0
    while running:
        with params_lock:
            wf = params['waveform']
        if wf == 'rosa Rauschen':
            samples, new_time = generate_pink_block(block_size)
        elif wf == 'rosa2':
            samples, new_time = generate_pink2_block(block_size)
        else:
            samples, new_time = generate_oscillator_stereo_block(block_size, current_time)
            current_time = new_time
        stream.write(samples.astype(np.float32).tobytes())
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

def update_waveform(val):
    with params_lock:
        params['waveform'] = waveform_var.get()

def update_output_mode(val):
    with params_lock:
        params['output_mode'] = output_mode_var.get()
    if output_mode_var.get() == "Bluetooth":
        bluetooth_frame.grid()  # Zeige Bluetooth-Auswahl
        update_bluetooth_device_menu()
    else:
        bluetooth_frame.grid_remove()

def update_bluetooth_device_menu():
    devices = scan_bluetooth_devices()
    if devices:
        global bluetooth_devices
        bluetooth_devices = devices
        bluetooth_device_var.set(str(devices[0][0]))
        with params_lock:
            params['bluetooth_device_index'] = devices[0][0]
        menu = bluetooth_menu["menu"]
        menu.delete(0, "end")
        for idx, name in devices:
            display = f"{idx}: {name}"
            menu.add_command(label=display, command=lambda value=str(idx): bluetooth_device_var.set(value))
    else:
        bluetooth_device_var.set("Kein Gerät")
        with params_lock:
            params['bluetooth_device_index'] = None

def bluetooth_device_changed(*args):
    try:
        value = int(bluetooth_device_var.get())
        with params_lock:
            params['bluetooth_device_index'] = value
    except ValueError:
        with params_lock:
            params['bluetooth_device_index'] = None

def update_start_freq(val):
    exponent = float(val)
    linear_value = 10 ** exponent
    with params_lock:
        params['start_freq'] = linear_value
    start_freq_entry_var.set(f"{linear_value:.4f}")

def update_end_freq(val):
    exponent = float(val)
    linear_value = 10 ** exponent
    with params_lock:
        params['end_freq'] = linear_value
    end_freq_entry_var.set(f"{linear_value:.4f}")

def update_wobble_speed(val):
    exponent = float(val)
    linear_value = 10 ** exponent
    with params_lock:
        params['wobble_period'] = linear_value
    wobble_speed_entry_var.set(f"{linear_value:.4f}")

def update_volume_left(val):
    with params_lock:
        params['volume_left'] = float(val)

def update_volume_right(val):
    with params_lock:
        params['volume_right'] = float(val)

def update_phase_shift(val):
    with params_lock:
        params['phase_shift'] = float(val)

def update_interp_mode():
    with params_lock:
        params['wobble_interp_log'] = bool(interp_var.get())

def update_frequency_mode(val):
    with params_lock:
        params['frequency_mode'] = frequency_mode_var.get()

def start_freq_entry_changed(event=None):
    try:
        value = float(start_freq_entry.get())
        if value < 1: value = 1
        if value > 10000: value = 10000
        exponent = np.log10(value)
        start_freq_scale.set(exponent)
        with params_lock:
            params['start_freq'] = value
    except ValueError:
        pass

def end_freq_entry_changed(event=None):
    try:
        value = float(end_freq_entry.get())
        if value < 1: value = 1
        if value > 10000: value = 10000
        exponent = np.log10(value)
        end_freq_scale.set(exponent)
        with params_lock:
            params['end_freq'] = value
    except ValueError:
        pass

def wobble_speed_entry_changed(event=None):
    try:
        value = float(wobble_speed_entry.get())
        if value < 0.1: value = 0.1
        if value > 100: value = 100
        exponent = np.log10(value)
        wobble_speed_scale.set(exponent)
        with params_lock:
            params['wobble_period'] = value
    except ValueError:
        pass

root = tk.Tk()
root.title("Wobbel-Funktionsgenerator")

waveform_var = tk.StringVar(root)
waveform_var.set("Sinus")
waveform_menu = tk.OptionMenu(root, waveform_var, "Sinus", "Rechteck", "Dreieck", "rosa Rauschen", "rosa2", command=update_waveform)
waveform_menu.grid(row=0, column=0, columnspan=3, pady=5)

output_mode_var = tk.StringVar(root)
output_mode_var.set("Audioausgang")
output_mode_menu = tk.OptionMenu(root, output_mode_var, "Audioausgang", "Bluetooth", command=update_output_mode)
output_mode_menu.grid(row=1, column=0, columnspan=3, pady=5)

bluetooth_frame = tk.Frame(root)
tk.Label(bluetooth_frame, text="Bluetooth-Gerät:").grid(row=0, column=0, sticky="w")
bluetooth_device_var = tk.StringVar()
bluetooth_menu = tk.OptionMenu(bluetooth_frame, bluetooth_device_var, "Kein Gerät")
bluetooth_menu.grid(row=0, column=1, sticky="w")
bluetooth_device_var.trace("w", bluetooth_device_changed)
bluetooth_frame.grid(row=2, column=0, columnspan=3, pady=5)
bluetooth_frame.grid_remove()

tk.Label(root, text="Frequenzmodus").grid(row=3, column=0, sticky="w")
frequency_mode_var = tk.StringVar(root)
frequency_mode_var.set("wobbeln")
frequency_mode_menu = tk.OptionMenu(root, frequency_mode_var, "Festfrequenz", "wobbeln", "Frequenzsprung", command=update_frequency_mode)
frequency_mode_menu.grid(row=3, column=1, columnspan=2, sticky="w")

tk.Label(root, text="Startfrequenz (1Hz bis 10kHz)").grid(row=4, column=0, sticky="w")
start_freq_scale = tk.Scale(root, from_=0, to=4, resolution=0.0001, orient=tk.HORIZONTAL, command=update_start_freq)
start_freq_scale.set(np.log10(200))
start_freq_scale.grid(row=4, column=1)
start_freq_entry_var = tk.StringVar()
start_freq_entry = tk.Entry(root, textvariable=start_freq_entry_var, width=10)
start_freq_entry.grid(row=4, column=2)
start_freq_entry_var.set("200.0000")
start_freq_entry.bind("<Return>", start_freq_entry_changed)
start_freq_entry.bind("<FocusOut>", start_freq_entry_changed)

tk.Label(root, text="Endfrequenz (1Hz bis 10kHz)").grid(row=5, column=0, sticky="w")
end_freq_scale = tk.Scale(root, from_=0, to=4, resolution=0.0001, orient=tk.HORIZONTAL, command=update_end_freq)
end_freq_scale.set(np.log10(800))
end_freq_scale.grid(row=5, column=1)
end_freq_entry_var = tk.StringVar()
end_freq_entry = tk.Entry(root, textvariable=end_freq_entry_var, width=10)
end_freq_entry.grid(row=5, column=2)
end_freq_entry_var.set("800.0000")
end_freq_entry.bind("<Return>", end_freq_entry_changed)
end_freq_entry.bind("<FocusOut>", end_freq_entry_changed)

tk.Label(root, text="Wobbelperiode (0,1s bis 100s)").grid(row=6, column=0, sticky="w")
wobble_speed_scale = tk.Scale(root, from_=-1, to=2, resolution=0.0001, orient=tk.HORIZONTAL, command=update_wobble_speed)
wobble_speed_scale.set(0)  # 10^0 = 1s
wobble_speed_scale.grid(row=6, column=1)
wobble_speed_entry_var = tk.StringVar()
wobble_speed_entry = tk.Entry(root, textvariable=wobble_speed_entry_var, width=10)
wobble_speed_entry.grid(row=6, column=2)
wobble_speed_entry_var.set("1.0000")
wobble_speed_entry.bind("<Return>", wobble_speed_entry_changed)
wobble_speed_entry.bind("<FocusOut>", wobble_speed_entry_changed)

tk.Label(root, text="Lautstärke links").grid(row=7, column=0, sticky="w")
volume_left_scale = tk.Scale(root, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=update_volume_left)
volume_left_scale.set(0.5)
volume_left_scale.grid(row=7, column=1, columnspan=2)

tk.Label(root, text="Lautstärke rechts").grid(row=8, column=0, sticky="w")
volume_right_scale = tk.Scale(root, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL, command=update_volume_right)
volume_right_scale.set(0.5)
volume_right_scale.grid(row=8, column=1, columnspan=2)

tk.Label(root, text="Phasenverschiebung (Sinus) (-180° bis 180°)").grid(row=9, column=0, sticky="w")
phase_shift_scale = tk.Scale(root, from_=-180, to=180, resolution=1, orient=tk.HORIZONTAL, command=update_phase_shift)
phase_shift_scale.set(0)
phase_shift_scale.grid(row=9, column=1, columnspan=2)

start_button = tk.Button(root, text="Start", command=start_audio)
start_button.grid(row=10, column=0, pady=5)
stop_button = tk.Button(root, text="Stop", command=stop_audio)
stop_button.grid(row=10, column=1, pady=5)

root.protocol("WM_DELETE_WINDOW", lambda: (stop_audio(), root.destroy()))
root.mainloop()
