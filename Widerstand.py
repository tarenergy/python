def get_color_code(value):
    color_map = {
        0: "schwarz", 1: "braun", 2: "rot", 3: "orange", 4: "gelb",
        5: "grün", 6: "blau", 7: "violett", 8: "grau", 9: "weiß"
    }
    
    if value < 10 or value > 99_000_000:
        return "Wert außerhalb des Bereichs für Standard-Widerstandsfarbcode."
    
    digits = []
    multiplier = 0
    
    while value >= 100:
        value //= 10
        multiplier += 1
    
    digits.append(value // 10)  # erste Ziffer
    digits.append(value % 10)   # zweite Ziffer
    
    color_code = [color_map[digits[0]], color_map[digits[1]], color_map[multiplier]]
    
    return " - ".join(color_code)

if __name__ == "__main__":
    try:
        resistance = int(input("Geben Sie den Widerstandswert in Ohm ein: "))
        print("Farbcode: ", get_color_code(resistance))
    except ValueError:
        print("Bitte eine gültige ganze Zahl eingeben.")
