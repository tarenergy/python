import pygame
import numpy as np
import pygame.sndarray
from pygame import mixer

# Initialisierung
pygame.init()
mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
clock = pygame.time.Clock()

# Fenstergröße
WIDTH, HEIGHT = 1050, 300
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Kinderklavier (3 Oktaven)")

# Farben
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)

# Tastatur-Layout
NUM_WHITE_KEYS = 21  # 3 Oktaven (7 weiße Tasten pro Oktave)
WHITE_KEY_WIDTH = WIDTH // NUM_WHITE_KEYS
WHITE_KEY_HEIGHT = HEIGHT * 4 // 5
BLACK_KEY_WIDTH = WHITE_KEY_WIDTH // 2
BLACK_KEY_HEIGHT = WHITE_KEY_HEIGHT // 2

# Noten für drei Oktaven (C3 bis B5)
NOTES = [
    'C3', 'C#3', 'D3', 'D#3', 'E3', 'F3', 'F#3', 'G3', 'G#3', 'A3', 'A#3', 'B3',
    'C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4', 'A#4', 'B4',
    'C5', 'C#5', 'D5', 'D#5', 'E5', 'F5', 'F#5', 'G5', 'G#5', 'A5', 'A#5', 'B5'
]

# Layout für weiße Tasten
WHITE_NOTES = ['C3', 'D3', 'E3', 'F3', 'G3', 'A3', 'B3', 
               'C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 
               'C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5']

# Wohltemperierte Stimmung: Frequenz = Basisfrequenz * 2^(n/12)
def get_frequency(note):
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    note_name = note[:-1]
    octave = int(note[-1])
    
    # A4 als Referenz (440 Hz)
    a4_index = 9
    a4_octave = 4
    a4_freq = 440.0
    
    note_index = notes.index(note_name)
    semitones_from_a4 = (octave - a4_octave) * 12 + (note_index - a4_index)
    
    return a4_freq * (2 ** (semitones_from_a4 / 12))

# Klavier-Tasten erstellen
def create_piano_keys():
    white_keys = []
    black_keys = []
    
    white_index = 0
    for i, note in enumerate(NOTES):
        if '#' not in note:  # Weiße Taste
            x = white_index * WHITE_KEY_WIDTH
            white_keys.append({
                'rect': pygame.Rect(x, 0, WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT),
                'note': note,
                'active': False,
                'label': note[0] + note[-1],
                'frequency': get_frequency(note)
            })
            white_index += 1
        else:  # Schwarze Taste
            prev_white_key = white_keys[-1]
            x = prev_white_key['rect'].x + (WHITE_KEY_WIDTH * 3 // 4) - (BLACK_KEY_WIDTH // 2)
            black_keys.append({
                'rect': pygame.Rect(x, 0, BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT),
                'note': note,
                'active': False,
                'label': note[:2] + note[-1],
                'frequency': get_frequency(note)
            })
    
    return white_keys, black_keys

# Verbesserte Audioerzeugung mit direkter Akkordüberlagerung
class AudioEngine:
    def __init__(self):
        self.sample_rate = 44100
        self.active_notes = {}
        
        # Pre-generieren aller Töne für bessere Performance
        self.sounds = {}
        for note in NOTES:
            self.sounds[note] = self.generate_sound(get_frequency(note))
    
    def generate_sound(self, frequency):
        # Tonlänge: 2 Sekunden (für komplettes Abklingen)
        duration = 4.0
        
        # Zeitvektor
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        
        # Verbesserte Wellenform für reichhaltigeren Klang
        # Grundton mit abklingender Amplitude
        amplitude = np.exp(-0.5 * t)
        wave = 0.6 * amplitude * np.sin(2 * np.pi * frequency * t)
        
        # Obertöne mit angepassten Amplituden für natürlicheren Klang
        wave += 0.3 * amplitude * np.sin(2 * np.pi * frequency * 2 * t)  # 1. Oberton
        wave += 0.3 * amplitude * np.sin(2 * np.pi * frequency * 3 * t)  # 2. Oberton
        wave += 0.3 * amplitude * np.sin(2 * np.pi * frequency * 4 * t)  # 3. Oberton
        
        # Attack-Decay-Sustain-Release Hüllkurve
        attack_time = 0.01  # 10ms
        decay_time = 5.0   # 100ms
        release_time = 5.0  # 300ms
        
        # Attack-Phase
        attack_samples = int(attack_time * self.sample_rate)
        if attack_samples > 0:
            attack_envelope = np.linspace(0, 1, attack_samples)
            wave[:attack_samples] *= attack_envelope
        
        # Release-Phase
        release_samples = int(release_time * self.sample_rate)
        if release_samples > 0 and len(wave) > release_samples:
            release_envelope = np.linspace(1, 0, release_samples)
            wave[-release_samples:] *= release_envelope
            
        # Normalisieren und in 16-bit konvertieren
        wave = wave / np.max(np.abs(wave)) * 0.9  # Leichte Reduzierung zur Vermeidung von Clipping
        wave_int = (wave * 32767).astype(np.int16)
        
        # Stereo-Sound (identisch für beide Kanäle)
        stereo_wave = np.column_stack((wave_int, wave_int))
        
        # Sound-Objekt erstellen
        sound = pygame.sndarray.make_sound(stereo_wave)
        return sound
        
    def play_note(self, note):
        if note in self.active_notes:
            return  # Ton wird bereits gespielt
        
        # Sound abrufen und abspielen
        sound = self.sounds[note]
        channel = pygame.mixer.find_channel(True)  # Einen freien Kanal finden
        
        if channel:
            channel.play(sound)  # Ohne Loops, spielt nur einmal
            self.active_notes[note] = {'channel': channel, 'sound': sound}
    
    def stop_note(self, note):
        if note in self.active_notes:
            self.active_notes[note]['channel'].stop()
            del self.active_notes[note]
    
    def is_playing(self, note):
        # Prüfen, ob der Ton noch aktiv ist
        if note in self.active_notes:
            if not self.active_notes[note]['channel'].get_busy():
                # Ton ist fertig abgespielt, aus der Liste entfernen
                del self.active_notes[note]
                return False
            return True
        return False

# Hauptprogramm
def main():
    running = True
    white_keys, black_keys = create_piano_keys()
    audio_engine = AudioEngine()
    
    small_font = pygame.font.Font(None, 20)
    regular_font = pygame.font.Font(None, 24)
    
    # Mausstatus
    mouse_pressed = False
    
    while running:
        screen.fill((240, 240, 240))
        
        # Status der Tasten aktualisieren (falls Ton abgelaufen)
        for key in white_keys + black_keys:
            if key['active'] and not audio_engine.is_playing(key['note']):
                key['active'] = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pressed = True
            
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_pressed = False
        
        # Wenn Maus gedrückt ist, Ton spielen
        if mouse_pressed:
            mouse_pos = pygame.mouse.get_pos()
            
            # Zuerst schwarze Tasten prüfen
            key_found = False
            for key in black_keys:
                if key['rect'].collidepoint(mouse_pos):
                    key_found = True
                    if not key['active']:
                        key['active'] = True
                        audio_engine.play_note(key['note'])
            
            # Wenn keine schwarze Taste gefunden wurde, weiße Tasten prüfen
            if not key_found:
                for key in white_keys:
                    if key['rect'].collidepoint(mouse_pos):
                        if not key['active']:
                            key['active'] = True
                            audio_engine.play_note(key['note'])
        
        # Weiße Tasten zeichnen
        for key in white_keys:
            color = GRAY if key['active'] else WHITE
            pygame.draw.rect(screen, color, key['rect'])
            pygame.draw.rect(screen, BLACK, key['rect'], 1)  # Rahmen
            
            # Beschriftung mit Oktave
            font = small_font if int(key['note'][-1]) == 3 else regular_font
            text = font.render(key['label'], True, BLACK)
            text_rect = text.get_rect(center=(key['rect'].x + WHITE_KEY_WIDTH//2, 
                                             key['rect'].y + WHITE_KEY_HEIGHT - 30))
            screen.blit(text, text_rect)
        
        # Schwarze Tasten zeichnen
        for key in black_keys:
            color = GRAY if key['active'] else BLACK
            pygame.draw.rect(screen, color, key['rect'])
            
            # Beschriftung für schwarze Tasten
            font = pygame.font.Font(None, 16)
            text = font.render(key['label'][:2], True, WHITE if not key['active'] else LIGHT_GRAY)
            text_rect = text.get_rect(center=(key['rect'].x + BLACK_KEY_WIDTH//2, 
                                             key['rect'].y + BLACK_KEY_HEIGHT - 20))
            screen.blit(text, text_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    # Vor dem Beenden alle aktiven Töne stoppen
    for note in list(audio_engine.active_notes.keys()):
        audio_engine.stop_note(note)
    
    pygame.quit()

if __name__ == "__main__":
    main()