import pygame
import numpy as np
import math

# --- Einstellungen ---
SAMPLE_RATE = 44100
WHITE_KEY_WIDTH = 40
WHITE_KEY_HEIGHT = 200
BLACK_KEY_WIDTH = 24
BLACK_KEY_HEIGHT = 120

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY  = (180, 180, 180)
DARK_GREY = (100, 100, 100)

# Notenreihenfolge (für ein Oktav: C bis B)
notes_order = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def note_frequency(note):
    """
    Berechnet die Frequenz einer Note im wohltemperierten Klavier.
    A4 (440 Hz) dient als Referenz.
    """
    # Zerlege den Notennamen in den Buchstaben (evtl. mit #) und die Oktave
    if len(note) == 2:
        key = note[0]
        octave = int(note[1])
    elif len(note) == 3:
        key = note[0:2]
        octave = int(note[2])
    else:
        raise ValueError("Notenformat nicht erkannt: " + note)
    # Berechne den semitonalen Abstand von A4
    semitone_distance = (octave - 4) * 12 + (notes_order.index(key) - notes_order.index("A"))
    frequency = 440 * (2 ** (semitone_distance / 12))
    return frequency

def generate_tone(frequency):
    """
    Erzeugt einen loopbaren Sinuston für eine gegebene Frequenz.
    Es wird genau eine Periode (in etwa) erzeugt, sodass der Ton nahtlos gelooped werden kann.
    """
    # Anzahl der Samples, sodass (ungefähr) eine Periode enthalten ist
    samples = int(SAMPLE_RATE / frequency)
    # Erzeuge eine Sinuswelle, die genau eine Periode umfasst (0 bis 2*pi)
    t = np.linspace(0, 2 * np.pi, samples, endpoint=False)
    waveform = 0.5 * np.sin(t)  # Amplitude 0.5
    # Konvertiere in 16-Bit Integer
    waveform = np.int16(waveform * 32767)
    # Damit Pygame den Sound korrekt verarbeitet, muss das Array 1D (Mono) sein
    sound = pygame.sndarray.make_sound(waveform)
    return sound

# --- Initialisierung von Pygame und Mixer ---
pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 1024)
pygame.init()

# Erzeuge die Notenliste: zwei Oktaven von C4 bis B5
all_notes = []
for octave in [4, 5]:
    for note in notes_order:
        all_notes.append(f"{note}{octave}")

# Erstelle für jede Note den zugehörigen Sound
sounds = {}
for note in all_notes:
    freq = note_frequency(note)
    sounds[note] = generate_tone(freq)

# --- Tasten-Layout berechnen ---

# Erstelle Listen für weiße und schwarze Tasten
white_keys = []
black_keys = []

# Bestimme die weißen Noten (ohne '#')
white_notes = [note for note in all_notes if "#" not in note]
# Die x-Position der weißen Tasten wächst fortlaufend
for i, note in enumerate(white_notes):
    rect = pygame.Rect(i * WHITE_KEY_WIDTH, 0, WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT)
    white_keys.append({
        "note": note,
        "rect": rect,
        "color": WHITE,
        "pressed": False,
        "sound": sounds[note],
        "channel": None
    })

# Hilfsfunktion: Finde den x-Offset einer weißen Taste mit bestimmtem Note (z.B. "C4")
def find_white_key_x(note_name):
    for key in white_keys:
        if key["note"] == note_name:
            return key["rect"].x
    return None

# Für schwarze Tasten: Diese erscheinen zwischen bestimmten weißen Tasten.
# In einem Oktav gibt es schwarze Tasten bei: C#, D#, F#, G#, A#
# Wir berechnen die Position, indem wir die linke weiße Taste suchen und einen Offset setzen.
for note in all_notes:
    if "#" in note:
        # Zerlege z.B. "C#4" in "C#" und "4"
        key_part = note[:-1]  # "C#"
        octave = note[-1]
        # Bestimme die weiße Taste, vor der der schwarze Ton liegt.
        # Bei C# und D#: vor C bzw. D; bei F#, G#, A#: vor F, G, A.
        if key_part in ["C#", "D#"]:
            base = key_part[0]  # z.B. "C" oder "D"
        else:
            base = key_part[0]  # "F", "G" oder "A"
        base_note = f"{base}{octave}"
        base_x = find_white_key_x(base_note)
        if base_x is None:
            continue
        # Setze den schwarzen Key ca. in der Mitte des Abstands zwischen der weißen Taste und der nächsten.
        x = base_x + WHITE_KEY_WIDTH - (BLACK_KEY_WIDTH // 2)
        rect = pygame.Rect(x, 0, BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT)
        black_keys.append({
            "note": note,
            "rect": rect,
            "color": BLACK,
            "pressed": False,
            "sound": sounds[note],
            "channel": None
        })

# Fenstergröße: Breite = Anzahl der weißen Tasten * WHITE_KEY_WIDTH, Höhe = WHITE_KEY_HEIGHT
width = len(white_keys) * WHITE_KEY_WIDTH
height = WHITE_KEY_HEIGHT
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Kinderklavier")

# Font für Notenbeschriftung
font = pygame.font.SysFont(None, 16)

clock = pygame.time.Clock()
running = True

def toggle_key(key):
    """Schaltet den Zustand einer Taste um: wenn nicht gedrückt, starte Dauerschleife; ansonsten stoppe den Ton."""
    if not key["pressed"]:
        # Taste aktivieren: Farbe wechseln und Sound in Dauerschleife abspielen
        key["pressed"] = True
        # Wähle die gedrückte Farbe (unabhängig, ob weiß oder schwarz)
        key["color"] = GREY if key["note"].find("#") < 0 else DARK_GREY
        # Spiele den Sound in Endlosschleife
        channel = key["sound"].play(loops=-1)
        key["channel"] = channel
    else:
        # Taste deaktivieren: Farbe zurücksetzen und Sound stoppen
        key["pressed"] = False
        key["color"] = WHITE if key["note"].find("#") < 0 else BLACK
        if key["channel"]:
            key["channel"].stop()
            key["channel"] = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            # Zuerst: Prüfe schwarze Tasten, da sie oben liegen
            key_found = False
            for key in black_keys:
                if key["rect"].collidepoint(pos):
                    toggle_key(key)
                    key_found = True
                    break
            if not key_found:
                # Prüfe weiße Tasten
                for key in white_keys:
                    if key["rect"].collidepoint(pos):
                        toggle_key(key)
                        break

    # Zeichne das Keyboard
    screen.fill((50, 50, 50))  # Hintergrund
    # Zeichne weiße Tasten
    for key in white_keys:
        pygame.draw.rect(screen, key["color"], key["rect"])
        pygame.draw.rect(screen, BLACK, key["rect"], 1)
        # Notenbeschriftung: unten mittig
        text = font.render(key["note"], True, BLACK)
        text_rect = text.get_rect(center=(key["rect"].centerx, key["rect"].bottom - 10))
        screen.blit(text, text_rect)
    # Zeichne schwarze Tasten
    for key in black_keys:
        pygame.draw.rect(screen, key["color"], key["rect"])
        pygame.draw.rect(screen, BLACK, key["rect"], 1)
        # Für die Beschriftung: weißer Text in der Mitte
        text = font.render(key["note"], True, WHITE)
        text_rect = text.get_rect(center=key["rect"].center)
        screen.blit(text, text_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
