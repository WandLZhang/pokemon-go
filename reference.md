# Pokemon GO mechanics

Every number here comes from the game master unless the row names another
source. `python rank.py constants` prints the live values, and `python rank.py
selftest` checks 39 of them against published anchors.

## Rules that break main-series advice

- **Super effective is 1.6x, not 2x.** Resisted is 0.625x. Double resisted is
  0.390625x. Two super-effective types stack to 2.56x.
- **Nothing is immune.** A main-series 0x becomes 0.390625x. Normal moves
  still damage a Ghost. Electric still damages Ground.
- **There's no physical or special split.** Every move uses the same Attack
  stat.
- **Base stats are GO's own.** They're derived from the main series, not
  copied. Machamp is 234 attack, 159 defense, 207 stamina.
- **A move has separate PvE and PvP values.** Wrap is 60 power and -33 energy
  in raids, 70 power and -45 energy in the league.
- **STAB is 1.2x**, not 1.5x.
- **Shadow adds attack and removes defense.** Attack 1.2x, defense 0.8333333.
  Both multipliers apply in raids and in the league.
- **IVs run 0 to 15.** Each IV adds to the base stat before the CP multiplier
  applies.

## Constants

| Value | Number | Source |
|---|---|---|
| STAB | 1.2 | `BATTLE_SETTINGS.sameTypeAttackBonusMultiplier` |
| Shadow attack | 1.2 | `BATTLE_SETTINGS.shadowPokemonAttackBonusMultiplier` |
| Shadow defense | 0.8333333 | `BATTLE_SETTINGS.shadowPokemonDefenseBonusMultiplier` |
| Boss wait between moves | 1.5 s | `BATTLE_SETTINGS.enemyAttackInterval` |
| Energy per HP lost | 0.5 | `BATTLE_SETTINGS.energyDeltaPerHealthLost` |
| Type multipliers | 1.6 / 1.0 / 0.625 / 0.390625 | `POKEMON_TYPE_*.attackScalar` |
| Max Pokemon level | 50 | `POKEMON_UPGRADE_SETTINGS.maxNormalUpgradeLevel` |
| Levels above trainer | 10 | `POKEMON_UPGRADE_SETTINGS.allowedLevelsAbovePlayer` |
| Power-ups per level | 2 | `POKEMON_UPGRADE_SETTINGS.upgradesPerLevel` |
| XL candy from | Pokemon level 40, trainer level 31 | `xlCandyMinPokemonLevel`, `xlCandyMinPlayerLevel` |
| CPM at 40 / 50 | 0.7903 / 0.8403 | `PLAYER_LEVEL_SETTINGS.cpMultiplier` |
| Trainer level cap | 80 | `len(PLAYER_LEVEL_SETTINGS.requiredExperience)` |

`defaultLevelCap` reads 70 and is a different thing. It's the level XP alone
reaches. Levels 71 to 80 also need Level-Up Research, so reading that field as
the cap understates it by 10.

## Formulas

```
CPM(L)      stored per whole level; CPM(L+0.5) = sqrt((CPM(L)^2 + CPM(L+1)^2) / 2)
CP          max(10, floor((Atk+IV) * sqrt(Def+IV) * sqrt(Sta+IV) * CPM^2 / 10))
HP          max(10, floor((Sta+IV) * CPM))
Damage      floor(0.5 * Power * Atk/Def * STAB * Effectiveness) + 1
Cycle DPS   (n * fast_damage + charged_damage) / (n * fast_time + charged_time)
            where n = charged_cost / fast_energy
Survival    HP / incoming DPS
TDO         cycle DPS * survival
```

CP uses stamina before the floor of 10 applies. HP applies it.

**Energy carries over in raids.** Firing a charged move debits its cost and
leaves the surplus, so `n` is the plain ratio. Rounding it up would discard
energy the game keeps, and that error runs up to 7% and reorders the list.

**The boss waits, the player doesn't.** A player taps as fast as the animation
allows. A raid boss idles `enemyAttackInterval` between moves. Leaving that
out understates survival time by a factor of 2 to 3.

**The boss rolls one moveset and keeps it.** Incoming damage is the average
over its whole movepool. Solving for the boss's best pair against each
attacker would let it counter-pick, which punishes anything weak to a single
move anywhere in the pool.

### What this model leaves out

- Neither side gains energy from damage taken. Worth 1 to 6% of DPS.
- No weather, friendship, Party Power, Mega bonus or dodging.

Friendship and the Mega bonus scale every attacker alike, so they drop out of
a ranking. Weather keys off the move's type and does reorder, so rank in
neutral weather. Against published DPS lists this engine runs 1 to 6% low,
which is the energy term.

## Power-up costs

| Climb | Stardust | Candy | XL candy |
|---|---|---|---|
| 1 to 40 | 270,000 | 304 | 0 |
| 30 to 40 | 150,000 | 182 | 0 |
| 40 to 50 | 250,000 | 0 | 296 |
| 30 to 50 | 400,000 | 182 | 296 |

The cost arrays are indexed by whole level and charged once per half-level
step. Level 40 to 41 pays `stardustCost[39]` twice. A wrong index still
produces plausible totals, so `selftest` pins all four rows.

A Pokemon at level 30 already has 87% of the CP multiplier it will ever have,
and 93% at level 40. Spread the dust across more attackers before you push any
one of them past 40.

## Raid bosses

These aren't in the game master. The client applies a flat multiplier and a
flat HP per tier, and the boss always has perfect Attack and Defense IVs.

| Tier | Multiplier | HP |
|---|---|---|
| 1 | 0.61 | 600 |
| 3 | 0.73 | 3,600 |
| 5 | 0.79 | 15,000 |

T3 went from 3,000 to 3,600 and T5 from 12,500 to 15,000 in the February 2019
rebalance. Articles older than that still print the low values.

Displayed boss CP uses a different formula from the one that sets its battle
stats, so you can't work backward from the CP on the raid egg.

## Trainer level 40

Great Ball Cap, +50 Pokemon storage, +75 item bag, 1 Elite Fast TM, 2 Lucky
Egg, 2 Incense, 2 Egg Incubator, 20 Max Revive, 40 Max Potion, 40 Ultra Ball,
30 Pinap Berry.

That's 137 items against a bag that grows by 75. The cap and the two storage
upgrades take no bag slot.

## Items

| Item | Effect | Source |
|---|---|---|
| Gift, Stickers | Don't use bag space | Niantic, below |
| Shadow Shard | 4 refine into 1 Purified Gem, automatically | `ITEM_SHADOW_GEM_FRAGMENT.upgradeRequirementCount` |
| Purified Gem | Subdues an enraged Shadow raid boss. Takes 8 across the group | GO Hub, below |
| Star Piece | 1.5x stardust for 30 minutes | `ITEM_STAR_PIECE.stardustBoost` |
| Rare Candy | Becomes one candy of whichever species you use it on | Niantic, below |
| Elite Fast TM | Picks the fast move, including legacy moves | Niantic, below |
| Charged TM | Rerolls the charged move at random | Niantic, below |

Niantic's "Types of Items and their Effects" page says five Shadow Shards make
a gem. The game master says four, and so does every other source. Four is
right.

## Sources

Game data comes from the [PokeMiners game master](https://github.com/PokeMiners/game_masters),
`latest/latest.json`. `fetch.sh` records the date and SHA of the copy in use.

Values that aren't in the game master:

- Type multipliers, cross-checked: [Pokemon GO type chart, Pokemon Database](https://pokemondb.net/go/type)
- Raid boss tiers, HP and the separate CP formula: [Raid Battle (GO), Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Raid_Battle_(GO))
- Boss move delay, cross-checked: [Pokebattler battle simulator](https://articles.pokebattler.com/battle-simulator/)
- Energy carryover and comprehensive DPS: [Energy (GO), Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/Energy_(GO))
- The 8-gem threshold: [Shadow Raids guide, GO Hub](https://pokemongohub.net/post/news/pokemon-go-shadow-raids-comprehensive-guide/)
- Trainer level rewards and XP: [Trainer Levels, Leek Duck](https://leekduck.com/references/trainer-levels/)
- Level 71 to 80 needing research: [Leveling update, Niantic](https://pokemongo.com/post/pgo-leveling-update-details-2025/)
- Gifts and stickers outside the bag, and item effects: [Available Items and your Bag, Niantic](https://niantic.helpshift.com/hc/en/6-pokemon-go/faq/3049-available-items-your-bag/)
- Purified Gem caps: [What are Purified Gems, Niantic](https://niantic.helpshift.com/hc/en/6-pokemon-go/faq/4055-what-are-purified-gems-and-how-do-i-collect-them/)
- Power-up cost totals: [Power-up costs, GO Hub](https://pokemongohub.net/post/guide/guide-to-power-up-costs-in-pokemon-go/), [XL Candy guide, GO Hub](https://pokemongohub.net/post/guide/xl-candy-guide-how-to-get-power-up-costs-and-mechanics/)

GamePress shut its Pokemon GO wiki down and every `gamepress.gg/pokemongo`
link now 404s. Don't cite it.
