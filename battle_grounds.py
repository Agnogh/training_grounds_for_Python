
# battle_setup.py plan
# 1. Reads "python_battlefiled.xlsx" and shows:
# - Hero (Heroes! A2 name-Not at this point), B2 class, C2 Armour, D2 HP)
# - Weapon (Weapons! A2 type, B2 Damage)
# - Monster (Monsters! B3 class, C3 Armour, D3 Damage, E3 HP)
#
# Flow:
#   1) "Welcome to battle" message
#   2) List heroes (only "Royal Guard" ATM) -> auto-select
#   3) List weapons ("Spear" only this one) -> auto-select
#   4) List monsters (only "Skeleton" mosnter) -> auto-select
#   5) Display stat blocks for all

import gspread
from google.oauth2.service_account import Credentials
import re
from dataclasses import dataclass
import random


def roll_damage(min_d: int, max_d: int) -> int:
    return random.randint(min_d, max_d)  # inclusive


def resolve_simultaneous_round(hero, weapon, monster, hero_hp: int,
                               monster_hp: int):
    """
    Both attack using start-of-round stats.
    Quick Hands -> hero makes 2 strikes (armour applies per eaqch strike).
    """
    # strikes-per-side
    # defining ability for double strike (if active, then 2,
    # otherwise only 1 attack)
    hero_strikes = 2 if "quick hands" in (hero.special or "").lower() else 1
    # can extend later if monster has specials ability 2 x attack
    monster_strikes = 1

    # roll raw damage per strike
    hero_raws = [roll_damage(weapon.damage_min, weapon.damage_max)
                 for _ in range(hero_strikes)]
    monster_raws = [roll_damage(monster.damage_min, monster.damage_max)
                    for _ in range(monster_strikes)]

    # defining armour per strike
    hero_nets = [max(0, r - monster.armour) for r in hero_raws]
    monster_nets = [max(0, r - hero.armour) for r in monster_raws]

    # apply simultaneously damage as each char attacks at same time
    dmg_to_monster = sum(hero_nets)
    dmg_to_hero = sum(monster_nets)
    # defining "remaining" HP after blows exchange
    new_monster_hp = max(0, monster_hp - dmg_to_monster)
    new_hero_hp = max(0, hero_hp - dmg_to_hero)

    # outcome tag - both killed, hero killed, monster killed
    if new_hero_hp <= 0 and new_monster_hp <= 0:
        outcome = "double_ko"
    elif new_monster_hp <= 0:
        outcome = "monster_defeated"
    elif new_hero_hp <= 0:
        outcome = "hero_defeated"
    else:
        outcome = "continue"

    # lines for pretty print
    lines = []
    for i, (raw, net) in enumerate(zip(hero_raws, hero_nets), start=1):
        label = f"strike {i}" if hero_strikes > 1 else "strike"
        lines.append(
            f"{hero.champion_of_light} {label}: {raw} "
            f"with {weapon.type} ({weapon.raw_weapon_damage}) "
            f"→ {monster.chamption_od_darknes} takes {net}"
            f"(armour {monster.armour})"
        )
    for i, (raw, net) in enumerate(zip(monster_raws, monster_nets), start=1):
        label = f"strike {i}" if monster_strikes > 1 else "strike"
        lines.append(
            f"{monster.chamption_od_darknes} {label}: {raw} "
            f"({monster.raw_moster_damage}) → {hero.champion_of_light} "
            f"takes {net} (armour {hero.armour})"
        )
    lines += [
        f"{hero.champion_of_light} HP: {hero_hp} → {new_hero_hp}",
        f"{monster.chamption_od_darknes} HP: {monster_hp} → {new_monster_hp}",
    ]

    return new_hero_hp, new_monster_hp, {"outcome": outcome, "lines": lines}


# --- Data classes ---


@dataclass
class Hero_Character:
    champion_of_light: str
    armour: int
    hit_points: int
    # (adding "Quick Hands" ability for Rogue)
    special: str = ""
    # (adding description for special ablity)
    special_desc: str = ""


@dataclass
class Weapon:
    type: str
    damage_min: int
    damage_max: int
    raw_weapon_damage: str


@dataclass
class Monster_Character:
    chamption_od_darknes: str
    armour: int
    damage_min: int
    damage_max: int
    hit_points: int
    raw_moster_damage: str


SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

CREDS = Credentials.from_service_account_file(
    "pythonbattlefield-2a7d07648ac1.json"
    )
CLIENT = gspread.authorize(CREDS.with_scopes(SCOPE))

# Quick sanity: list spreadsheets this service account can see
for f in CLIENT.list_spreadsheet_files():
    print("Seen by service account ->", f.get("name"), f.get("id"))

# this is to use the correct ID (with the hyphen after the 1
# I was missing all this damn time)
SHEET_ID = (
    "1-QrsVmnaWtkZMZV8pu5HJkQnQXWFyk3L"
    "PyD9UdntkLI"
)

sh = CLIENT.open_by_key(SHEET_ID)
print("Opened:", sh.title)
print("Tabs:", [ws.title for ws in sh.worksheets()])


# Weapons and armour range and values
# =========================
def parse_damage_range(text: str) -> tuple[int, int]:
    """
    Accepts formats like '0-7', '0–7' (en-dash), '07',
    or a single number '7'. Returns (low, high).
    """
    if text is None:
        raise ValueError("Damage cell is empty")

    s = str(text).strip()

    # 'min-max' with hyphen or en-dash
    m = re.match(r"^\s*(\d+)\s*[-–]\s*(\d+)\s*$", s)
    if m:
        low, high = int(m.group(1)), int(m.group(2))
        if low > high:
            low, high = high, low
        return low, high

    # Compact '07' meaning 0..7
    if s.isdigit() and len(s) == 2:
        return int(s[0]), int(s[1])

    # Single number -> 0..number
    if s.isdigit():
        return 0, int(s)

    raise ValueError(f"Unrecognized damage format: {s!r}")


def stat_block(title: str, lines: list[str]) -> str:
    width = max(len(title), *(len(line) for line in lines), 20)
    border = "-" * (width + 4)
    content = [border, f"| {title.ljust(width)} |", border]
    for line in lines:
        content.append(f"| {line.ljust(width)} |")
    content.append(border)
    return "\n".join(content)


def auto_pick_single(label: str, options: list[str]) -> str:
    print(f"\n{label}:")
    for i, opt in enumerate(options, start=1):
        print(f"  {i}) {opt}")
    choice = options[0]  # only one option -> auto-select
    print(f"Selected: {choice}")
    return choice


def choose_from_list(label: str, options: list[str]) -> str:
    print(f"\n{label}:")
    for i, opt in enumerate(options, start=1):
        print(f"  {i}) {opt}")
    while True:
        raw = input("Pick a number (default 1): ").strip()
        if raw == "":
            return options[0]
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        print("Invalid choice. Try again.")


def read_hero_row(ws, row: int) -> Hero_Character:
    hero_class = ws.acell(f"B{row}").value
    hero_armour = int(ws.acell(f"C{row}").value)
    hero_hp = int(ws.acell(f"D{row}").value)
    hero_special = (ws.acell(f"E{row}").value or "").strip()
    hero_special_desc = (ws.acell(f"F{row}").value or "").strip()
    return Hero_Character(
        champion_of_light=str(hero_class),
        armour=hero_armour,
        hit_points=hero_hp,
        special=hero_special,
        special_desc=hero_special_desc,
    )


def as_range_or_none(val):
    """Return (low, high) as val is a ranges
    ('2-4', '2–4', '24' compact), else None."""
    try:
        return parse_damage_range(val)
    except Exception:
        return None


def coerce_int_strict(val, label):
    """Turn a cell into an int. Accepts '99' or '99.0'.
    Rejects ranges like '2-4'."""
    s = str(val).strip()
    if re.fullmatch(r"\d+(\.0+)?", s):
        return int(float(s))
    raise ValueError(f"{label} must be a single number, got {val!r}")


# things (heroes, vilins, weapons) to
#  load from Google Sheets
# =========================


def load_from_gsheets():
    # I am using Key ID rather than name (CLIENT.open)
    sh = CLIENT.open_by_key(SHEET_ID)

    # Heroes tab: B2 name, C2 armour, D2 HP
    heroes_ws = sh.worksheet("Heroes")
    heroes = [read_hero_row(heroes_ws, 2), read_hero_row(heroes_ws, 3)]

    # Weapons tab: A2 name, B2 damage
    weapons_ws = sh.worksheet("Weapons")
    weapon_name = weapons_ws.acell("A2").value
    weapon_damage_raw = weapons_ws.acell("B2").value
    w_low, w_high = parse_damage_range(weapon_damage_raw)
    # adding type despite having one weapon as more will follow
    weapon = Weapon(
        type=str(weapon_name),
        damage_min=w_low,
        damage_max=w_high,
        raw_weapon_damage=str(weapon_damage_raw),
    )

    # Monsters tab: B3 class, C3 armour, D3 is HP
    # E3 is damage (range)
    monsters_ws = sh.worksheet("Monsters")
    monster_class = monsters_ws.acell("B3").value
    monster_armour = int(monsters_ws.acell("C3").value)

    monster_hp = coerce_int_strict(monsters_ws.acell("D3").value,
                                   "Monsters!D3 (HP)")
    monster_damage_raw = str(monsters_ws.acell("E3").value)
    m_low, m_high = parse_damage_range(monster_damage_raw)
    # for future monesters that will be added
    monster = Monster_Character(
        chamption_od_darknes=str(monster_class),
        armour=monster_armour,
        damage_min=m_low,
        damage_max=m_high,
        hit_points=monster_hp,
        raw_moster_damage=monster_damage_raw,
    )

    return heroes, weapon, monster


# Main game flow
# =========================
def main():
    print("Welcome to battl")

    heroes, weapon, monster = load_from_gsheets()


# choose hero now that we have aditional hero in play
    hero_names = [h.champion_of_light for h in heroes]
    picked_name = choose_from_list("Choose your Hero", hero_names)
    hero = next(h for h in heroes if h.champion_of_light == picked_name)

    # show chosen hero stats
    print()
    print(stat_block(
        f"Hero: {hero.champion_of_light}",
        [
            f"Armour: {hero.armour}",
            f"Hit Points: {hero.hit_points}",
            f"Special: {hero.special or '—'}",
        ],
    ))

    print(stat_block(
        f"Weapon: {weapon.type}",
        [f"Damage: {weapon.raw_weapon_damage} (parsed"
         f"{weapon.damage_min}-{weapon.damage_max})"],
    ))
    print(stat_block(
        f"Monster: {monster.chamption_od_darknes}",
        [
            f"Armour: {monster.armour}",
            f"Hit Points: {monster.hit_points}",
            f"Damage: {monster.raw_moster_damage} (parsed"
            f"{monster.damage_min}-{monster.damage_max})",
        ],
    ))

    """ Keeping this for now in case 2 heroes fails
    # 1) Hero list (one option to choose from)
    picked_hero = auto_pick_single("Choose your Hero of light",
                                   [hero.champion_of_light])
    print()
    print("choosing your chanpion")
    print()
    print(stat_block(
        f"Hero: {picked_hero}",
        [
            f"Armour: {hero.armour}",
            f"Hit Points: {hero.hit_points}",
        ],
    ))
    """


# --- One simultaneous round ---
    hero_hp, monster_hp, rep = resolve_simultaneous_round(hero, weapon,
                                                          monster,
                                                          hero.hit_points,
                                                          monster.hit_points)
    print()
    print(stat_block("Round 1 — Simultaneous", rep["lines"]))

# One time display
    if rep["outcome"] == "double_ko":
        print(stat_block("Round 1 — Result",
                         ["Double KO! Both fall together."]))
    elif rep["outcome"] == "monster_defeated":
        print(stat_block("Round 1 — Result", [f"{monster.chamption_od_darknes}"
                                              f"is defeated!"]))
    elif rep["outcome"] == "hero_defeated":
        print(stat_block("Round 1 — Result", [f"{hero.champion_of_light}"
                                              f"is defeated!"]))
    else:
        print(stat_block("Round 1 — Result", ["Both fighters still stand."]))

    print()
    print(stat_block("Round 1 — Simultaneous", rep["lines"]))

    # Outcome banner
    if rep["outcome"] == "double_ko":
        print(stat_block("Round 1 — Result",
                         ["Double KO! Both fall together."]))
    elif rep["outcome"] == "monster_defeated":
        print(stat_block("Round 1 — Result",
                         [f"{monster.chamption_od_darknes} is defeated!"]))
    elif rep["outcome"] == "hero_defeated":
        print(stat_block("Round 1 — Result",
                         [f"{hero.champion_of_light} is defeated!"]))
    else:
        print(stat_block("Round 1 — Result",
                         ["Both fighters still in the fight."]))


if __name__ == "__main__":
    main()


""" don't need these things for confirmation
if something works

# Trying ot open the spreadsheet using the key
sh = CLIENT.open_by_key(SHEET_ID)
print("Tabs:", [ws.title for ws in sh.worksheets()])

# Open Heroes tab in worksheet and read A2 only
heroes_ws = sh.worksheet("Heroes")
cell_value = heroes_ws.acell("A2").value
print("Value in Heroes!A2:", cell_value)

"""

"""
 "" creating player character ""

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

 "" creating enemy characters ""

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


 "" function for randomly selecting enemy mosters ""


def random_enemy():
    return random.choice(monster_characters).copy()



    "" function for calculated damange ""


def calculate_damage(damage_range, multiplier=1):
    return random.randint(*damage_range) * multiplier


"" function for combat announacement + disengagge mid combat + description ""


def battle(player, enemy):
    print(f"\nBattle begins! {player['class']} vs {enemy['class']}!")

    while player["hp"] > 0 and enemy["hp"] > 0:
        action = input("\nType 'run' to flee, otheriwise type anything like\n"
                       "'die undead beast' for your hero to keep attacking \n"
                       "and battle continuing: ").lower()
        if action == "run":
            print("You ran and live to fight another day!")
            return
        "" Player character attack phase ""
        base_damage = calculate_damage(player["damage"])
        special_text = ""
        total_damage = base_damage
        "" defining special atatcks ""
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
        "" fire and poison damage after 1st attack""
        enemy["hp"] -= effective_damage

        if player.get("special") == "Fire":
            enemy["hp"] -= fire_damage
            special_text += "\nMage burned the enemy! 1 extra fire damage."
        if player.get("special") == "Poison":
            enemy["hp"] -= poison_damage
            special_text += "\nRogue stung! 1 extra poison damage."

        "" Enemy Attack Phase ""

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

        "" trying out the main function ""


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

"""
