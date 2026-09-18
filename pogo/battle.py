"""Pokemon GO battle math.

GO is not the main series. No physical/special split, super effective is
1.6x not 2x, and every move carries its own energy and duration. Each
formula below names the game master field it reads.

Declared simplifications, both of which scale DPS and TDO downward by a few
percent without reordering much:

- Neither side gains energy from damage taken. The game master carries
  `energyDeltaPerHealthLost` and `bossEnergyRegenerationPerHealthLost`, both
  0.5, and this model reads neither. Costs 1-6% of DPS.
- No weather, friendship, Party Power, Mega bonus or dodging. Friendship and
  Mega scale every attacker alike and drop out of a ranking. Weather is
  per-move-type and does reorder, so rank in neutral weather.
"""

import math
from dataclasses import dataclass

# Raid boss stats aren't in the game master. The client applies a flat tier
# multiplier and a flat HP value, and the boss always has 15/15 Atk/Def IVs.
# reference.md carries the citations.
RAID_TIERS = {
    1: {"cpm": 0.61, "hp": 600},
    3: {"cpm": 0.73, "hp": 3600},
    5: {"cpm": 0.79, "hp": 15000},
}
BOSS_IV = 15

# A Pokemon level is always a multiple of 0.5.
LEVEL_STEP = 0.5


def _check_level(gm, level, label="level"):
    if level < 1 or level > gm.max_pokemon_level:
        raise ValueError(f"{label} {level} outside 1..{gm.max_pokemon_level}")
    steps = level / LEVEL_STEP
    if abs(steps - round(steps)) > 1e-9:
        raise ValueError(f"{label} {level} isn't a multiple of {LEVEL_STEP}")


def cpm(gm, level):
    """CP multiplier at a level. Whole levels are stored; halves interpolate."""
    _check_level(gm, level)
    low = int(math.floor(level))
    if low == level:
        return gm.cpm_table[low - 1]
    a = gm.cpm_table[low - 1]
    b = gm.cpm_table[low]
    return math.sqrt((a * a + b * b) / 2.0)


def combat_power(gm, species, ivs, level):
    """CP = floor(Atk * sqrt(Def) * sqrt(Sta) * CPM^2 / 10), floored at 10.

    CP uses stamina before the HP floor of 10 applies.
    """
    m = cpm(gm, level)
    atk = species.base_attack + ivs[0]
    dfn = species.base_defense + ivs[1]
    sta = species.base_stamina + ivs[2]
    cp = atk * math.sqrt(dfn) * math.sqrt(sta) * m * m / 10.0
    return max(10, int(math.floor(cp)))


def hit_points(gm, species, iv_stamina, level):
    """HP = max(10, floor((Sta + IV) * CPM)). Shedinja lives on the floor."""
    return max(10, int(math.floor((species.base_stamina + iv_stamina) * cpm(gm, level))))


@dataclass
class Combatant:
    """Resolved stats for one side of a fight."""

    species: object
    attack: float
    defense: float
    hp: int
    shadow: bool = False

    @property
    def types(self):
        return self.species.types


def build(gm, species, ivs, level, shadow=False):
    m = cpm(gm, level)
    attack = (species.base_attack + ivs[0]) * m
    defense = (species.base_defense + ivs[1]) * m
    if shadow:
        attack *= gm.shadow_attack
        defense *= gm.shadow_defense
    return Combatant(species, attack, defense, hit_points(gm, species, ivs[2], level), shadow)


def build_boss(gm, species, tier):
    """A raid boss: perfect Atk/Def IVs, tier multiplier, flat tier HP."""
    if tier not in RAID_TIERS:
        raise ValueError(f"tier {tier} not in {sorted(RAID_TIERS)}")
    t = RAID_TIERS[tier]
    return Combatant(
        species,
        (species.base_attack + BOSS_IV) * t["cpm"],
        (species.base_defense + BOSS_IV) * t["cpm"],
        t["hp"],
    )


def damage(gm, power, attacker, defender, move_type):
    """floor(0.5 * Power * Atk/Def * STAB * Effectiveness) + 1."""
    stab = gm.stab if move_type in attacker.types else 1.0
    eff = gm.effectiveness(move_type, defender.types)
    raw = 0.5 * power * (attacker.attack / defender.defense) * stab * eff
    return int(math.floor(raw)) + 1


def movesets(gm, species):
    """Every legal fast and charged pair, elite moves included."""
    for fast_id in species.all_fast():
        fast = gm.moves.get(fast_id)
        if fast is None or fast.energy_delta <= 0 or fast.duration_ms <= 0:
            continue
        for charged_id in species.all_charged():
            charged = gm.moves.get(charged_id)
            if charged is None or charged.energy_delta >= 0 or charged.duration_ms <= 0:
                continue
            yield fast_id, fast, charged_id, charged


def cycle_dps(gm, attacker, defender, fast, charged, move_interval=0.0):
    """Sustained DPS of one fast and charged pair, no dodging.

    Energy carries over in raids, so the long-run count of fast moves per
    charged move is cost / gain. Rounding that up would throw away the
    surplus the game keeps.

    move_interval adds idle time between moves. It's zero for the player,
    who taps as fast as the animation allows, and enemyAttackInterval for a
    raid boss, which waits.
    """
    cost = -charged.energy_delta
    if fast.energy_delta <= 0 or cost <= 0:
        return 0.0
    n = cost / fast.energy_delta
    fast_damage = damage(gm, fast.power, attacker, defender, fast.type)
    charged_damage = damage(gm, charged.power, attacker, defender, charged.type)
    total_damage = n * fast_damage + charged_damage
    total_time = (n * (fast.duration_s + move_interval)
                  + charged.duration_s + move_interval)
    return total_damage / total_time


def best_moveset(gm, attacker, defender):
    """Highest-DPS pair for this attacker. Returns (dps, fast_id, charged_id)."""
    best = (0.0, None, None)
    for fast_id, fast, charged_id, charged in movesets(gm, attacker.species):
        dps = cycle_dps(gm, attacker, defender, fast, charged)
        if dps > best[0]:
            best = (dps, fast_id, charged_id)
    return best


def incoming_dps(gm, boss, attacker):
    """Damage the boss deals, averaged over its whole movepool.

    A raid boss rolls one moveset when the raid starts and keeps it, so the
    expectation across the pool is the honest model. Solving for the boss's
    single best pair against each attacker instead would let the boss
    counter-pick, which punishes anything weak to one move in the pool.

    The boss also waits BATTLE_SETTINGS.enemyAttackInterval between moves.
    """
    values = [cycle_dps(gm, boss, attacker, fast, charged, gm.enemy_attack_interval)
              for _, fast, _, charged in movesets(gm, boss.species)]
    values = [v for v in values if v > 0]
    return sum(values) / len(values) if values else 0.0


def can_attack(gm, combatant):
    """True when this Pokemon has at least one usable pair."""
    return any(True for _ in movesets(gm, combatant.species))


def matchup(gm, attacker, boss):
    """Rank one attacker against one boss. Returns DPS, TDO and survival time.

    Raises ValueError when the boss has no usable moveset, which is a problem
    with the boss rather than with the attacker.
    """
    dps, fast_id, charged_id = best_moveset(gm, attacker, boss)
    if dps == 0.0:
        return None
    against = incoming_dps(gm, boss, attacker)
    if against <= 0:
        raise ValueError(
            f"{boss.species.name} has no usable moveset, so nothing can be "
            f"ranked against it")
    survival_s = attacker.hp / against
    return {
        "dps": dps,
        "tdo": dps * survival_s,
        "survival_s": survival_s,
        "incoming_dps": against,
        "fast": fast_id,
        "charged": charged_id,
    }


def powerup_cost(gm, start, end):
    """Stardust and candy to climb from one level to another.

    POKEMON_UPGRADE_SETTINGS indexes its cost arrays by whole level, and
    charges that cost once per half-level step. So level 40 to 41 pays
    stardustCost[39] twice. XL candy replaces normal candy from
    xlCandyMinPokemonLevel up.
    """
    _check_level(gm, start, "start")
    _check_level(gm, end, "end")
    if start >= end:
        raise ValueError(f"start {start} isn't below end {end}")
    dust = candy = xl = 0
    level = start
    while level < end - 1e-9:
        index = int(math.floor(level)) - 1
        dust += gm.stardust_cost[index]
        if level >= gm.xl_min_pokemon_level:
            xl += gm.xl_candy_cost[int(math.floor(level)) - gm.xl_min_pokemon_level]
        else:
            candy += gm.candy_cost[index]
        level += LEVEL_STEP
    return {"stardust": dust, "candy": candy, "xl_candy": xl}


def selftest(gm):
    """Check the constants before any ranking is trusted."""
    checks = []

    # Type chart index order. POKEMON_TYPES is the proto enum order and
    # nothing in the game master states it, so these matchups are the only
    # thing holding it. They're chosen to break under any single label swap:
    # every type appears as an attacker or a defender in a non-1.0 cell.
    known = [
        ("DRAGON", ("FAIRY",), 0.390625),
        ("DRAGON", ("STEEL",), 0.625),
        ("DRAGON", ("DRAGON",), 1.6),
        ("NORMAL", ("GHOST",), 0.390625),
        ("GHOST", ("NORMAL",), 0.390625),
        ("GROUND", ("FLYING",), 0.390625),
        ("FIGHTING", ("ROCK", "DARK"), 1.6 * 1.6),
        ("FIGHTING", ("BUG",), 0.625),
        ("WATER", ("FIRE", "GROUND"), 1.6 * 1.6),
        ("ELECTRIC", ("WATER", "FLYING"), 1.6 * 1.6),
        ("PSYCHIC", ("DARK",), 0.390625),
        ("BUG", ("PSYCHIC",), 1.6),
        ("FAIRY", ("DRAGON",), 1.6),
        ("ICE", ("STEEL",), 0.625),
        ("ICE", ("ICE",), 0.625),
        ("POISON", ("GRASS",), 1.6),
        ("POISON", ("GROUND",), 0.625),
        ("FLYING", ("FIGHTING",), 1.6),
        ("FLYING", ("POISON",), 1.0),
        ("STEEL", ("FAIRY",), 1.6),
    ]
    for atk, defs, expected in known:
        got = gm.effectiveness(atk, defs)
        checks.append((f"{atk} vs {'/'.join(defs)}", got, expected,
                       abs(got - expected) < 1e-9))

    # CPM anchors.
    for level, expected in ((1, 0.094), (20, 0.5974), (30, 0.7317),
                            (40, 0.7903), (50, 0.8403)):
        got = cpm(gm, level)
        checks.append((f"CPM L{level}", got, expected, abs(got - expected) < 1e-6))

    mid = cpm(gm, 20.5)
    checks.append(("CPM L20.5 bracketed", round(mid, 5), "0.5974<x<0.6063",
                   cpm(gm, 20) < mid < cpm(gm, 21)))

    # Off-grid levels must be rejected, not snapped to the nearest half.
    try:
        cpm(gm, 20.3)
        off_grid_rejected = False
    except ValueError:
        off_grid_rejected = True
    checks.append(("CPM rejects L20.3", off_grid_rejected, True, off_grid_rejected))

    # A level 40 perfect Machamp is 3056 CP in game.
    machamp = gm.find("MACHAMP")[0]
    got = combat_power(gm, machamp, (15, 15, 15), 40)
    checks.append(("Machamp 15/15/15 L40 CP", got, 3056, got == 3056))

    # HP floors at 10. Shedinja is base stamina 1 and would otherwise be 0.
    shedinja = gm.find("SHEDINJA")
    if shedinja:
        got = hit_points(gm, shedinja[0], 0, 40)
        checks.append(("Shedinja HP floor", got, 10, got == 10))

    checks.append(("shadow attack", gm.shadow_attack, 1.2,
                   abs(gm.shadow_attack - 1.2) < 1e-9))
    checks.append(("STAB", gm.stab, 1.2, abs(gm.stab - 1.2) < 1e-9))
    checks.append(("boss move interval", gm.enemy_attack_interval, 1.5,
                   abs(gm.enemy_attack_interval - 1.5) < 1e-9))

    # Power-up cost anchors. These pin the whole-level indexing: a wrong
    # index still produces plausible numbers, so check published totals.
    to_40 = powerup_cost(gm, 1, 40)
    checks.append(("dust L1->L40", to_40["stardust"], 270000,
                   to_40["stardust"] == 270000))
    checks.append(("candy L1->L40", to_40["candy"], 304, to_40["candy"] == 304))
    to_50 = powerup_cost(gm, 40, 50)
    checks.append(("dust L40->L50", to_50["stardust"], 250000,
                   to_50["stardust"] == 250000))
    checks.append(("XL candy L40->L50", to_50["xl_candy"], 296,
                   to_50["xl_candy"] == 296))
    checks.append(("no normal candy past L40", to_50["candy"], 0,
                   to_50["candy"] == 0))
    checks.append(("dust L30->L50", powerup_cost(gm, 30, 50)["stardust"], 400000,
                   powerup_cost(gm, 30, 50)["stardust"] == 400000))

    # Duplicate forms must collapse, or every ranking lists each Pokemon twice.
    uniques = gm.unique_species()
    checks.append(("unique < raw forms", len(uniques), f"<{len(gm.species)}",
                   len(uniques) < len(gm.species)))

    return checks
