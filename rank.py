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
import json
import logging
import sys
from pathlib import Path

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


def cmd_keepers(gm, args):
    """The only Pokemon worth scanning into Calcy, by attacking type.

    Everything not on this list is transfer fodder for a raids-first player,
    so scanning it wastes an evening. The output is a Pokemon GO search
    string: paste it in game and only the candidates show.
    """
    target = battle.neutral_target()
    per_type = {}
    for species in gm.unique_species():
        attacker = battle.build(gm, species, DEFAULT_IVS, args.level)
        for _, fast, charged_id, charged in battle.movesets(gm, species):
            dps = battle.cycle_dps(gm, attacker, target, fast, charged)
            if dps <= 0:
                continue
            best = per_type.setdefault(charged.type, {})
            if dps > best.get(species.name, (0.0, None))[0]:
                best[species.name] = (dps, charged_id)

    keep = {}
    for move_type in sorted(per_type):
        ranked = sorted(per_type[move_type].items(), key=lambda kv: -kv[1][0])
        top = ranked[:args.per_type]
        print(f"\n{move_type}")
        for i, (name, (dps, charged_id)) in enumerate(top, 1):
            print(f"  {i:>2}. {name:<28} {dps:>6.2f} DPS  {_fmt_move(charged_id)}")
        for name, _ in top:
            keep.setdefault(name, set()).add(move_type)

    # GO search matches the species name, so strip the form suffix and
    # dedupe. A name you don't own simply matches nothing.
    terms = sorted({name.split("_")[0].lower() for name in keep})
    print(f"\n{len(keep)} forms, {len(terms)} distinct names to search.\n")
    print("Paste these into the Pokemon GO search bar, one batch at a time:")
    for i in range(0, len(terms), args.batch):
        print(f"\n  {','.join(terms[i:i + args.batch])}")
    print("\nScan what matches in Calcy IV. Transfer the rest.")
    return 0


def cmd_evolve(gm, args):
    """What each evolution item in the bag can actually buy.

    An evolution item is dead weight until you hold the Pokemon it needs, so
    this lists every species each one unlocks and how the result ranks as an
    attacker. Spend them, don't delete them.
    """
    bag = json.loads(Path(args.bag).read_text())
    held = {v["item_id"]: (name, v["count"])
            for name, v in bag["items"].items() if "item_id" in v}

    target = battle.neutral_target()

    def best_dps(species):
        attacker = battle.build(gm, species, DEFAULT_IVS, DEFAULT_LEVEL)
        dps, _, charged_id = battle.best_moveset(gm, attacker, target)
        return dps, charged_id

    uses = {}
    for species in gm.unique_species():
        for evolves_into, item_id, candy in species.evolutions:
            if item_id and item_id in held:
                uses.setdefault(item_id, []).append((species, evolves_into, candy))

    for item_id, (name, count) in sorted(held.items(), key=lambda kv: -kv[1][1]):
        rows = uses.get(item_id)
        if not rows:
            continue
        print(f"\n{name} x{count}")
        scored = []
        for species, evolves_into, candy in rows:
            results = gm.find(evolves_into)
            if not results:
                continue
            dps, charged_id = best_dps(results[0])
            scored.append((dps, species.name, evolves_into, candy, charged_id))
        scored.sort(reverse=True)
        for dps, from_name, into, candy, charged_id in scored[:args.top]:
            tag = f"{from_name} -> {into}"
            print(f"  {tag:<38} {candy:>4} candy  {dps:>6.2f} DPS  "
                  f"{_fmt_move(charged_id)}")
        if len(scored) > args.top:
            print(f"  ... and {len(scored) - args.top} more, all below "
                  f"{scored[args.top - 1][0]:.2f} DPS")
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

    keepers = sub.add_parser("keepers",
                             help="which Pokemon are worth scanning, by type")
    keepers.add_argument("--per-type", type=int, default=6)
    keepers.add_argument("--level", type=float, default=DEFAULT_LEVEL)
    keepers.add_argument("--batch", type=int, default=12,
                         help="names per search string")

    evolve = sub.add_parser("evolve", help="what your evolution items can buy")
    evolve.add_argument("--bag", default="data/bag.json")
    evolve.add_argument("--top", type=int, default=8)

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
        "keepers": cmd_keepers,
        "evolve": cmd_evolve,
        "powerup": cmd_powerup,
    }[args.command](gm, args)


if __name__ == "__main__":
    sys.exit(main())
