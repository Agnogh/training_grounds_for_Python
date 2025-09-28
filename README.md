
## 1 Game Overview
### 1a *Theme & Inspiration*

Inspired by pen-and-paper RPGs and old-school dungeon crawlers.

Designed around balance: tougher heroes tend to have weaker specials and vice-versa (and similarly for monsters & weapons).

### 1b *Design Goals*

Transparent math: every strike prints the rolls and Armour interactions.

Readable log: each round (including “starting state”) is saved to a “Combat tab” (worksheeet)in Google Sheets.

Simple, replayable loop: choose hero, weapon, monster → fight → optionally flee

Player has 10 hero characters and 5 monsters (enemies) to choose from. 
Selection is possible for your heroes, weapons and monsters.
Follow on screen instructions and description text to make selection easier. Then when combat starts again follow printout to see progress of the battle and decide after each battle round if combat will continue or will your hero disengagge.


## 2 Game rules

### *A Battle Round consists of:*

Combat round -> Simultaneous Strikes (Hero ↔ Monster) but using just "regular" attack

Post-Round Special Effects that can increase, reduced hit points, or have have effect on opponent armour.

Player controls only the Hero and can pick weapons to equip hero

Monsters come with "build in weapons" (claws, fangs, mystical powers)

You can withdraw your hero at the prompt (press any key to continue, or 'F' to flee).
This prompt will show before new round begins as long as either both characters (hero and monster) are still standing/alive. 

Damage & Armour are applied per strike. Some weapons/skills ignore or reduce Armour.

HP can go below 0 for both sides (by design), so overkill is visible in logs.


## 3 Characters & Gear
### 3a *Heroes*

Hero list: 
*Royal Guard*, *Rogue*, *Assassin*, *Knight*, *Paladin*, Crusader*, *Mage*, *Priest*, *Cleric*, *Druid*

Each hero has: Armour, HP, and an optional Special ability

### 3b *Monsters*

Monsters list: *Vampire, Skeleton, Werewolf, Wraight, Zombie*

Each monster has: Armour, HP, Damage Range, and in some cases Special ability.

### 3c *Weapons*

List of weapons: *Spear, Dual daggers, Shadow blade, Flail, Long sword, Axe, Staff, Mace, Whip, Hammer*

Weapons define base damage ranges and sometimes have special rules:


## 4 Special abilities in gameplay

### 4a *Heros special abilities*
Royal Guard     ->      *Veteran warrior* - Starts high HP

Rogue       ->      *Quick hands* ability to attack 2 times per round (extra attack)

Assassin       ->      *Deadly poison* Poison damage (2 HP damage if armour was bypassed)

Knight       ->      *Extra Armour* Extra Armour applied

Paladin       ->      *Healing touch* Can heal oneself 1 HP per turn

Crusader       ->      *Destroys undead* Damages undead enemies 1HP per turn (ignores enemy armour)

Mage       ->      *Fireball* 1 fire damage per round (ignores armour)

Priest       ->      *Spectral shield* Hero can take max 1 damage (after armour was bypasssed)

Cleric       ->      *Holly might* Takes down enemy armour each round by 1

Druid       ->      *Thorns Shield*	Every successful attack on hero returns 1 damage back to enemy (ignores enemy armour)



### 4b *Monsters special abilities*

Vampire     ->      *Drain life* Every sucessfull attack regenerates 1HP to monster

Skeleton     ->      *Armoured* High armour applied 

Werewolf     ->      *Shread armour* Every successful attack reduces hero armour by one

Wraight     ->     *Ghost shield* Can receive max 1 damage per attack (after armour is bypassed)

Zombie     ->      *Death grip* Does extra 1 damage (ignores hero armour)



### 4c *Weapons special abilities*

Dual daggers        ->      *Double stab* Attack 2 times (1-3) + (1-3) but armour defense is applied once

Flail        ->      *Spiked ball on chain* -> 0-3 + (0-6)

Axe        ->      *Deep slash* -> Damage (0-4) is multipled by 2 = (0, 2, 4, 6, 8)

Whip        ->      *Lash me gently* Ignores armour

Hammer        ->      *Shield breaker* -> Destroys 1 armour after each succesful attack



## 5 How Combat Works (Detail)

### *Rolls*

Hero: 1 (or 2 due to special ability) strikes

Monster: 1 strike (currently there are no monsters with dual strike).

### *Armour & Caps*

Armour is applied per strike using the snapshot armour at strike time. Snapshot is used to display status or armour during Combat round as in next battle round armour might be reduced=

Caps (Ghost shield/Spectral shield) reduce per strike net damage to 1 (after armour has been applied).

### *Post-Round Effects*

To see the list of post round effects check 
## 4 Special abilities in gameplay

### *Display*

- First lines show combat round - strike math and HP after strikes (before specials).

- Then [Post-round] (when special abilities are applied) notes for each effect.

- Finally [After effects] lines show final HP/Armour.



## 6 Quality
### 6a *Testing*

Manual testing of all heroes, monsters, and weapons to verify:

Testing was done by me and random folks I managed to stop and ask them to give game a try on my laptop while they drink coffee, hot choco, or in most cases (since I am in Ireland) alchocol despite it was early morning on workday.

Bugfixes
Damage math matches printed rolls.

Ghost/Spectral caps apply correctly.

Armour snapshots display the armour used during the strike, not the post-round modified value. (error was that current armour value was calculated after it was reduced, but shown during initial combat round)

Hit Points caluclated correctly take into account Damage inficted, armour on the recieveing end, total hit point defender has and any speciala ability that might interfreere with Hit Points caluclation

Specials trigger only when conditions are met.
All Relevant special are triggering for coresponsding hero, monster and weapon and only when it is needed

PEP8 validation: pass (via pycodestyle / pep8).

### 6b *Fixed Bugs (highlights)*

Immortal Paladin & Vampire interactions resolved.
-> Since it was set that heros and monsters cannot drop below 0Hit points, Paladin healed himself and Vamire drained life (both for 1HP) triggering that Battle round goes on indefinatly

Flail extra damage not applied → fixed (reads extra range from text; defaults to 0–6).
-> Fixed in the way how we get the info from the spreadsheat 

Output refinements for Axe (×2 math shown) and Dual Daggers/Flail (show components).
-> a bit confusing in the code and not set properly for when writing the code, but esentially, seperated code was done so that dual damage and double damage are not the same (as they shouldn't be)

HP display now shows “after strikes, before specials” and then “after effects.”
-> This is due to not thinking about the need that final Hit Points was displayed and we had a formated text showing hit points after combat round (so after regular attack). That showed, that despite math was correct, final amount of hit points was shown before special abilities displayed making it look like as if the special abilities are nto calculating correctly hit points.

Armour shown reflects the armour at the time of each strike (not the post-round value).
-> Simialr as with hit points, but this was order of writing code. In formated string, it displayed already reduced armour, despite deduction will take place in next round and not current one. Math was correct, just display was no in its place.

Several specials originally clamped HP at 0 → now can drop below 0 to show overkill.
-> Decided to drop below 0 Hit points due to Paladin and Vampire abilities as reviwing from 0 to 1 will keep hero on monster in play. But reviwing from -3 to -2 will not keep them in play

Monster damage was using min instead of max in some branches
-> Copy/paste issue where I forgot to chaneg to mac for monster max damage 

## 7 Google Sheets Integration

The game reads Heroes, Weapons, and Monsters from tabs in a Google Sheet.

All combat rounds are written to a Combat tab with headers:

A: Damage done         (hero raw pre-armour)
B: Damage inflicted    (hero net → monster after armour/caps)
C: Damage received     (monster raw to hero)
D: Damage taken        (monster net → hero after armour/caps)
E: Hero ability        (text)
F: Monster ability     (text)
G: Weapon ability      (text)
H: Armour Hero         (end of round, after specials)
I: Armour Monster      (end of round, after specials)
J: Hero HP             (end of round, after specials)
K: Monster HP          (end of round, after specials)


A Round 0 row is logged first with starting HP/Armour.

When multiple battles are played, a dashed separator row is added.

Share the sheet with your Google service account email (found in the JSON) so the app can read/write.

I had a fare share of setbacks with this as I did expose keys not once but twice. I created new speradsheet and managed (with the help of kind people from stack like *Sophie*, *Hilla* and *Mika*) to remove commits that contained exposed keys. 

All combat rounds are logged to Google Sheets for tracking &auditing.
##### *https://docs.google.com/spreadsheets/d/1-QrsVmnaWtkZMZV8pu5HJkQnQXWFyk3LPyD9UdntkLI/edit?gid=0#gid=0*

## 8 Tech Stack

Python (game logic, Google Sheets I/O via gspread + google-auth)

Node.js + Express (serves a web terminal UI; Code Institute template)

Heroku (hosting)

Google Sheets API (data source + combat log)



## 9 Deployment to Heroku

### *One-time app setup*

#### *Add buildpacks (order matters):*

Node.js
Python

#### *Set Config Vars (Settings → Config Vars):*

CREDS → I paste the entire Service Account JSON
SHEET_ID was not used despite folks from Stack advised to do so

#### *Procfile* should be:*

web: node index.js


### Deploy

Despite I found this on YouTube
*heroku login*

*heroku git:remote -a <my-app-name>*

*git push heroku main*

*heroku open*
I decided to go with "confirmed option" and linked the project in Heroku by selecting GitHub > Link the project > Add



## 10 *Known Limitations / Future Ideas*


I had lots of ideas but project is already strecthd outside of the time allocated and folkd from Code Institute will not grant me more time so i had to cut it short.


*- Monsters currently perform 1 strike; multi-strike monsters would be fun

*- Add more abilities with richer conditions*

*- % to hit with some range weapon that would either have greater damage or multiple attacks to balance*

*- stun where monster or hero would skip their next attack chance*

*- prolonged damage where there would be "bleeding wounds" thta keep draining HP, or poison that keep damaginf, or fire that keeps burning*

*- lifesteal variants -> where HP would be drained from one character to another (-1 HP fo rone side and +1 HP for the other side)*

*- cloack of invisibility -> where one side could complety avoid first attack*

*- smoke bomb -> where damage recieved would be halved*

*- fury -> next attack does double damage*

*- sacrifice -> character loses certain amount of HP, but does tripple damage*

*-Front-end polish (animations, color coding for damage/heal/caps).*


## 11 Credits & Thanks

Template: Code Institute Python Essentials Template (web terminal).

Mentorship & sanity-saver: you know who you are.

Libraries: gspread, google-auth, Node/Express.


## 12 Final note

This project grew from curiosity into a fully hosted, auditable little battler. Have fun breaking it—and the log will tell you exactly how wild the combat can get. 💥

I especially had so much setbacks with google spreadsheet as I have pushed multiple times my key so i was panicking around to ge tit removed. Learned finally how to do it

Other pretty insane setback was deplying to Heroku. Error on my part that I didn't read how I should be using template from Code institute, but took me full 2 days to figure out what files I need to have in order to push/connect the damn thing with GitHub.

In both cases there were some nice folks on Stack Overflow like Alvaro, Mika, Asia, Hilla, Jeheeya, Sophie that helped me with ideas and suggestions and command lines to try out

Bless their hearts

### 12a Thanks

- Thank to folks from Stack Overflow

- Thanks to person that invented YouTube and bunch of enthusiastic peopel sharing their work on YouTube, 

- Thanks to random folks in the coffee shop for QAing the game 

- Thanks for my team at work that they are complety useless so I could write code during working hours and still outperform most of them.

#### I put way more time than expected after redoing the project, but I loved doing it. Connecting to spreadsheet was pain as I (again) exposed the keys so I had to nuke the sheet and start over

### Other setback was with Heroku deployment that is really easy but for some reason I got stuck on it for several hours



"# venvmodule" 
# Python battle grounds







![CI logo](https://codeinstitute.s3.amazonaws.com/fullstack/ci_logo_small.png)



## Reminders

- Your code must be placed in the `run.py` file
- Your dependencies must be placed in the `requirements.txt` file
- Do not edit any of the other files or your code may not deploy properly

## Creating the Heroku app

When you create the app, you will need to add two buildpacks from the _Settings_ tab. The ordering is as follows:

1. `heroku/python`
2. `heroku/nodejs`

You must then create a _Config Var_ called `PORT`. Set this to `8000`

If you have credentials, such as in the Love Sandwiches project, you must create another _Config Var_ called `CREDS` and paste the JSON into the value field.

Connect your GitHub repository and deploy as normal.

## Constraints

The deployment terminal is set to 80 columns by 24 rows. That means that each line of text needs to be 80 characters or less otherwise it will be wrapped onto a second line.

---

Happy coding!
