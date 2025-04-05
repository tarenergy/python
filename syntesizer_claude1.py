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
WIDTH, HEIGHT = 800, 400
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Synthesizer")

# Farben
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Klasse für die Erzeugung von Wellenformen
class ToneGenerator:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
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

# Die Tastenbelegung für den Synthesizer (QWERTY-Layout)
KEY_TO_FREQUENCY = {
    pygame.K_a: 261.63,  # C4
    pygame.K_w: 277.18,  # C#4
    pygame.K_s: 293.66,  # D4
    pygame.K_e: 311.13,  # D#4
    pygame.K_d: 329.63,  # E4
    pygame.K_f: 349.23,  # F4
    pygame.K_t: 369.99,  # F#4
    pygame.K_g: 392.00,  # G4
    pygame.K_y: 415.30,  # G#4
    pygame.K_h: 440.00,  # A4
    pygame.K_u: 466.16,  # A#4
    pygame.K_j: 493.88,  # B4
    pygame.K_k: 523.25,  # C5
}

# Hauptprogramm
def main():
    generator = ToneGenerator(SAMPLE_RATE)
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
        
        # Tastatur zeichnen
        key_width = 40
        key_height = 120
        white_key_pos = 100
        black_key_pos = 85
        start_x = (WIDTH - (7 * key_width)) // 2
        
        white_keys = [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_g, pygame.K_h, pygame.K_j, pygame.K_k]
        black_keys = [pygame.K_w, pygame.K_e, pygame.K_t, pygame.K_y, pygame.K_u]
        black_key_positions = [0, 1, 3, 4, 5]  # Positionen der schwarzen Tasten relativ zu den weißen
        
        # Weiße Tasten
        for i, key in enumerate(white_keys):
            color = BLUE if key in active_keys else WHITE
            pygame.draw.rect(window, color, (start_x + i * key_width, 200, key_width, key_height))
            key_text = font.render(pygame.key.name(key), True, BLACK)
            window.blit(key_text, (start_x + i * key_width + 10, 280))
        
        # Schwarze Tasten
        for i, pos in enumerate(black_key_positions):
            if i < len(black_keys):
                key = black_keys[i]
                color = BLUE if key in active_keys else BLACK
                pygame.draw.rect(window, color, (start_x + pos * key_width + key_width // 2, 200, key_width // 2, key_height // 1.5))
                key_text = font.render(pygame.key.name(key), True, WHITE)
                window.blit(key_text, (start_x + pos * key_width + key_width // 2 + 5, 230))
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    try:
        main()
    finally:
        pygame.quit()