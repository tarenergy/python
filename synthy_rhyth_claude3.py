import pygame
import numpy as np
import time
from pygame import mixer

# Initialisierung von Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2)

# Konstanten
SAMPLE_RATE = 44100  # Abtastrate in Hz
MAX_AMPLITUDE = 32767  # Maximale Amplitude für 16-bit Audio

# Fenster einrichten
WIDTH, HEIGHT = 800, 650
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Synthesizer mit Rhythmusgenerator")

# Farben
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)  # Farbe für das neue Instrument

# Klasse für die Erzeugung von Wellenformen
class ToneGenerator:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def generate_drum_sound(self, type="kick", duration=0.1, volume=0.7):
        """Generiert verschiedene Drum-Sounds."""
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, False)
        
        if type == "kick":
            # Kick-Drum (Bass Drum)
            frequency = 150
            decay = np.exp(-t * 30)
            wave = np.sin(2 * np.pi * frequency * t) * decay * volume * MAX_AMPLITUDE
        elif type == "snare":
            # Snare-Drum
            noise = np.random.uniform(-0.5, 0.5, num_samples)
            decay = np.exp(-t * 15)
            wave = noise * decay * volume * MAX_AMPLITUDE
        elif type == "hihat":
            # Hi-Hat
            noise = np.random.uniform(-0.2, 0.2, num_samples)
            decay = np.exp(-t * 50)
            wave = noise * decay * volume * MAX_AMPLITUDE
        elif type == "clap":
            # Clap-Sound (neues Instrument)
            noise = np.random.uniform(-0.3, 0.3, num_samples)
            # Typischer Clap-Sound hat eine leichte Verzögerung am Anfang
            envelope = np.zeros_like(t)
            clap_start = int(0.01 * self.sample_rate)  # 10ms Verzögerung
            envelope[clap_start:] = np.exp(-(t[:-clap_start] * 20))
            wave = noise * envelope * volume * MAX_AMPLITUDE
        else:
            # Default: Kick-Drum
            frequency = 150
            decay = np.exp(-t * 30)
            wave = np.sin(2 * np.pi * frequency * t) * decay * volume * MAX_AMPLITUDE
        
        # Konvertiere zu Stereo (2D-Array)
        stereo_wave = np.column_stack((wave, wave))
        return stereo_wave.astype(np.int16)
        
    def generate_sine_wave(self, frequency, duration, volume=0.5):
        """Generiert eine Sinuswelle mit der angegebenen Frequenz und Dauer."""
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, False)
        wave = np.sin(2 * np.pi * frequency * t) * volume * MAX_AMPLITUDE
        # Konvertiere zu Stereo (2D-Array)
        stereo_wave = np.column_stack((wave, wave))
        return stereo_wave.astype(np.int16)
    
    def generate_square_wave(self, frequency, duration, volume=0.5):
        """Generiert eine Rechteckwelle mit der angegebenen Frequenz und Dauer."""
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, False)
        wave = np.sign(np.sin(2 * np.pi * frequency * t)) * volume * MAX_AMPLITUDE
        # Konvertiere zu Stereo (2D-Array)
        stereo_wave = np.column_stack((wave, wave))
        return stereo_wave.astype(np.int16)
    
    def generate_sawtooth_wave(self, frequency, duration, volume=0.5):
        """Generiert eine Sägezahnwelle mit der angegebenen Frequenz und Dauer."""
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, False)
        wave = 2 * (t * frequency - np.floor(0.5 + t * frequency)) * volume * MAX_AMPLITUDE
        # Konvertiere zu Stereo (2D-Array)
        stereo_wave = np.column_stack((wave, wave))
        return stereo_wave.astype(np.int16)
    
    def generate_triangle_wave(self, frequency, duration, volume=0.5):
        """Generiert eine Dreieckswelle mit der angegebenen Frequenz und Dauer."""
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, False)
        wave = 2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1
        wave = wave * volume * MAX_AMPLITUDE
        # Konvertiere zu Stereo (2D-Array)
        stereo_wave = np.column_stack((wave, wave))
        return stereo_wave.astype(np.int16)

# Die Tastenbelegung für den Synthesizer (QWERTZ-Layout)
KEY_TO_FREQUENCY = {
    pygame.K_a: 261.63,  # C4
    pygame.K_w: 277.18,  # C#4
    pygame.K_s: 293.66,  # D4
    pygame.K_e: 311.13,  # D#4
    pygame.K_d: 329.63,  # E4
    pygame.K_f: 349.23,  # F4
    pygame.K_t: 369.99,  # F#4
    pygame.K_g: 392.00,  # G4
    pygame.K_z: 415.30,  # G#4
    pygame.K_h: 440.00,  # A4
    pygame.K_u: 466.16,  # A#4
    pygame.K_j: 493.88,  # B4
    pygame.K_k: 523.25,  # C5
}

# Rhythmus-Klasse
class RhythmGenerator:
    def __init__(self, generator):
        self.generator = generator
        self.is_playing = False
        self.bpm = 120
        self.beat = 0
        self.max_beats = 16
        self.last_beat_time = 0
        
        # Drum-Patterns (1 = spielen, 0 = nicht spielen)
        self.patterns = {
            "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            "snare": [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
            "hihat": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
            "clap": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1]  # Pattern für das neue Clap-Instrument
        }
        
        # Aktive Drum-Spuren
        self.active_drums = {
            "kick": True,
            "snare": True,
            "hihat": True,
            "clap": True  # Das neue Instrument ist standardmäßig aktiv
        }
        
        # Cache für die Drum-Sounds
        self.drum_sounds = {
            "kick": self.generator.generate_drum_sound("kick"),
            "snare": self.generator.generate_drum_sound("snare"),
            "hihat": self.generator.generate_drum_sound("hihat"),
            "clap": self.generator.generate_drum_sound("clap")  # Sound für das neue Instrument
        }
        
        # Sounds vorerstellen
        self.sound_objects = {
            "kick": pygame.sndarray.make_sound(self.drum_sounds["kick"]),
            "snare": pygame.sndarray.make_sound(self.drum_sounds["snare"]),
            "hihat": pygame.sndarray.make_sound(self.drum_sounds["hihat"]),
            "clap": pygame.sndarray.make_sound(self.drum_sounds["clap"])  # Sound-Objekt für das neue Instrument
        }
    
    def toggle_drum(self, drum_type):
        """Aktiviert oder deaktiviert eine Drum-Spur."""
        self.active_drums[drum_type] = not self.active_drums[drum_type]
    
    def toggle_pattern_at(self, drum_type, beat_index):
        """Ändert den Status eines Beats im Pattern."""
        self.patterns[drum_type][beat_index] = 1 - self.patterns[drum_type][beat_index]
    
    def set_bpm(self, bpm):
        """Setzt das Tempo in BPM (Beats pro Minute)."""
        self.bpm = max(40, min(240, bpm))
    
    def start_stop(self):
        """Startet oder stoppt den Rhythmus-Generator."""
        self.is_playing = not self.is_playing
        self.beat = 0
        self.last_beat_time = pygame.time.get_ticks()
    
    def update(self):
        """Aktualisiert den Rhythmus-Generator und spielt Beats ab."""
        if not self.is_playing:
            return
        
        current_time = pygame.time.get_ticks()
        beat_duration = 60000 / self.bpm / 4  # Dauer eines 16tel-Beats in ms
        
        if current_time - self.last_beat_time >= beat_duration:
            self.last_beat_time = current_time
            
            # Drum-Sounds abspielen, falls aktiv und im Pattern eingeschaltet
            for drum_type in self.active_drums:
                if self.active_drums[drum_type] and self.patterns[drum_type][self.beat] == 1:
                    self.sound_objects[drum_type].play()
            
            # Zum nächsten Beat gehen
            self.beat = (self.beat + 1) % self.max_beats
            
            return True  # Beat wurde abgespielt
        
        return False  # Kein Beat wurde abgespielt
    
    def draw(self, surface, x, y, width, height):
        """Zeichnet die Rhythmus-Grid auf die Oberfläche."""
        grid_width = width
        grid_height = 160  # Erhöht, um Platz für vier Drum-Typen zu schaffen
        cell_width = grid_width / self.max_beats
        cell_height = grid_height / 4  # Vier Drum-Typen (inkl. des neuen Instruments)
        
        font = pygame.font.SysFont(None, 24)
        
        # Hintergrund
        pygame.draw.rect(surface, GRAY, (x, y, grid_width, grid_height))
        
        # Beschriftungen
        labels = ["Kick", "Snare", "Hi-Hat", "Clap"]  # Beschriftung für das neue Instrument hinzugefügt
        for i, label in enumerate(labels):
            label_surf = font.render(label, True, WHITE)
            surface.blit(label_surf, (x - 60, y + i * cell_height + cell_height / 2 - 10))
        
        # Grid zeichnen
        drum_types = ["kick", "snare", "hihat", "clap"]  # Das neue Instrument in die Liste aufgenommen
        colors = [GREEN, GREEN, GREEN, PURPLE]  # Eigene Farbe für das neue Instrument
        
        for i, drum_type in enumerate(drum_types):
            for j in range(self.max_beats):
                cell_color = colors[i] if self.patterns[drum_type][j] == 1 else BLACK
                if self.is_playing and j == self.beat:
                    # Aktiver Beat-Marker
                    border_color = WHITE
                    pygame.draw.rect(surface, border_color, (x + j * cell_width, y + i * cell_height, cell_width, cell_height), 2)
                
                # Zelleninhalt
                cell_rect = pygame.Rect(x + j * cell_width + 2, y + i * cell_height + 2, cell_width - 4, cell_height - 4)
                pygame.draw.rect(surface, cell_color, cell_rect)
                
                # Jeder vierte Beat hervorheben (für bessere Lesbarkeit)
                if j % 4 == 0:
                    pygame.draw.line(surface, WHITE, (x + j * cell_width, y), (x + j * cell_width, y + grid_height), 2)

        # BPM-Anzeige
        bpm_text = font.render(f"BPM: {self.bpm}", True, WHITE)
        surface.blit(bpm_text, (x, y + grid_height + 10))
        
        # Play/Stop-Button
        button_text = "Stop" if self.is_playing else "Play"
        button_color = RED if self.is_playing else GREEN
        button_rect = pygame.Rect(x + grid_width - 80, y + grid_height + 10, 80, 30)
        pygame.draw.rect(surface, button_color, button_rect)
        button_label = font.render(button_text, True, WHITE)
        surface.blit(button_label, (button_rect.x + 20, button_rect.y + 5))
        
        # BPM +/- Buttons
        bpm_minus_rect = pygame.Rect(x + 100, y + grid_height + 10, 30, 30)
        bpm_plus_rect = pygame.Rect(x + 180, y + grid_height + 10, 30, 30)
        pygame.draw.rect(surface, BLUE, bpm_minus_rect)
        pygame.draw.rect(surface, BLUE, bpm_plus_rect)
        minus_label = font.render("-", True, WHITE)
        plus_label = font.render("+", True, WHITE)
        surface.blit(minus_label, (bpm_minus_rect.x + 12, bpm_minus_rect.y + 7))
        surface.blit(plus_label, (bpm_plus_rect.x + 12, bpm_plus_rect.y + 7))
        
        return {
            "grid_rect": pygame.Rect(x, y, grid_width, grid_height),
            "play_button": button_rect,
            "bpm_minus": bpm_minus_rect,
            "bpm_plus": bpm_plus_rect,
            "controls_height": grid_height + 50  # Höhe des gesamten Rhythmus-Bereichs inkl. Steuerelemente
        }

# Hauptprogramm
def main():
    generator = ToneGenerator(SAMPLE_RATE)
    rhythm = RhythmGenerator(generator)
    running = True
    clock = pygame.time.Clock()
    current_waveform = "sine"  # Standard-Wellenform
    volume = 0.5  # Standard-Lautstärke
    duration = 0.5  # Standard-Notendauer in Sekunden
    active_keys = set()  # Menge der aktuell gedrückten Tasten
    
    # UI-Elemente
    waveform_buttons = [
        {"rect": pygame.Rect(50, 50, 120, 40), "text": "Sine", "wave": "sine", "color": BLUE},
        {"rect": pygame.Rect(190, 50, 120, 40), "text": "Square", "wave": "square", "color": GREEN},
        {"rect": pygame.Rect(330, 50, 120, 40), "text": "Sawtooth", "wave": "sawtooth", "color": RED},
        {"rect": pygame.Rect(470, 50, 120, 40), "text": "Triangle", "wave": "triangle", "color": YELLOW}
    ]
    
    volume_rect = pygame.Rect(50, 120, 200, 20)
    
    font = pygame.font.SysFont(None, 36)
    
    # Rhythmus-UI-Elemente
    rhythm_controls = {}
    
    while running:
        window.fill(BLACK)
        
        # Ereignisschleife
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Tastendruck
            elif event.type == pygame.KEYDOWN:
                if event.key in KEY_TO_FREQUENCY and event.key not in active_keys:
                    active_keys.add(event.key)
                    freq = KEY_TO_FREQUENCY[event.key]
                    
                    # Auswahl der Wellenform
                    if current_waveform == "sine":
                        wave = generator.generate_sine_wave(freq, duration, volume)
                    elif current_waveform == "square":
                        wave = generator.generate_square_wave(freq, duration, volume)
                    elif current_waveform == "sawtooth":
                        wave = generator.generate_sawtooth_wave(freq, duration, volume)
                    elif current_waveform == "triangle":
                        wave = generator.generate_triangle_wave(freq, duration, volume)
                    
                    # Abspielen des Tons
                    sound = pygame.sndarray.make_sound(wave)
                    sound.play(-1)  # Endlosschleife
                    # Speichern des Sound-Objekts für später
                    active_keys.add((event.key, sound))
            
            # Tastenloslassen
            elif event.type == pygame.KEYUP:
                to_remove = []
                for k in active_keys:
                    if isinstance(k, tuple) and k[0] == event.key:
                        k[1].stop()  # Sound stoppen
                        to_remove.append(k)
                for item in to_remove:
                    active_keys.remove(item)
                if event.key in active_keys:
                    active_keys.remove(event.key)
            
            # Mausklick
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Wellenform-Buttons
                for button in waveform_buttons:
                    if button["rect"].collidepoint(mouse_pos):
                        current_waveform = button["wave"]
                
                # Lautstärkeregler
                if volume_rect.collidepoint(mouse_pos):
                    volume = (mouse_pos[0] - volume_rect.x) / volume_rect.width
                
                # Rhythmus-Controls
                if "grid_rect" in rhythm_controls:
                    grid_rect = rhythm_controls["grid_rect"]
                    if grid_rect.collidepoint(mouse_pos):
                        # Überprüfen, welche Zelle geklickt wurde
                        cell_x = (mouse_pos[0] - grid_rect.x) / (grid_rect.width / rhythm.max_beats)
                        cell_y = (mouse_pos[1] - grid_rect.y) / (grid_rect.height / 4)  # Angepasst für 4 Drum-Typen
                        
                        if 0 <= int(cell_x) < rhythm.max_beats and 0 <= int(cell_y) < 4:  # Angepasst für 4 Drum-Typen
                            drum_types = ["kick", "snare", "hihat", "clap"]  # Erweitert um das neue Instrument
                            rhythm.toggle_pattern_at(drum_types[int(cell_y)], int(cell_x))
                    
                    # Play/Stop-Button
                    if rhythm_controls["play_button"].collidepoint(mouse_pos):
                        rhythm.start_stop()
                    
                    # BPM-Buttons
                    if rhythm_controls["bpm_minus"].collidepoint(mouse_pos):
                        rhythm.set_bpm(rhythm.bpm - 5)
                    if rhythm_controls["bpm_plus"].collidepoint(mouse_pos):
                        rhythm.set_bpm(rhythm.bpm + 5)
            
        # UI zeichnen
        
        # Wellenform-Buttons
        for button in waveform_buttons:
            color = button["color"] if current_waveform == button["wave"] else GRAY
            pygame.draw.rect(window, color, button["rect"])
            text = font.render(button["text"], True, WHITE)
            text_rect = text.get_rect(center=button["rect"].center)
            window.blit(text, text_rect)
        
        # Lautstärkeregler
        pygame.draw.rect(window, GRAY, volume_rect)
        pygame.draw.rect(window, GREEN, (volume_rect.x, volume_rect.y, volume_rect.width * volume, volume_rect.height))
        volume_text = font.render(f"Volume: {int(volume * 100)}%", True, WHITE)
        window.blit(volume_text, (volume_rect.x + volume_rect.width + 20, volume_rect.y))
        
        # Rhythmus-Grid zeichnen
        rhythm_controls = rhythm.draw(window, 50, 160, 700, 120)
        
        # Rhythmus-Generator aktualisieren
        rhythm.update()
        
        # Tastatur zeichnen (unter dem Rhythmus-Grid)
        key_width = 40
        key_height = 120
        white_key_pos = 100
        black_key_pos = 85
        start_x = (WIDTH - (7 * key_width)) // 2
        start_y = 160 + rhythm_controls["controls_height"] + 20  # Position unter dem Rhythmus-Grid
        
        white_keys = [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_g, pygame.K_h, pygame.K_j, pygame.K_k]
        black_keys = [pygame.K_w, pygame.K_e, pygame.K_t, pygame.K_z, pygame.K_u]
        black_key_positions = [0, 1, 3, 4, 5]  # Positionen der schwarzen Tasten relativ zu den weißen
        
        # Weiße Tasten
        for i, key in enumerate(white_keys):
            color = BLUE if key in active_keys else WHITE
            pygame.draw.rect(window, color, (start_x + i * key_width, start_y, key_width, key_height))
            key_text = font.render(pygame.key.name(key), True, BLACK)
            window.blit(key_text, (start_x + i * key_width + 10, start_y + 80))
        
        # Schwarze Tasten
        for i, pos in enumerate(black_key_positions):
            if i < len(black_keys):
                key = black_keys[i]
                color = BLUE if key in active_keys else BLACK
                pygame.draw.rect(window, color, (start_x + pos * key_width + key_width // 2, start_y, key_width // 2, key_height // 1.5))
                key_text = font.render(pygame.key.name(key), True, WHITE)
                window.blit(key_text, (start_x + pos * key_width + key_width // 2 + 5, start_y + 30))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    try:
        main()
    finally:
        pygame.quit()