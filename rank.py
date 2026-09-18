#!/usr/bin/env python3
"""Rank a Pokemon GO box against a raid boss, straight off the game master.

    source .venv/bin/activate
    python rank.py selftest
    python rank.py constants
    python rank.py counters ZAMAZENTA --tier 5
    python rank.py counters ZAMAZENTA --box data/box.csv --top 20
    python rank.py powerup --from 20 --to 40

PvE only. PvP ranks come from PvPoke, which simulates shields and baiting;
see README.md.
"""

import argparse
import logging
import sys

from pogo import battle, box
from pogo.gamemaster import GameMaster

DEFAULT_LEVEL = 40.0
DEFAULT_IVS = (15, 15, 15)


def _fmt_move(move_id):
    """Nine moves in the current game master have an integer id, not a name.

    The PokeMiners dumper had no enum name for them, so Dynamax Cannon
    arrives as 482. They're real moves, so print the number rather than
    dropping the row.
    """
    if move_id is None:
        return "-"
    if not isinstance(move_id, str):
        return f"move {move_id}"
    return move_id.replace("_FAST", "").replace("_", " ").title()


def cmd_selftest(gm, args):
    checks = battle.selftest(gm)
    width = max(len(name) for name, _, _, _ in checks)
    failed = 0
    for name, got, expected, ok in checks:
        flag = "ok  " if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"{flag} {name:<{width}}  got={got}  want={expected}")
    print(f"\n{len(checks) - failed}/{len(checks)} passed")
    return 1 if failed else 0


def cmd_constants(gm, args):
    """Everything the ranking depends on, in one place for the audit pass."""
    print(f"game master       {gm.path}")
    print(f"species forms     {len(gm.species)}")
    print(f"moves             {len(gm.moves)}")
    print(f"STAB              {gm.stab}")
    print(f"shadow attack     {gm.shadow_attack}")
    print(f"shadow defense    {gm.shadow_defense}")
    print(f"boss move interval {gm.enemy_attack_interval}s")
    print(f"max Pokemon level {gm.max_pokemon_level}")
    print(f"levels above player {gm.levels_above_player}")
    print(f"XL candy from player level {gm.xl_min_player_level}, "
          f"Pokemon level {gm.xl_min_pokemon_level}")
    print(f"trainer level cap {gm.trainer_level_cap} "
          f"({gm.xp_only_level_cap} by XP alone, then Level-Up Research)")
    print("type multipliers  "
          f"{sorted({v for row in gm.type_chart.values() for v in row.values()})}")
    print("\nraid tiers (not in the game master, see reference.md):")
    for tier, values in sorted(battle.RAID_TIERS.items()):
        print(f"  T{tier}  cpm={values['cpm']}  hp={values['hp']}")
    return 0


def _boss(gm, name, tier):
    matches = gm.find(name)
    if not matches:
        sys.exit(f"no species matches {name!r}")
    species = matches[0]
    return species, battle.build_boss(gm, species, tier)


def _from_box(gm, path, level_cap):
    entries, fuzzy = box.load(path)
    if fuzzy:
        print(f"warning: {len(fuzzy)} of {len(entries)} rows have IV ranges "
              f"rather than exact IVs. Appraisal-scan those in Calcy IV first.",
              file=sys.stderr)
    out, unresolved = [], []
    for entry in entries:
        species = box.resolve(gm, entry)
        if species is None:
            unresolved.append(entry.species)
            continue
        level = entry.level or DEFAULT_LEVEL
        level = min(level, level_cap)
        combatant = battle.build(gm, species, entry.ivs, level, entry.shadow)
        out.append((entry.nickname or species.name, combatant, entry, level))
    if unresolved:
        print(f"warning: {len(unresolved)} rows did not match a species: "
              f"{sorted(set(unresolved))}", file=sys.stderr)
    return out


def _all_species(gm, level):
    out = []
    for species in gm.unique_species():
        if not species.all_fast() or not species.all_charged():
            continue
        combatant = battle.build(gm, species, DEFAULT_IVS, level)
        out.append((species.name, combatant, None, level))
    return out


def cmd_counters(gm, args):
    species, boss = _boss(gm, args.boss, args.tier)
    if not battle.can_attack(gm, boss):
        sys.exit(f"{species.name} has no usable moveset in the game master, so "
                 f"there's nothing to rank against. Ditto and Smeargle do this.")
    print(f"Boss: {species.name} {'/'.join(species.types)} "
          f"T{args.tier}  atk={boss.attack:.1f} def={boss.defense:.1f} hp={boss.hp}")

    if args.box:
        roster = _from_box(gm, args.box, args.level_cap)
        source = f"{args.box} ({len(roster)} Pokemon)"
    else:
        roster = _all_species(gm, args.level)
        source = f"every species at level {args.level:g}, {'/'.join(map(str, DEFAULT_IVS))}"
    print(f"Attackers: {source}\n")

    rows = []
    for name, attacker, entry, level in roster:
        result = battle.matchup(gm, attacker, boss)
        if result is None:
            continue
        result["name"] = name
        result["level"] = level
        result["shadow"] = attacker.shadow
        rows.append(result)

    rows.sort(key=lambda r: r[args.sort], reverse=True)
    header = f"{'#':>3}  {'Pokemon':<22} {'Lv':>5}  {'DPS':>7} {'TDO':>8} {'Sec':>6}  Moveset"
    print(header)
    print("-" * len(header))
    for i, r in enumerate(rows[:args.top], 1):
        tag = f"{r['name']}{' (shadow)' if r['shadow'] else ''}"
        print(f"{i:>3}  {tag:<22} {r['level']:>5.1f}  {r['dps']:>7.2f} "
              f"{r['tdo']:>8.1f} {r['survival_s']:>6.1f}  "
              f"{_fmt_move(r['fast'])} + {_fmt_move(r['charged'])}")
    if not rows:
        print("(nothing could attack this boss)")
    return 0


def cmd_powerup(gm, args):
    try:
        cost = battle.powerup_cost(gm, args.start, args.end)
    except ValueError as exc:
        sys.exit(str(exc))
    print(f"level {args.start:g} -> {args.end:g}: "
          f"{cost['stardust']:,} stardust, {cost['candy']} candy, "
          f"{cost['xl_candy']} XL candy")
    if args.end > gm.xl_min_pokemon_level:
        print(f"XL candy applies from Pokemon level {gm.xl_min_pokemon_level} up, "
              f"and needs trainer level {gm.xl_min_player_level}+.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="log the parsed CSV payload row by row")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("selftest", help="check constants against known values")
    sub.add_parser("constants", help="print every constant the ranking uses")

    counters = sub.add_parser("counters", help="rank attackers against a boss")
    counters.add_argument("boss")
    counters.add_argument("--tier", type=int, default=5,
                          choices=sorted(battle.RAID_TIERS))
    counters.add_argument("--box", help="Calcy IV CSV export")
    counters.add_argument("--top", type=int, default=20)
    counters.add_argument("--sort", default="dps", choices=["dps", "tdo", "survival_s"])
    counters.add_argument("--level", type=float, default=DEFAULT_LEVEL,
                          help="level to assume when no box is given")
    counters.add_argument("--level-cap", type=float, default=50.0,
                          help="cap box levels, e.g. trainer level + 10")

    powerup = sub.add_parser("powerup", help="stardust and candy for a climb")
    powerup.add_argument("--from", dest="start", type=float, required=True)
    powerup.add_argument("--to", dest="end", type=float, required=True)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    gm = GameMaster()
    return {
        "selftest": cmd_selftest,
        "constants": cmd_constants,
        "counters": cmd_counters,
        "powerup": cmd_powerup,
    }[args.command](gm, args)


if __name__ == "__main__":
    sys.exit(main())
