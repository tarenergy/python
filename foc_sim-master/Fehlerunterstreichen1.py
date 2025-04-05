import re

def check_errors(text, mistakes, user_input):
    """
    Überprüft, ob der Nutzer die richtigen Fehler unterstrichen hat.
    """
    correct = set(mistakes)
    user_selected = set(re.findall(r'\*\*(.*?)\*\*', user_input))
    
    if correct == user_selected:
        return True, "Richtig! Alle Fehler wurden korrekt markiert."
    else:
        missing = correct - user_selected
        extra = user_selected - correct
        feedback = "Falsch! "
        if missing:
            feedback += f"Fehlende Fehler: {', '.join(missing)}. "
        if extra:
            feedback += f"Zu viele Markierungen: {', '.join(extra)}. "
        return False, feedback


def play_game():
    """
    Startet das Spiel "Fehler unterstreichen".
    """
    sentences = [
        ("Die Katze **sprigt** über den Zaun.", ["sprigt"]),
        ("Er hatt **gestern** ein Buch gelesen.", ["hatt"]),
        ("Sie **fährt** morgen nach Hamburg.", []),
        ("Das **Kind spield** im Garten.", ["spield"])
    ]
    
    score = 0
    print("Willkommen zum Spiel 'Fehler unterstreichen'!")
    print("Markiere die fehlerhaften Wörter mit ** vor und nach dem Wort.")
    print("Beispiel: Die Katze **sprigt** über den Zaun.")
    print("Lass richtige Wörter unverändert.")
    print("\n")
    
    for i, (sentence, mistakes) in enumerate(sentences, 1):
        print(f"Satz {i}: {sentence.replace('**', '')}")
        user_input = input("Deine Markierung: ")
        correct, message = check_errors(sentence, mistakes, user_input)
        print(message)
        if correct:
            score += 1
        print("\n")
    
    print(f"Spiel beendet! Dein Score: {score}/{len(sentences)}")
    
if __name__ == "__main__":
    play_game()
