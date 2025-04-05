import sounddevice as sd
import numpy as np
import wave
import threading
import time

# Aufnahmeparameter
SAMPLE_RATE = 44100  # Abtastrate in Hz
CHANNELS = 1          # Mono-Aufnahme
DURATION = 0          # Dynamisch, Aufnahme läuft bis "q" gedrückt wird
FILENAME = "aufnahme.wav"

# Globale Variablen für die Aufnahme
recording = True
frames = []
start_time = None

def callback(indata, frames_count, time_info, status):
    """Callback-Funktion für die Audioaufnahme."""
    if status:
        print(status)
    frames.append(indata.copy())

def record_audio():
    """Startet die Audioaufnahme."""
    global start_time
    start_time = time.time()
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16', callback=callback):
        while recording:
            sd.sleep(100)  # Kurzes Warten, um CPU zu entlasten

    # WAV-Datei speichern
    with wave.open(FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))
    print(f"Aufnahme gespeichert als {FILENAME}")

def check_quit():
    """Wartet auf die Eingabe von 'q' zum Beenden der Aufnahme."""
    global recording
    while True:
        if input("Drücke 'q' + Enter, um die Aufnahme zu beenden: ") == "q":
            recording = False
            break

# Threads für Audioaufnahme und Quit-Check starten
record_thread = threading.Thread(target=record_audio)
quit_thread = threading.Thread(target=check_quit)
record_thread.start()
quit_thread.start()

# Warten auf Beenden der Threads
record_thread.join()
quit_thread.join()
