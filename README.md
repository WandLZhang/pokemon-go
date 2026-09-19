# Pokemon GO

Roster and bag for WillisZhang, ranked for raids. Nothing here scores PvP.

Season: Twilight Trails, Sept 8 to Dec 1 2026. GO Battle League Season 28.

## Do this next

`python rank.py next` prints the sequence from the data. Steps appear only
while they're needed, and the command asserts that no step transfers a
Pokemon a later step wants to evolve.

**Candy blocks everything except raiding.** The `evolve` search returns four
Pokemon, none of them an upgrade, so there's one unblocked move.

**1. Raid.** 14 Premium Battle Passes, and raids need no candy. At 10,000 XP a
tier 5 win that's 140,000 of the 193,417 to level 40. Each win also pays 500
stardust, 3 XL candy and a shot at Rare Candy, which are the three things
holding the rest of the plan up.

Zamazenta is the live tier 5 through Sept 22. Fighting and Steel, so bring
Fire and Ground. `python rank.py counters ZAMAZENTA --box` ranks your six.

Level 40 falls out of this step. It pays +50 Pokemon storage, +75 item bag,
20 Max Revives, 40 Ultra Balls and an Elite Fast TM.

**2. Evolve as candy arrives.** Spend it in this order. None of these are
affordable today, so this is a shopping list, not a to-do list.

| Evolve | Becomes | Rank | Cost |
|---|---|---|---|
| Beldum 413 | Metagross 1603-1832 | **#1 Steel** | 125 candy |
| Cranidos 807 | Rampardos 1461-1551 | **#1 Rock** | 50 candy |
| Deino 586 | Hydreigon 2000-2253 | **#1 Dark** | 125 candy |
| Sobble 772 | Inteleon 2085-2304 | **#1 Water** | 125 candy |
| Trumbeak 621 | Toucannon 1129-1197 | #2 Flying | 100 candy |
| Porygon 770 | Porygon-Z 1462-1539 | #3 Normal | 125 candy + Upgrade + Sinnoh Stone |
| Piloswine 1385 | Mamoswine 1965-2017 | #3 Ground | 100 candy + Sinnoh Stone |
| Tyrunt 913 | Tyrantrum 1746-1849 | #3 Rock | 50 candy |

Cranidos and Tyrunt are the cheapest at 50, and Cranidos is a #1 in the game.

**3. Giovanni.** The Super Rocket Radar can't be replaced, so go in with the
team step 1 built. He closes with Shadow Reshiram: Fighting for Persian,
Psychic for Machamp, Rhyperior for Reshiram.

## Where you are

`python rank.py state` reads `data/trainer.json`, `data/bag.json` and
`data/box_list.csv`, so it can't drift from them.

```
WillisZhang, level 39, buddy Pancham
  XP to 40      193,417
  stardust        36,934
  box             171 of 325
  bag             374 of 550
  power-up ceiling level 49
```

**Two currencies, both empty.** Candy blocks evolving and stardust blocks
powering up, which is why raiding is the only move left. 36,934 dust is 7
power-ups on a level 30 Pokemon and 3 on a level 40 one, against 150,000 to
take one Pokemon from level 30 to 40. So power up almost nothing until raids
refill both.

### Type coverage

`roster` scores each type against the best attacker in the game whose fast
and charged moves share that type. All 18:

| | | | |
|---|---|---|---|
| Bug 100% | Dark 100% | Rock 100% | Steel 100% |
| Water 100% | Flying 99% | Fighting 95% | Poison 91% |
| Electric 88% | Ghost 87% | Grass 85% | Fairy 81% |
| Psychic 81% | Ground 80% | Ice 78% | Fire 76% |
| Dragon 73% | Normal 70% | | |

Dragon and Fire don't close by evolving. Those need raid legendaries, which
is one more reason to spend the passes.

The denominator is the best **same-type** attacker. In 7 types the real
strongest carries a mixed pair: Calyrex Shadow Rider runs Confusion into
Shadow Ball for Ghost, Zacian Crowned Sword runs Metal Claw into Play Rough
for Fairy. Against those, Dark is 83% and Water 94%, not 100%.

### The five Sinnoh Stones

**10 holdings want one and you hold 5.** Every one is also short of the
100 candy, which is what the grayed-out picker means, so the stones aren't
the binding item. Same ranking as step 2, filtered to the ones needing a
stone:

| Evolve | Becomes | Rank |
|---|---|---|
| Porygon 770 | Porygon-Z | #3 Normal, your worst type. Also uses the Upgrade |
| Piloswine 1385 | Mamoswine | #3 Ground, and #1 Ice |
| Roselia 1553 | Roserade | #4 Grass |
| Togetic 955 | Togekiss | #7 Fairy |
| Electabuzz 1310 | Electivire | #8 Electric |

Then Yanma #14, Tangela #17, Gligar #19, Magby #21, Dusclops #25. Spend the
five from the top.

## Running it

```sh
source .venv/bin/activate
./fetch.sh                  # refresh the game master
python rank.py selftest     # 39 checks against published values
```

| Command | Answers |
|---|---|
| `next` | The ordered action sequence, derived from `data/` |
| `state` | Where the account stands |
| `roster` | Your best six per attacking type, and what each slot costs |
| `box` | Keep, evolve, hold or transfer, per Pokemon |
| `plan` | The transfer pass as paste-able search strings |
| `evolve` | What each evolution item in the bag can buy |
| `counters BOSS --box` | Rank your box against a raid boss |
| `powerup --from --to` | Stardust and candy for a climb |
| `constants` | Every constant the ranking uses |

`plan --markdown` prints one fenced block per search line. A multi-line block
pasted into the game's single-line search field drops everything after the
first newline.

## Layout

| Path | Holds |
|---|---|
| `data/box_list.csv` | The box. `species,cp,shiny,lucky,shadow,purified,favorite,tag,costume` |
| `data/bag.json` | Item counts |
| `data/trainer.json` | Level, XP, stardust, storage caps |
| `data/gamemaster.stamp` | Date and SHA of the game master in use |
| `pogo/gamemaster.py` | Loads and indexes the PokeMiners dump |
| `pogo/battle.py` | CPM, CP, damage, cycle DPS, TDO, power-up costs |
| `pogo/roster.py` | Turns the box into keep or transfer calls |
| `pogo/cli.py` | Commands and the argument parser |
| `reference.md` | Verified game mechanics, each constant named to its source |

Every number in `data/` traces to the game master, a screenshot, or a cited
source. Two lines in `bag.json` are marked `derived`: the Poke Ball and Hyper
Potion counts come from the drop that was made, not from a fresh scroll.
Projected CP is a computed range, not an observation.

## Keeping it current

The three files in `data/` are the state. Act in game, update the file, and
every command follows. Don't hand-write numbers into this README that a
command can print.

`data/box_list.csv` carries no IVs, candy, legacy moves or size, and no form
column, so regional variants collapse together. List-view screenshots don't
show any of that. For raids the IV gap costs 3 to 5% DPS, less than one level
band.

Before any mass transfer, search `@special`, `costume` and `xxl` in game and
favorite what they return. The Piplup 611 marked `costume` is the one the game
stopped; nothing else is checked.

Run `/verify` before committing. It dispatches read-only audit agents over the
docs and the constants. Fix every finding.
