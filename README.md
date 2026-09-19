# Pokemon GO

Roster and bag for WillisZhang, ranked for raids. Nothing here scores PvP.

Season: Twilight Trails, Sept 8 to Dec 1 2026. GO Battle League Season 28.

## Do this next

**Candy blocks evolving, stardust blocks powering up.** Raiding is the only
unblocked move, and it pays both.

**1. Raid.** 14 Premium Battle Passes, and raids need no candy. At 10,000 XP a
tier 5 win that's 140,000 of the 193,417 to level 40. Each win also pays 500
stardust, 3 XL candy, and a shot at Rare Candy.

Zamazenta is the live tier 5 through Sept 22. Fighting and Steel, so bring
Fire and Ground. Best six from the current box:

| | Pokemon | DPS |
|---|---|---|
| 1 | Pheromosa 1182 | 23.6 |
| 2 | Flareon 1532 | 20.1 |
| 3 | Excadrill 1469 | 19.9 |
| 4 | Charizard 1673 | 19.5 |
| 5 | Rhyperior 1734 | 18.9 |
| 6 | Pyroar 2117 | 18.4 |

Level 40 falls out of this step. It pays +50 Pokemon storage, +75 item bag,
20 Max Revives, 40 Ultra Balls and an Elite Fast TM.

**2. Evolve as candy arrives.** A shopping list, not a to-do list: none of
these are affordable today. Search `evolve` in game, which is the only check
on what candy allows.

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

Cranidos and Tyrunt are cheapest at 50, and Cranidos is a #1 in the game.

**3. Giovanni.** The Super Rocket Radar can't be replaced, so go in with the
team step 1 builds. He closes with Shadow Reshiram: Fighting for Persian,
Psychic for Machamp, Rhyperior for Reshiram.

## Where you are

| | |
|---|---|
| Trainer | Level 39, 193,417 XP to 40 |
| Stardust | 36,934 |
| Box | 171 of 325 |
| Bag | 374 of 550 |
| Buddy | Pancham |

36,934 dust is 7 power-ups on a level 30 Pokemon and 3 on a level 40 one,
against 150,000 to take one Pokemon from level 30 to 40. Power up almost
nothing until raids refill it.

### Type coverage

Each type against the best attacker in the game whose fast and charged moves
share that type:

| | | | |
|---|---|---|---|
| Bug 100% | Dark 100% | Rock 100% | Steel 100% |
| Water 100% | Flying 99% | Fighting 95% | Poison 91% |
| Electric 88% | Ghost 87% | Grass 85% | Fairy 81% |
| Psychic 81% | Ground 80% | Ice 78% | Fire 76% |
| Dragon 73% | Normal 70% | | |

Dragon and Fire don't close by evolving. Those need raid legendaries, which
is one more reason to spend the passes.

That denominator is the best **same-type** attacker. In 7 types the real
strongest carries a mixed pair: Calyrex Shadow Rider runs Confusion into
Shadow Ball for Ghost, Zacian Crowned Sword runs Metal Claw into Play Rough
for Fairy. Against those, Dark is 83% and Water 94%, not 100%.

### The five Sinnoh Stones

**10 holdings want one and you hold 5.** Every one is also short of the 100
candy, which is what the grayed-out picker means, so the stones aren't the
binding item.

| Evolve | Becomes | Rank |
|---|---|---|
| Porygon 770 | Porygon-Z | #3 Normal, your worst type. Also uses the Upgrade |
| Piloswine 1385 | Mamoswine | #3 Ground, and #1 Ice |
| Roselia 1553 | Roserade | #4 Grass |
| Togetic 955 | Togekiss | #7 Fairy |
| Electabuzz 1310 | Electivire | #8 Electric |

Then Yanma #14, Tangela #17, Gligar #19, Magby #21, Dusclops #25.

## The data

| File | Holds |
|---|---|
| `data/box_list.csv` | The box. `species,cp,shiny,lucky,shadow,purified,favorite,tag,costume` |
| `data/bag.json` | Item counts |
| `data/trainer.json` | Level, XP, stardust, storage caps |
| `data/gamemaster.stamp` | Date and SHA of the game master last pulled |
| `reference.md` | Verified mechanics, each constant named to its source |

`./fetch.sh` pulls the current PokeMiners game master into `data/`, which is
gitignored at 19 MB. Every DPS, CP projection and coverage figure above was
computed against it.

Every number traces to the game master, a screenshot, or a cited source. Two
lines in `bag.json` are marked `derived`: the Poke Ball and Hyper Potion
counts come from the drop that was made, not a fresh scroll. Projected CP is
a computed range, not an observation.

## Keeping it current

The three files in `data/` are the state. Act in game, update the file.

`box_list.csv` carries no IVs, candy, legacy moves or size, and no form
column, so regional variants collapse together. List-view screenshots don't
show any of that. For raids the IV gap costs 3 to 5% DPS, less than one level
band.

Before any mass transfer, search `@special`, `costume` and `xxl` in game and
favorite what they return. The Piplup 611 marked `costume` is the one the game
stopped; nothing else is checked.

## Why there's no code here

There was: 1,550 lines that loaded the game master, computed DPS and CP, and
emitted keep-or-transfer verdicts. 7 of the first 26 commits were fixing it,
and every fix introduced the next bug. The arithmetic it did was sound. The
verdicts on top needed judgment, and it kept reaching wrong ones: evolve a
Charmander into a Charizard already in the box, transfer the Salamence that
was fighting, transfer a costume Piplup, put legendaries in the transfer pile.

The numbers above still come from the game master. They come from queries
written when a question needs them, then discarded. `git log` has the engine
if it turns out to be missed.
