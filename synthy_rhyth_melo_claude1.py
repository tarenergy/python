import pygame
import numpy as np
import time
from pygame import mixer
from enum import Enum
import threading
import random

# Pygame initialisieren
pygame.init()
mixer.init(frequency=44100, size=-16, channels=2)

# Bildschirmgröße
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Synthesizer mit Rhythmus- und Melodiegenerator")

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (70, 70, 70)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PURPLE = (128, 0, 128)

# Schriftarten
font_small = pygame.font.SysFont('Arial', 16)
font_medium = pygame.font.SysFont('Arial', 24)
font_large = pygame.font.SysFont('Arial', 32)

# Sample Rate und Buffer Größe
SAMPLE_RATE = 44100
BUFFER_SIZE = 4096

# Musikstile als Enum
class MusikStil(Enum):
    WALZER = 1
    FOXTROTT = 2
    SAMBA = 3
    DISCO_FOX = 4
    REGGAE = 5

# Aktueller Musikstil
aktueller_stil = MusikStil.WALZER

# Frequenzen für die Töne (zwei Oktaven)
noten_frequenzen = {
    # Erste Oktave (kleine Oktave)
    'y': 261.63,  # C4
    's': 277.18,  # C#4
    'x': 293.66,  # D4
    'd': 311.13,  # D#4
    'c': 329.63,  # E4
    'v': 349.23,  # F4
    'g': 369.99,  # F#4
    'b': 392.00,  # G4
    'h': 415.30,  # G#4
    'n': 440.00,  # A4
    'j': 466.16,  # A#4
    'm': 493.88,  # B4
    
    # Zweite Oktave (eingestrichene Oktave)
    ',': 523.25,  # C5
    'l': 554.37,  # C#5
    '.': 587.33,  # D5
    'ö': 622.25,  # D#5
    '-': 659.25,  # E5
    'p': 698.46,  # F5
    'ü': 739.99,  # F#5
    '+': 783.99,  # G5
}

# Aktive Töne speichern
aktive_toene = {}

# Schlagzeug-Samples generieren
def create_drum_sound(frequency, duration=0.1, volume=0.5, decay=0.1):
    """Erstellt ein einfaches Schlagzeug-Sample."""
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    decay_factor = np.exp(-t / decay)
    wave = np.sin(2 * np.pi * frequency * t) * volume * decay_factor
    
    # Umwandeln in 16-bit PCM
    wave = np.int16(wave * 32767)
    
    # Stereo-Sound erzeugen
    stereo_wave = np.column_stack((wave, wave))
    
    return pygame.sndarray.make_sound(stereo_wave)

# Schlagzeug-Sounds erstellen
drums = {
    'kick': create_drum_sound(60, duration=0.3, volume=0.8, decay=0.1),    
    'snare': create_drum_sound(200, duration=0.2, volume=0.7, decay=0.05),
    'hihat': create_drum_sound(800, duration=0.1, volume=0.4, decay=0.02),
    'tom': create_drum_sound(100, duration=0.2, volume=0.6, decay=0.08),
    'crash': create_drum_sound(300, duration=0.3, volume=0.5, decay=0.15)
}

# Drum-Pattern initialisieren (16 Schritte, 5 Instrumente)
current_pattern = {
    'kick': [0] * 16,
    'snare': [0] * 16,
    'hihat': [0] * 16,
    'tom': [0] * 16,
    'crash': [0] * 16
}

# Preset-Pattern für verschiedene Musikstile
def get_rhythm_pattern(stil):
    """Liefert ein Rhythmus-Pattern für den ausgewählten Musikstil."""
    if stil == MusikStil.WALZER:
        return {
            'kick': [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            'snare': [0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
            'hihat': [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
            'tom': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
            'crash': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }
    elif stil == MusikStil.FOXTROTT:
        return {
            'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            'snare': [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
            'hihat': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'tom': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            'crash': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }
    elif stil == MusikStil.SAMBA:
        return {
            'kick': [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0],
            'snare': [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0],
            'hihat': [1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1],
            'tom': [0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1],
            'crash': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }
    elif stil == MusikStil.DISCO_FOX:
        return {
            'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            'hihat': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
            'tom': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
            'crash': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }
    elif stil == MusikStil.REGGAE:
        return {
            'kick': [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            'hihat': [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
            'tom': [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
            'crash': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }
    else:
        # Standard-Pattern
        return {
            'kick': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            'hihat': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            'tom': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            'crash': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        }

# Aktuelles Rhythmus-Pattern setzen
current_pattern = get_rhythm_pattern(aktueller_stil)

# Tonerzeuger für Synthesizer
def generate_tone(frequency, volume=0.5, waveform="sine"):
    """Erzeugt einen Ton mit der angegebenen Frequenz und Wellenform."""
    duration = 0.5  # Tondauer in Sekunden
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    
    if waveform == "sine":
        wave = np.sin(2 * np.pi * frequency * t)
    elif waveform == "square":
        wave = np.sign(np.sin(2 * np.pi * frequency * t))
    elif waveform == "sawtooth":
        wave = 2 * (t * frequency - np.floor(0.5 + t * frequency))
    else:  # Standard: Sinus
        wave = np.sin(2 * np.pi * frequency * t)
    
    # Lautstärke anpassen
    wave = wave * volume * 0.5
    
    # Attack-Decay-Sustain-Release (ADSR) Hüllkurve
    attack = int(0.05 * SAMPLE_RATE)
    decay = int(0.05 * SAMPLE_RATE)
    sustain_level = 0.7
    release = int(0.1 * SAMPLE_RATE)
    
    adsr = np.ones(len(wave))
    # Attack
    if attack > 0:
        adsr[:attack] = np.linspace(0, 1, attack)
    # Decay
    if decay > 0:
        adsr[attack:attack+decay] = np.linspace(1, sustain_level, decay)
    # Sustain ist bereits gesetzt durch np.ones
    # Release
    if release > 0:
        adsr[-release:] = np.linspace(sustain_level, 0, release)
    
    # ADSR anwenden
    wave = wave * adsr
    
    # Umwandeln in 16-bit PCM
    wave = np.int16(wave * 32767)
    
    # Stereo-Sound erzeugen
    stereo_wave = np.column_stack((wave, wave))
    
    return pygame.sndarray.make_sound(stereo_wave)

# Melodiegenerator
class MelodieGenerator:
    def __init__(self, stil, bpm=120):
        self.stil = stil
        self.bpm = self.get_bpm_for_stil(stil)
        self.tonfolgen = self.get_tonfolgen_for_stil(stil)
        self.aktueller_schritt = 0
        self.is_playing = False
        self.player_thread = None
    
    def get_bpm_for_stil(self, stil):
        """Liefert das Tempo (BPM) für den ausgewählten Musikstil."""
        if stil == MusikStil.WALZER:
            return 90
        elif stil == MusikStil.FOXTROTT:
            return 120
        elif stil == MusikStil.SAMBA:
            return 100
        elif stil == MusikStil.DISCO_FOX:
            return 126
        elif stil == MusikStil.REGGAE:
            return 80
        else:
            return 120  # Standard-Tempo
    
    def get_tonfolgen_for_stil(self, stil):
        """Liefert charakteristische Tonfolgen für den ausgewählten Musikstil."""
        # Hier werden nur die Tasten der deutschen Tastaturbelegung verwendet
        if stil == MusikStil.WALZER:
            return [
                ['y', 'v', 'b', 'y', 'c', 'v', 'y', ','],
                ['x', 'c', 'v', 'b', 'n', 'b', 'v', 'c']
            ]
        elif stil == MusikStil.FOXTROTT:
            return [
                ['y', 'v', 'b', 'n', 'b', 'v', 'y', 'y'],
                ['x', 'c', 'v', 'b', 'n', 'm', ',', '.']
            ]
        elif stil == MusikStil.SAMBA:
            return [
                ['y', 's', 'x', 'd', 'c', 'v', 'g', 'b'],
                ['c', 'v', 'b', 'n', 'm', ',', '.', '-']
            ]
        elif stil == MusikStil.DISCO_FOX:
            return [
                ['y', 'c', 'v', 'c', 'y', 'c', 'v', 'b'],
                ['n', 'b', 'v', 'c', 'y', 'c', 'v', 'c']
            ]
        elif stil == MusikStil.REGGAE:
            return [
                ['y', 'x', 'c', 'v', 'b', 'n', 'm', ','],
                ['c', 'v', 'b', 'n', 'm', ',', 'l', '.']
            ]
        else:
            return [['y', 'c', 'v', 'b', 'n']]
    
    def set_stil(self, stil):
        """Setzt den Musikstil und aktualisiert Tempo und Tonfolgen."""
        self.stil = stil
        self.bpm = self.get_bpm_for_stil(stil)
        self.tonfolgen = self.get_tonfolgen_for_stil(stil)
    
    def play_melodie(self):
        """Spielt eine zufällige Melodie basierend auf dem aktuellen Musikstil."""
        if self.is_playing:
            return
        
        self.is_playing = True
        self.player_thread = threading.Thread(target=self._play_melodie_thread)
        self.player_thread.daemon = True
        self.player_thread.start()
    
    def _play_melodie_thread(self):
        """Thread-Funktion für das Abspielen der Melodie."""
        try:
            # Wähle eine zufällige Tonfolge aus den verfügbaren für diesen Stil
            tonfolge = random.choice(self.tonfolgen)
            beat_duration = 60.0 / self.bpm  # Dauer eines Beats in Sekunden
            
            while self.is_playing:
                # Aktuelle Taste aus der Tonfolge
                taste = tonfolge[self.aktueller_schritt % len(tonfolge)]
                
                # Ton abspielen, wenn die Taste in den noten_frequenzen ist
                if taste in noten_frequenzen:
                    frequenz = noten_frequenzen[taste]
                    ton = generate_tone(frequenz, volume=0.3)
                    ton.play()
                
                # Warte einen Beat
                time.sleep(beat_duration)
                
                # Nächster Schritt
                self.aktueller_schritt += 1
                
        except Exception as e:
            print(f"Fehler im Melodie-Thread: {e}")
            self.is_playing = False
    
    def stop_melodie(self):
        """Stoppt die aktuelle Melodie."""
        self.is_playing = False
        if self.player_thread and self.player_thread.is_alive():
            self.player_thread.join(timeout=1.0)

# Rhythmus-Player
class RhythmusPlayer:
    def __init__(self, pattern, bpm=120):
        self.pattern = pattern
        self.bpm = bpm
        self.current_step = 0
        self.is_playing = False
        self.player_thread = None
    
    def set_pattern(self, pattern):
        """Setzt das aktuelle Rhythmus-Pattern."""
        self.pattern = pattern
    
    def set_bpm(self, bpm):
        """Setzt das Tempo (BPM)."""
        self.bpm = bpm
    
    def play_rhythm(self):
        """Startet den Rhythmus-Player."""
        if self.is_playing:
            return
        
        self.is_playing = True
        self.player_thread = threading.Thread(target=self._play_rhythm_thread)
        self.player_thread.daemon = True
        self.player_thread.start()
    
    def _play_rhythm_thread(self):
        """Thread-Funktion für das Abspielen des Rhythmus."""
        try:
            beat_duration = 60.0 / self.bpm / 4  # Sechzehntel-Noten (16 Schritte pro Takt)
            
            while self.is_playing:
                # Spiele jeden Sound, der in diesem Schritt aktiv ist
                for drum_name, pattern in self.pattern.items():
                    if pattern[self.current_step] == 1:
                        drums[drum_name].play()
                
                # Warte einen Sechzehntel-Schlag
                time.sleep(beat_duration)
                
                # Nächster Schritt (0-15)
                self.current_step = (self.current_step + 1) % 16
                
        except Exception as e:
            print(f"Fehler im Rhythmus-Thread: {e}")
            self.is_playing = False
    
    def stop_rhythm(self):
        """Stoppt den Rhythmus-Player."""
        self.is_playing = False
        if self.player_thread and self.player_thread.is_alive():
            self.player_thread.join(timeout=1.0)

# Melodie-Generator initialisieren
melodie_generator = MelodieGenerator(aktueller_stil)

# Rhythmus-Player initialisieren
rhythmus_player = RhythmusPlayer(current_pattern, melodie_generator.bpm)

# Wellenform für den Synthesizer
aktueller_waveform = "sine"
waveform_options = ["sine", "square", "sawtooth"]

# GUI-Elemente definieren
class Button:
    def __init__(self, x, y, width, height, text, color, text_color=BLACK, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.action = action
        self.highlighted = False
    
    def draw(self, surface):
        if self.highlighted:
            highlight_color = tuple(min(c + 30, 255) for c in self.color)
            pygame.draw.rect(surface, highlight_color, self.rect)
            pygame.draw.rect(surface, self.color, self.rect.inflate(-4, -4))
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        
        pygame.draw.rect(surface, BLACK, self.rect, 2)  # Umrandung
        
        text_surf = font_medium.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def check_hover(self, pos):
        self.highlighted = self.rect.collidepoint(pos)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.action:
                self.action()
                return True
        return False

class ToggleButton(Button):
    def __init__(self, x, y, width, height, text, color, toggle_color, text_color=BLACK, action=None, toggle_action=None):
        super().__init__(x, y, width, height, text, color, text_color, action)
        self.toggled = False
        self.original_color = color
        self.toggle_color = toggle_color
        self.toggle_action = toggle_action
    
    def draw(self, surface):
        if self.toggled:
            if self.highlighted:
                highlight_color = tuple(min(c + 30, 255) for c in self.toggle_color)
                pygame.draw.rect(surface, highlight_color, self.rect)
                pygame.draw.rect(surface, self.toggle_color, self.rect.inflate(-4, -4))
            else:
                pygame.draw.rect(surface, self.toggle_color, self.rect)
        else:
            super().draw(surface)
        
        text_surf = font_medium.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.toggled = not self.toggled
                if self.toggled and self.action:
                    self.action()
                elif not self.toggled and self.toggle_action:
                    self.toggle_action()
                return True
        return False

class DrumPad:
    def __init__(self, x, y, width, height, drum_name, step):
        self.rect = pygame.Rect(x, y, width, height)
        self.drum_name = drum_name
        self.step = step
        self.active = current_pattern[drum_name][step] == 1
        self.highlighted = False
    
    def draw(self, surface, is_current_step=False):
        if is_current_step:
            pygame.draw.rect(surface, YELLOW, self.rect.inflate(4, 4))
        
        if self.active:
            if self.highlighted:
                pygame.draw.rect(surface, ORANGE, self.rect)
            else:
                pygame.draw.rect(surface, RED, self.rect)
        else:
            if self.highlighted:
                pygame.draw.rect(surface, LIGHT_GRAY, self.rect)
            else:
                pygame.draw.rect(surface, GRAY, self.rect)
        
        pygame.draw.rect(surface, BLACK, self.rect, 1)  # Umrandung
    
    def check_hover(self, pos):
        self.highlighted = self.rect.collidepoint(pos)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
                current_pattern[self.drum_name][self.step] = 1 if self.active else 0
                if self.active:
                    # Ton abspielen, wenn aktiviert
                    drums[self.drum_name].play()
                return True
        return False

# Funktionen für Buttons
def toggle_rhythm():
    if rhythmus_player.is_playing:
        rhythmus_player.stop_rhythm()
        if rhythm_button.toggled:
            rhythm_button.toggled = False
    else:
        rhythmus_player.set_pattern(current_pattern)
        rhythmus_player.set_bpm(melodie_generator.bpm)
        rhythmus_player.play_rhythm()

def toggle_melodie():
    if melodie_generator.is_playing:
        melodie_generator.stop_melodie()
        if melody_button.toggled:
            melody_button.toggled = False
    else:
        melodie_generator.play_melodie()

def set_musikstil(stil):
    global aktueller_stil, current_pattern
    aktueller_stil = stil
    melodie_generator.set_stil(stil)
    
    # Rhythmus-Pattern aktualisieren
    current_pattern = get_rhythm_pattern(stil)
    rhythmus_player.set_pattern(current_pattern)
    rhythmus_player.set_bpm(melodie_generator.bpm)
    
    # Wenn der Rhythmus gerade spielt, neu starten
    if rhythmus_player.is_playing:
        rhythmus_player.stop_rhythm()
        rhythmus_player.play_rhythm()
    
    # Wenn die Melodie gerade spielt, neu starten
    if melodie_generator.is_playing:
        melodie_generator.stop_melodie()
        melodie_generator.play_melodie()

def set_walzer():
    set_musikstil(MusikStil.WALZER)

def set_foxtrott():
    set_musikstil(MusikStil.FOXTROTT)

def set_samba():
    set_musikstil(MusikStil.SAMBA)

def set_disco_fox():
    set_musikstil(MusikStil.DISCO_FOX)

def set_reggae():
    set_musikstil(MusikStil.REGGAE)

def change_waveform():
    global aktueller_waveform
    current_index = waveform_options.index(aktueller_waveform)
    next_index = (current_index + 1) % len(waveform_options)
    aktueller_waveform = waveform_options[next_index]
    waveform_button.text = f"Waveform: {aktueller_waveform}"

# Tastenfeld für den Synthesizer
class SynthKey:
    def __init__(self, x, y, width, height, key, frequency, color=WHITE, is_black=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.key = key
        self.frequency = frequency
        self.color = color
        self.is_black = is_black
        self.is_pressed = False
        self.sound = None
    
    def draw(self, surface):
        if self.is_pressed:
            pygame.draw.rect(surface, BLUE if not self.is_black else DARK_GRAY, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        
        pygame.draw.rect(surface, BLACK, self.rect, 1)  # Umrandung
        
        # Tastenbezeichnung anzeigen
        text_surf = font_small.render(self.key, True, BLACK if not self.is_black else WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def handle_keyboard_event(self, key_pressed, was_pressed):
        if key_pressed == self.key:
            if was_pressed and not self.is_pressed:
                self.is_pressed = True
                self.sound = generate_tone(self.frequency, volume=0.5, waveform=aktueller_waveform)
                self.sound.play(-1)  # Endlos spielen, bis wir es stoppen
                return True
            elif not was_pressed and self.is_pressed:
                self.is_pressed = False
                if self.sound:
                    self.sound.stop()
                return True
        return False

# GUI-Elemente erstellen
# Rhythmus-Steuerung
rhythm_button = ToggleButton(20, 20, 150, 40, "Rhythmus starten", GREEN, RED, action=toggle_rhythm)

# Melodie-Steuerung
melody_button = ToggleButton(190, 20, 150, 40, "Melodie starten", GREEN, RED, action=toggle_melodie)

# Musikstil-Buttons
walzer_button = Button(20, 80, 150, 40, "Walzer", CYAN, action=set_walzer)
foxtrott_button = Button(190, 80, 150, 40, "Foxtrott", CYAN, action=set_foxtrott)
samba_button = Button(360, 80, 150, 40, "Samba", CYAN, action=set_samba)
disco_fox_button = Button(530, 80, 150, 40, "Disco-Fox", CYAN, action=set_disco_fox)
reggae_button = Button(700, 80, 150, 40, "Reggae", CYAN, action=set_reggae)

# Waveform-Button
waveform_button = Button(360, 20, 200, 40, f"Waveform: {aktueller_waveform}", PURPLE, WHITE, action=change_waveform)

# Schlagzeug-Pads erstellen
drum_pads = []
drum_names = list(current_pattern.keys())
pad_width, pad_height = 50, 30
pad_spacing_x, pad_spacing_y = 10, 10
start_x, start_y = 20, 140

for i, drum_name in enumerate(drum_names):
    for step in range(16):
        x = start_x + step * (pad_width + pad_spacing_x)
        y = start_y + i * (pad_height + pad_spacing_y)
        drum_pads.append(DrumPad(x, y, pad_width, pad_height, drum_name, step))

# Synthesizer-Tasten erstellen
synth_keys = []
white_key_width, white_key_height = 40, 120
black_key_width, black_key_height = 30, 80
start_x, start_y = 20, 350

# Weiße Tasten (erste Reihe - untere Oktave)
white_keys_row1 = ['y', 'x', 'c', 'v', 'b', 'n', 'm']
for i, key in enumerate(white_keys_row1):
    x = start_x + i * white_key_width
    y = start_y
    synth_keys.append(SynthKey(x, y, white_key_width, white_key_height, key, noten_frequenzen[key], WHITE))

# Schwarze Tasten (erste Reihe - untere Oktave)
black_keys_row1 = ['s', 'd', 'g', 'h', 'j']
black_positions = [0.5, 1.5, 3.5, 4.5, 5.5]  # Position relativ zu den weißen Tasten
for i, key in enumerate(black_keys_row1):
    x = start_x + black_positions[i] * white_key_width - black_key_width // 2
    y = start_y
    synth_keys.append(SynthKey(x, y, black_key_width, black_key_height, key, noten_frequenzen[key], BLACK, True))

# Weiße Tasten (zweite Reihe - obere Oktave)
white_keys_row2 = [',', '.', '-', 'p', '+']
start_x_row2 = start_x + 7 * white_key_width + 20  # Etwas Abstand zwischen den Reihen
for i, key in enumerate(white_keys_row2):
    x = start_x_row2 + i * white_key_width
    y = start_y
    synth_keys.append(SynthKey(x, y, white_key_width, white_key_height, key, noten_frequenzen[key], WHITE))

# Schwarze Tasten (zweite Reihe - obere Oktave)
black_keys_row2 = ['l', 'ö', 'ü']
black_positions_row2 = [0.5, 1.5, 3.5]
for i, key in enumerate(black_keys_row2):
    x = start_x_row2 + black_positions_row2[i] * white_key_width - black_key_width // 2
    y = start_y
    synth_keys.append(SynthKey(x, y, black_key_width, black_key_height, key, noten_frequenzen[key], BLACK, True))

# Hauptschleife
running = True
clock = pygame.time.Clock()

while running:
    # Events verarbeiten
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Maus-Events für Buttons
        if event.type == pygame.MOUSEMOTION:
            for button in [rhythm_button, melody_button, walzer_button, foxtrott_button, 
                           samba_button, disco_fox_button, reggae_button, waveform_button]:
                button.check_hover(event.pos)
            
            for pad in drum_pads:
                pad.check_hover(event.pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            rhythm_button.handle_event(event)
            melody_button.handle_event(event)
            walzer_button.handle_event(event)
            foxtrott_button.handle_event(event)
            samba_button.handle_event(event)
            disco_fox_button.handle_event(event)
            reggae_button.handle_event(event)
            waveform_button.handle_event(event)
            
            for pad in drum_pads:
                pad.handle_event(event)
        
        # Tastatur-Events für Synthesizer
        if event.type == pygame.KEYDOWN:
            key_name = pygame.key.name(event.key)
            for key in synth_keys:
                if key.handle_keyboard_event(key_name, True):
                    break
        
        if event.type == pygame.KEYUP:
            key_name = pygame.key.name(event.key)
            for key in synth_keys:
                if key.handle_keyboard_event(key_name, False):
                    break
    
    # Bildschirm löschen
    screen.fill(LIGHT_GRAY)
    
    # Titel zeichnen
    title = font_large.render("Synthesizer mit Rhythmus- und Melodiegenerator", True, BLACK)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 5))
    
    # Buttons zeichnen
    rhythm_button.draw(screen)
    melody_button.draw(screen)
    walzer_button.draw(screen)
    foxtrott_button.draw(screen)
    samba_button.draw(screen)
    disco_fox_button.draw(screen)
    reggae_button.draw(screen)
    waveform_button.draw(screen)
    
    # Aktuellen Musikstil anzeigen
    stil_text = font_medium.render(f"Aktueller Stil: {aktueller_stil.name} - BPM: {melodie_generator.bpm}", True, BLACK)
    screen.blit(stil_text, (600, 25))
    
    # Schlagzeug-Grid-Überschriften
    drum_title = font_medium.render("Rhythmus-Generator (16 Schritte)", True, BLACK)
    screen.blit(drum_title, (20, 120))
    
    for i, drum_name in enumerate(drum_names):
        text = font_small.render(drum_name, True, BLACK)
        screen.blit(text, (start_x - text.get_width() - 10, start_y + i * (pad_height + pad_spacing_y) + pad_height//2 - text.get_height()//2))
    
    # Schlagzeug-Pads zeichnen
    for pad in drum_pads:
        is_current_step = rhythmus_player.is_playing and pad.step == rhythmus_player.current_step
        pad.draw(screen, is_current_step)
    
    # Synthesizer-Überschrift
    synth_title = font_medium.render("Synthesizer (Zwei Oktaven mit deutscher Tastaturbelegung)", True, BLACK)
    screen.blit(synth_title, (20, 320))
    
    # Synthesizer-Tasten zeichnen
    for key in synth_keys:
        key.draw(screen)
    
    # Bildschirm aktualisieren
    pygame.display.flip()
    clock.tick(60)

# Aufräumen
if rhythmus_player.is_playing:
    rhythmus_player.stop_rhythm()

if melodie_generator.is_playing:
    melodie_generator.stop_melodie()

pygame.quit()