""" this should be low version of turn based gaem with elements of RPG"""

import random

""" creating player character"""
player_character = {
    1: {"class": "Guard", "hp": 5, "armor": 1, "damage": (0, 5)},
    2: {"class": "Rogue", "hp": 4, "armor": 0, "damage": (1, 2)},
}

""" creating enemy characters"""
monster_characters = {
    1: {"class": "Vampire", "hp": 6, "armor": 0, "damage": (2, 4)},
}


def display_characters():
    print("\nAvailable warriors of light: ")
    for key, value in player_character.items():
        shield = value.get('shield', 0)
        total_armor = value.get('armor', 0)
        print(
            f"{key}: {value['class']} - HP: {value['hp']}, \n"
            f"Armor: {value.get('armor', 0)}, Damage: {value['damage']}")


def select_character():
    while True:
        display_characters()
        choice = input("\nEnter number (1) to select character or 0 to view: ")
        if choice == "0":
            continue
        elif choice in [str(i) for i in range(1, 3)]:
            char_id = int(choice)
            return player_character[char_id].copy()
        else:
            print("Invalid input. Try again.")


""" function for randomly selecting enemy mosters"""


def random_enemy():
    return random.choice(monster_characters).copy()


""" trying out the main function """


while True:
    print("\n--- SELECT YOUR WARRIOR OF LIGT---")
    player = select_character()
    enemy = random_enemy()
    print(f"\nRandom enemy selected: {enemy['class']}")
