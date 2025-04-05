import pygame
import numpy as np
import random

# Initialisiere Pygame und den Mixer (Stereo, 16 Bit, 44100 Hz)
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Bildschirm-Einstellungen
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Synthesizer und Drum Machine")

# ----------------------------
# Funktionen zur Tonerzeugung
# ----------------------------

def generate_sine_wave(freq, duration=1.0, volume=0.5, sample_rate=44100):
    """Erzeugt einen Sinuston mit linearem Abklingen (Envelope)."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * freq * t)
    # Einfache Abklingkurve
    envelope = np.linspace(1, 0, tone.shape[0])
    tone *= envelope
    tone = (tone * volume * (2**15 - 1)).astype(np.int16)
    # Erzeuge Stereo: beide Kanäle identisch
    stereo = np.column_stack((tone, tone))
    return pygame.sndarray.make_sound(stereo)

def get_freq(note, octave):
    """Berechnet die Frequenz (Hz) eines Tones anhand des Notennamens und der Oktave.
       C4 (mittleres C) wird mit ca. 261.63 Hz angenommen."""
    note_base = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4,
                 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
    base_freq = 261.63
    n = note_base[note] + (octave - 4) * 12
    return base_freq * (2 ** (n / 12))

# ----------------------------------------------------
# Tastaturzuordnung (deutsche Belegung) für zwei Oktaven
# ----------------------------------------------------
# Untere Oktave (4): A, W, S, E, D, F, T, G, Z, H, U, J
# Obere Oktave (5): K, O, L, P, ö, ä, X, C, V, B, N, M

note_keys = {
    pygame.K_a: ('C', 4),
    pygame.K_w: ('C#', 4),
    pygame.K_s: ('D', 4),
    pygame.K_e: ('D#', 4),
    pygame.K_d: ('E', 4),
    pygame.K_f: ('F', 4),
    pygame.K_t: ('F#', 4),
    pygame.K_g: ('G', 4),
    pygame.K_z: ('G#', 4),
    pygame.K_h: ('A', 4),
    pygame.K_u: ('A#', 4),
    pygame.K_j: ('B', 4),
    
    pygame.K_k: ('C', 5),
    pygame.K_o: ('C#', 5),
    pygame.K_l: ('D', 5),
    pygame.K_p: ('D#', 5),
    ord('ö'): ('E', 5),
    ord('ä'): ('F', 5),
    pygame.K_x: ('F#', 5),
    pygame.K_c: ('G', 5),
    pygame.K_v: ('G#', 5),
    pygame.K_b: ('A', 5),
    pygame.K_n: ('A#', 5),
    pygame.K_m: ('B', 5)
}

# Pre-generiere die Töne für alle zugeordneten Tasten
notes = {}
for key, (note, octave) in note_keys.items():
    freq = get_freq(note, octave)
    sound = generate_sine_wave(freq, duration=1.0, volume=0.5)
    notes[key] = sound

# ----------------------------
# Schlagzeug-Sounds erzeugen
# ----------------------------

def generate_kick(duration=0.5, volume=0.8, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    freqs = np.linspace(150, 50, t.shape[0])
    tone = np.sin(2 * np.pi * freqs * t)
    envelope = np.linspace(1, 0, t.shape[0])
    tone *= envelope
    tone = (tone * volume * (2**15 - 1)).astype(np.int16)
    stereo = np.column_stack((tone, tone))
    return pygame.sndarray.make_sound(stereo)

def generate_snare(duration=0.3, volume=0.5, sample_rate=44100):
    num_samples = int(sample_rate * duration)
    noise = np.random.uniform(-1, 1, num_samples)
    envelope = np.linspace(1, 0, num_samples)
    noise *= envelope
    noise = (noise * volume * (2**15 - 1)).astype(np.int16)
    stereo = np.column_stack((noise, noise))
    return pygame.sndarray.make_sound(stereo)

def generate_hihat(duration=0.2, volume=0.3, sample_rate=44100):
    num_samples = int(sample_rate * duration)
    noise = np.random.uniform(-1, 1, num_samples)
    envelope = np.linspace(1, 0, num_samples)
    noise *= envelope
    noise = (noise * volume * (2**15 - 1)).astype(np.int16)
    stereo = np.column_stack((noise, noise))
    return pygame.sndarray.make_sound(stereo)

def generate_clap(duration=0.3, volume=0.5, sample_rate=44100):
    num_samples = int(sample_rate * duration)
    noise = np.random.uniform(-1, 1, num_samples)
    envelope = np.linspace(1, 0, num_samples)
    noise *= envelope
    noise = (noise * volume * (2**15 - 1)).astype(np.int16)
    stereo = np.column_stack((noise, noise))
    return pygame.sndarray.make_sound(stereo)

def generate_tom(duration=0.5, volume=0.6, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    freqs = np.linspace(200, 80, t.shape[0])
    tone = np.sin(2 * np.pi * freqs * t)
    envelope = np.linspace(1, 0, t.shape[0])
    tone *= envelope
    tone = (tone * volume * (2**15 - 1)).astype(np.int16)
    stereo = np.column_stack((tone, tone))
    return pygame.sndarray.make_sound(stereo)

drum_sounds = {
    "kick": generate_kick(),
    "snare": generate_snare(),
    "hihat": generate_hihat(),
    "clap": generate_clap(),
    "tom": generate_tom()
}

# -------------------------------------
# Rhythmus-Generator: 16 Felder x 5 Instrumente
# -------------------------------------
# rhythm_grid[row][step] ist True, wenn das jeweilige Instrument in diesem Schritt ausgelöst wird.
rhythm_grid = [[False for _ in range(16)] for _ in range(5)]
drum_instruments = ["kick", "snare", "hihat", "clap", "tom"]

# -----------------------
# Melodiegenerator
# -----------------------
# Wir verwenden den C-Dur-Skala (nur C, D, E, F, G, A, B)
scale_notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']

def generate_melody(style, num_bars=4, bpm=120):
    """Generiert eine Melodie als Liste von (Sound, Dauer)-Tupeln.
       Für 'Walzer' wird 3/4-Takt verwendet, ansonsten 4/4."""
    melody = []
    beat_duration = 60 / bpm
    if style == "Walzer":
        beats_per_bar = 3
    else:
        beats_per_bar = 4
    for bar in range(num_bars):
        remaining = beats_per_bar
        while remaining > 0:
            possible_durations = [0.5, 1.0]  # Halbe oder volle Beats
            duration = random.choice(possible_durations)
            if duration > remaining:
                duration = remaining
            note_name = random.choice(scale_notes)
            octave = random.choice([4, 5])
            freq = get_freq(note_name, octave)
            sound = generate_sine_wave(freq, duration=duration * beat_duration, volume=0.5)
            melody.append((sound, duration * beat_duration))
            remaining -= duration
    return melody

# Standardstil und Melodie-Variablen
current_style = "Walzer"  # 1: Walzer, 2: Foxtrott, 3: Samba, 4: Disco-Fox, 5: Reggae
melody_sequence = []
melody_index = 0
melody_playing = False
next_melody_tick = 0

# -----------------------
# Timer und Sequencer
# -----------------------
bpm = 120
# Bei 4/4-Takt und 16 Schritten pro Takt (16tel-Noten) ist die Schritt-Dauer:
step_duration_ms = int(60 / (bpm * 4) * 1000)
DRUM_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(DRUM_EVENT, step_duration_ms)
current_step = 0

# Position und Größe des Drum-Grids
grid_origin = (50, 400)
cell_width = 40
cell_height = 40

# -----------------------
# Hauptschleife
# -----------------------
clock = pygame.time.Clock()
running = True

while running:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Tastatur-Eingaben: Synthesizer und Melodiegenerator-Stil
        elif event.type == pygame.KEYDOWN:
            # Synthesizer: Spiele Note, wenn zugeordnete Taste gedrückt wird
            if event.key in notes:
                notes[event.key].play()
            # Auswahl des Melodiegenerator-Stils:
            elif event.key == pygame.K_1:
                current_style = "Walzer"
                print("Stil: Walzer")
            elif event.key == pygame.K_2:
                current_style = "Foxtrott"
                print("Stil: Foxtrott")
            elif event.key == pygame.K_3:
                current_style = "Samba"
                print("Stil: Samba")
            elif event.key == pygame.K_4:
                current_style = "Disco-Fox"
                print("Stil: Disco-Fox")
            elif event.key == pygame.K_5:
                current_style = "Reggae"
                print("Stil: Reggae")
            # Starte den Melodiegenerator (Taste "M")
            elif event.key == pygame.K_m:
                melody_sequence = generate_melody(current_style, num_bars=4, bpm=bpm)
                melody_index = 0
                melody_playing = True
                next_melody_tick = current_time
                print("Melodie gestartet im Stil:", current_style)

        # Mit der Maus das Drum-Grid bearbeiten
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            gx, gy = grid_origin
            if gx <= mx < gx + 16 * cell_width and gy <= my < gy + 5 * cell_height:
                col = (mx - gx) // cell_width
                row = (my - gy) // cell_height
                rhythm_grid[row][col] = not rhythm_grid[row][col]

        # DRUM_EVENT: Schritt-Synchronisation für das Schlagzeug
        elif event.type == DRUM_EVENT:
            for i, instrument in enumerate(drum_instruments):
                if rhythm_grid[i][current_step]:
                    drum_sounds[instrument].play()
            current_step = (current_step + 1) % 16

    # Melodie abspielen
    if melody_playing and current_time >= next_melody_tick:
        if melody_index < len(melody_sequence):
            sound, duration = melody_sequence[melody_index]
            sound.play()
            next_melody_tick = current_time + int(duration * 1000)
            melody_index += 1
        else:
            melody_playing = False

    # Bildschirm zeichnen
    screen.fill((30, 30, 30))

    # Zeichne das Drum-Grid
    for i in range(5):
        for j in range(16):
            rect = pygame.Rect(grid_origin[0] + j * cell_width,
                               grid_origin[1] + i * cell_height,
                               cell_width, cell_height)
            color = (0, 200, 0) if rhythm_grid[i][j] else (50, 50, 50)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (80, 80, 80), rect, 1)
    # Hebe den aktuellen Schritt hervor
    step_rect = pygame.Rect(grid_origin[0] + current_step * cell_width,
                            grid_origin[1],
                            cell_width, 5 * cell_height)
    pygame.draw.rect(screen, (200, 200, 0), step_rect, 3)

    # Zeige Anweisungen
    font = pygame.font.SysFont(None, 24)
    instructions = "Synth: Tasten spielen | M: Melodie starten | 1-5: Stil (1=Walzer,2=Foxtrott,3=Samba,4=Disco-Fox,5=Reggae)"
    text = font.render(instructions, True, (255, 255, 255))
    screen.blit(text, (50, 50))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
