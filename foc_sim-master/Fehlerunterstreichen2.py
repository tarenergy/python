import random

def check_errors(sentence, mistakes, user_input):
    """
    Überprüft, ob der Nutzer die Fehler richtig korrigiert hat.
    """
    correct = mistakes
    user_words = user_input.split()
    
    if correct == user_words:
        return True, "Richtig! Alle Fehler wurden korrekt korrigiert."
    else:
        feedback = "Falsch! "
        if len(user_words) < len(correct):
            feedback += f"Fehlende Korrekturen: {', '.join(correct[len(user_words):])}. "
        if len(user_words) > len(correct):
            feedback += f"Zu viele Korrekturen: {', '.join(user_words[len(correct):])}. "
        return False, feedback


def play_game():
    """
    Startet das Spiel "Fehler korrigieren".
    """
    sentences = [
        ("Die Katze sprigt über den Zaun.", ["springt"]),
        ("Er hatt gestern ein Buch gelesen.", ["hat"]),
        ("Das Kind spield im Garten.", ["spielt"]),
        ("Sie färt morgen nach Hamburg.", ["fährt"]),
        ("Wir haben gestern gehn ins Kino.", ["sind gegangen"]),
        ("Das Wetter ist sehr schlect heute.", ["schlecht"]),
        ("Ich müss meine Hausaufgaben machen.", ["muss"]),
        ("Der Hund belltt laut im Garten.", ["bellt"]),
        ("Sie möch ein Eis essen.", ["möchte"]),
        ("Mein Vater arbietet bei einer großen Firma.", ["arbeitet"]),
        ("Gestern habe ich eine Apffel gegessen.", ["Apfel"]),
        ("Das Haus ist sehr groß unt schön.", ["und"]),
        ("Der Zug ist sehr schenll.", ["schnell"]),
        ("Sie geht gerne schimmen.", ["schwimmen"]),
        ("Ich kan gut Deutsch sprechen.", ["kann"]),
        ("Heute ist ein regnericher Tag.", ["regnerischer"]),
        ("Die Blummen im Garten sind schön.", ["Blumen"]),
        ("Er ist sehr intiligent.", ["intelligent"]),
        ("Wir haben eine neuen Lehrer.", ["einen"]),
        ("Das Kind ist sehr freuntlich.", ["freundlich"]),
        ("Die Katze ist weiß und fleckig.", ["weiß"]),
        ("Ich esse gerne Banannen.", ["Bananen"]),
        ("Mein Freund fiert nächste Woche Geburtstag.", ["feiert"]),
        ("Die Sonne schind heute sehr hell.", ["scheint"]),
        ("Das Wetter ist zimlich warm.", ["ziemlich"]),
        ("Wir gehen heute zum Staddpark.", ["Stadtpark"]),
        ("Mein Bruder spielt gerne mit seiner Freudin.", ["Freundin"]),
        ("Ich trage eine blaue Jace.", ["Jacke"]),
        ("Er schreibt einen lange Brief.", ["langen"]),
        ("Sie mag keine roten Äpffel.", ["Äpfel"]),
        ("Wir essen gerne Tommaten.", ["Tomaten"]),
        ("Mein Vater fährt ein neuses Auto.", ["neues"]),
        ("Das Mädchen hat ein schöne Stimme.", ["eine"]),
        ("Er kan sehr gut Gittare spielen.", ["kann", "Gitarre"]),
        ("Wir treffen uns am Bahnof.", ["Bahnhof"]),
        ("Der Junge schreibt mit eine Bleistift.", ["einem"]),
        ("Die Blätter sind gelb un orange.", ["und"]),
        ("Ich habe eine neue Schue.", ["Schuhe"]),
        ("Sie trinkt gerne Orangesafft.", ["Orangensaft"]),
        ("Der Tisch ist sehr stabiel.", ["stabil"]),
        ("Er hat einen neuen Ruckzak gekauft.", ["Rucksack"]),
        ("Sie wohnt in eine schönen Haus.", ["einem"]),
        ("Der Hund hat braune Auggen.", ["Augen"]),
        ("Das Wasser ist sehr klaahr.", ["klar"]),
        ("Ich habe einen klenen Bruder.", ["kleinen"]),
        ("Mein Liebingstier ist eine Ente.",["Lieblingstier"]),
        ("Papa ist fech.",["frech"]),
        ("Sie trägt einen roten Schall.", ["Schal"]),
        ("Wir fahren morgen nach Berliin.", ["Berlin"]),
        ("Er liest gerne Detektifromane.", ["Detektivromane"]),
        ("Ich mag keine spinaten Suppe.", ["Spinat"])
    ]
    
    score = 0
    print("Willkommen zum Spiel 'Fehler korrigieren'!")
    print("Gib die korrigierten Wörter nacheinander ein, getrennt durch Leerzeichen.")
    print("Lass richtige Wörter unverändert.")
    print("\n")
    
    random.shuffle(sentences)
    for i, (sentence, mistakes) in enumerate(sentences[:10], 1):
        print(f"Satz {i}: {sentence}")
        user_input = input("Deine Korrekturen: ")
        correct, message = check_errors(sentence, mistakes, user_input)
        print(message)
        if correct:
            score += 1
        print("\n")
    
    print(f"Spiel beendet! Dein Score: {score}/{10}")
    
if __name__ == "__main__":
    play_game()