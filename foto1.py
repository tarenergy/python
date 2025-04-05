import cv2
import pygame
import numpy as np

# Pygame initialisieren
pygame.init()

# Bildschirmgröße
WIDTH, HEIGHT = 640, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Foto aufnehmen")

# Kamera initialisieren
cap = cv2.VideoCapture(0)
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

captured_image = None
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                # Bild aufnehmen
                ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    captured_image = pygame.surfarray.make_surface(np.rot90(frame))
            elif event.key == pygame.K_l:
                # Bild löschen
                captured_image = None
    
    screen.fill((0, 0, 0))
    if captured_image:
        screen.blit(captured_image, (0, 0))
    pygame.display.flip()

cap.release()
pygame.quit()
