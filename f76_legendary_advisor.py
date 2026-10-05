#!/usr/bin/env python3
"""
f76_legendary_advisor.py
========================
Decide what to do with a Fallout 76 legendary item:

    KEEP  |  SCRAP (learn the mod)  |  CAMP VENDOR SELL  |  LEGENDARY EXCHANGE (scrip)  |  NPC VENDOR SELL

Usage
-----
    python f76_legendary_advisor.py melee --one Juggernaut's --two Riposting --three Lightweight
    python f76_legendary_advisor.py ranged --one Quad --two Rapid --three "V.A.T.S. Optimized" --rate fast --build commando
    python f76_legendary_advisor.py armor --one Unyielding --two Luck --three Sentinel's --four Limit-Breaking --build bloodied
    python f76_legendary_advisor.py pa --one Overeater's --two Powered --three Thru-hiker's
    python f76_legendary_advisor.py armor --one Bolstering --json
    python f76_legendary_advisor.py --list ranged 1

All of --one/--two/--three/--four are optional. Effect names are matched
case-insensitively and ignore punctuation ("vats optimized" == "V.A.T.S. Optimized",
"aa" == "Anti-Armor").

The tier data is the comprehensive community tier-list database (280 category
rows / ~142 distinct effect names, covering every 1st-4th star legendary
effect obtainable on ranged weapons, melee weapons, armor and power armor),
embedded below. Point --tierfile at an updated copy of that file to override it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap

# ---------------------------------------------------------------------------
# 1. EMBEDDED TIER LIST (the supplied standard; override with --tierfile)
# ---------------------------------------------------------------------------

EMBEDDED_TIERLIST = """
FALLOUT 76 LEGENDARY MOD TIER LIST - COMPREHENSIVE EDITION
Purpose: Program-readable reference for evaluating legendary effects.
Source basis: the full legendary-crafting effect catalog (every effect obtainable
via random roll or crafted with Legendary Modules at a legendary crafting bench),
cross-referenced against current community consensus as of September 2026.
This supersedes the original shorter tier-list file. It covers every 1st, 2nd,
3rd and 4th-star effect currently craftable/droppable for each item category.

Tier meanings:
S = extremely desirable / commonly part of top-end builds
A = excellent / generally worth keeping
B = good but situational
C = usable but usually replaceable
D = niche / mostly convenience
F = generally not worth keeping

NOTE: Effect value is weapon/build dependent. This file provides general
community-opinion tiers, not absolute rankings. Tiers reflect general-purpose
usefulness; a "D" effect can be an "S" effect for the one build it's built for
(e.g. Feral's only matters to ghoul melee characters).

COVERAGE NOTE: this file lists every effect once per item category it can
legally appear on, at every star rank it can appear at. Many effect names
(Strength, Luck, Durability, etc.) appear more than once because the same
name exists as a different-tier mod on different item types (e.g. "Agility"
is a 2-star Armor/PA stat mod AND a separate 3-star Ranged/Melee stat mod).
Counted this way there are 280 category-specific rows covering roughly 140
distinct effect names. 4-star effects only exist via legendary crafting or on
unique unlearned items; they do not drop randomly as of this writing.

[RANGED_WEAPONS]
[1_STAR]
S|Quad|+300% ammo capacity; excellent on many automatic/rapid-fire weapons
S|Anti-Armor|+50% Armor Penetration; strong general-purpose damage vs high-resistance enemies
S|Bloodied|Damage increases up to +130% as Health decreases; huge low-health ceiling
S|Two Shot|+1 projectile, +75% damage, at the cost of accuracy/recoil; strong on many weapons
A|Vampire's|Restore 2% Health over 2s per hit; excellent survivability on fast-firing weapons
A|Aristocrat's|Up to +50% damage based on caps held; strong while maintaining high caps
A|Junkie's|Damage increases per active addiction, up to +100%; strong for deliberate addiction builds
B|Instigating|+50% damage vs targets above 60% Health; excellent opening/single-shot damage
B|Executioner's|+50% damage vs targets below 40% Health; strong finishing damage
B|Furious|+5% damage per Onslaught stack (up to 9 stacks); good sustained single-target damage
B|Juggernaut's|Damage increases up to +100% as Health increases (full-health ceiling)
B|Stalker's|+100% Sneak Attack damage; strong for stealth/sniper playstyles
B|Sniper's|+100% damage to distant targets; excellent for dedicated long-range rifles
C|Troubleshooter's|+50% damage to Robots, -15% damage from them on armor
C|Ghoul Slayer's|+50% damage to Ghouls, -15% damage from them on armor
C|Mutant Slayer's|+50% damage to Super Mutants, -15% damage from them on armor
C|Zealot's|+50% damage to Scorched, -15% damage from them on armor
C|Hunter's|+50% damage to Animals, -15% damage from them on armor
C|Mutant's|Damage increases up to +50% as you gain mutations
C|Berserker's|Damage increases up to +50% as Damage Resistance decreases; niche for unarmored builds
D|Assassin's|+50% damage to Humans; mostly PvP/human-target focused
D|Exterminator's|+50% damage to Mirelurks and Insects; very niche
D|Nocturnal|+50% damage while Cloaked; situational, needs a stealth-boy/cloak build
D|Suppressor's|Reduce target's damage output by 25% for 5s; defensive utility, less valuable than damage
D|Adrenal|+10% damage per kill while on a Kill Streak; niche, resets on death/downtime
D|Gourmand's|Damage increases up to +40% as Hunger/Thirst are filled; requires active upkeep
D|Lucid|(Ghoul only) Damage scales with Feral meter; niche, ghoul-character-specific
D|Medic's|Attacks heal friendly targets by 5% Health; support utility, minimal solo value

[2_STAR]
S|Explosive|Projectiles explode for +20% weapon damage; excellent general utility on compatible weapons
S|Rapid|+25% weapon speed (fire rate); excellent on automatic weapons
S|Vital|+50% Critical damage; very strong for VATS crit builds
A|V.A.T.S. Enhanced|+50% chance to hit a target in VATS; excellent for VATS-focused weapons
B|Hitman's|+25% damage while aiming; good for aiming-down-sights builds
B|Crippling|+50% limb damage; useful utility for cripple-focused play
B|Inertial|Replenish 15 AP per kill; useful AP-sustain utility
C|Last Shot|Last round in the magazine has a 25% chance to deal +100% damage; weapon dependent
D|Basher's|+50% bash damage; mostly bash-oriented niche builds

[3_STAR]
S|V.A.T.S. Optimized|-35% VATS Action Point cost; excellent for VATS weapons
S|Swift|+15% reload speed; excellent sustained-combat utility
A|Lucky|+15 bonus VATS critical charge; excellent VATS utility
A|Lightweight|-90% weapon weight; strong convenience/weight reduction
A|Durability|Breaks 50% slower; excellent quality of life
B|Nimble|+100% faster movement speed while aiming; good mobility
B|Ghost's|10% chance to turn invisible for 2s on hit; useful defensive utility
B|Resilient|+500 Damage Resistance while reloading; situational survivability
B|Luck|+3 Luck; useful for VATS crit chance and general Luck-dependent perks
B|Steadfast|+50 Damage Resistance while aiming; niche defensive utility
C|Agility|+3 Agility; useful depending on build
C|Perception|+3 Perception; useful depending on build
C|Endurance|+3 Endurance; useful depending on build
C|Strength|+3 Strength; useful depending on build (carry weight/melee synergy on ranged is weak)
C|Intelligence|+3 Intelligence; mostly XP-gain value
D|Charisma|+3 Charisma; mostly team/support utility
D|Glowing|Kills generate rads (human) or glow (ghoul); largely a downside/gimmick effect

[4_STAR]
S|Pin-Pointer's|+20% weak spot damage; excellent for precision/VATS-headshot builds
S|Bully's|+25% damage per crippled limb the target has; excellent alongside Crippling/limb-focused builds
A|Encircler's|+10% damage per nearby combat target (up to +50%); strong in crowded fights
A|Tarnished|Damage increases up to +120% as weapon durability decreases; strong late-fight scaling, punishing early
A|Conductor's|Crits restore Health/AP to you and nearby teammates; strong team-support/crit synergy
B|Polished|Damage increases up to +60% the higher your weapon condition; rewards keeping guns repaired
B|Fracturer's|Crippling a limb causes an explosion dealing damage to nearby targets
B|Pyromaniac's|+50% bonus damage vs burning targets; strong paired with fire weapons/mods
B|Viper's|+50% bonus damage vs poisoned targets; strong paired with poison weapons/mods
B|Thrill-Seeker's|Reload speed increases with Kill Streak count
B|Stabilizer's|+50% improved weapon recoil and stability; solid QoL for full-auto weapons
C|Severing|+50% damage to bleeding targets; niche, needs a bleed source
C|Electrician's|Reloading emits a stun shockwave; niche crowd-control utility
C|Satiated|Kills restore Hunger/Thirst (or Feral for ghouls); minor convenience

[MELEE_WEAPONS]
[1_STAR]
S|Anti-Armor|+50% Armor Penetration; excellent general-purpose damage
S|Bloodied|Damage increases up to +130% as Health decreases; massive low-health ceiling
A|Vampire's|Restore 2% Health over 2s per hit; excellent survivability with rapid attacks
A|Aristocrat's|Up to +50% damage based on caps held; excellent full-health damage option
A|Junkie's|Damage increases per active addiction, up to +100%; strong if maintaining addictions
A|Instigating|+50% damage vs targets above 60% Health; excellent for huge single-hit weapons
B|Furious|+5% damage per Onslaught stack (up to 9 stacks); good sustained single-target damage
B|Executioner's|+50% damage vs targets below 40% Health; strong finishing damage
B|Juggernaut's|Damage increases up to +100% as Health increases; decent full-health option
B|Mutant's|Damage increases up to +50% as you gain mutations
C|Troubleshooter's|+50% damage to Robots
C|Ghoul Slayer's|+50% damage to Ghouls
C|Mutant Slayer's|+50% damage to Super Mutants
C|Zealot's|+50% damage to Scorched
C|Hunter's|+50% damage to Animals
C|Berserker's|Damage increases up to +50% as Damage Resistance decreases; niche unarmored builds
C|Feral's|(Ghoul only) Target kills make you go feral faster; strong but only for ghoul melee builds
D|Assassin's|+50% damage to Humans; PvP/human-target focused
D|Exterminator's|+50% damage to Mirelurks and Insects; very niche
D|Nocturnal|+50% damage while Cloaked; needs a stealth setup, awkward on melee
D|Suppressor's|Reduce target's damage output by 25% for 5s
D|Adrenal|+10% damage per kill while on a Kill Streak; niche
D|Gourmand's|Damage scales with Hunger/Thirst upkeep; niche
D|Lucid|(Ghoul only) Damage scales with Feral meter; niche
D|Medic's|Attacks heal friendly targets by 5% Health; minimal solo value

[2_STAR]
S|Rapid|+40% weapon speed; classic melee god-roll effect
S|Heavy Hitter's|+40% Power Attack damage; excellent melee damage on compatible weapons
A|Vital|+50% Critical damage; strong for VATS crit melee builds
B|Crippling|+50% limb damage
B|Inertial|Replenish 15 AP per kill
B|Steady|+25% melee damage while not moving; strong for stationary tanks
B|Riposting|+50% blocked-damage reflection; strong on block-focused weapons
D|Pick Pocketer's|50% chance for a small amount of caps on target kills; gimmick

[3_STAR]
S|Strength|+3 Strength; classic melee god-roll third star (damage + carry weight)
S|V.A.T.S. Optimized|-35% VATS Action Point cost; excellent for VATS melee
A|Lucky|+15 bonus VATS critical charge
A|Luck|+3 Luck
A|Durability|Breaks 50% slower; excellent quality of life
A|Lightweight|-90% weapon weight
B|Blocker|+15% more damage blocked; strong for block-heavy melee builds
B|Defender's|40% chance to automatically block attacks (melee); strong defensive utility
B|Barbarian|+1 Strength per kill while on a Kill Streak (max 10); strong snowballing niche
B|Endurance|+3 Endurance
C|Agility|+3 Agility
C|Perception|+3 Perception
C|Intelligence|+3 Intelligence
D|Charisma|+3 Charisma
D|Glowing|Kills generate rads/glow; largely a downside effect

[4_STAR]
S|Pounder's|+10% damage per Onslaught stack, up to 10 stacks; excellent scaling melee damage
S|Bully's|+25% damage per crippled limb the target has
A|Fencer's|+12.5% melee damage, +12.5% more per nearby teammate (up to +50% full team)
A|Encircler's|+10% damage per nearby combat target (up to +50%)
A|Tarnished|Damage increases up to +120% as weapon durability decreases
A|Icemen's|VATS hits apply a slowing Cryo effect; strong crowd-control utility
B|Conductor's|Crits restore Health/AP to you and nearby teammates
B|Charged|Light attacks build charge released on a Heavy Attack; strong for power-attack builds
B|Polished|Damage increases up to +60% the higher your weapon condition
B|Fracturer's|Crippling a limb causes a small area explosion
B|Pyromaniac's|+50% bonus damage vs burning targets
B|Viper's|+50% bonus damage vs poisoned targets
B|Thrill-Seeker's|Attack speed increases with Kill Streak count
C|Severing|+50% damage to bleeding targets
C|Combo-Breaker's|50% chance to not consume AP on hit (10% for auto-melee); niche AP economy
C|Satiated|Kills restore Hunger/Thirst or Feral meter

[REGULAR_ARMOR]
[1_STAR]
S|Unyielding|Up to +3 to all SPECIAL (except END) as Health drops; defining low-health-build effect
S|Overeater's|Increases max Health up to +40 as Hunger/Thirst are filled; premier full-health defense
A|Aristocrat's|Reflects incoming damage based on caps held (up to 10%); strong with high caps
A|Troubleshooter's|-15% damage from Robots; strong for robot-heavy content/specialized sets
A|Auto Stim|Auto-uses a Stimpak when hit below 25% Health, once every 60s; strong emergency safety net
B|Bolstering|Up to 10% damage reduction at lower Health; useful defensive option
B|Life Saving|50% chance to self-revive with a Stimpak when incapacitated, once/60s
B|Chameleon|Turn invisible while sneaking and not moving; good stealth utility
B|Regenerating|+0.5% Heal Rate; steady passive sustain
C|Vanguard's|Up to 6% damage reduction as Health increases; usable but below top choices
C|Mutant's|Up to 5% damage reduction as you gain mutations
C|Heavyweight|Up to 10% damage reduction at high encumbrance (150%+); niche, requires overweight play
C|Nocturnal|+4 PER/AGI while Cloaked; situational but strong at night with a cloak build
D|Ghoul Slayer's|-15% damage from Ghouls
D|Mutant Slayer's|-15% damage from Super Mutants
D|Zealot's|-15% damage from Scorched
D|Hunter's|-15% damage from Animals
D|Exterminator's|-15% damage from Mirelurks and Insects
D|Assassin's|-15% damage from Humans
D|Adrenal|+10 Damage/Energy Resist per kill on a Kill Streak (max 10); niche
D|Lucid|(Ghoul only) DR scales with Feral meter; niche
D|Cloaking|Being hit in melee grants brief invisibility once/30s; awkward proc condition

[2_STAR]
S|Powered|+5% Action Point regen; universally useful sustain
A|Intelligence|+2 Intelligence; strong for XP/leveling
A|Strength|+2 Strength; strong for carry weight
A|Luck|+2 Luck; strong for VATS crit builds
A|Endurance|+2 Endurance; strong survivability
A|Elementalist|+25 to all resistances (physical/energy/rad/etc.); strong flat all-around defense
B|Agility|+2 Agility; useful AP/stealth utility
B|Poisoner's|+50 Poison Resistance; useful against poison-heavy content
B|Fireproof|+50 Fire Resistance; useful defensive specialization
B|HazMat|+50 Radiation Resistance
B|Warming|+50 Cryo Resistance
B|Hardy|7% less Explosion damage
C|Perception|+2 Perception; build dependent
C|Charisma|+2 Charisma; mostly team/support utility
C|Fierce|Fortifies limb resistance per Kill Streak stack; niche
C|Rushing|Gain AP over time on a Kill Streak; niche
C|Pain Killer|Heal over time on a Kill Streak; niche
D|Antiseptic|+25% reduced disease chance from environmental hazards; very situational
D|Glutton|Hunger/Thirst grow 10% slower; minor convenience

[3_STAR]
S|Sentinel's|-5% damage taken while not moving; strong defensive effect when stationary
S|Arms Keeper's|Weapon weights reduced by 20%; excellent weapon-weight reduction
A|Thru-hiker's|Food/Drink/Chem weights reduced by 20%; major perk-card savings
A|Acrobat's|-50% fall damage; excellent QoL, especially with jetpacks
A|Secret Agent's|-25% sneaking noise, -25% detection chance; strong stealth utility
A|Cavalier's|-10% damage taken while sprinting; strong for players who move/sprint frequently
B|Pack Rat's|Junk item weights reduced by 20%; great for junk-heavy characters
B|Belted|Ammo weight reduced by 20%; good for ammo-heavy characters
B|Doctor's|+5% effectiveness of Stimpaks/RadAway/Rad-X; useful convenience
B|Durability|Breaks 50% slower; good general-purpose option
B|Active|+20 max AP; solid general utility
B|Adamantium|-15% limb damage taken; solid defensive niche
B|Reflex|+2% Evade; small but always-on defensive value
B|Defender's|5% chance to auto-block attacks; niche defensive proc
C|Safecracker's|+1 Lockpicking, +1 Hacking skill; niche
C|Healthy|+20 max HP; minor sustain boost
C|Burning|5% chance to burn melee attackers; minor reactive damage
C|Electrified|5% chance to shock melee attackers; minor reactive damage
C|Frozen|5% chance to freeze/slow melee attackers; minor reactive utility
C|Toxic|5% chance to poison melee attackers; minor reactive damage
C|Vector|+10% bonus VATS accuracy vs distant targets; niche
D|Diver's|Breathe underwater; extremely situational
D|Dissipating|+0.25% radiation damage recovery rate; very marginal

[4_STAR]
S|Limit-Breaking|Each worn armor piece reduces VATS crit cost by 10% (up to -50% full stack); excellent VATS crit builds
S|Ranger's|Ranged weapons deal +5% bonus damage per piece (up to +25%); major ranged damage boost
A|Tanky's|+200 Damage Resist for 10s when standing still, 20s cooldown (up to +1000 full stack); strong defensive option
A|Sawbones's|Passive Health regen, up to +5/s at full stack; strong sustain
B|Runner's|Sprint AP cost reduced up to -100% at full stack; excellent mobility
B|Hauler's|+30 carry capacity per piece; solid QoL
B|Battle-Loader's|Chance to instantly reload when bashing (up to 75% full stack); niche bash-synergy
C|Bruiser's|Melee weapons deal up to +25% bonus damage at full stack; team-support oriented if you don't melee yourself
C|Raging|+3% damage for 10s after being hit; minor reactive damage boost
C|Miasma's|Poisonous DoT cloud on being hit, scales per piece; niche offensive utility

[POWER_ARMOR]
[1_STAR]
S|Overeater's|Increases max Health up to +40 as Hunger/Thirst are filled; premier general-purpose defense
A|Troubleshooter's|-15% damage from Robots; excellent for robot-heavy encounters
A|Aristocrat's|Reflects incoming damage based on caps held; good alternative with high caps
A|Auto Stim|Auto-uses a Stimpak when hit below 25% Health, once/60s; strong safety net
B|Bolstering|Up to 10% damage reduction at lower Health; useful defensive option
B|Regenerating|+0.5% Heal Rate; steady passive sustain
B|Chameleon|Turn invisible while sneaking and not moving
C|Vanguard's|Up to 6% damage reduction as Health increases; usable but less attractive
C|Mutant's|Up to 5% damage reduction as you gain mutations
C|Nocturnal|+4 PER/AGI while Cloaked; situational
D|Ghoul Slayer's|-15% damage from Ghouls
D|Mutant Slayer's|-15% damage from Super Mutants
D|Zealot's|-15% damage from Scorched
D|Hunter's|-15% damage from Animals
D|Exterminator's|-15% damage from Mirelurks and Insects
D|Assassin's|-15% damage from Humans
D|Adrenal|+10 Damage/Energy Resist per kill on a Kill Streak; niche
D|Lucid|(Ghoul only) DR scales with Feral meter; niche
D|Cloaking|Being hit in melee grants brief invisibility once/30s

[2_STAR]
S|Powered|+5% Action Point regen
A|Intelligence|+2 Intelligence; excellent for XP
A|Strength|+2 Strength; carry weight/melee
A|Endurance|+2 Endurance; survivability
A|Luck|+2 Luck; VATS builds
A|Elementalist|+25 to all resistances; strong flat all-around defense
B|Agility|+2 Agility
B|Poisoner's|+50 Poison Resistance
B|Fireproof|+50 Fire Resistance
B|HazMat|+50 Radiation Resistance
B|Warming|+50 Cryo Resistance
B|Hardy|7% less Explosion damage
C|Perception|+2 Perception; build dependent
C|Charisma|+2 Charisma; mostly team/support
C|Fierce|Fortifies limb resistance per Kill Streak stack; niche
C|Rushing|Gain AP over time on a Kill Streak; niche
C|Pain Killer|Heal over time on a Kill Streak; niche
D|Antiseptic|+25% reduced disease chance; very situational
D|Glutton|Hunger/Thirst grow 10% slower

[3_STAR]
S|Sentinel's|-5% damage taken while not moving
S|Arms Keeper's|Weapon weights reduced by 20%
A|Thru-hiker's|Food/Drink/Chem weights reduced by 20%; can eliminate substantial perk investment
A|Cavalier's|-10% damage taken while sprinting
B|Pack Rat's|Junk item weights reduced by 20%
B|Belted|Ammo weight reduced by 20%
B|Doctor's|+5% effectiveness of Stimpaks/RadAway/Rad-X
B|Durability|Breaks 50% slower
B|Active|+20 max AP
B|Defender's|5% chance to auto-block attacks
C|Safecracker's|+1 Lockpicking, +1 Hacking skill
C|Healthy|+20 max HP
C|Burning|5% chance to burn melee attackers
C|Electrified|5% chance to shock melee attackers
C|Frozen|5% chance to freeze/slow melee attackers
C|Toxic|5% chance to poison melee attackers
C|Vector|+10% bonus VATS accuracy vs distant targets
D|Dissipating|+0.25% radiation damage recovery rate; very marginal

[4_STAR]
S|Rejuvenator's|Gradually restores wearer's and teammates' Health/AP in a 50ft radius; outstanding sustain and team support
S|Reflective|Returns up to 50% of damage received back to the attacker at full stack; strong defensive/offensive combo
S|Ranger's|Ranged weapons deal +5% bonus damage per piece (up to +25%); excellent ranged PA damage
S|Limit-Breaking|Each worn armor piece reduces VATS crit cost by 10% (up to -50%); excellent crit-oriented option
A|Aegis|Fortifies resistances for wearer and nearby teammates within 50ft; strong team defensive aura
A|Scanner's|VATS attack AP cost reduced up to -25% at full stack; excellent VATS PA utility
A|Tanky's|+200 Damage Resist for 10s when standing still (up to +1000 full stack)
A|Stalwart's|Power armor breaks 5% slower for you and teammates within 50ft (up to -25% full stack)
B|Propelling|Movement/sprint speed increased up to +25% at full stack; great movement
B|Radioactive-Powered|+2 AP regen at the cost of rads, up to +10 AP at full stack
B|Runner's|Sprint AP cost reduced up to -100% at full stack
B|Sawbones's|Passive Health regen, up to +5/s at full stack
B|Battle-Loader's|Chance to instantly reload when bashing (up to 75% full stack)
B|Hauler's|+30 carry capacity per piece
C|Miasma's|Poisonous DoT cloud on being hit, scales per piece; situational
C|Bruiser's|Melee weapons deal up to +25% bonus damage at full stack
C|Raging|+3% damage for 10s after being hit
D|Choo-Choo's|Chance for bonus damage + "Bloody Mess" when sprinting into targets; mostly fun/gimmick

[QUICK_KEEP_LIST]
RANGED_1_STAR|Quad|Anti-Armor|Bloodied|Two Shot|Vampire's|Aristocrat's|Junkie's
RANGED_2_STAR|Explosive|Rapid|Vital|V.A.T.S. Enhanced
RANGED_3_STAR|V.A.T.S. Optimized|Swift|Lucky|Lightweight|Durability
RANGED_4_STAR|Pin-Pointer's|Bully's|Encircler's|Tarnished|Conductor's
MELEE_1_STAR|Anti-Armor|Bloodied|Vampire's|Aristocrat's|Junkie's|Instigating
MELEE_2_STAR|Rapid|Heavy Hitter's|Vital
MELEE_3_STAR|Strength|V.A.T.S. Optimized|Lucky|Luck|Durability|Lightweight
MELEE_4_STAR|Pounder's|Bully's|Fencer's|Encircler's|Tarnished|Icemen's
ARMOR_1_STAR|Unyielding|Overeater's|Aristocrat's|Troubleshooter's|Auto Stim
ARMOR_2_STAR|Powered|Intelligence|Strength|Luck|Endurance|Elementalist
ARMOR_3_STAR|Sentinel's|Arms Keeper's|Thru-hiker's|Acrobat's|Secret Agent's|Cavalier's
ARMOR_4_STAR|Limit-Breaking|Ranger's|Tanky's|Sawbones's
POWER_ARMOR_1_STAR|Overeater's|Troubleshooter's|Aristocrat's|Auto Stim
POWER_ARMOR_2_STAR|Powered|Intelligence|Strength|Endurance|Luck|Elementalist
POWER_ARMOR_3_STAR|Sentinel's|Arms Keeper's|Thru-hiker's|Cavalier's
POWER_ARMOR_4_STAR|Rejuvenator's|Reflective|Ranger's|Limit-Breaking|Aegis|Scanner's|Tanky's|Stalwart's

[PROGRAMMING_NOTES]
- Treat tiers as general community-opinion priors, not universal rankings.
- Evaluate complete legendary combinations when possible.
- Weapon-specific effects can change value substantially.
- Quad is much more valuable on many rapid-fire weapons than on slow single-shot weapons.
- Instigating is more valuable on high-damage single-shot weapons; worse on fast/automatic ones.
- Vampire's is more valuable as weapon fire/attack rate increases.
- Unyielding is primarily a low-health armor effect; largely dead weight on a full-health build.
- Overeater's is a primary full-health defensive effect for armor and power armor.
- Ghoul-exclusive effects (Feral's, Lucid) are only usable on ghoul characters; they are
  effectively unusable dead rolls for human characters and should be evaluated as such.
- Enemy-specific damage effects (Troubleshooter's, Ghoul/Mutant Slayer's, Zealot's,
  Hunter's, Exterminator's, Assassin's) swing hard by content: strong for a themed
  event/boss, weak as a general-purpose daily driver.
- 4-star effects are primarily obtained via legendary crafting (Legendary Modules) or
  found on certain unique/quest items; they are not part of standard random drop tables
  as of this writing, so treat 4-star recommendations as crafting targets more than
  "should I keep this drop" targets.
- SPECIAL-stat effects (Strength, Agility, Endurance, etc.) exist at both 2-star (Armor/PA,
  +2) and 3-star (Ranged/Melee weapons, +3) tiers as different mods with the same name;
  this file lists them separately under their correct star section.

"""

# The embedded database (comprehensive edition) covers every category/star
# combination directly, so no supplemental patch table is needed any more.
SUPPLEMENTAL = {}

# ---------------------------------------------------------------------------
# 2. PARSING
# ---------------------------------------------------------------------------

TIER_POINTS = {"S": 5.0, "A": 4.0, "B": 2.5, "C": 1.5, "D": 0.5, "F": 0.0}
TIER_ORDER = ["S", "A", "B", "C", "D", "F"]

CATEGORY_ALIASES = {
    "ranged": "RANGED_WEAPONS",
    "range": "RANGED_WEAPONS",
    "gun": "RANGED_WEAPONS",
    "guns": "RANGED_WEAPONS",
    "rifle": "RANGED_WEAPONS",
    "melee": "MELEE_WEAPONS",
    "armor": "REGULAR_ARMOR",
    "armour": "REGULAR_ARMOR",
    "regular": "REGULAR_ARMOR",
    "regular-armor": "REGULAR_ARMOR",
    "pa": "POWER_ARMOR",
    "power": "POWER_ARMOR",
    "poweramor": "POWER_ARMOR",
    "powerarmor": "POWER_ARMOR",
    "power-armor": "POWER_ARMOR",
    "power_armor": "POWER_ARMOR",
}

CATEGORY_LABEL = {
    "RANGED_WEAPONS": "Ranged weapon",
    "MELEE_WEAPONS": "Melee weapon",
    "REGULAR_ARMOR": "Regular armor",
    "POWER_ARMOR": "Power armor",
}

# Rows in the standard that are catch-all buckets rather than real effect names.
CATCHALL_PATTERNS = {
    "special": re.compile(r"special", re.I),
    "enemy": re.compile(r"enemy-specific", re.I),
    "weight": re.compile(r"weight reduction", re.I),
    "other": re.compile(r"^other|niche effects", re.I),
}

SPECIAL_STATS = {
    "strength", "perception", "endurance", "charisma",
    "intelligence", "agility", "luck",
}

ENEMY_SPECIFIC = {
    "troubleshooters", "ghoulslayers", "mutantslayers", "zealots",
    "assassins", "exterminators", "hunters",
}

NAME_ALIASES = {
    "aa": "antiarmor",
    "antiarmour": "antiarmor",
    "bloody": "bloodied",
    "ts": "twoshot",
    "ffr": "rapid",
    "vats": "vatsenhanced",
    "vatsopt": "vatsoptimized",
    "vo": "vatsoptimized",
    "uny": "unyielding",
    "oe": "overeaters",
    "eater": "overeaters",
    "overeater": "overeaters",
    "ap": "powered",
    "int": "intelligence",
    "str": "strength",
    "end": "endurance",
    "per": "perception",
    "cha": "charisma",
    "agi": "agility",
    "thruhiker": "thruhikers",
    "weaponweight": "armskeepers",
    "wwr": "armskeepers",
    "junkfr": "packrats",
}


def norm(name: str) -> str:
    """Normalize an effect name for lookup: lowercase, strip punctuation/space."""
    key = re.sub(r"[^a-z0-9]", "", (name or "").lower())
    return NAME_ALIASES.get(key, key)


class Effect:
    def __init__(self, tier, name, desc, category, star, source="standard"):
        self.tier = tier
        self.name = name
        self.desc = desc
        self.category = category
        self.star = star
        self.source = source

    @property
    def points(self):
        return TIER_POINTS.get(self.tier, 0.0)

    def __repr__(self):
        return f"<Effect {self.tier}|{self.name}|{self.category}:{self.star}star>"


def parse_tierlist(text: str):
    """Parse the tier-list standard into {(category, star): {normkey: Effect}}."""
    table, catchalls = {}, {}
    category, star = None, None
    skip = False

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if line.startswith("[") and line.endswith("]"):
            tag = line[1:-1].upper()
            if tag in CATEGORY_LABEL:
                category, star, skip = tag, None, False
            elif tag == "4_STAR_REGULAR_ARMOR":
                category, star, skip = "REGULAR_ARMOR", 4, False
            elif tag == "4_STAR_POWER_ARMOR":
                category, star, skip = "POWER_ARMOR", 4, False
            elif re.fullmatch(r"([1-4])_STAR", tag):
                star, skip = int(tag[0]), False
            else:
                skip = True  # QUICK_KEEP_LIST, PROGRAMMING_NOTES, etc.
            continue

        if skip or category is None or star is None or "|" not in line:
            continue

        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2 or parts[0].upper() not in TIER_POINTS:
            continue  # not a tier row (e.g. quick-keep lines)

        tier = parts[0].upper()
        name = parts[1]
        desc = parts[2] if len(parts) > 2 else ""
        eff = Effect(tier, name, desc, category, star)

        bucket = table.setdefault((category, star), {})
        matched_catchall = False
        for kind, pattern in CATCHALL_PATTERNS.items():
            if pattern.search(name) and norm(name) not in SPECIAL_STATS:
                catchalls.setdefault((category, star), {})[kind] = eff
                matched_catchall = True
                break
        if not matched_catchall:
            bucket[norm(name)] = eff

    # Fold in supplemental entries (do not overwrite the standard).
    for (cat, star), rows in SUPPLEMENTAL.items():
        bucket = table.setdefault((cat, star), {})
        for tier, name, desc in rows:
            if norm(name) not in bucket:
                bucket[norm(name)] = Effect(tier, name, desc, cat, star,
                                            source="supplemental")
    return table, catchalls


def load_table(path=None):
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            return parse_tierlist(fh.read())
    return parse_tierlist(EMBEDDED_TIERLIST)


# ---------------------------------------------------------------------------
# 3. LOOKUP
# ---------------------------------------------------------------------------

class Resolved:
    """An effect the user supplied, resolved against the tier table."""

    def __init__(self, star, raw_name):
        self.star = star
        self.raw = raw_name
        self.effect = None
        self.tier = None
        self.points = 0.0
        self.adjusted = 0.0
        self.notes = []
        self.unrated = False
        self.via = "exact"

    @property
    def display(self):
        return self.effect.name if self.effect else self.raw


def resolve(table, catchalls, category, star, raw_name):
    r = Resolved(star, raw_name)
    key = norm(raw_name)
    bucket = table.get((category, star), {})
    cat_catch = catchalls.get((category, star), {})

    eff = bucket.get(key)

    # Power armor 4-star falls back to regular armor 4-star and vice versa
    # only in the rare case a name is missing from one side's own section.
    if eff is None and star == 4:
        other = "POWER_ARMOR" if category == "REGULAR_ARMOR" else "REGULAR_ARMOR"
        eff = table.get((other, 4), {}).get(key)
        if eff is not None:
            r.via = f"{CATEGORY_LABEL[other].lower()} 4-star table"

    if eff is None:
        if key in SPECIAL_STATS and cat_catch.get("special"):
            eff, r.via = cat_catch["special"], "SPECIAL-stat catch-all row"
        elif key in ENEMY_SPECIFIC and cat_catch.get("enemy"):
            eff, r.via = cat_catch["enemy"], "enemy-specific catch-all row"
        elif key.endswith("weight") and cat_catch.get("weight"):
            eff, r.via = cat_catch["weight"], "weight-reduction catch-all row"

    # Effect typed into the wrong star slot: find it elsewhere and say so.
    if eff is None:
        for (c, s), rows in table.items():
            if c == category and s != star and key in rows:
                eff = rows[key]
                r.via = (f"found in the {s}-star table, not {star}-star - "
                         f"check the slot you meant")
                break
    if eff is None:
        for (c, s), rows in table.items():
            if key in rows:
                eff = rows[key]
                r.via = (f"found under {CATEGORY_LABEL[c].lower()} {s}-star; "
                         f"treated as an approximation here")
                break

    if eff is None:
        r.unrated = True
        r.notes.append("Not in the tier-list standard - left unrated and "
                       "excluded from scoring. Judge it yourself.")
        return r

    r.effect = eff
    r.tier = eff.tier
    r.points = eff.points
    r.adjusted = eff.points
    if eff.source == "supplemental":
        r.notes.append("Supplemental entry (not part of the supplied standard).")
    return r


# ---------------------------------------------------------------------------
# 4. CONTEXT ADJUSTMENTS (build + fire rate), from the PROGRAMMING_NOTES
# ---------------------------------------------------------------------------

BUILDS = {
    "bloodied": {
        "up": {"bloodied": 1.0, "unyielding": 1.0, "junkies": 0.5,
               "bolstering": 1.0, "nocturnal": 0.5, "lifesaving": 0.5},
        "down": {"overeaters": -1.5, "aristocrats": -1.0, "juggernauts": -2.0,
                 "sentinels": -0.5},
    },
    "full-health": {
        "up": {"overeaters": 1.0, "juggernauts": 1.0, "aristocrats": 0.75,
               "sentinels": 0.5, "endurance": 0.5},
        "down": {"bloodied": -3.0, "unyielding": -2.5, "nocturnal": -0.5},
    },
    "vats": {
        "up": {"vital": 1.0, "vatsoptimized": 1.0, "vatsenhanced": 1.0,
               "luckyhit": 0.75, "luck": 0.75, "inertial": 0.5,
               "limitbreaking": 1.0, "scanner": 1.0},
        "down": {"hitmans": -1.0, "nimble": -0.5},
    },
    "commando": {
        "up": {"quad": 1.0, "rapid": 0.75, "vampires": 0.75, "explosive": 0.75},
        "down": {"instigating": -1.5, "lastshot": -0.5, "heavyhitters": -1.0},
    },
    "heavy": {
        "up": {"quad": 1.0, "vampires": 1.0, "explosive": 0.75,
               "armskeepers": 0.75, "belted": 0.75},
        "down": {"instigating": -1.5, "twoshot": -0.5},
    },
    "rifleman": {
        "up": {"instigating": 1.0, "hitmans": 0.75, "twoshot": 0.5,
               "vital": 0.5},
        "down": {"quad": -1.0},
    },
    "stealth": {
        "up": {"instigating": 1.0, "chameleon": 1.0, "secretagents": 1.0,
               "nocturnal": 1.0, "unyielding": 0.75, "agility": 0.5},
        "down": {"explosive": -1.5},
    },
    "melee": {
        "up": {"rapid": 1.0, "heavyhitters": 1.0, "strength": 0.75,
               "instigating": 0.75, "vampires": 0.75},
        "down": {"quad": -1.0, "ranger": -1.0, "rangers": -1.5},
    },
    "junkie": {"up": {"junkies": 1.5}, "down": {}},
    "aristocrat": {"up": {"aristocrats": 1.0}, "down": {"bloodied": -1.0}},
    "pvp": {"up": {"assassins": 2.0}, "down": {}},
    "support": {
        "up": {"rejuvenators": 1.0, "aegis": 1.0, "stalwart": 1.0,
               "charisma": 1.0},
        "down": {},
    },
}

RATE_MODS = {
    "fast": {"quad": 0.75, "vampires": 0.75, "rapid": 0.5,
             "instigating": -2.0, "twoshot": -0.5, "lastshot": -0.5},
    "medium": {},
    "slow": {"quad": -1.5, "vampires": -1.0, "instigating": 1.5,
             "twoshot": 0.5, "rapid": 0.25, "lastshot": 0.5},
}

SLOT_WEIGHT = {1: 1.0, 2: 0.9, 3: 0.6, 4: 1.0}


def apply_context(resolved_list, builds, rate):
    for r in resolved_list:
        if r.unrated or r.effect is None:
            continue
        key = norm(r.effect.name)
        delta = 0.0
        for b in builds:
            spec = BUILDS.get(b, {})
            if key in spec.get("up", {}):
                delta += spec["up"][key]
                r.notes.append(f"Synergy with {b} build (+)")
            if key in spec.get("down", {}):
                delta += spec["down"][key]
                r.notes.append(f"Works against a {b} build (-)")
        if rate and rate in RATE_MODS and key in RATE_MODS[rate]:
            d = RATE_MODS[rate][key]
            delta += d
            r.notes.append(
                f"{'Better' if d > 0 else 'Worse'} on a {rate} fire/attack-rate weapon"
            )
        r.adjusted = max(0.0, min(5.0, r.points + delta))


def score(resolved_list, use_adjusted=True):
    """Return 0-100 score over the slots that were actually supplied and rated."""
    num = den = 0.0
    for r in resolved_list:
        if r.unrated or r.effect is None:
            continue
        w = SLOT_WEIGHT.get(r.star, 0.8)
        num += w * (r.adjusted if use_adjusted else r.points)
        den += w * 5.0
    if den == 0:
        return None
    return round(100.0 * num / den, 1)


# ---------------------------------------------------------------------------
# 5. VERDICT
# ---------------------------------------------------------------------------

ACTIONS = {
    "KEEP": "KEEP",
    "SCRAP": "SCRAP at a legendary crafting station (learn the mod)",
    "CAMP": "CAMP VENDOR SELL (player market)",
    "EXCHANGE": "LEGENDARY EXCHANGE for scrip (Rusty Pick)",
    "NPC": "NPC VENDOR SELL for caps",
}


def decide(resolved, personal, market, args, category):
    """Return (action_key, confidence, reasons[], alternates[])."""
    reasons, alternates = [], []
    rated = [r for r in resolved if not r.unrated and r.effect]
    if not rated:
        return ("SCRAP", "low",
                ["Nothing in the roll could be rated against the standard."],
                ["EXCHANGE"])

    best = max(rated, key=lambda r: r.adjusted)
    star1 = next((r for r in rated if r.star == 1), None)
    tiers = [r.tier for r in rated]
    has_S = "S" in tiers
    has_SA = has_S or "A" in tiers
    slots_given = len(resolved)
    unlearned = {norm(x) for x in (args.unlearned or [])}
    unlearned_hits = [r for r in rated
                      if norm(r.effect.name) in unlearned and r.tier in ("S", "A")]

    # --- Learning a mod you don't own beats almost everything else ---------
    if unlearned_hits:
        names = ", ".join(r.effect.name for r in unlearned_hits)
        reasons.append(f"You listed {names} as unlearned; scrapping teaches the "
                       f"mod permanently, which outlives this one item.")
        if personal >= 85:
            reasons[-1] = (f"You listed {names} as unlearned - but at "
                           f"{personal}/100 this roll is too good to destroy. "
                           f"Keep it and scrap a worse copy to learn the mod.")
            return ("KEEP", "high", reasons, ["SCRAP"])
        if personal >= 75:
            reasons.append("The roll itself is also strong, so keeping it is "
                           "defensible if you already have a spare to scrap.")
            return ("SCRAP", "medium", reasons, ["KEEP"])
        return ("SCRAP", "high", reasons, ["EXCHANGE"])

    # --- Strong for you ----------------------------------------------------
    if personal >= 75:
        reasons.append(f"Personal-fit score {personal}/100 - this is at or near "
                       f"a god roll for how you play.")
        if star1 and star1.tier == "S":
            reasons.append(f"1-star {star1.display} is S-tier, the slot that "
                           f"matters most.")
        if slots_given < (4 if category in ("REGULAR_ARMOR", "POWER_ARMOR") else 3):
            reasons.append("Roll is incomplete - the empty star slots are upside, "
                           "not a downside.")
        return ("KEEP", "high", reasons, ["CAMP"])

    if personal >= 62:
        reasons.append(f"Personal-fit score {personal}/100 - solid, usable roll.")
        reasons.append("Worth keeping as a daily driver or a stopgap until "
                       "something better drops.")
        return ("KEEP", "medium", reasons, ["CAMP"])

    # --- Weak for you but valuable to somebody else ------------------------
    if market >= 68 and market - personal >= 8:
        reasons.append(f"Raw desirability {market}/100 but only {personal}/100 "
                       f"for your build - other players want this more than you do.")
        reasons.append("Price it on a CAMP vendor rather than scripping it.")
        return ("CAMP", "high", reasons, ["EXCHANGE"])

    if market >= 62:
        reasons.append(f"Desirability {market}/100 - good enough that the player "
                       f"market will pay for it.")
        if has_S:
            s_names = ", ".join(r.display for r in rated if r.tier == "S")
            reasons.append(f"S-tier effect present: {s_names}.")
        return ("CAMP", "medium", reasons, ["EXCHANGE", "KEEP"])

    # --- Middling ----------------------------------------------------------
    if market >= 45:
        reasons.append(f"Desirability {market}/100 - middling. One good effect "
                       f"({best.display}, {best.tier}-tier) but the roll as a "
                       f"whole is not a keeper.")
        if args.scrip_capped:
            reasons.append("You are scrip-capped, so list it cheap in your CAMP "
                           "instead of burning the exchange on it.")
            return ("CAMP", "medium", reasons, ["EXCHANGE"])
        reasons.append("Best value is converting it to scrip for legendary modules.")
        return ("EXCHANGE", "medium", reasons, ["CAMP", "SCRAP"])

    if market >= 28:
        reasons.append(f"Desirability {market}/100 - low. Effects are mostly "
                       f"replaceable filler.")
        reasons.append("Scrip it; it is not worth vendor space or a listing slot.")
        return ("EXCHANGE", "high", reasons, ["NPC"])

    # --- Junk --------------------------------------------------------------
    reasons.append(f"Desirability {market}/100 - junk roll; every effect is "
                   f"C-tier or below.")
    if slots_given <= 1 or args.scrip_capped:
        reasons.append("A 1-star junk item returns very little scrip, so caps "
                       "from an NPC vendor are the better trade."
                       if slots_given <= 1 else
                       "You are scrip-capped, so take the caps instead.")
        alternates.append("EXCHANGE")
        return ("NPC", "medium", reasons, alternates)
    reasons.append("Multi-star items still return decent scrip even when the "
                   "effects are bad.")
    return ("EXCHANGE", "medium", reasons, ["NPC"])


# ---------------------------------------------------------------------------
# 6. OUTPUT
# ---------------------------------------------------------------------------

BAR = "=" * 68


def bar_for(value):
    filled = int(round(value / 5.0))
    return "[" + "#" * filled + "." * (20 - filled) + "]"


def wrap(text, indent="    ", width=68, hang=0):
    return textwrap.fill(text, width=width, initial_indent=indent,
                         subsequent_indent=indent + " " * hang)


def render(category, resolved, personal, market, action, confidence,
           reasons, alternates, args):
    out = []
    out.append(BAR)
    out.append(f" FALLOUT 76 LEGENDARY ADVISOR - {CATEGORY_LABEL[category]}")
    out.append(BAR)

    out.append("")
    out.append(" ROLL")
    if not resolved:
        out.append("    (no effects supplied)")
    for r in resolved:
        tier = r.tier or "?"
        label = f"  {r.star}-star  [{tier}]  {r.display}"
        if r.adjusted != r.points and not r.unrated:
            label += f"  ({r.points:.1f} -> {r.adjusted:.1f} in context)"
        out.append(label)
        if r.effect and r.effect.desc:
            out.append(wrap(r.effect.desc, indent="            ", width=72))
        if r.via != "exact":
            out.append(f"            via: {r.via}")
        for n in dict.fromkeys(r.notes):
            out.append(f"            - {n}")

    out.append("")
    out.append(" SCORES")
    fit_label = "Personal fit"
    if args.build:
        fit_label += f" ({', '.join(args.build)})"
    width = max(21, len(fit_label))
    out.append(f"    {'Market desirability':<{width}} {market:>5}/100  "
               f"{bar_for(market)}")
    out.append(f"    {fit_label:<{width}} {personal:>5}/100  "
               f"{bar_for(personal)}")

    out.append("")
    out.append(f" VERDICT: {ACTIONS[action]}   (confidence: {confidence})")
    for r in reasons:
        out.append(wrap("- " + r, indent="    ", hang=2))

    if alternates:
        out.append("")
        out.append(" ALSO REASONABLE")
        for a in alternates:
            out.append(f"    - {ACTIONS[a]}")

    out.append("")
    out.append(" NOTES")
    for n in [
        "Tiers are community-opinion priors, not absolute rankings; weapon "
        "and build context can change an effect's value substantially.",
        "NPC vendors share a limited caps pool, so save them for genuine junk.",
        "Scrapping at a legendary crafting station is only worth it for mods "
        "you have not learned yet - pass --unlearned to weight that.",
    ]:
        out.append(wrap("- " + n, indent="    ", hang=2))
    out.append(BAR)
    return "\n".join(out)


def list_table(table, category, star):
    rows = table.get((category, star), {})
    if not rows:
        print(f"No data for {CATEGORY_LABEL[category]} {star}-star.")
        return
    print(f"{CATEGORY_LABEL[category]} - {star} star")
    print("-" * 60)
    for tier in TIER_ORDER:
        for eff in sorted((e for e in rows.values() if e.tier == tier),
                          key=lambda e: e.name):
            mark = " *" if eff.source == "supplemental" else ""
            print(f"  {tier}  {eff.name}{mark}")
            if eff.desc:
                print(textwrap.fill(eff.desc, width=60,
                                    initial_indent="       ",
                                    subsequent_indent="       "))
    if any(e.source == "supplemental" for e in rows.values()):
        print("\n  * = supplemental entry, not in the supplied standard")


# ---------------------------------------------------------------------------
# 7. CLI
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="f76_legendary_advisor.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Advise whether to keep, scrap, exchange, CAMP sell or "
                    "NPC vendor sell a Fallout 76 legendary item.",
        epilog=textwrap.dedent("""\
            examples:
              %(prog)s melee --one Juggernaut's --two Riposting --three Lightweight
              %(prog)s ranged --one Quad --two Rapid --three "V.A.T.S. Optimized" --build commando --rate fast
              %(prog)s armor --one Unyielding --two Luck --three Sentinel's --four Limit-Breaking --build bloodied vats
              %(prog)s pa --one Overeater's --two Powered --three Thru-hiker's --json
              %(prog)s --list armor 3
            """),
    )
    p.add_argument("category", nargs="?",
                   help="ranged | melee | armor | pa")
    p.add_argument("--one", "-1", dest="one", help="1-star effect")
    p.add_argument("--two", "-2", dest="two", help="2-star effect")
    p.add_argument("--three", "-3", dest="three", help="3-star effect")
    p.add_argument("--four", "-4", dest="four", help="4-star effect (armor / power armor)")
    p.add_argument("--build", nargs="*", default=[],
                   metavar="TAG",
                   help="build tags: " + ", ".join(sorted(BUILDS)))
    p.add_argument("--rate", choices=["slow", "medium", "fast"],
                   help="weapon fire rate / attack speed (weapons only)")
    p.add_argument("--unlearned", nargs="*", default=[], metavar="EFFECT",
                   help="effects you have NOT yet learned as craftable mods")
    p.add_argument("--scrip-capped", action="store_true",
                   help="you have hit the daily scrip limit")
    p.add_argument("--tierfile", help="path to an updated tier-list file")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--list", nargs=2, metavar=("CATEGORY", "STAR"),
                   help="print the tier table for a category/star and exit")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        table, catchalls = load_table(args.tierfile)
    except OSError as e:
        parser.error(f"could not read tier file: {e}")

    if args.list:
        cat_raw, star_raw = args.list
        cat = CATEGORY_ALIASES.get(cat_raw.lower().strip())
        if not cat:
            parser.error(f"unknown category '{cat_raw}'")
        if not star_raw.isdigit() or not 1 <= int(star_raw) <= 4:
            parser.error("star must be 1-4")
        list_table(table, cat, int(star_raw))
        return 0

    if not args.category:
        parser.print_help()
        return 1

    category = CATEGORY_ALIASES.get(args.category.lower().strip())
    if not category:
        parser.error(f"unknown category '{args.category}' "
                     f"(use ranged, melee, armor or pa)")

    for b in args.build:
        if b not in BUILDS:
            parser.error(f"unknown build tag '{b}'. Valid: "
                         + ", ".join(sorted(BUILDS)))

    supplied = [(1, args.one), (2, args.two), (3, args.three), (4, args.four)]
    supplied = [(s, v) for s, v in supplied if v]
    if not supplied:
        parser.error("give at least one of --one/--two/--three/--four")

    resolved = [resolve(table, catchalls, category, star, name)
                for star, name in supplied]

    market = score(resolved, use_adjusted=False)
    apply_context(resolved, args.build, args.rate)
    personal = score(resolved, use_adjusted=True)

    if market is None:
        market = personal = 0.0

    action, confidence, reasons, alternates = decide(
        resolved, personal, market, args, category)

    if args.json:
        print(json.dumps({
            "category": category,
            "roll": [{
                "star": r.star,
                "input": r.raw,
                "effect": r.display,
                "tier": r.tier,
                "base_points": r.points,
                "adjusted_points": round(r.adjusted, 2),
                "unrated": r.unrated,
                "resolution": r.via,
                "notes": list(dict.fromkeys(r.notes)),
            } for r in resolved],
            "market_score": market,
            "personal_score": personal,
            "build": args.build,
            "rate": args.rate,
            "action": action,
            "action_text": ACTIONS[action],
            "confidence": confidence,
            "reasons": reasons,
            "alternates": [ACTIONS[a] for a in alternates],
        }, indent=2))
    else:
        print(render(category, resolved, personal, market, action,
                     confidence, reasons, alternates, args))
    return 0


if __name__ == "__main__":
    sys.exit(main())