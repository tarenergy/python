import pygame
import numpy as np
import math
from pygame import mixer

# Initialisierung
pygame.init()
mixer.init(frequency=44100, size=-16, channels=2)
clock = pygame.time.Clock()

# Fenstergröße
WIDTH, HEIGHT = 1050, 300  # Breiter für zusätzliche Oktave
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

# Layout für weiße Tasten (einfacher zu lesen ohne die schwarzen Halbtöne)
WHITE_NOTES = ['C3', 'D3', 'E3', 'F3', 'G3', 'A3', 'B3', 
               'C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4', 
               'C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5']

# Wohltemperierte Stimmung: Frequenz = Basisfrequenz * 2^(n/12)
# Basisfrequenz ist A4 = 440 Hz (Standard-Stimmung)
def get_frequency(note):
    # Noten-Indizes (A4 ist der Ausgangspunkt mit 440 Hz)
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # Notennamen und Oktave trennen
    note_name = note[:-1]
    octave = int(note[-1])
    
    # A4 als Referenz (Index 9 in Oktave 4)
    a4_index = 9
    a4_octave = 4
    a4_freq = 440.0
    
    # Berechne Halbtonabstand zu A4
    note_index = notes.index(note_name)
    semitones_from_a4 = (octave - a4_octave) * 12 + (note_index - a4_index)
    
    # Berechne Frequenz: f = f_ref * 2^(n/12)
    return a4_freq * (2 ** (semitones_from_a4 / 12))

# Töne generieren
def generate_tone(frequency, duration=10.0, sample_rate=44100):
    # Sinus-Welle mit abgerundeten Kanten für sanfteren Klang
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Grundton
    tone = 0.7 * np.sin(2 * np.pi * frequency * t)
    
    # Obertöne hinzufügen für einen reicheren Klang
    #tone += 0.2 * np.sin(2 * np.pi * frequency * 2 * t)  # Erste Obertöne
    #tone += 0.1 * np.sin(2 * np.pi * frequency * 3 * t)  # Zweite Obertöne
    
    # Anstiegs- und Abklingzeit
    fade_samples = int(sample_rate * 0.001)  # 100ms fade
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    
    # Fade-in und Fade-out anwenden
    if len(tone) > 2 * fade_samples:
        tone[:fade_samples] *= fade_in
        tone[-fade_samples:] *= fade_out
    
    # Normalisieren auf [-1, 1]
    tone = tone / np.max(np.abs(tone))
    
    # Konvertieren in 16-bit
    return (tone * 32767).astype(np.int16)

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
                'label': note[0] + note[-1],  # Notenbuchstabe mit Oktave (z.B. C3)
                'sound': None
            })
            white_index += 1
        else:  # Schwarze Taste
            # Position berechnen (zwischen zwei weißen Tasten)
            prev_white_key = white_keys[-1]
            x = prev_white_key['rect'].x + (WHITE_KEY_WIDTH * 3 // 4) - (BLACK_KEY_WIDTH // 2)
            black_keys.append({
                'rect': pygame.Rect(x, 0, BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT),
                'note': note,
                'active': False,
                'label': note[:2] + note[-1],  # Notenbuchstabe mit # und Oktave
                'sound': None
            })
    
    return white_keys, black_keys

# Mischen von Tönen, die gleichzeitig gespielt werden
class ToneManager:
    def __init__(self):
        self.playing_tones = {}
        self.sample_rate = 44100
        
    def play_tone(self, note):
        frequency = get_frequency(note)
        
        # Wenn Ton bereits spielt, nicht neu starten
        if note in self.playing_tones:
            return
        
        # Ton generieren
        tone_data = generate_tone(frequency, duration=1.0, sample_rate=self.sample_rate)
        
        # Sound-Objekt erstellen
        sound = pygame.mixer.Sound(tone_data)
        
        # Endlosschleife
        sound.play(loops=-1)
        
        # Ton speichern
        self.playing_tones[note] = sound
        
    def stop_tone(self, note):
        if note in self.playing_tones:
            self.playing_tones[note].stop()
            del self.playing_tones[note]
    
    def is_playing(self, note):
        return note in self.playing_tones

# Hauptprogramm
def main():
    running = True
    white_keys, black_keys = create_piano_keys()
    tone_manager = ToneManager()
    
    # Kleiner Font für die dritte Oktave wegen engerer Tasten
    small_font = pygame.font.Font(None, 20)
    regular_font = pygame.font.Font(None, 24)
    
    while running:
        screen.fill((240, 240, 240))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Zuerst schwarze Tasten prüfen (da sie oben liegen)
                key_found = False
                for key in black_keys:
                    if key['rect'].collidepoint(mouse_pos):
                        key_found = True
                        key['active'] = not key['active']
                        
                        if key['active']:
                            tone_manager.play_tone(key['note'])
                        else:
                            tone_manager.stop_tone(key['note'])
                            
                # Wenn keine schwarze Taste gefunden wurde, weiße Tasten prüfen
                if not key_found:
                    for key in white_keys:
                        if key['rect'].collidepoint(mouse_pos):
                            key['active'] = not key['active']
                            
                            if key['active']:
                                tone_manager.play_tone(key['note'])
                            else:
                                tone_manager.stop_tone(key['note'])
        
        # Weiße Tasten zeichnen
        for key in white_keys:
            color = GRAY if key['active'] else WHITE
            pygame.draw.rect(screen, color, key['rect'])
            pygame.draw.rect(screen, BLACK, key['rect'], 1)  # Rahmen
            
            # Beschriftung mit Oktave
            # Kleinere Schrift für schmalere Tasten
            font = small_font if int(key['note'][-1]) == 3 else regular_font
            text = font.render(key['label'], True, BLACK)
            text_rect = text.get_rect(center=(key['rect'].x + WHITE_KEY_WIDTH//2, 
                                             key['rect'].y + WHITE_KEY_HEIGHT - 30))
            screen.blit(text, text_rect)
        
        # Schwarze Tasten zeichnen (über den weißen)
        for key in black_keys:
            color = GRAY if key['active'] else BLACK
            pygame.draw.rect(screen, color, key['rect'])
            
            # Beschriftung für schwarze Tasten (in Weiß)
            # Kleinere Schrift für schmalere Tasten
            font = pygame.font.Font(None, 16)
            text = font.render(key['label'][:2], True, WHITE if not key['active'] else LIGHT_GRAY)
            text_rect = text.get_rect(center=(key['rect'].x + BLACK_KEY_WIDTH//2, 
                                             key['rect'].y + BLACK_KEY_HEIGHT - 20))
            screen.blit(text, text_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()