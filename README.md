# Fallout 76 Legendary Advisor

A Python tool for evaluating **Fallout 76 legendary weapons, armor, and power armor** and recommending what to do with them.

The advisor scores both:

- the **base item** itself (for example, *The Fixer*, *Super Sledge*, *Secret Service Armor*, or *Union Power Armor*), and
- its **1–4 star legendary effects**.

It then recommends one of five actions:

- **KEEP**
- **SCRAP** at a legendary crafting station to learn a mod
- **CAMP VENDOR SELL**
- **LEGENDARY EXCHANGE** for scrip
- **NPC VENDOR SELL** for caps

The program can be used through either a **Tkinter GUI** or the **command line**.

---

## Features

- Evaluates **ranged weapons, melee weapons, regular armor, and power armor**.
- Combines a base item's tier with its legendary-effect tiers instead of grading the roll in isolation.
- Supports **1-star through 4-star effects** where applicable.
- Calculates both a general **Market Desirability** score and a context-sensitive **Personal Fit** score.
- Adjusts recommendations for supported build types such as Bloodied, full-health, V.A.T.S., Commando, Heavy, Rifleman, Stealth, Melee, Junkie's, Aristocrat's, PvP, and Support.
- Can account for weapon attack/fire rate.
- Can prioritize scrapping when an item contains a valuable legendary mod you have **not learned yet**.
- Can account for being **scrip-capped**.
- Supports human-readable terminal output and **JSON output**.
- Includes commands for browsing the loaded legendary-effect and base-item tier lists.
- Automatically finds its data files when they are stored beside the Python script.
- Falls back to an embedded legendary-mod database if no external legendary-mod tier file is found.
- Launches a GUI automatically when run with no command-line arguments.

---

## Requirements

- **Python 3**
- No third-party Python packages are required.
- **Tkinter** is required only for the graphical interface.

Tkinter is normally included with the standard Python installers for Windows and macOS. On some Linux distributions it may need to be installed separately.

### Debian / Ubuntu

```bash
sudo apt install python3-tk
```

### Fedora

```bash
sudo dnf install python3-tkinter
```

The command-line interface works without Tkinter.

---

## Project Files

Place the program and its three data files in the same directory:

```text
Fallout76-Legendary-Advisor/
├── f76_legendary_advisor.py
├── fallout76_legendary_mod_tierlist.txt
├── fallout76_weapon_tier_list.txt
├── fallout76_armor_power_&_armor_tier_list.txt
└── README.md
```

The filenames do not have to match those examples exactly. The program auto-detects `.txt` files in its own directory using keywords:

| Data | Filename must contain | Excludes |
|---|---|---|
| Legendary effects | `legendary` and `mod` | — |
| Weapons | `weapon` and `tier` | `legendary` |
| Armor / Power Armor | `armor` and `tier` | `legendary`, `weapon` |

This means versioned filenames such as `fallout76_weapon_tier_list(2).txt` can still be detected.

> If multiple files match the same rule, the program sorts the matching filenames and uses the first one. Keeping only the current version of each data file beside the script avoids ambiguity.

---

## Quick Start

### GUI

Run the program without arguments:

```bash
python f76_legendary_advisor.py
```

The graphical interface will open automatically. From there you can choose the item category, item name, legendary effects, build context, and other options before evaluating the item.

### Command Line

General form:

```bash
python f76_legendary_advisor.py CATEGORY [OPTIONS]
```

Supported primary categories are:

```text
ranged
melee
armor
pa
```

The program also recognizes several aliases, but the four values above are recommended for scripts and documentation.

---

## Examples

### Ranged weapon

```bash
python f76_legendary_advisor.py ranged \
  --item "The Fixer" \
  --one Quad \
  --two Rapid \
  --three "V.A.T.S. Optimized" \
  --build commando vats \
  --rate fast
```

### Melee weapon

```bash
python f76_legendary_advisor.py melee \
  --item "Super Sledge" \
  --one "Juggernaut's" \
  --two Riposting \
  --three Lightweight
```

### Regular armor

```bash
python f76_legendary_advisor.py armor \
  --item "Secret Service Armor" \
  --one Unyielding \
  --two Luck \
  --three "Sentinel's" \
  --build bloodied vats
```

### Power armor

```bash
python f76_legendary_advisor.py pa \
  --item "Union Power Armor" \
  --one "Overeater's" \
  --two Powered \
  --three "Thru-hiker's"
```

### Evaluate only the legendary roll

`--item` is optional. To grade the effects without including the base weapon or armor tier:

```bash
python f76_legendary_advisor.py ranged \
  --one Anti-Armor \
  --two Explosive \
  --three Lightweight
```

You must provide either an item name, at least one legendary effect, or both.

---

## Command-Line Options

| Option | Description |
|---|---|
| `category` | Item category: `ranged`, `melee`, `armor`, or `pa`. |
| `--item NAME` | Specific weapon, armor, or power-armor name to include in grading. |
| `--one EFFECT` | 1-star legendary effect. Aliases: `--1`, `-1`. |
| `--two EFFECT` | 2-star legendary effect. Aliases: `--2`, `-2`. |
| `--three EFFECT` | 3-star legendary effect. Aliases: `--3`, `-3`. |
| `--four EFFECT` | 4-star legendary effect. Aliases: `--4`, `-4`. |
| `--build TAG [TAG ...]` | Apply one or more build-context adjustments. |
| `--rate slow\|medium\|fast` | Supply weapon fire rate / attack speed context. |
| `--unlearned EFFECT [EFFECT ...]` | Mark legendary mods that you have not yet learned. |
| `--scrip-capped` | Tell the advisor that the daily scrip limit has been reached. |
| `--json` | Output the result as machine-readable JSON. |
| `--list CATEGORY STAR` | Display legendary effects for a category and star level. |
| `--list-items CATEGORY` | Display all base items loaded for a category. |
| `--moddata PATH` | Override the automatically detected legendary-mod tier file. |
| `--weapondata PATH` | Override the automatically detected weapon tier file. |
| `--armordata PATH` | Override the automatically detected armor/power-armor tier file. |

A legacy `--tierfile` option is also accepted as an alias for `--moddata`.

For the built-in command reference:

```bash
python f76_legendary_advisor.py --help
```

---

## Supported Build Tags

The following build tags are currently recognized:

```text
aristocrat
bloodied
commando
full-health
heavy
junkie
melee
pvp
rifleman
stealth
support
vats
```

Multiple tags can be supplied at once:

```bash
python f76_legendary_advisor.py ranged \
  --item "The Fixer" \
  --one Bloodied \
  --two Vital \
  --three "V.A.T.S. Optimized" \
  --build bloodied vats commando
```

Build tags do **not** rewrite the source tier lists. They modify the item's contextual/personal score so that effects useful to the supplied build can be valued differently from their general market desirability.

---

## Market Score vs. Personal Score

The advisor reports two major scores:

### Market Desirability

Represents the general desirability of the item and its effects without applying your chosen build adjustments.

This is useful for deciding whether another player may value an item even when it is not useful for your own character.

### Personal Fit

Represents the value of the item after contextual adjustments such as build tags and weapon speed are applied.

For example, a roll can have high market value but lower personal value for your character. In that situation, the advisor may recommend selling it through a CAMP vendor instead of keeping it.

---

## Unlearned Legendary Mods

Use `--unlearned` to tell the advisor which legendary effects you have not yet learned as craftable mods.

Example:

```bash
python f76_legendary_advisor.py ranged \
  --item "Combat Rifle" \
  --one Quad \
  --two Explosive \
  --three Lightweight \
  --unlearned Quad Explosive
```

For valuable unlearned effects, the program may prioritize **SCRAP** because learning the mod can have more long-term value than the individual item.

Very strong rolls can still receive a **KEEP** recommendation, with scrapping a worse duplicate suggested instead.

---

## Scrip-Capped Mode

If you have already reached the daily Legendary Exchange limit, add:

```bash
--scrip-capped
```

Example:

```bash
python f76_legendary_advisor.py melee \
  --item "Board" \
  --one Hunter's \
  --two Crippling \
  --scrip-capped
```

This allows the recommendation system to consider CAMP or NPC vendor alternatives rather than recommending an exchange that you currently cannot use effectively.

---

## Listing Tier-List Data

### List legendary effects

Syntax:

```bash
python f76_legendary_advisor.py --list CATEGORY STAR
```

Example:

```bash
python f76_legendary_advisor.py --list armor 3
```

Valid star values are `1` through `4`.

### List base items

Syntax:

```bash
python f76_legendary_advisor.py --list-items CATEGORY
```

Examples:

```bash
python f76_legendary_advisor.py --list-items ranged
python f76_legendary_advisor.py --list-items melee
python f76_legendary_advisor.py --list-items armor
python f76_legendary_advisor.py --list-items pa
```

---

## JSON Output

Add `--json` to receive structured output suitable for scripts, bots, web applications, or other tools.

```bash
python f76_legendary_advisor.py ranged \
  --item "The Fixer" \
  --one Quad \
  --two Rapid \
  --three "V.A.T.S. Optimized" \
  --json
```

The JSON result includes information such as:

```json
{
  "category": "RANGED_WEAPONS",
  "item": {},
  "roll": [],
  "market_score": 0,
  "personal_score": 0,
  "build": [],
  "rate": null,
  "action": "KEEP",
  "action_text": "KEEP",
  "confidence": "high",
  "reasons": [],
  "alternates": [],
  "data_sources": {}
}
```

The values above are only an illustration of the JSON schema, not a sample evaluation score.

---

## Name Matching

Item and legendary-effect names are designed to be forgiving:

- matching is case-insensitive,
- punctuation is ignored when normalizing names, and
- unambiguous partial-name matching can be used.

For automation, however, using the full canonical name from the tier-list files is recommended.

Names containing spaces or apostrophes should normally be quoted in your shell:

```bash
--one "Vampire's"
--three "V.A.T.S. Optimized"
--item "Secret Service Armor"
```

---

## Tier System

The data files use the following general tier scale:

| Tier | Meaning |
|---|---|
| **S** | Exceptional / top-tier |
| **A** | Excellent |
| **B** | Good / viable |
| **C** | Decent / situational |
| **D** | Weak / niche |
| **F** | Extremely weak / novelty |

The legendary-mod list uses the same broad S–F structure while emphasizing effect desirability and build dependence.

The rankings are intended as practical community-oriented priors rather than absolute rules. A lower-tier effect can still become highly valuable in a specialized build.

---

## Editing and Updating the Tier Lists

One of the main design goals of the advisor is to keep ranking data separate from program logic.

You can update the `.txt` data files without editing the Python source.

Typical rows use pipe-separated fields:

```text
S|The Fixer|Excellent commando platform with strong stealth, VATS and critical performance.
```

Legendary-effect files are additionally organized by item category and star level:

```text
[RANGED_WEAPONS]
[1_STAR]
S|Quad|Large magazine increase; excellent on many automatic/rapid-fire weapons
A|Vampire's|Excellent survivability on fast-firing weapons
```

Keep the section names and pipe-separated structure intact so the parser can read the files correctly.

---

## Using Custom Data Files

Automatic detection is convenient for normal use, but every data source can be overridden explicitly.

```bash
python f76_legendary_advisor.py ranged \
  --item "The Fixer" \
  --one Quad \
  --moddata ./data/my_legendary_mods.txt \
  --weapondata ./data/my_weapons.txt \
  --armordata ./data/my_armor.txt
```

This is useful for testing alternate rankings, keeping several snapshots of the Fallout 76 meta, or integrating the advisor into another project.

---

## Missing Data Files

The program is designed to degrade gracefully:

- If the external **legendary-mod tier list** is missing, the program uses its built-in legendary-effect data.
- If the **weapon tier list** is missing, weapon effects can still be graded, but weapon base-item scoring is unavailable.
- If the **armor tier list** is missing, armor effects can still be graded, but armor/power-armor base-item scoring is unavailable.

For the most complete recommendations, keep all three current data files beside the script.

---

## Recommendation Logic

The final verdict is based on more than simply checking whether an effect is S-tier.

The advisor considers factors such as:

1. The tier of the **base weapon or armor platform**.
2. The tiers of the supplied **legendary effects**.
3. General **market desirability**.
4. Your selected **build context**.
5. Weapon attack/fire-rate context when supplied.
6. Whether a desirable effect is listed as **unlearned**.
7. Whether you are currently **scrip-capped**.
8. Whether the roll is strong enough to keep even if learning one of its mods would otherwise be valuable.

The result includes a confidence level, explanatory reasons, and alternate actions when another choice is also reasonable.

---

## Important Notes

- Tier lists represent generalized community-oriented rankings, not a guarantee of trade value or build performance.
- Fallout 76 balance changes can alter the value of an item or effect. Update the text files when the game changes.
- A specialized build may make a normally niche effect substantially more valuable.
- CAMP vendor value is not the same as an exact caps price; the advisor recommends whether an item is worth exposing to the player market, not a specific listing price.
- The advisor is intended to support player decisions, not replace build testing or personal preference.

---

## Troubleshooting

### The GUI does not open

Run:

```bash
python f76_legendary_advisor.py
```

If Python reports that Tkinter is unavailable, install the Tkinter package for your operating system or use the CLI instead.

### My item is not being recognized

Check the currently loaded item names:

```bash
python f76_legendary_advisor.py --list-items ranged
```

Replace `ranged` with the correct category.

### My legendary effect is not being recognized

Inspect the available effects for the relevant slot:

```bash
python f76_legendary_advisor.py --list ranged 1
python f76_legendary_advisor.py --list ranged 2
python f76_legendary_advisor.py --list ranged 3
```

### The wrong tier-list file appears to be loading

If several matching `.txt` files are beside the script, remove old duplicates or explicitly specify the desired file with `--moddata`, `--weapondata`, or `--armordata`.

---

## Data Snapshot

The supplied weapon and armor lists are labeled for **Fallout 76 Update 70 / September 2026** and are oriented toward general PvE/endgame use. The rankings are meant to be maintained independently of the program, so they can be revised as future balance patches change the game.