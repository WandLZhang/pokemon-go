# Pokemon GO

Roster and bag for WillisZhang. Raids first, GO Battle League second.

Season: Twilight Trails, Sept 8 to Dec 1 2026. GO Battle League Season 28.

Game mechanics: [reference.md](reference.md). Ranking engine: [rank.py](rank.py).

## Do this now

1. **Spend one Sinnoh Stone on Roselia. Hold the other four.**

   The stones aren't the constraint, candy is. Every one of these costs 100
   candy, 120 if it's shadow and 90 if it's purified. A greyed-out entry in
   the stone picker means you're short of candy for that species, and the bar
   under each name is how far along you are.

   | Evolve | CP | Becomes | Rank | Candy ready |
   |---|---|---|---|---|
   | Roselia (favorite) | 1553 | Roserade | **#4 Grass** | yes |
   | Piloswine (shiny) | 1385 | Mamoswine | **#3 Ground** | partway |
   | Murkrow | 1048 | Honchkrow | #7 Flying | no |
   | Togetic | 955 | Togekiss | #7 Fairy | no |
   | Electabuzz | 1310 | Electivire | #8 Electric | no |
   | Gligar | 1046 / 371 | Gliscor | #19 Ground | one of them |
   | Lickitung | 793 | Lickilicky | #46 Ghost | yes |

   Roselia is the only ready one worth a stone. Lickilicky is #46 and does
   nothing in a raid, so don't spend one there just because you can.

   **Piloswine is the best target on the board** and it's closest to ready.
   Catch Swinub. Buddy walking won't get you there: Piloswine is 3 km per
   candy, so 100 candy is a 300 km walk against the 1,701 km you've logged in
   the life of the account. Catching pays 3 candy, 6 with a Pinap, and you
   hold 39 Pinap.

2. **Transfer 137 Pokemon.** `python rank.py box` names them. That frees 137
   slots and pays 137 candy plus stardust.

3. **Drop Poke Ball 236 to 50, and all 11 Hyper Potions.** Frees 197 and takes
   the bag to 374 of 550. You hold 82 Ultra Balls and 41 Great Balls, so the
   Poke Balls do nothing at level 39.

4. **Fight Giovanni.** Your Super Rocket Radar is unused. It came from GO
   Pass: Flying Taxi, which expired on July 1, so there's no way to get
   another one. He closes with **Shadow Reshiram**, and Shadow adds 1.2x
   attack.

5. **Beat one Rocket grunt.** You hold 3 Shadow Shards and 4 refine into a
   Purified Gem. One grunt drops one shard.

Giovanni's lineup: Shadow Persian, then one of Shadow Rhyperior, Shadow
Machamp or Shadow Kangaskhan, then Shadow Reshiram. Bring Fighting for the
first and third slots, Psychic for Machamp, and Ground or Rock for Reshiram.
Your Rhyperior is the Reshiram answer.

## Bag, 571 of 550

You can't receive items until you're under 550. Counts live in
`data/bag.json`, and they reconcile to 571.

| Item | Count | Call |
|---|---|---|
| Poke Ball | 236 | **Drop to 50.** You have 82 Ultra and 41 Great |
| Ultra Ball | 82 | Keep. This is your catching stock |
| Max Potion | 52 | Keep. Raid currency |
| Great Ball | 41 | Keep |
| Pinap Berry | 39 | Keep. Doubles catch candy |
| Razz Berry | 38 | Keep |
| Premium Battle Pass | 14 | **14 raid entries.** Spend them on the Fire and Ground bosses you're short of |
| Nanab Berry | 13 | Drop if you need more room. It calms, it doesn't help you catch |
| Hyper Potion | 11 | **Drop all.** Max Potion replaces it |
| Rare Candy | 6 | Hold for a legendary you're short on |
| Sinnoh Stone | 5 | **Spend all 5.** See above |
| Lure Module | 5 | Keep |
| Metal Coat | 3 | Only Scyther wants one. **Two are dead weight** |
| Unova Stone | 3 | Only Minccino wants one. **Two are dead weight** |
| Incense | 3 | Keep |
| Shadow Shard | 3 | **Beat one grunt** for the fourth |
| Charged TM | 2 | Hold for a raid attacker with a bad charged move |
| Sun Stone | 2 | Petilil and Helioptile. Neither is a raid attacker |
| Dragon Scale | 1 | Your shiny Horsea, 125 candy |
| Upgrade | 1 | No Porygon in the box. Dead until you catch one |
| Revive | 1 | **Spin gyms before you raid.** Level 40 pays 20 Max Revives |
| Star Piece | 1 | Save for a Community Day |
| Super Rocket Radar | 1 | **Use it.** See step 4 |
| Rocket Radar, Poffin, Egg Incubator, Raid Pass, 3 special Lures, Daily Adventure Incense | 1 each | Keep |

Gifts and stickers sit outside the bag and don't count toward the 550.

## Trainer

| Stat | Value |
|---|---|
| Level | 39 |
| XP to level 40 | 193,417 |
| Total XP | 3,759,583 |
| **Stardust** | **36,934** |
| Caught | 2,359 |
| Walked | 1,701.2 km |
| PokeStops | 1,155 |
| Friends | 23 |
| Buddy | Pancham |

Your power-up ceiling is level 49. Reaching trainer level 40 raises it to 50.

**Stardust is the binding constraint, not candy and not items.** 36,934 buys
about six power-ups at level 30 and above. Taking one Pokemon from level 30 to
40 costs 150,000. Evolving costs no dust at all, so evolve freely and power up
almost nothing until the dust recovers.

Level 40 also drops 137 items into the bag and grows the bag by 75. The full
reward list is in [reference.md](reference.md#trainer-level-40).

## Roster

311 Pokemon transcribed into `data/box_list.csv`. Run `python rank.py box`.

**The CP column is unreliable.** A Sinnoh Stone picker screenshot covering 12
of these species matched on 4 and disagreed on 8. Species names came through
clean, so the keep and transfer calls hold, but any specific CP here needs
checking against the game. Re-transcribe `capture/box/` before trusting a CP.

Transferring never removes a Pokedex entry. A species stays registered once
caught, so keeping one of every species is a collection preference. `box`
treats it that way and only keeps one of each when you pass `--collection`.

The game refuses to transfer a favorite, so those land in their own bucket
and need unfavoriting first.

Still waiting on `data/box.csv`, the Calcy IV export, for the IV tiebreak
among the keepers and for anything PvP.

Calcy reads one Pokemon at a time, so scanning a whole box costs an evening.
`python rank.py keepers` cuts it down. It ranks every species by its best
charged move per type against a neutral target, then prints the names as
Pokemon GO search strings. Paste a batch into the in-game search bar, scan
what matches in Calcy, and transfer the rest. At `--per-type 8` that's 77
names instead of the full box. A name you don't own matches nothing, so the
search filters itself.

Appraisal-scan before exporting. Calcy writes an IV range for anything you
never appraised, and the loader flags those rows rather than ranking them.

### Getting the CSV off the phone

There's no route from this workstation to an Android device, and `adb` needs
one. Calcy's export goes through the Android share sheet, so send it either
way:

1. Attach the CSV in chat. It lands on disk here, the same as a screenshot.
2. Share it to Google Drive, then share that file with
   `admin@williszhang.altostrat.com`. The gcloud token on this box carries the
   `drive` scope, so it can pull the file directly.

Calcy writes the CSV from its **History** screen, in the three-dot menu, not
from the renaming settings.

## Running it

```sh
source .venv/bin/activate
./fetch.sh                      # pull the current game master
python rank.py selftest         # 39 checks against published values
python rank.py constants        # every constant the ranking uses
python rank.py counters ZAMAZENTA --tier 5 --top 15
python rank.py counters ZAMAZENTA --box data/box.csv --level-cap 49
python rank.py box                    # keep or transfer, per Pokemon
python rank.py keepers --per-type 8   # which Pokemon are worth scanning
python rank.py evolve                 # what your evolution items can buy
python rank.py powerup --from 30 --to 40
```

`data/bag.json` holds the item counts read off the screenshots. `evolve`
reads it, so correcting a count there corrects the advice.

`counters` ranks every species at level 40 with perfect IVs, including forms
you can't obtain. Pass `--box` to rank what you own.

Run `/verify` before committing. It dispatches read-only audit agents over the
docs and the constants. Fix every finding.
