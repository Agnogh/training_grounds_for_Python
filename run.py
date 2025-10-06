# I AM ADDING ALL CONTENT FROM battle_grounds.py TO run.py as Code institute
# mandates it, but you can find same thig in battle_grounds.py file

# Your code goes here.
# You can delete these comments, but do not change the name of this file
# Write your code to expect a terminal of 80 characters wide and 24 rows high

# this should call my game entry point - run.py
# from battle_grounds import main


# battle_setup.py plan
# 1. Reads "python_battlefiled.xlsx" and shows:
# - Hero (Heroes! A-name(NA ATP), B-class, C-Armour, D-HP, E-Spec. skill)
# - Weapon (Weapons! A-Weapon(type), B-Damage)
# - Monster (Monsters! B-Class, C-Armour, D-Damage, E-HP, F-Special skill)
#
# Flow:
#   1) "Welcome to battle" message
#   2) List heroes ->
#   3) List weapons ->
#   4) List monsters ->
#   5) Display stat blocks for all
#   6) Display combat round + math behind weapon calculation abd spec ability
#   7) Display HP status after combat round
#   8) Display Special ability effects if any
#   9) Display HP and Armour status at the end of Battle round
#   10) Ability to continue battle or not
#   11) Final result when either hero or monster or both are killed

# adding just random comment so I save it so I can commit it
# so i have the version before merging template from
# https://github.com/Code-Institute-Org/python-essentials-template.git
# as this si the one I need to use in order to have my project
# accepted. Maybe that is why I had issues with Heroku

import gspread
from google.oauth2.service_account import Credentials
import re
from dataclasses import dataclass
import random

# Based on stack I need to add this standard library
import os
import json


def roll_damage(min_d: int, max_d: int) -> int:
    return random.randint(min_d, max_d)  # inclusive


def _norm(s: str) -> str:
    """Lowercase/trim convenience for matching text safely."""
    return (s or "").strip().lower()


# Not used anymore as I decided not to go with canonical
# as I switched to read raw text, but I am keeping it
# as it took me great deal to figure it out!!
def hero_special_for(hero) -> str:
    he = _norm(getattr(hero, "special", ""))
    if "healing touch" in he:
        return "healing_touch"
    if "quick" in he and "hand" in he:
        return "quick_hands"
    if "thorns" in he and "shield" in he:
        return "thorns_shield"
    if "fireball" in he:
        return "fireball"
    if "destroy" in he and "undead" in he:
        return "destroy_undead"
    if "deadly" in he and "poison" in he:
        return "deadly_poison"
    if "holly" in he and "might" in he:
        return "holly_might"
    return "none"


def resolve_simultaneous_round(hero, weapon, monster, hero_hp: int,
                               monster_hp: int,
                               allow_revive: bool = True,
                               # need to add this for top limit of HP
                               hero_max_hp: int | None = None,
                               ):
    # Applying normalization
    hero_special = _norm(getattr(hero, "special", ""))
    monster_special = _norm(getattr(monster, "special", ""))
    weapon_special = _norm(getattr(weapon, "special", ""))
    weapon_type = _norm(getattr(weapon, "type", ""))

    # ===== STRIKES (simultaneous) =====
    hero_strikes = 1
    if ("quick" in hero_special and "hand" in hero_special):
        hero_strikes = 2

    # Priest defensive skill to take max 1 HP damage(Ghost Shield)
    # not gonna refactor that at this point as it works, maybe in future
    spectral_shield_priest = (
        "spectral" in hero_special and "shield" in hero_special
        )

    # §§§ WEAPON SPECIAL ABILITES §§§
    # 2 times string with one weapons (dual daggers)
    two_rolls_dual_dagger = (
        ("attack" in weapon_special
         and "2" in weapon_special
         and "time" in weapon_special) or
        ("attack" in weapon_special
         and "two" in weapon_special
         and "time" in weapon_special) or
        ("dual" in weapon_type
         and "dagger" in weapon_type)
                )

    dual_slash_axe_double_damage = (
        # Text-based detection from Special column (Axe)
        ("deep" in weapon_special and "slash" in weapon_special)
        # optional safety net by name; remove if you want strict text-only
        or ("axe" in weapon_type)
    )

    ignore_armour_whip = (
        ("ignores" in weapon_special and "armour" in weapon_special)
        or ("whip" in weapon_type)
        or ("lash" in weapon_type)
    )

    break_armour_hammer = (
        ("shield" in weapon_special and "breaker" in weapon_special)
        or ("hammer" in weapon_type)  # safety by name
        or ("warhammer" in weapon_type)     # and in case I change the name
        or ("sledgehammer" in weapon_type)  # and in case I change some more
    )

    flail_with_spike_ball_on_chain = (
        # name-based safety
        ("flail" in weapon_type)
        # text-based safety from Special column
        or ("spiked" in weapon_special and "ball" in weapon_special
            and "chain" in weapon_special)
        # description text safety
        or ("0-6" in weapon_special or "0–6" in weapon_special)
    )

    # read "0-6" from Special
    extra_spiked_ball = None
    if flail_with_spike_ball_on_chain:
        base_flail_damage_range = (weapon.damage_min, weapon.damage_max)
        matches = re.findall(r"\b(\d+)\s*[-–]\s*(\d+)\b", weapon_special or "")
        parsed = []
        for a, b in matches:
            low_flail_damage, high_flail_damage = int(a), int(b)
            if low_flail_damage > high_flail_damage:
                low_flail_damage, high_flail_damage = high_flail_damage,
                low_flail_damage
            parsed.append((low_flail_damage, high_flail_damage))
        if parsed:
            # prefer the first range that is NOT the base weapon range
            extra_spiked_ball = next(
                (damage_range_flail for damage_range_flail in parsed
                 if damage_range_flail != base_flail_damage_range),
                parsed[-1])
        else:
            # Force 0–6 when no explicit range is in Special
            extra_spiked_ball = (0, 6)

    # for now I am not planing to create monster that atatcks 2 times
    monster_strikes = 1

    # raw rolls (this is just damage dealt before armour deducts it)
    monster_raw_damage = [roll_damage(monster.damage_min, monster.damage_max)
                          for _ in range(monster_strikes)]

    hero_raw_components = []
    for _ in range(hero_strikes):
        #  # Dual Daggers (roll twice > sums up > displays as one dmg)
        if two_rolls_dual_dagger:
            a = roll_damage(weapon.damage_min, weapon.damage_max)
            b = roll_damage(weapon.damage_min, weapon.damage_max)
            comps = [a, b]
        # for flail + spiked ball weapon
        elif flail_with_spike_ball_on_chain:
            # Flail -one base roll + one extra-roll with different dmg range
            a = roll_damage(weapon.damage_min, weapon.damage_max)
            extra_low, extra_high = extra_spiked_ball  # from step 2
            extra = roll_damage(extra_low, extra_high)
            comps = [a, extra]
        # this is for regular / normal weapon (roll once)
        else:
            a = roll_damage(weapon.damage_min, weapon.damage_max)
            comps = [a]

        hero_raw_components.append(comps)

    # base and total per strike (apply ×2 if hero has Axe)
    hero_raw_totals = []
    for comps in hero_raw_components:
        base_damage = sum(comps)
        total_damage = (
            base_damage * 2 if dual_slash_axe_double_damage else base_damage
        )
        hero_raw_totals.append((base_damage, total_damage))

    # value of damage after armour is applied -apply armour per strike
    # + with Ghost Shield
    hero_actual_damage = []
    hero_cap_flags = []   # track which strikes got capped (cosmetics)
    for (base_damage, total_damage) in hero_raw_totals:
        if ignore_armour_whip:
            net = total_damage
        else:
            net = max(0, total_damage - monster.armour)

        capped = False
        if (
            "ghost" in monster_special
            and "shield" in monster_special
            and net > 1
        ):
            net = 1
            capped = True

        hero_actual_damage.append(net)
        hero_cap_flags.append(capped)

    # First apply hero armour, then cap to max 1 damage
    monster_actual_damage = []
    monster_cap_flags = []
    for r in monster_raw_damage:
        net = max(0, r - hero.armour)
        capped = False
        if spectral_shield_priest and net > 1:
            net = 1
            capped = True
        monster_actual_damage.append(net)
        monster_cap_flags.append(capped)

    # actual damage done and assigning to variable dmg_to_monster/hero
    dmg_to_monster = sum(hero_actual_damage)
    dmg_to_hero = sum(monster_actual_damage)

    # HitPoints calculation hero/monster
    new_monster_hp = monster_hp - dmg_to_monster
    new_hero_hp = hero_hp - dmg_to_hero

    # Snapshots / cpilboard / temp save for display armour used during strikes
    # amount that strike from Hero had to go through
    monster_armour_during_hero_attack = monster.armour
    # amount of hero amrour that monster's attack had to go through
    hero_armour_during_monster_attack = hero.armour

    # HitPoints calculation hero/monster
    hero_hp_after_strikes = new_hero_hp
    monster_hp_after_strikes = new_monster_hp

    # ===== POST-ROUND (always runs, can revive if allowed) =====

    specials_applied = []
    # if special is equal to "drain life" and damage to hero is over 0
    # Vapire spec ability Drain life
    if ("drain" in monster_special and "life" in
            monster_special) and dmg_to_hero > 0:
        if allow_revive or new_monster_hp > 0:
            new_monster_hp += 1
            specials_applied.append(
                f"Drain Life: {monster.champion_of_darkness} "
                f"drains {hero.champion_of_light} and "
                f"regenerates itself for 1 HP")

    # Hammer/Warhammer reduce monsters armour by 1 after every battle round
    if break_armour_hammer:
        if monster.armour > 0:
            before_hammer_hit = monster.armour
            monster.armour = max(0, monster.armour - 1)
            specials_applied.append(
                f"{weapon.type}: -1 to {monster.champion_of_darkness} armour"
                f" → destroys the monster's armour from "
                f"{before_hammer_hit} to {monster.armour}"
            )
        else:
            specials_applied.append(
                f"{weapon.type}: no effect (armour already 0)"
            )

    # Zombie effect death grip
    if ("death" in monster_special and "grip" in monster_special):
        before_death_grip = new_hero_hp
        new_hero_hp = new_hero_hp - 1  # now it will go below 0HP
        specials_applied.append(f"Death Grip: {hero.champion_of_light}"
                                f" dropped from {before_death_grip} HP"
                                f" to {new_hero_hp} HP.")

    # Armour Shred -1 armour to hero appllied AFTER battle round
    if (
        "armour" in monster_special
        and ("shread" in monster_special or "shred" in monster_special)
    ):
        successful_hits_by_werewolf = sum(1 for net in monster_actual_damage
                                          if net > 0)
        if successful_hits_by_werewolf > 0:
            before_armour_shred_armour = hero.armour
            if before_armour_shred_armour > 0:
                hero.armour = before_armour_shred_armour - 1
                specials_applied.append(
                    f"Armour Shred: {hero.champion_of_light} armour "
                    f"dropped from {before_armour_shred_armour} "
                    f"to {hero.armour} due to {monster_special}"
                    f" reducing it (-1)."
                )
            else:
                specials_applied.append(
                    f"Armour Shred: no effect, {hero.champion_of_light} "
                    f"armour is already at {hero.armour}! "
                    )

    # if hero ability "Healing Touch" exist (+1 HP, capped at max)
    if ("healing" in hero_special and "touch" in hero_special):
        if allow_revive or new_hero_hp > 0:     #
            hp_after_healing = new_hero_hp + 1     # add 1HP to temp variable
            if hero_max_hp is not None:     # if hero is at maxHP
                # takes smaller value between the 2 and assign to "healted_to"
                hp_after_healing = min(hero_max_hp, hp_after_healing)
            gain = hp_after_healing - new_hero_hp
            if gain > 0:        # if there was increase of HP
                new_hero_hp = hp_after_healing
                specials_applied.append(
                    f"Healing Touch: {hero.champion_of_light} healed"
                    f" themselves for +1 HP putting them on "
                    f"{hp_after_healing}")
            else:       # if hero is at full health trigger following
                specials_applied.append(
                    f"Healing Touch: no effect. {hero.champion_of_light}"
                    f" is at {hero_max_hp} HP)")

    # Druid special ability "Thornes shield" and formated description steing
    if ("thorns" in hero_special and "shield" in
            hero_special) and dmg_to_hero > 0:
        before_thorns_shield = new_monster_hp
        new_monster_hp = new_monster_hp - 1  # allows now to go below 0
        specials_applied.append(
            f"Thorns Shield: spiked defence made "
            f"{monster.champion_of_darkness} drop"
            f" from {before_thorns_shield} HP to "
            f"{new_monster_hp} HP"
        )

    # Mage special ability "fireball" and formated description steing
    if "fireball" in hero_special:
        before_fireball = new_monster_hp
        new_monster_hp = new_monster_hp - 1  # to make sure HP goes below 0
        specials_applied.append(
            f"Fireball effect: {hero.champion_of_light} does fire "
            f"damage to {monster.champion_of_darkness}, causing "
            f"it to drop HP from {before_fireball} to {new_monster_hp}"
        )

    # Crusader special ability "destroy undead" and formated description steing
    if ("destroy" in hero_special and "undead" in hero_special):
        before_destroy_undead = new_monster_hp
        new_monster_hp = new_monster_hp - 1  # now HP can drop below 0
        specials_applied.append(
            f"Destroy undead: {hero.champion_of_light} cast "
            f" Destroy undead and reduced "
            f"{monster.champion_of_darkness} HP from "
            f"{before_destroy_undead} to {new_monster_hp}"
        )

    # Assassin special ability "deadly poison" if armour was penetrated
    if ("deadly" in hero_special and "poison" in hero_special):
        if any(net > 0 for net in hero_actual_damage):
            before_deadly_poison = new_monster_hp
            new_monster_hp = new_monster_hp - 2
            specials_applied.append(
                f"Deadly Poison: {monster.champion_of_darkness} "
                f"got reduced from {before_deadly_poison} HP to "
                f"{new_monster_hp} HP due to "
                f"{hero.champion_of_light} special skill "
                f"{hero_special}"
                )

    # --- Holly Might: -1 armour AFTER the battle round ---
    if "might" in hero_special and ("holly" in hero_special
                                    or "holy" in hero_special):
        before_holly_might_armour = monster.armour
        if before_holly_might_armour > 0:
            monster.armour = before_holly_might_armour - 1
            specials_applied.append(
                f"Holly Might: {monster.champion_of_darkness} armour"
                f" dropped from {before_holly_might_armour} "
                f"to {monster.armour} HP due to {hero_special}"
                f" reducing it (-1)"
            )
        else:
            specials_applied.append(
                f"Holly Might: no effect {monster.champion_of_darkness}"
                f" armour is already at {monster.armour}."
                )

    if hero_strikes == 2 and not ("quick" in hero_special
                                  and "hand" in hero_special):
        if ("attack" in weapon_special) or ("x2" in weapon_special):
            specials_applied.append(f"{weapon.type}: attack 2 times"
                                    f"(grants +1 strike)")

    # ===== pretty print lines =====
    lines = []
    for i, ((base_damage, total_damage), comps, net, capped) in enumerate(zip(
        hero_raw_totals, hero_raw_components,
        hero_actual_damage, hero_cap_flags),
        start=1
    ):
        label = f"strike {i}" if hero_strikes > 1 else "strike"
        # Left-hand math display
        if len(comps) == 2:
            lhs = f"{comps[0]} + {comps[1]} = {base_damage}"
        else:
            lhs = f"{base_damage}"

        # Axe (×2 damage) appends multiplier part
        if dual_slash_axe_double_damage:
            lhs = f"{lhs} × 2 = {total_damage}"

        # Optional note about special weapon behavior
        note = ""
        if flail_with_spike_ball_on_chain and extra_spiked_ball:
            extra_lo, extra_hi = extra_spiked_ball
            note = f" + Spiked ball (extra {extra_lo}-{extra_hi})"
        elif two_rolls_dual_dagger and len(comps) == 2:
            note = " (2 daggers stab)"
        elif dual_slash_axe_double_damage:
            note = " + (Damage multiplier x2)"

        # If I ever want to use variables over hardcoded text

        lines.append(
            f"{hero.champion_of_light} {label}: {lhs} damage with "
            f"{weapon.type} (weapon range {weapon.raw_weapon_damage}){note} "
            f"→ {monster.champion_of_darkness} takes "
            f"{net} damage due to armour {monster_armour_during_hero_attack}"
            + (" (Damage capped to 1HP due to Ghost Shield)" if capped else "")
            + (" (Whip ignores standard armour)" if ignore_armour_whip else "")
        )

    for i, (raw, net, monster_strike_capped) in enumerate(zip(
                                       monster_raw_damage,
                                       monster_actual_damage,
                                       monster_cap_flags), start=1):
        label = f"strike {i}" if monster_strikes > 1 else "strike"
        lines.append(
            f"{monster.champion_of_darkness} {label}:"
            f" {raw} damage (weapon range {monster.raw_monster_damage})"
            f" → {hero.champion_of_light} takes {net} damage due to"
            f" armour {hero_armour_during_monster_attack}"
            + (" (Damage capped to 1HP due to "
               "Spectral Shield)" if monster_strike_capped else "")
        )

    lines += [
        f"{hero.champion_of_light} HP: {hero_hp} → {hero_hp_after_strikes}",
        f"{monster.champion_of_darkness} HP: {monster_hp} → "
        f"{monster_hp_after_strikes}",
    ]

    # show post-round effect (if any) + final HP after effects (+ or -)
    for note in specials_applied:
        lines.append(f"[Post-round] {note}")
    if specials_applied:
        lines += [
            f"[After effects] {hero.champion_of_light} HP = {new_hero_hp} ;"
            f" Armour = {hero.armour}",
            f"[After effects] {monster.champion_of_darkness} "
            f" HP = {new_monster_hp} ; Armour = {monster.armour}"
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
        "hero_raw_total":    sum(total for (_base, total) in hero_raw_totals),
        "hero_net_total":    dmg_to_monster,
        "monster_raw_total": sum(monster_raw_damage),
        "monster_net_total": dmg_to_hero,
        "specials_applied":  specials_applied,
        "outcome": outcome,
        "lines": lines,
    }
    return new_hero_hp, new_monster_hp, report


def battle_loop(hero, weapon, monster, combat_rows):
    round_no = 1
    hero_hp = hero.hit_points
    monster_hp = monster.hit_points

    while True:
        # no revives now if you dropped to 0 or below after combat round
        hero_hp, monster_hp, rep = resolve_simultaneous_round(
            hero, weapon, monster, hero_hp, monster_hp, allow_revive=False,
            hero_max_hp=hero.hit_points,
        )

        # Show what happened current round
        print()
        print(stat_block(f"Battle round {round_no}", rep["lines"]))

        # Log this round into the combat log
        combat_rows.append([
            rep["hero_raw_total"],      # damage done (pre-armour) by hero
            rep["hero_net_total"],      # Damage inflicted to monster after arm
            rep["monster_raw_total"],  # damage received by hero raw before arm
            rep["monster_net_total"],  # actual damage taken by hero after amr
            hero.special or "—",        # Hero ability (just text for nwo)
            monster.special or "—",     # Monster ability (just text)
            weapon.special or "—",      # Weapon ability (just text)
            hero.armour,        # log Hero armour after effects
            monster.armour,     # log armour Monster after all effects
            hero_hp,        # log Hero HP at hte end of battle round
            monster_hp,         # log Monster HP end of round
        ])

        # Outcome banner for good win, bad win and both kill
        if rep["outcome"] == "double_ko":
            print(stat_block("Battle result",
                             [f"Double kill! Both "
                              f"{monster.champion_of_darkness}"
                              f" & {hero.champion_of_light} fall."]))
            break
        elif rep["outcome"] == "monster_defeated":
            print(stat_block("Battle result",
                             [
                                 f"{monster.champion_of_darkness}"
                                 f" is defeated!"
                             ]
                             +
                             [
                                 f"{hero.champion_of_light}"
                                 f" slayed the servant of darkness!"
                             ]
                             ))
            break
        elif rep["outcome"] == "hero_defeated":
            print(stat_block("Battle result",
                             [
                                 f"{hero.champion_of_light} is defeated!"
                             ]
                             +
                             [
                                 f"{monster.champion_of_darkness}"
                                 f" stands on top of the broken"
                                 f" body of your hero!"
                             ]
                             ))
            break

        # for player to have option to continue or flee
        choice = input("Press Enter to continue, or"
                       " 'F' + Enter to "
                       "flee the battle: ").strip().lower()
        if choice == "f":
            print(stat_block(
                "Battle",
                [
                    f"{hero.champion_of_light} disengages"
                    f" and flees from battlefield. "
                ]
                +
                [
                    f"{monster.champion_of_darkness} is too"
                    f" powerful for our hero."
                ],
            ))
            break

        round_no += 1

    return hero_hp, monster_hp, rep["outcome"]


# --- Data classes ---


@dataclass
class Hero_Character:
    champion_of_light: str
    armour: int
    hit_points: int
    # (spec. ability name)
    special: str = ""
    # (adding description for special ablity)
    special_desc: str = ""


@dataclass
class Monster_Character:
    champion_of_darkness: str   # B column
    armour: int     # (Column C)
    damage_min: int     # from E column
    damage_max: int     # also from E column
    hit_points: int  # Columnd D
    raw_monster_damage: str
    special: str = ""   # (cloumn F)
    special_desc: str = ""  # (column G)


@dataclass
class Weapon:
    type: str
    damage_min: int
    damage_max: int
    raw_weapon_damage: str
    # in case I add description for special
    special: str = ""
    # and I might decide that "description" is pulled from cell


SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

# Mika Tarkinsen told me to add this as early warning
# so I know what to fix when I start getting auth error
# that i had no idea what was going on
creds_json = os.environ.get("CREDS")
if not creds_json:
    raise RuntimeError(
        "Missing CREDS env var. Heroku > Settings > Config Vars."
    )

CREDS = Credentials.from_service_account_info(
    json.loads(creds_json))

CLIENT = gspread.authorize(CREDS.with_scopes(SCOPE))


# this is to use the correct ID (with the hyphen after the 1
# I was missing all this damn time)
SHEET_ID = os.environ.get(
    "SHEET_ID",
    "1-QrsVmnaWtkZMZV8pu5HJkQnQXWFyk3LPyD9UdntkLI",
    )


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


# this could be removed, but I feel it might be better to keep it
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
        champion_of_darkness=str(m_class),
        armour=m_armour,
        damage_min=m_min,
        damage_max=m_max,
        hit_points=m_hp,
        raw_monster_damage=m_raw,
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
            champion_of_darkness=str(b),
            armour=armour,
            damage_min=m_low,
            damage_max=m_high,
            hit_points=hp,
            raw_monster_damage=raw,
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
             # special ability (we are on now!!)
             special=(c or "").strip(),
             # in case description for spec ability is added
             
         ))
    return weapons


def coerce_int_strict(val, label):
    """Turn a cell into an int. Accepts '99' or '99.0'.
    Rejects ranges like '2-4'."""
    s = str(val).strip()
    if re.fullmatch(r"\d+(\.0+)?", s):
        return int(float(s))
    raise ValueError(f"{label} must be a single number, got {val!r}")


def ensure_combat_ws(sh):
    """Get or create the 'Combat' sheet and write the header."""
    try:
        combat_ws = sh.worksheet("Combat")
        # This is not to touch existing data
        # Thank you Alvaro Fillipe from Stack
        return combat_ws
    except gspread.exceptions.WorksheetNotFound:
        combat_ws = sh.add_worksheet(title="Combat", rows=200, cols=11)

    # Combat headers (A1-K1)
    header = [
        "Damage done",      # hero raw pre-armour absorption (weapon mult inc)
        "Damage inflicted",     # hero damage after armour absorption
        "Damage received",  # monster raw damage done pre-armour absorption
        "Damage taken",     # monster net dmg to hero (after armour absorption)
        "Hero ability",     # shonw as text (expanstion possible later)
        "Monster ability",      # shown as text
        "Weapon ability",       # shown as text for now
        "Armour Hero",      # after post-round effects - end of the round
        "Armour Monster",   # after post-round effects -end of battle round
        "Hero HP",          # end-of-round at the end of the round
        "Monster HP",       # after regular and special take effect
    ]
    combat_ws.update(values=[header], range_name="A1:K1")
    return combat_ws

    # Thanks Alvaro


def write_combat_rows(combat_ws, rows, add_separator=True, use_dash_line=True):
    """
    Append battle's rows to the bottom of the 'Combat' sheet.
    """
    if not rows:
        return

    # to detect if there is anything under header
    has_previous_battles = bool(combat_ws.acell("A2").value)

    batch = []
    if add_separator and has_previous_battles:
        # put dashed across all 11 columns, or leave blank (fallback safety)
        sep = (["────────"] * 11) if use_dash_line else ([""] * 11)
        batch.append(sep)

    batch.extend(rows)

    # Append in one shot (newer gspread). Fallback to append_row (older vers)
    try:
        combat_ws.append_rows(batch, value_input_option="USER_ENTERED")
    except AttributeError:
        for r in batch:
            combat_ws.append_row(r, value_input_option="USER_ENTERED")

# things (heroes, vilins, weapons) to
# load from Google Sheets
# =========================


def load_from_gsheets():
    # I am using Key ID rather than name (CLIENT.open)
    sh = CLIENT.open_by_key(SHEET_ID)

# THIS IS FOR DEBUGFOR INCREASE OF STATS
    # I am keeping this one-time debug:
    # despite my modifications in Sheet are seen now
    print(f"\n[List ID] Using sheet id: {SHEET_ID}")
    print("[Name of tabs] Tabs:", [ws.title for ws in sh.worksheets()])
    heroes_ws = sh.worksheet("Heroes")
    # ------------------------------------------------------------------

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
    print("Welcome to battle")

    heroes, weapons, monsters = load_from_gsheets()


# Keeping this debug as it will serve me as a list for players
# DEBUG: verify we read HP/Armour/Special from the sheet
    print("\n[Heroes list] Loaded heroes:")
    for idx, h in enumerate(heroes, start=2):  # start=2 ≈ sheet row 2
        print(
            f"  Heroes!row {idx}: {h.champion_of_light}, "
            f"HP={h.hit_points}, Armour={h.armour}, Special={h.special!r}"
        )

# choose hero now that we have aditional hero in play
    hero_names = [h.champion_of_light for h in heroes]
    picked_name = choose_from_list("Choose your Hero", hero_names)
    hero = next(h for h in heroes if h.champion_of_light == picked_name)

# List of Monsters + abilities
    print("\n[Monster list] Loaded monsters:")
    for idx, m in enumerate(monsters, start=2):  # start=2 ≈ sheet row 2
        print(
            f"  Monsters!row {idx}: {m.champion_of_darkness}, "
            f"HP={m.hit_points}, Armour={m.armour}, "
            f"Damage={m.raw_monster_damage}, Special={m.special!r}"
        )

# choose monster (by class)
    monster_names = [m.champion_of_darkness for m in monsters]
    picked_monster = choose_from_list("Choose your Opponent", monster_names)
    monster = next(m for m in monsters if
                   m.champion_of_darkness == picked_monster)

# List of Weapons
    print("\n[Weaponry] Loaded weapons:")
    for idx, w in enumerate(weapons, start=2):  # start=2 ≈ sheet row 2
        print(
            f"  Weapons!row {idx}: {w.type}, "
            f"Damage={w.raw_weapon_damage}, "
            f"Special={w.special!r}"
        )

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
        [f"Damage: {weapon.raw_weapon_damage} (parsed "
         f"{weapon.damage_min}-{weapon.damage_max})"],
    ))
    print(stat_block(
        f"Monster: {monster.champion_of_darkness}",
        [
            f"Armour: {monster.armour}",
            f"Hit Points: {monster.hit_points}",
            f"Damage: {monster.raw_monster_damage} (parsed"
            f" {monster.damage_min}-{monster.damage_max})",
            f"Special: {monster.special or '—'}",
        ],
    ))

    # Prepare in-memory combat log and Round 0 (starting values)
    combat_rows = []
    combat_rows.append([
        0,      # Damage done
        0,      # Damage inflicted
        0,      # Damage received
        0,      # Damage taken
        hero.special or "—",        # Hero ability (just text)
        monster.special or "—",     # Monster ability (jsut text)
        weapon.special or "—",      # Weapon ability (just text)
        hero.armour,        # Armour Hero (starting value)
        monster.armour,     # Armour Monster (starting value)
        hero.hit_points,        # Hero HP (starting value)
        monster.hit_points,     # Monster HP (starting value)
    ])

    # Still need this until someone dies or hero runs away
    final_hero_hp, final_monster_hp, outcome = battle_loop(
        hero, weapon, monster, combat_rows
    )

    # Flush the combat log to the "Combat" sheet in one go
    sh = CLIENT.open_by_key(SHEET_ID)      # safe: one extra open per run
    combat_ws = ensure_combat_ws(sh)
    write_combat_rows(combat_ws, combat_rows)
    print("\n[Log] Wrote combat log to 'Combat' sheet.")


if __name__ == "__main__":
    main()
