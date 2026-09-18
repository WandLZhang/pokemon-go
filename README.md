# Pokemon GO

Roster and bag for WillisZhang. Raids first, GO Battle League second.

Season: Twilight Trails, Sept 8 to Dec 1 2026. GO Battle League Season 28.

Game mechanics: [reference.md](reference.md). Ranking engine: [rank.py](rank.py).

## Do this now

1. **Drop Poke Ball 236 to 50.** Frees 186 slots.
2. **Drop all 11 Hyper Potions.** Max Potion does the same job and you hold 52.
3. **Fight Giovanni.** Your Super Rocket Radar is unused. It came from GO Pass:
   Flying Taxi, which expired on July 1, so there's no way to get another one.
   He closes with **Shadow Reshiram**, and Reshiram already ranks near the top
   of the Fire attackers this engine scores. Shadow adds 1.2x attack on top.
4. **Beat one Rocket grunt.** You hold 3 Shadow Shards and 4 refine into a
   Purified Gem. One grunt drops one shard.

Steps 1 and 2 free 197 slots and take the bag to 374 of 550.

Giovanni's lineup: Shadow Persian, then one of Shadow Rhyperior, Shadow
Machamp or Shadow Kangaskhan, then Shadow Reshiram. Bring Fighting for the
first and third slots, Psychic for Machamp, and Ground or Rock for Reshiram.

## Bag, 571 of 550

You can't receive items until you're under 550.

| Item | Count | Call |
|---|---|---|
| Poke Ball | 236 | **Drop to 50.** Worst ball you own, and stops refill it |
| Max Potion | 52 | Keep. Raid currency |
| Great Ball | 41 | Keep |
| Gift | 21 | Free. Gifts sit outside the bag |
| Hyper Potion | 11 | **Drop all.** Max Potion replaces it |
| Rare Candy | 6 | Hold for a legendary you're short on |
| Sinnoh Stone | 5 | Keep |
| Incense | 3 | Keep |
| Metal Coat | 3 | Keep |
| Unova Stone | 3 | Keep |
| Shadow Shard | 3 | **Beat one grunt** for the fourth |
| Charged TM | 2 | Hold for a raid attacker with a bad charged move |
| Sun Stone | 2 | Keep |
| Revive | 1 | **Spin gyms before you raid.** Level 40 pays 20 Max Revives |
| Dragon Scale | 1 | Keep |
| Upgrade | 1 | Keep |
| Star Piece | 1 | Save for a Community Day |
| Poffin | 1 | Keep |
| Rocket Radar | 1 | Assembled |
| Super Rocket Radar | 1 | **Use it.** See step 3 |

Those rows total 374 items. The bag reads 571, and gifts don't count against
it, so **197 items aren't in the screenshots**. Berries, Ultra Balls, passes
and lures are all missing. Send the rest of the scroll and I'll finish this.

## Trainer

| Stat | Value |
|---|---|
| Level | 39 |
| XP to level 40 | 193,417 |
| Total XP | 3,759,583 |
| Caught | 2,359 |
| Walked | 1,701.2 km |
| PokeStops | 1,155 |
| Friends | 23 |
| Buddy | Pancham |

Your power-up ceiling is level 49. Reaching trainer level 40 raises it to 50.

Level 40 also drops 137 items into the bag and grows the bag by 75. The full
reward list is in [reference.md](reference.md#trainer-level-40).

## Roster

Waiting on `data/box.csv`, the Calcy IV export.

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
