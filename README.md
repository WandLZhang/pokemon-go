# Pokemon GO

Roster and bag for WillisZhang. Raids first, GO Battle League second.

Season: Twilight Trails, Sept 8 to Dec 1 2026. GO Battle League Season 28.

## Do this next

**1. Clear the bag.** It reads 571 of 550, so PokeStops are giving you nothing.

- Poke Ball 236 down to 50. You hold 82 Ultra and 41 Great; at level 39 the
  Poke Balls do nothing.
- All 11 Hyper Potions. Max Potion does the same job and you hold 52.

That's 571 to 374, and item income restarts.

**2. Evolve the five the game offers.** Search `evolve` in your Pokemon list.

| Evolve | Leads to | Worth it? |
|---|---|---|
| Popplio 862 | Primarina, #6 Fairy | Yes, the only one that adds an attacker |
| Chimchar 533 | Infernape, #15 Fire | Yes, new to the bench |
| Bulbasaur 625 | Venusaur 1524-1667 | Barely. You own Venusaur 1435 |
| Charmander 402 | Charizard 1184-1323 | No. You own Charizard 1673 |
| Pancham 823 | Pangoro, #32 Dark | No. Your buddy, weak attacker |

Do all five anyway. That candy has no other use and each one pays 1,000 XP.
Only the first step of each is affordable, so none reach the end form today.

**3. Raid. This is the real move.**

Raids need no candy, which is the wall everything else sits behind. You hold
14 Premium Battle Passes, and each tier 5 win pays 10,000 XP, 500 stardust,
3 XL candy, and a chance at Rare Candy.

Zamazenta is the live tier 5 through Sept 22. Fighting and Steel, so bring
Fire and Ground. Your best six as the box stands:

| | Pokemon | DPS | Moveset |
|---|---|---|---|
| 1 | Pheromosa 1182 | 23.6 | Low Kick + Focus Blast |
| 2 | Flareon 1532 | 20.1 | Fire Spin + Overheat |
| 3 | Excadrill 1469 | 19.9 | Mud Slap + Earthquake |
| 4 | Charizard 1673 | 19.5 | Fire Spin + Blast Burn |
| 5 | Rhyperior 1734 | 18.9 | Mud Slap + Earthquake |
| 6 | Pyroar 2117 | 18.4 | Fire Fang + Overheat |

**4. Level 40 lands on its own.** 14 raids at 10,000 plus 53 evolutions at
1,000 covers the 193,417 you need. It pays +50 Pokemon storage, +75 item bag,
20 Max Revives, 40 Ultra Balls and an Elite Fast TM.

**5. Giovanni last.** The Super Rocket Radar can't be replaced, and by then
you have a free slot and a better team. He closes with Shadow Reshiram:
Fighting for Persian, Psychic for Machamp, Rhyperior for Reshiram.

## Where you are

| | |
|---|---|
| Trainer level | 39, 193,417 XP short of 40 |
| Stardust | 36,934 |
| Box | 180 of 325, after transferring 145 |
| Bag | 571 of 550, over cap |
| Buddy | Pancham |

**Stardust is the binding constraint.** 36,934 buys about six power-ups at
level 30 and above, and one Pokemon from level 30 to 40 costs 150,000.
Evolving costs no dust, so evolve freely and power up almost nothing until
raids refill it.

### Type coverage

Maxed: Bug, Dark, Rock, Steel, Water. Close behind: Flying 99%, Ghost 97%,
Poison 97%, Fighting 95%.

Weakest: Normal 70%, Dragon 73%, Fire 76%, Ice 78%, Ground 80%, Psychic 81%,
Fairy 81%. Dragon and Fire don't close by evolving. Those need raid
legendaries, which is one more reason to spend the passes.

### The five Sinnoh Stones

None are spendable. Every candidate is short of the 100 candy, which is what
the greyed-out stone picker means. Ranked for when the candy arrives:

| Stone to | Buys |
|---|---|
| Piloswine to Mamoswine | 13.9 Ground and 13.0 Ice, your two weak useful types |
| Porygon to Porygon-Z | 14.6 Normal, your worst type. Also uses the Upgrade |
| Roselia to Roserade | 14.1 Grass, 13.4 Poison |
| Electabuzz to Electivire | 13.9 Electric |
| Togetic to Togekiss | 11.9 Fairy |

Skip Murkrow and Misdreavus. You own Honchkrow 2163 and Mismagius 1884.

## Running it

```sh
source .venv/bin/activate
./fetch.sh                  # refresh the game master
python rank.py selftest     # 39 checks against published values
```

| Command | Answers |
|---|---|
| `roster` | Your best six per attacking type, and what each slot costs |
| `box` | Keep, evolve, hold or transfer, per Pokemon |
| `plan` | The transfer pass as paste-able search strings |
| `evolve` | What each evolution item in the bag can buy |
| `keepers` | Which species are worth scanning into Calcy |
| `counters BOSS` | Rank attackers against a raid boss |
| `powerup --from --to` | Stardust and candy for a climb |
| `constants` | Every constant the ranking uses |

`plan --markdown` prints one fenced block per search line. A multi-line block
pasted into the game's single-line search field drops everything after the
first newline.

## Layout

| Path | Holds |
|---|---|
| `data/box_list.csv` | The box. Species, CP, shiny, shadow, favorite, tag |
| `data/bag.json` | Item counts, reconciled to the in-game total |
| `data/gamemaster.stamp` | Date and SHA of the game master in use |
| `pogo/gamemaster.py` | Loads and indexes the PokeMiners dump |
| `pogo/battle.py` | CPM, CP, damage, cycle DPS, TDO, power-up costs |
| `pogo/roster.py` | Turns the box into keep or transfer calls |
| `pogo/box.py` | Calcy IV CSV loader |
| `pogo/cli.py` | Commands and the argument parser |
| `scripts/adb/` | Pulling data off an Android phone. Has its own README |
| `reference.md` | Verified game mechanics, each constant named to its source |

Nothing in `data/` is guessed. Every number traces to the game master, a
screenshot, or a cited source.

## Data quality

`data/box_list.csv` was 325 rows transcribed by hand from overlapping
screenshots, then validated against an independent Sinnoh Stone picker
screenshot on all 12 species it covered. The 145 transferred rows are gone,
leaving 180.

It carries no IVs, no candy counts, no legacy moves, no costumes and no size.
List-view screenshots don't show those. For raids that's fine: a perfect IV
spread is worth 3 to 5% DPS while one level band is worth more. Before any
mass transfer, search `@special`, `costume` and `xxl` in game and favorite
what they return.

Run `/verify` before committing. It dispatches read-only audit agents over the
docs and the constants. Fix every finding.
