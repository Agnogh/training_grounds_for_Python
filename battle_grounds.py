""" this should be low version of turn based gaem with elements of RPG"""

import random

""" creating player character"""
player_character = {
    1: {"class": "Guard", "hp": 5, "armor": 1, "damage": (0, 5),
        "special": None},
    2: {"class": "Rogue", "hp": 4, "armor": 0, "damage": (1, 2),
        "special": "poison"},
    3: {"class": "Knight", "hp": 6, "armor": 2, "shield": 1, "damage": (2, 5),
        "special": None},
    4: {"class": "Paladin", "hp": 6, "armor": 2, "damage": (3, 4),
        "special": "heal"},
    5: {"class": "Prisoner", "hp": 7, "armor": 0, "damage": (0, 5),
        "special": "double_damage"},
    6: {"class": "Mage", "hp": 5, "armor": 0, "damage": (4, 6),
        "special": "fire"},
}

""" creating enemy characters"""
monster_characters = [
    {"class": "Vampire", "hp": 6, "armor": 0, "damage": (2, 4),
     "special": "lifesteal"},
    {"class": "Skeleton Warrior", "hp": 6, "armor": 2, "damage": (4, 5),
     "special": None},
    {"class": "Wraith", "hp": 5, "armor": 0, "damage": (3, 4),
     "special": "reflect"},
    {"class": "Werewolf", "hp": 8, "armor": 1, "damage": (5, 6),
     "special": None},
]


def display_characters():
    print("\nAvailable warriors of light: ")
    for key, value in player_character.items():
        # spec = value.get('special', 'None')
        # shield = value.get('shield', 0)
        # total_armor = value.get('armor', 0) + shield
        print(
            f"{key}: {value['class']} - HP: {value['hp']}, \n"
            f"Armor: {value.get('armor', 0)}, Damage: {value['damage']}")


def select_character():
    while True:
        display_characters()
        choice = input("\nEnter (1-X) to select character or 0 to view: ")
        if choice == "0":
            continue
        elif choice in [str(i) for i in range(1, 5)]:
            char_id = int(choice)
            return player_character[char_id].copy()
        else:
            print("Invalid input. Try again.")


""" function for randomly selecting enemy mosters"""


def random_enemy():
    return random.choice(monster_characters).copy()


""" function for calculated damange"""


def calculate_damage(damage_range, multiplier=1):
    return random.randint(*damage_range) * multiplier


""" function for combat announacement + disengagge mid combat + description """


def battle(player, enemy):
    print(f"\nBattle begins! {player['class']} vs {enemy['class']}!")

    while player["hp"] > 0 and enemy["hp"] > 0:
        action = input("\nType 'run' to flee, otheriwise type anything like\n"
                       "'die undead beast' for your hero to keep attacking \n"
                       "and battle continuing: ").lower()
        if action == "run":
            print("You ran and live to fight another day!")
            return


""" PLazer character attack phase """

""" Enemy Attack Phase """

""" trying out the main function """


while True:
    print("\n--- SELECT YOUR WARRIOR OF LIGT---")
    player = select_character()
    enemy = random_enemy()

    print(f"\nRandomly selected enemz is : {enemy['class']}")
    battle(player, enemy)

    base_damage = calculate_damage(player["damage"])
    total_damage = base_damage

    enemy_damage = calculate_damage(enemy["damage"])
    player_armor = player.get("armor", 0) + player.get("shield", 0)
    damage_received = max(enemy_damage - player_armor, 0)
    player["hp"] -= damage_received
