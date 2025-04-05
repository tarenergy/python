import cv2

def main():
    # Kamera öffnen (Index 0 ist die Standardkamera)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Fehler: Kamera konnte nicht geöffnet werden.")
        return
    
    while True:
        # Einzelnes Frame einlesen
        ret, frame = cap.read()
        if not ret:
            print("Fehler beim Lesen des Frames.")
            break
        
        # Frame im Fenster anzeigen
        cv2.imshow("Kamera-Stream", frame)
        
        # Beenden mit der Taste 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Kamera freigeben und Fenster schließen
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
