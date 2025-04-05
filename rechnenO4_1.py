import random

def generate_problem():
    """Erzeugt eine zufällige Rechenaufgabe mit zwei Zahlen kleiner 100."""
    num1 = random.randint(1, 99)
    num2 = random.randint(1, 99)
    operation = random.choice(['+', '-', '*'])
    
    if operation == '+':
        correct_answer = num1 + num2
    elif operation == '-':
        correct_answer = num1 - num2
    else:  # Multiplication
        correct_answer = num1 * num2
    
    return num1, operation, num2, correct_answer

def math_game():
    """Startet das Mathe-Lernspiel."""
    score = 0
    wrong_streak = 0
    
    print("Willkommen zum Mathe-Lernspiel!")
    
    while True:
        num1, operation, num2, correct_answer = generate_problem()
        
        try:
            user_answer = int(input(f"Was ist {num1} {operation} {num2}? "))
        except ValueError:
            print("Bitte eine gültige Zahl eingeben!")
            continue
        
        if user_answer == correct_answer:
            print("Richtig!")
            score += 1
            wrong_streak = 0  # Reset bei richtiger Antwort
        else:
            print(f"Falsch! Die richtige Antwort wäre {correct_answer} gewesen.")
            wrong_streak += 1
        
        if wrong_streak >= 3:
            print("Drei falsche Antworten hintereinander. Spiel verloren!")
            break
        
        print(f"Punkte: {score}\n")

    print(f"Spiel beendet! Dein Endstand: {score} Punkte")

if __name__ == "__main__":
    math_game()
