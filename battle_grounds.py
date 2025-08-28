import random
import gspread
from google.oauth2.service_account import Credentials

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
    ]

CREDS = Credentials.from_service_account_file('pythonbattlefield-34d11d65bfdc.json')
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open('python_battlefield')

print([ws.title for ws in SHEET.worksheets()])

""" this should be low version of turn based gaem with elements of RPG"""

""" creating player character"""

player_character = {
    1: {"class": "Guard", "hp": 5, "armor": 1, "damage": (0, 5),
        "special": None},
    2: {"class": "Rogue", "hp": 4, "armor": 0, "damage": (1, 2),
        "special": "Poison"},
    3: {"class": "Knight", "hp": 6, "armor": 2, "shield": 1, "damage": (2, 5),
        "special": None},
    4: {"class": "Paladin", "hp": 6, "armor": 2, "damage": (3, 4),
        "special": "Heal"},
    5: {"class": "Prisoner", "hp": 7, "armor": 0, "damage": (0, 5),
        "special": "Double damage"},
    6: {"class": "Mage", "hp": 5, "armor": 0, "damage": (4, 6),
        "special": "Fire"},
}

""" creating enemy characters"""

monster_characters = [
    {"class": "Vampire", "hp": 6, "armor": 0, "damage": (2, 4),
     "special": "Lifesteal"},
    {"class": "Skeleton Warrior", "hp": 6, "armor": 2, "damage": (4, 5),
     "special": None},
    {"class": "Wraith", "hp": 5, "armor": 0, "damage": (3, 4),
     "special": "Reflect"},
    {"class": "Werewolf", "hp": 8, "armor": 1, "damage": (5, 6),
     "special": None},
]


def display_characters():
    print("\nAvailable warriors of light: ")
    for key, value in player_character.items():
        spec = value.get('special', 'None')
        shield = value.get('shield', 0)
        total_armor = value.get('armor', 0) + shield
        print(
            f"{key}: {value['class']} - HP: {value['hp']}, \n"
            f"Armor: {value.get('armor', 0)} (+ {shield}"
            f" shield = {total_armor}),"
            f"Damage: {value['damage']},"
            f"Special: {spec}")


def select_character():
    while True:
        display_characters()
        choice = input("\nEnter (1-7) to select character or 0 to view: ")
        if choice == "0":
            continue
        elif choice in [str(i) for i in range(1, 7)]:
            char_id = int(choice)
            return player_character[char_id].copy()
        else:
            print("Invalid input. Pick between offered selection.")


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
        """ Player character attack phase """
        base_damage = calculate_damage(player["damage"])
        special_text = ""
        total_damage = base_damage
        """ defining special atatcks """
        if player.get("special") == "Double damage":
            total_damage = base_damage * 2
        elif player.get("special") == "Poison":  # "poison" also "2x DMG"
            poison_damage = 1  # Applies after innital attack
            total_damage = base_damage * 2
        elif player.get("special") == "Fire":
            fire_damage = 1  # Ignores armor
        else:
            poison_damage = fire_damage = 0

        armor_block = enemy.get("armor", 0)
        effective_damage = max(total_damage - armor_block, 0)
        """ fire and poison damage after 1st attack"""
        enemy["hp"] -= effective_damage

        if player.get("special") == "Fire":
            enemy["hp"] -= fire_damage
            special_text += "\nMage burned the enemy! 1 extra fire damage."
        if player.get("special") == "Poison":
            enemy["hp"] -= poison_damage
            special_text += "\nRogue stung! 1 extra poison damage."

        """ Enemy Attack Phase """

        enemy_damage = calculate_damage(enemy["damage"])
        player_armor = player.get("armor", 0) + player.get("shield", 0)
        damage_received = max(enemy_damage - player_armor, 0)
        player["hp"] -= damage_received

        print(f"\nYou dealt {total_damage} damage.\nEnemy armor"
              f" absorbed {armor_block}.\n"
              f"Effective damage: {effective_damage}")
        print(f"{enemy['class']} struck back with {enemy_damage} damage.\n"
              f"Your armor absorbed {player_armor}.\n"
              f"You received: {damage_received} damage")

        # --- Special Effects (non combat) ---
        if player.get("special") == "Heal":
            player["hp"] += 1
            print(
                  f"\nPaladin healed 1HP with his\n"
                  f"ability 'lay on hands' and is now on\n "
                  f"{player['hp']} Current HP incread by 1")
        if enemy.get("special") == "Lifesteal":
            enemy["hp"] += 1
            print(
                  f"\nVampire recovered 1HP with its\n"
                  f"ability 'life steal' and is now on\n"
                  f"{enemy['hp']} Current HP increaed by 1")
        if enemy.get("special") == "Reflect":
            reflected = max(total_damage - player_armor, 0)
            player["hp"] -= reflected
            print(f"\nWraith returned {reflected} damage. {player['class']}"
                  f"is now on {player['hp']} HP = Current HP - {reflected}")

        # Show current HP after round
        print(f"\n\n[STATUS]\n{player['class']} HP: {player['hp']} - "
              f"{enemy['class']} HP: {enemy['hp']}")
        print(special_text)

        # --- End of Battle ---
        if player["hp"] <= 0 and enemy["hp"] <= 0:
            print("It's a draw!")
        elif player["hp"] <= 0:
            print("You failed and forces of darknes prevailed!")
        elif enemy["hp"] <= 0:
            print("You send undead beast back to darknes!")
        else:
            print("Battle rages between good and evil!")

        """ trying out the main function """


while True:
    print("\n--- SELECT YOUR WARRIOR OF LIGHT---")
    player = select_character()
    enemy = random_enemy()

    print(f"\nRandomly selected enemy is : {enemy['class']}")
    battle(player, enemy)

    play_again = input("Do you want to fight the evil again? (yes): ").lower()
    if play_again != "yes":
        print("Thanks for playing!")
        break
