"""Turn a box list into a keep or transfer call, one Pokemon at a time.

The box list carries species and CP but no IVs, which is enough. For raids a
perfect IV spread is worth 3 to 5% DPS while a level band is worth more, so
species and what it evolves into decide almost everything. IVs settle ties
later, once the keepers are scanned.
"""

import csv
import math
from dataclasses import dataclass, field

from . import battle

FLAGS = ("shiny", "lucky", "shadow", "purified", "favorite")

# The game refuses to transfer a favorite, so these need unfavoriting first.
LOCKED_FLAGS = ("favorite",)

# Never put these in the transfer pile on raid value alone. A shadow gets a
# 1.2x attack multiplier, so it beats its own normal form outright. A shiny
# and a lucky can't be replaced by catching another one.
PRECIOUS_FLAGS = ("shiny", "lucky", "shadow", "purified")

# Transferring never touches the Pokedex. A species stays registered once
# caught, so keeping one of each is a collection choice, not a requirement.
DEX_IS_PERMANENT = True

# Minimum CP in Pokemon GO. Anything below it is a transcription error.
MIN_CP = 10

# Game master item ids read back as the names on the bag screen.
ITEM_NAMES = {
    "ITEM_GEN4_EVOLUTION_STONE": "Sinnoh Stone",
    "ITEM_GEN5_EVOLUTION_STONE": "Unova Stone",
    "ITEM_SUN_STONE": "Sun Stone",
    "ITEM_KINGS_ROCK": "King's Rock",
    "ITEM_METAL_COAT": "Metal Coat",
    "ITEM_DRAGON_SCALE": "Dragon Scale",
    "ITEM_UP_GRADE": "Upgrade",
}


@dataclass
class Holding:
    species_name: str
    cp: int | None
    flags: set
    species: object
    final: object = None
    candy_to_final: int = 0
    items_to_final: tuple = ()
    dps: float = 0.0
    move_type: str = None
    type_rank: int = 0
    verdict: str = ""
    reason: str = ""
    copy_index: int = 0

    @property
    def precious(self):
        """Irreplaceable, or strictly better than its normal form."""
        return bool(self.flags & set(PRECIOUS_FLAGS))

    @property
    def locked(self):
        """The game won't transfer it until the flag comes off."""
        return bool(self.flags & set(LOCKED_FLAGS))

    @property
    def cp_is_impossible(self):
        return self.cp is not None and self.cp < MIN_CP


def load_list(gm, path):
    """Read the transcribed box list. Unresolvable species stop the run."""
    out, unresolved = [], []
    with open(path, newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("species") or "").strip()
            if not name:
                continue
            matches = gm.find(name)
            if not matches:
                unresolved.append(name)
                continue
            flags = {f for f in FLAGS if (row.get(f) or "0").strip() not in ("", "0")}
            raw_cp = (row.get("cp") or "").strip()
            out.append(Holding(
                species_name=name,
                cp=int(raw_cp) if raw_cp else None,
                flags=flags,
                species=matches[0],
            ))
    if unresolved:
        raise ValueError(
            f"{len(unresolved)} species didn't resolve: {sorted(set(unresolved))}. "
            f"Fix the transcription rather than rank a box with holes in it.")
    return out


def final_form(gm, species, seen=None):
    """Walk to the strongest end of the evolution chain.

    Branching lines exist, so take the branch whose end form hits hardest
    rather than the first one listed.
    """
    seen = seen or set()
    if species.template_id in seen or not species.evolutions:
        return species, 0, ()
    seen = seen | {species.template_id}

    target = battle.neutral_target()
    best = (None, 0, (), -1.0)
    for evolves_into, item_id, candy in species.evolutions:
        matches = gm.find(evolves_into)
        if not matches:
            continue
        deeper, deeper_candy, deeper_items = final_form(gm, matches[0], seen)
        attacker = battle.build(gm, deeper, (15, 15, 15), 40)
        dps = battle.best_moveset(gm, attacker, target)[0]
        items = ((item_id,) if item_id else ()) + deeper_items
        if dps > best[3]:
            best = (deeper, (candy or 0) + deeper_candy, items, dps)

    if best[0] is None:
        return species, 0, ()
    return best[0], best[1], best[2]


def evolved_cp(current_cp, from_species, to_species):
    """Project CP after evolving. Returns (low, high) across the IV range.

    Evolving keeps the level and the IVs, so the CP ratio is just the ratio
    of the two stat products. IVs don't cancel out of that ratio, but they
    move it by about a percent against base stats in the hundreds, so the
    spread from IV 0 to IV 15 is the honest error bar.
    """
    if current_cp is None:
        return None

    def product(species, iv):
        return ((species.base_attack + iv)
                * math.sqrt(species.base_defense + iv)
                * math.sqrt(species.base_stamina + iv))

    ratios = [product(to_species, iv) / product(from_species, iv) for iv in (0, 15)]
    return (int(current_cp * min(ratios)), int(current_cp * max(ratios)))


def type_leaderboard(gm, level=40.0, same_type_only=True):
    """Best DPS per species per attacking type, and each species' rank.

    A T-type attacker needs both moves to be type T. Counting a pair by its
    charged move alone credits the fast move's damage to a matchup it may
    not even be neutral in. Mienshao carries Grass Knot but punches with
    Fighting, so scoring it as a Grass attacker overstates it against
    anything that resists Fighting.
    """
    target = battle.neutral_target()
    per_type = {}
    for species in gm.unique_species():
        attacker = battle.build(gm, species, (15, 15, 15), level)
        for _, fast, _, charged in battle.movesets(gm, species):
            if same_type_only and fast.type != charged.type:
                continue
            dps = battle.cycle_dps(gm, attacker, target, fast, charged)
            slot = per_type.setdefault(charged.type, {})
            if dps > slot.get(species.template_id, 0.0):
                slot[species.template_id] = dps

    ranks = {}
    for move_type, scores in per_type.items():
        for i, (template_id, dps) in enumerate(
                sorted(scores.items(), key=lambda kv: -kv[1]), 1):
            current = ranks.get(template_id)
            if current is None or i < current[0]:
                ranks[template_id] = (i, move_type, dps)
    return ranks


def evaluate(gm, holdings, keep_rank=30, keep_one_of_each=False,
             respect_favorites=True, buddy=None):
    """Score every holding, then call it.

    keep_rank is how deep a species has to place in its best type to earn a
    slot. Rank 30 out of roughly 1,200 species is generous on purpose.

    keep_one_of_each is off by default. Transferring doesn't cost the
    Pokedex entry, so a living collection is a preference to opt into.
    """
    ranks = type_leaderboard(gm)

    for h in holdings:
        h.final, h.candy_to_final, h.items_to_final = final_form(gm, h.species)
        entry = ranks.get(h.final.template_id)
        if entry:
            h.type_rank, h.move_type, h.dps = entry

    collection = set()
    if keep_one_of_each:
        best_of_species = {}
        for h in holdings:
            current = best_of_species.get(h.species.pokemon_id)
            if current is None or (h.cp or 0) > (current.cp or 0):
                best_of_species[h.species.pokemon_id] = h
        collection = {id(h) for h in best_of_species.values()}

    # Rank every copy of a species so only the best one earns the slot. A
    # second Nihilego adds nothing to a raid party you bring one of.
    by_species = {}
    for h in sorted(holdings, key=lambda x: -(x.cp or 0)):
        by_species.setdefault(h.species.pokemon_id, []).append(h)

    for h in holdings:
        copies = by_species[h.species.pokemon_id]
        h.copy_index = copies.index(h)
        ranked = bool(h.type_rank) and h.type_rank <= keep_rank
        evolving = h.final.template_id != h.species.template_id

        if buddy and h.species.pokemon_id == buddy.upper() and h.copy_index == 0:
            # The game refuses to transfer your active buddy.
            h.verdict = "BUDDY"
            h.reason = "your buddy, the game won't transfer it"
        elif h.cp_is_impossible:
            h.verdict = "RECHECK"
            h.reason = f"CP {h.cp} is below the game minimum of {MIN_CP}"
        elif ranked and h.copy_index == 0 and evolving:
            h.verdict = "EVOLVE"
            items = ", ".join(ITEM_NAMES.get(i, i) for i in h.items_to_final if i)
            cost = f"{h.candy_to_final} candy"
            if items:
                cost += f" + {items}"
            proj = evolved_cp(h.cp, h.species, h.final)
            arrow = f" -> {proj[0]}-{proj[1]} CP" if proj else ""
            h.reason = f"{h.final.name} #{h.type_rank} {h.move_type}{arrow}, {cost}"
        elif ranked and h.copy_index == 0:
            h.verdict = "KEEP"
            h.reason = f"#{h.type_rank} {h.move_type}, {h.dps:.1f} DPS"
        elif h.locked and respect_favorites:
            h.verdict = "LOCKED"
            h.reason = "favorite, unfavorite it first"
        elif h.precious:
            h.verdict = "HOLD"
            h.reason = ", ".join(sorted(h.flags))
        elif id(h) in collection:
            h.verdict = "COLLECTION"
            h.reason = "only copy"
        else:
            spare = " spare copy" if h.copy_index else ""
            if h.locked:
                spare += ", unfavorite first"
            h.verdict = "TRANSFER"
            h.reason = (f"no raid value{spare}" if not ranked
                        else f"{h.copy_index + 1}th best copy")

    return holdings
