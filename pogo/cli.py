"""Command line surface. rank.py is the entry point; this is the work.

Commands split three ways: check the engine (selftest, constants), ask the
game master a question (counters, powerup), or act on the box
(box, plan, roster, evolve).
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from pogo import battle, roster
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
    exact = [s for s in matches if s.pokemon_id == name.upper().replace(" ", "_")]
    if not exact and len(matches) > 1:
        names = ", ".join(sorted(m.name for m in matches)[:12])
        sys.exit(f"{name!r} matches {len(matches)} species: {names}. Be specific.")
    species = (exact or matches)[0]
    return species, battle.build_boss(gm, species, tier)


def _from_box(gm, path, level_cap):
    """Load the maintained box list as attackers at assumed perfect IVs.

    box_list.csv has no IVs, and for raids that costs 3 to 5% DPS. Level is
    unknown too, so everything is scored at level_cap. Read the output as
    the ceiling of what you own, not what it does today.
    """
    out = []
    for h in roster.load_list(gm, path):
        combatant = battle.build(gm, h.species, DEFAULT_IVS, level_cap)
        out.append((h.species_name, combatant, h, level_cap))
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
        attackers = _from_box(gm, args.box, args.level_cap)
        source = f"{args.box} ({len(attackers)} Pokemon)"
    else:
        attackers = _all_species(gm, args.level)
        source = f"every species at level {args.level:g}, {'/'.join(map(str, DEFAULT_IVS))}"
    print(f"Attackers: {source}\n")

    rows = []
    for name, attacker, entry, level in attackers:
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
        if args.top and len(scored) > args.top:
            print(f"  ... and {len(scored) - args.top} more, all below "
                  f"{scored[args.top - 1][0]:.2f} DPS")
    return 0


def cmd_box(gm, args):
    """Keep or transfer, for every Pokemon in the transcribed box list."""
    holdings = roster.evaluate(gm, roster.load_list(gm, args.list),
                               keep_rank=args.keep_rank,
                               keep_one_of_each=args.collection,
                               respect_favorites=not args.unfavorite,
                               buddy=args.buddy)
    order = {"KEEP": 0, "EVOLVE": 1, "HOLD": 2, "BUDDY": 3, "LOCKED": 4,
             "COLLECTION": 5, "TRANSFER": 6, "RECHECK": 7}
    counts = {}
    for h in holdings:
        counts[h.verdict] = counts.get(h.verdict, 0) + 1

    print(f"{len(holdings)} Pokemon, "
          f"{len({h.species.pokemon_id for h in holdings})} species\n")
    for verdict in sorted(counts, key=lambda v: order[v]):
        print(f"  {verdict:<9} {counts[verdict]:>4}")

    for verdict in ("RECHECK", "KEEP", "EVOLVE"):
        rows = [h for h in holdings if h.verdict == verdict]
        rows.sort(key=lambda h: (h.type_rank or 9999, -(h.cp or 0)))
        print(f"\n== {verdict} ({len(rows)}) ==")
        for h in rows[:args.top]:
            flags = f" [{','.join(sorted(h.flags))}]" if h.flags else ""
            cp = f"{h.cp:>5}" if h.cp is not None else "    ?"
            print(f"  {h.species_name:<18} {cp} CP  {h.reason}{flags}")
        if len(rows) > args.top:
            print(f"  ... {len(rows) - args.top} more")

    transfers = [h for h in holdings if h.verdict == "TRANSFER"]
    if transfers:
        print(f"\n== TRANSFER ({len(transfers)}) ==")
        by_species = {}
        for h in transfers:
            by_species.setdefault(h.species_name, []).append(h.cp)
        for name in sorted(by_species):
            cps = ", ".join(str(c) if c is not None else "?"
                            for c in sorted(by_species[name],
                                            key=lambda c: -(c or 0)))
            print(f"  {name:<18} {cps}")
        print(f"\n  Frees {len(transfers)} slots and pays "
              f"{len(transfers)} candy plus stardust.")
    return 0


def _search_batches(names, size):
    """Pokemon GO search strings, comma separated. Comma means OR."""
    ordered = sorted({n.split("_")[0].lower() for n in names})
    return [",".join(ordered[i:i + size]) for i in range(0, len(ordered), size)]


def cmd_plan(gm, args):
    """The transfer pass as taps, not as a list to read.

    Most species leave the box entirely, so those collapse into a search
    string: paste it, select all, transfer. Only the species where some
    copies stay need reading, and those print with CPs.
    """
    import collections

    holdings = roster.evaluate(gm, roster.load_list(gm, args.list),
                               keep_rank=args.keep_rank,
                               keep_one_of_each=args.collection,
                               respect_favorites=False,
                               buddy=args.buddy)
    owned = collections.Counter(h.species.pokemon_id for h in holdings)
    going = collections.defaultdict(list)
    for h in holdings:
        if h.verdict == "TRANSFER":
            going[h.species.pokemon_id].append(h)

    sweep = {k: v for k, v in going.items() if len(v) == owned[k]}
    pick = {k: v for k, v in going.items() if len(v) < owned[k]}
    unfavorite = [h for h in holdings if h.verdict == "TRANSFER" and h.locked]
    total = sum(len(v) for v in going.values())

    held = len(holdings)
    print(f"TRANSFER {total}. Box {held} -> {held - total}.\n")
    if not total:
        print("Nothing left to transfer. Re-run after the next capture.")
        return 0
    print("0. Before any of this, run these three searches and favorite what")
    print("   they return. The box list carries none of these flags, so the")
    print("   plan below can't see them.\n")
    print("   @special   legacy or event-exclusive moves, no Elite TM restores them")
    print("   costume    event Pokemon, not re-catchable and blocked from HOME")
    print("   xxl        worth +178 in a Showcase, which pays stardust\n")
    print("   The mass-transfer prompt will offer to INCLUDE these. Leave them out.\n")

    if unfavorite:
        print(f"1. Unfavorite these {len(unfavorite)} first. The game won't "
              f"transfer a favorite.\n")
        for batch in _search_batches([h.species_name for h in unfavorite], args.batch):
            print(f"   {batch}")
        print()

    swept = sum(len(v) for v in sweep.values())
    print(f"2. Paste each line into the Pokemon GO search bar, then select all "
          f"and transfer.\n   {swept} Pokemon across {len(sweep)} species, none "
          f"of which you keep a copy of.\n")
    names = [v[0].species_name for v in sweep.values()]
    batches = _search_batches(names, args.batch)
    for i, batch in enumerate(batches, 1):
        if args.markdown:
            # One fenced block per line. A multi-line block copied into the
            # game's single-line search field loses everything after the
            # first newline.
            print(f"\nLine {i} of {len(batches)}\n```\n{batch}\n```")
        else:
            print(f"   {batch}")

    if pick:
        picked = sum(len(v) for v in pick.values())
        print(f"\n3. These {picked} need picking, because you keep another copy. "
              f"Search the name and transfer the CP listed.\n")
        for key in sorted(pick, key=lambda k: pick[k][0].species_name):
            rows = pick[key]
            keep = [h for h in holdings
                    if h.species.pokemon_id == key and h.verdict != "TRANSFER"]
            drop = ", ".join(str(h.cp) for h in sorted(rows, key=lambda x: -(x.cp or 0)))
            held = ", ".join(str(h.cp) for h in sorted(keep, key=lambda x: -(x.cp or 0)))
            print(f"   {rows[0].species_name:<14} transfer {drop:<16} keep {held}")
    return 0


def cmd_roster(gm, args):
    """The strongest six you can field per attacking type, and what each costs.

    A raid party is six, so that's the unit. Each Pokemon is scored at its
    final evolved form, since evolving costs no stardust and is therefore
    the cheapest upgrade available. One Pokemon can hold a slot in two types
    when it carries two same-type movesets.
    """
    holdings = roster.load_list(gm, args.list)
    for h in holdings:
        h.final, h.candy_to_final, h.items_to_final = roster.final_form(gm, h.species)
    target = battle.neutral_target()
    ranks, best_by_type = roster.type_leaderboard(gm, level=args.level)

    per_type = {}
    for h in holdings:
        final = h.final
        attacker = battle.build(gm, final, DEFAULT_IVS, args.level)
        best = {}
        for _, fast, charged_id, charged in battle.movesets(gm, final):
            if fast.type != charged.type:
                continue
            dps = battle.cycle_dps(gm, attacker, target, fast, charged)
            if dps > best.get(charged.type, (0.0, None))[0]:
                best[charged.type] = (dps, charged_id)
        for move_type, (dps, charged_id) in best.items():
            per_type.setdefault(move_type, []).append((dps, h, charged_id))

    gaps = []
    for move_type in sorted(per_type):
        rows = sorted(per_type[move_type], key=lambda r: -r[0])
        # One entry per end species. You field one Granbull, not three, and
        # the spare copies tie on DPS because DPS is scored at a fixed level.
        # Within a species the highest CP wins, so sort on that first.
        rows.sort(key=lambda r: (-r[0], -(r[1].cp or 0)))
        seen, team = set(), []
        for dps, h, charged_id in rows:
            key = h.final.pokemon_id
            if key in seen:
                continue
            seen.add(key)
            team.append((dps, h, charged_id))
            if len(team) == args.size:
                break

        world_best = best_by_type.get(move_type, 0.0)
        lead = team[0][0] if team else 0.0
        share = lead / world_best * 100 if world_best else 0
        print(f"\n{move_type}   best {lead:.1f} DPS, {share:.0f}% of the best "
              f"same-type {move_type} attacker in the game")
        if share < args.gap:
            gaps.append((share, move_type))
        for i, (dps, h, charged_id) in enumerate(team, 1):
            evolving = h.final.template_id != h.species.template_id
            if evolving:
                proj = roster.evolved_cp(h.cp, h.species, h.final)
                cp = f"{proj[0]}-{proj[1]}" if proj else "?"
                items = ", ".join(roster.ITEM_NAMES.get(x, x)
                                  for x in h.items_to_final if x)
                cost = f"{h.candy_to_final} candy" + (f" + {items}" if items else "")
                what = f"{h.species_name} {h.cp} -> {h.final.name} {cp} CP"
            else:
                cost = "ready"
                what = f"{h.final.name} {h.cp} CP"
            flags = f" [{','.join(sorted(h.flags))}]" if h.flags else ""
            print(f"  {i}. {what:<44} {dps:>5.1f}  {cost}{flags}")

    if gaps:
        print(f"\nWeakest coverage, under {args.gap}% of the game's best:")
        for share, move_type in sorted(gaps):
            print(f"  {move_type:<10} {share:.0f}%")
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
                        help="log each parsed box row")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("selftest", help="check constants against known values")
    sub.add_parser("constants", help="print every constant the ranking uses")

    counters = sub.add_parser("counters", help="rank attackers against a boss")
    counters.add_argument("boss")
    counters.add_argument("--tier", type=int, default=5,
                          choices=sorted(battle.RAID_TIERS))
    counters.add_argument("--box", nargs="?", const="data/box_list.csv",
                          help="rank your box. Defaults to data/box_list.csv")
    counters.add_argument("--top", type=int, default=20)
    counters.add_argument("--sort", default="dps", choices=["dps", "tdo", "survival_s"])
    counters.add_argument("--level", type=float, default=DEFAULT_LEVEL,
                          help="level to assume when no box is given")
    counters.add_argument("--level-cap", type=float, default=40.0,
                          help="level to score box entries at")

    evolve = sub.add_parser("evolve", help="what your evolution items can buy")
    evolve.add_argument("--bag", default="data/bag.json")
    evolve.add_argument("--top", type=int, default=8)

    boxcmd = sub.add_parser("box", help="keep or transfer, per Pokemon")
    boxcmd.add_argument("--list", default="data/box_list.csv")
    boxcmd.add_argument("--keep-rank", type=int, default=30,
                        help="how deep in its type a species must place")
    boxcmd.add_argument("--top", type=int, default=40)
    boxcmd.add_argument("--unfavorite", action="store_true",
                        help="treat favorites as transferable")
    boxcmd.add_argument("--buddy", default="PANCHAM")
    boxcmd.add_argument("--collection", action="store_true",
                        help="keep one of every species. Off by default, since\ntransferring never costs the Pokedex entry")

    plan = sub.add_parser("plan", help="the transfer pass as paste-able searches")
    plan.add_argument("--list", default="data/box_list.csv")
    plan.add_argument("--keep-rank", type=int, default=30)
    plan.add_argument("--batch", type=int, default=14,
                      help="names per search string")
    plan.add_argument("--buddy", default="PANCHAM")
    plan.add_argument("--collection", action="store_true",
                      help="keep one of every species, matching box --collection")
    plan.add_argument("--markdown", action="store_true",
                      help="one fenced block per search line")

    rost = sub.add_parser("roster", help="your best six per attacking type")
    rost.add_argument("--list", default="data/box_list.csv")
    rost.add_argument("--size", type=int, default=6)
    rost.add_argument("--level", type=float, default=DEFAULT_LEVEL)
    rost.add_argument("--gap", type=float, default=70.0,
                      help="flag types under this %% of the game best")

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
        "evolve": cmd_evolve,
        "box": cmd_box,
        "plan": cmd_plan,
        "roster": cmd_roster,
        "powerup": cmd_powerup,
    }[args.command](gm, args)
