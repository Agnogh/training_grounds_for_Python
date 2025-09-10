
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


def _norm(s: str) -> str:
    """Lowercase/trim convenience for matching text safely."""
    return (s or "").strip().lower()


def hero_special_for(hero) -> str:
    he = _norm(getattr(hero, "special", ""))
    if "healing touch" in he:
        return "healing_touch"
    if "quick" in he and "hand" in he:
        return "quick_hands"
    if "thorns" in he and "shield" in he:
        return "thorns_shield"
    return "none"


def monster_special_for(monster) -> str:
    """
    this should wire Vampire -> 'drain_life'.
    Later I might add mapping for tohers
    (Skeleton->none, ghost_shield for Wraight, Zombies death grip..).
    """
    m = _norm(monster.chamption_od_darknes)  # e.g., "vampire"
    if m == "vampire":      # for vapire ability
        return "drain_life"
    if m in ("wraight", "wraith"):      # I made typo so if i ever fix it
        return "ghost_shield"
    if m == "zombie":       # if monster is zombie
        return "death_grip"     # give it spec abiltiy for zombie
    return "none"


def resolve_simultaneous_round(hero, weapon, monster, hero_hp: int,
                               monster_hp: int,
                               allow_revive: bool = True,
                               # need to add this for top limit of HP
                               hero_max_hp: int | None = None,
                               ):
    """
    Still simultanous but adding vampire skill drain life:
    - Vampire: 'Drain Life' -> if monster dealt damage to hero > 0
      actual damage this round, heal vampire for +1 HP *after*
      the strikes (can revive vampire if vampire ends up on 0hp
      after combat round -allow_revive=True).

    more specials ability later
    """
    monster_special = monster_special_for(monster)   # monsters spec ability
    hero_special = hero_special_for(hero)      # hero healing hands ability
    # will be added once I start adding special ability for weapons
    # weapon_special  = weapon_special_for(weapon)

    # ===== STRIKES (simultaneous) =====
    # this is for spec.abiltiy quick hands (2 times attack)
    hero_strikes = 2 if "quick hands" in _norm(hero.special) else 1
    # for now I am nto planing to create monster that atatcks 2 times
    monster_strikes = 1

    # raw rolls (this is just damage dealt before armour deducts it)
    hero_raw_damage = [roll_damage(weapon.damage_min,  weapon.damage_max)
                       for _ in range(hero_strikes)]
    monster_raw_damage = [roll_damage(monster.damage_min, monster.damage_max)
                          for _ in range(monster_strikes)]

    # value of damange after armour is applied -apply armour per strike
    # + with Ghost Shield
    hero_actual_damage = []
    hero_cap_flags = []   # track which strikes got capped (cosmetics)

    for r in hero_raw_damage:
        # armour first as wraight has 1 armour
        net = max(0, r - monster.armour)

        # now Ghost Shield - cap 1 *per strike* after armour abosrbs dmg
        capped = False
        if monster_special == "ghost_shield" and net > 1:
            net = 1
            capped = True

        hero_actual_damage.append(net)
        hero_cap_flags.append(capped)
    monster_actual_damage = [max(0, r - hero.armour)
                             for r in monster_raw_damage]  # monster -> hero

    # actual damage done and assigning to variable dmg_to_monster/hero
    dmg_to_monster = sum(hero_actual_damage)
    dmg_to_hero = sum(monster_actual_damage)

    # HP calculations HP - damange after armour absorbtion
    new_monster_hp = max(0, monster_hp - dmg_to_monster)
    new_hero_hp = max(0, hero_hp - dmg_to_hero)

    # ===== POST-ROUND (always runs, can revive if allowed) =====
    specials_applied = []
    # if special is equal to "drain life" and damage to hero is over 0
    if monster_special == "drain_life" and dmg_to_hero > 0:
        if allow_revive or new_monster_hp > 0:
            # add 1HP to var new_monster_hp
            new_monster_hp += 1
            specials_applied.append("Drain Life: monster +1 HP")

    if monster_special == "death_grip":
        before_death_grip = new_hero_hp
        new_hero_hp = max(0, new_hero_hp - 1)
        specials_applied.append(
            f"Death Grip effect: hero had {before_death_grip} and after "
            f"Zombie effect that passed through armour, it "
            f"reduced hero HP by -1 HP and new HP is {new_hero_hp}")

    # if hero ability "Healing Touch" exist (+1 HP, capped at max)
    if "healing touch" in hero_special:
        if allow_revive or new_hero_hp > 0:     #
            hp_after_healing = new_hero_hp + 1     # add 1HP to temp variable
            if hero_max_hp is not None:     # if hero is at maxHP
                # takes smaller value between the 2 and assign to "healted_to"
                hp_after_healing = min(hero_max_hp, hp_after_healing)
            gain = hp_after_healing - new_hero_hp
            if gain > 0:        # if there was increase of HP
                new_hero_hp = hp_after_healing
                specials_applied.append("Healing Touch: hero +1 HP")
            else:       # if hero is at full health trigger following
                specials_applied.append("Healing Touch: no effect-max HP)")

    # Druid special ability "Thornes shield" and formated description steing
    if "thorns shield" in hero_special:
        monster_attempted_damage = any(raw > 0 for raw in monster_raw_damage)
        if monster_attempted_damage:
            before_thornes_shielkd = new_monster_hp
            new_monster_hp = max(0, new_monster_hp - 1)
            specials_applied.append(
                f"Thonrs shield effect returns 1 HP damage resulting"
                f"monster drops from {before_thornes_shielkd} to"
                f"{new_monster_hp}")

    # ===== pretty print lines =====
    lines = []
    for i, (raw, net, capped) in enumerate(zip(
        hero_raw_damage,
        hero_actual_damage, hero_cap_flags),
        start=1
    ):
        label = f"strike {i}" if hero_strikes > 1 else "strike"
        lines.append(
            f"{hero.champion_of_light} {label}: {raw} with"
            f"{weapon.type} ({weapon.raw_weapon_damage}) "
            f"→ {monster.chamption_od_darknes} takes"
            f"{net} (armour {monster.armour})"
            + (" (capped by Ghost Shield)" if capped else "")
        )
    for i, (raw, net) in enumerate(zip(monster_raw_damage,
                                       monster_actual_damage), start=1):
        label = f"strike {i}" if monster_strikes > 1 else "strike"
        lines.append(
            f"{monster.chamption_od_darknes} {label}:"
            f"{raw} ({monster.raw_moster_damage}) "
            f"→ {hero.champion_of_light} takes {net} (armour {hero.armour})"
        )

    lines += [
        f"{hero.champion_of_light} HP: {hero_hp} → {new_hero_hp}",
        f"{monster.chamption_od_darknes} HP: {monster_hp} → {new_monster_hp}",
    ]

    # show post-round effect (if any) + final HP after effects (+ or -)
    for note in specials_applied:
        lines.append(f"[Post-round] {note}")
    if specials_applied:
        lines += [
            f"[After effects] {hero.champion_of_light} HP = {new_hero_hp}",
            f"[After effects] {monster.chamption_od_darknes}"
            f"HP = {new_monster_hp}",
        ]

    # final outcome after everything (battle rounds & effect of spec. ability)
    if new_hero_hp <= 0 and new_monster_hp <= 0:
        outcome = "double_ko"   # when both are 0 HP
    elif new_monster_hp <= 0:
        outcome = "monster_defeated"    # when monster HP is 0
    elif new_hero_hp <= 0:
        outcome = "hero_defeated"   # when hero HP is 0
    else:
        outcome = "continue"    # non of above and combat continues

    report = {
        "hero_raw_total":    sum(hero_raw_damage),
        "hero_net_total":    dmg_to_monster,
        "monster_raw_total": sum(monster_raw_damage),
        "monster_net_total": dmg_to_hero,
        "specials_applied":  specials_applied,
        "outcome": outcome,
        "lines": lines,
    }
    return new_hero_hp, new_monster_hp, report


def battle_loop(hero, weapon, monster):
    round_no = 1
    hero_hp = hero.hit_points
    monster_hp = monster.hit_points

    while True:
        hero_hp, monster_hp, rep = resolve_simultaneous_round(
            hero, weapon, monster, hero_hp, monster_hp, allow_revive=True,
            hero_max_hp=hero.hit_points,
        )

        # Show what happened current round
        print()
        print(stat_block(f"Battle round {round_no}", rep["lines"]))

        # Outcome banner for good win, bad win and both kill
        if rep["outcome"] == "double_ko":
            print(stat_block("Battle result",
                             [f"Double kill! Both"
                              f"{monster.chamption_od_darknes}"
                              f" & {hero.champion_of_light} fall."]))
            break
        elif rep["outcome"] == "monster_defeated":
            print(stat_block("Battle result",
                             [f"{monster.chamption_od_darknes}"
                              f"is defeated!"
                              f"{hero.champion_of_light}"
                              f"slayed the servent of dark!"]
                             ))
            break
        elif rep["outcome"] == "hero_defeated":
            print(stat_block("Battle result",
                             [f"{hero.champion_of_light} is defeated!"
                              f"{monster.chamption_od_darknes}"
                              f"has defeated hero"]
                             ))
            break

        # for player ot have option to continue or flee
        choice = input("Press any key to continue, or 'F' to"
                       "flee the battle: ").strip().lower()
        if choice == "f":
            print(stat_block("Battle", [f"{hero.champion_of_light} disengages"
                                        f"and flees."]))
            break

        round_no += 1

    return hero_hp, monster_hp, rep["outcome"]


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
class Monster_Character:
    chamption_od_darknes: str   # B column
    armour: int     # (Column C)
    damage_min: int     # from E column
    damage_max: int     # also from E column
    hit_points: int  # Columnd D
    raw_moster_damage: str
    special: str = ""   # (cloumn F)
    special_desc: str = ""  # (column G)


@dataclass
class Weapon:
    type: str
    damage_min: int
    damage_max: int
    raw_weapon_damage: str
    # in case I add description for special
    # special: str = ""
    # and I might decide that "description" is pulled from cell


SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

CREDS = Credentials.from_service_account_file(
    "pythonbattlefield-2a7d07648ac1.json"
    )
CLIENT = gspread.authorize(CREDS.with_scopes(SCOPE))

# Quick sanity: list spreadsheets this service account can see
# I am still getting errors so commenting this part as well
# for f in CLIENT.list_spreadsheet_files():
#    print("Seen by service account ->", f.get("name"), f.get("id"))

# this is to use the correct ID (with the hyphen after the 1
# I was missing all this damn time)
SHEET_ID = (
    "1-QrsVmnaWtkZMZV8pu5HJkQnQXWFyk3L"
    "PyD9UdntkLI"
)

# still getting the errors so maybe commenting this will help
# sh = CLIENT.open_by_key(SHEET_ID)
# print("Opened:", sh.title)
# print("Tabs:", [ws.title for ws in sh.worksheets()])


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


def read_monster_row(ws, row: int) -> Monster_Character:
    m_class = ws.acell(f"B{row}").value
    m_armour = int(ws.acell(f"C{row}").value)
    m_hp = int(ws.acell(f"D{row}").value)
    m_raw = str(ws.acell(f"E{row}").value)
    m_min, m_max = parse_damage_range(m_raw)
    m_special = (ws.acell(f"F{row}").value or "").strip()
    m_special_desc = (ws.acell(f"G{row}").value or "").strip()
    return Monster_Character(
        chamption_od_darknes=str(m_class),
        armour=m_armour,
        damage_min=m_min,
        damage_max=m_min,
        hit_points=m_hp,
        raw_moster_damage=m_raw,
        special=m_special,
        special_desc=m_special_desc,
    )


def read_heroes_block(ws) -> list[Hero_Character]:
    # B..F = class, armour, hp, special, special_desc (rows 2..11)
    block = ws.get("B2:F11")  # onw API now
    heroes: list[Hero_Character] = []

    for r_idx, row in enumerate(block, start=2):        # r_idx 2 to 11
        row = (row + ["", "", "", "", ""])[:5]      # trmms to 5 el (B->F)
        b, c, d, e, f = row
        if not str(b or "").strip():        # skip blank class
            continue
        armour = coerce_int_strict(c, f"Heroes!C{r_idx}")
        hp = coerce_int_strict(d, f"Heroes!D{r_idx}")
        heroes.append(Hero_Character(
            champion_of_light=str(b),
            armour=armour,
            hit_points=hp,
            special=str(e or ""),
            special_desc=str(f or ""),
        ))
    return heroes


def read_monsters_block(ws) -> list[Monster_Character]:
    # B to G = class, armour, hp, damage, special, special_desc (rows 2to 6)
    block = ws.get("B2:G6")  # one API call now
    monsters: list[Monster_Character] = []

    for r_idx, row in enumerate(block, start=2):        # r_idx matches row num
        row = (row + ["", "", "", "", "", ""])[:6]      # trimms at 6 elements
        b, c, d, e, f, g = row
        if not str(b or "").strip():        # skip blank class
            continue
        armour = coerce_int_strict(c, f"Monsters!C{r_idx}")
        hp = coerce_int_strict(d, f"Monsters!D{r_idx}")
        raw = str(e or "")
        m_low, m_high = parse_damage_range(raw)
        monsters.append(Monster_Character(
            chamption_od_darknes=str(b),
            armour=armour,
            damage_min=m_low,
            damage_max=m_high,
            hit_points=hp,
            raw_moster_damage=raw,
            special=str(f or ""),
            special_desc=str(g or ""),
        ))
    return monsters


def read_weapons_block(ws) -> list[Weapon]:
    # A, B & C = type, damage & special ability(rows 2 to 11)
    block = ws.get("A2:C11")
    weapons: list[Weapon] = []
    for r_idx, row in enumerate(block, start=2):
        row = (row + ["", "", ""])[:3]
        a, b, c = row       # add "d" if spec desc is added
        weapon_type = (a or "").strip()
        if not weapon_type:
            continue
        dmg_raw = (b or "").strip()
        low, high = parse_damage_range(dmg_raw)
        weapons.append(Weapon(
             type=weapon_type,
             damage_min=low,
             damage_max=high,
             raw_weapon_damage=dmg_raw,
             # special ability (have to comment out for now)
             # special=(c or "").strip(),
             # i case description for spec ability is added
             # special_desc=str(d or ""),
         ))
    return weapons


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

    heroes_ws = sh.worksheet("Heroes")
    weapons_ws = sh.worksheet("Weapons")
    monsters_ws = sh.worksheet("Monsters")

    # HEROES (B2:F11) — one call to avoid erros due
    # to frequesnt requests
    # Quota exceeded for quota metric 'Read requests' and limit
    # 'Read requests per minute per user' of service
    # 'sheets.googleapis.com' for consumer 'project_number:317396774673'.
    heroes = read_heroes_block(heroes_ws)

    # WEAPONS — block read (A2:C11)
    weapons = read_weapons_block(weapons_ws)

    # MONSTERS (B2:G6) — one call to avoid
    # calling API a lot
    monsters = read_monsters_block(monsters_ws)

    return heroes, weapons, monsters

# I need to drop this part as I am geting
# File "C:\ Users\Zombie\Desktop vscode-projects
# training_grounds_for_Python\.venv\Lib
# site-packages\gspread\http_client.py",
# line 236, in values_get r = self.request
# ("get", url, params=params)

# Main game flow
# =========================


def main():
    print("Welcome to battl")

    heroes, weapons, monsters = load_from_gsheets()


# choose hero now that we have aditional hero in play
    hero_names = [h.champion_of_light for h in heroes]
    picked_name = choose_from_list("Choose your Hero", hero_names)
    hero = next(h for h in heroes if h.champion_of_light == picked_name)

# choose monster (by class)
    monster_names = [m.chamption_od_darknes for m in monsters]
    picked_monster = choose_from_list("Choose your Opponent", monster_names)
    monster = next(m for m in monsters if
                   m.chamption_od_darknes == picked_monster)

# choose weapon (all weapons now)
    weapon_names = [w.type for w in weapons]
    picked_weapon = choose_from_list("Choose your Weapon", weapon_names)
    weapon = next(w for w in weapons if w.type == picked_weapon)

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
            f"Special: {monster.special or '—'}",
        ],
    ))

    # --- Multi-round battle until defeat or flee ---
    final_hero_hp, final_monster_hp, outcome = battle_loop(hero,
                                                           weapon, monster)


"""
    # One round (to try Drain Life)
    hero_hp, monster_hp, rep = resolve_simultaneous_round(
        hero, weapon, monster, hero.hit_points, monster.hit_points
    )
    print()
    print(stat_block("Round 1 — Simultaneous", rep["lines"]))


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

"""
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
