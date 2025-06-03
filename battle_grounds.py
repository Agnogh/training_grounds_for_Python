""" this should be low version of turn based gaem with elements of RPG"""

""" creating player character"""
player_character = {
    1: {"class": "Guard", "hp": 5, "armour": 1, "damage": (0, 5)},
}

""" creating enemy characters"""
monster_charcters = {
    1: {"class": "Vampire", "hp": 6, "armour": 0, "damage": (2, 4)},
}

def display_characters():
    print("\nAvailable warriors of light: ")
    for key, value in characters.items():
        shield = value.get('shield', 0)
        armour = value.get('armour', 0)


print(f"{key}: {value['class']} - HP: {value['hp']}, Armor: {value.get('armor', 0)}, Damage: {value['damage']}")
