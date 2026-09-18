"""Load and index the PokeMiners game master.

Every constant this repo uses comes from here. Nothing is typed in by hand
except POKEMON_TYPES, which is the proto enum order and gets checked in
battle.selftest().
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

GAMEMASTER = Path(__file__).resolve().parent.parent / "data" / "gamemaster.json"

# Index order of the attackScalar array in each POKEMON_TYPE_* template.
# This is the HoloPokemonType proto enum order. selftest() checks it against
# known matchups before any ranking runs.
POKEMON_TYPES = [
    "NORMAL", "FIGHTING", "FLYING", "POISON", "GROUND", "ROCK",
    "BUG", "GHOST", "STEEL", "FIRE", "WATER", "GRASS",
    "ELECTRIC", "PSYCHIC", "ICE", "DRAGON", "DARK", "FAIRY",
]

_POKEMON_RE = re.compile(r"^V(\d{4})_POKEMON_(.+)$")
_MOVE_RE = re.compile(r"^V(\d{4})_MOVE_(.+)$")
_COMBAT_MOVE_RE = re.compile(r"^COMBAT_V(\d{4})_MOVE_(.+)$")


def _strip_type(t):
    return t.replace("POKEMON_TYPE_", "") if t else None


@dataclass
class Move:
    """A fast or charged move. PvE and PvP values differ, so both live here."""

    move_id: str
    type: str
    # PvE
    power: float = 0.0
    energy_delta: int = 0
    duration_ms: int = 0
    damage_window_ms: int = 0
    # PvP
    pvp_power: float = 0.0
    pvp_energy_delta: int = 0
    pvp_turns: int = 0

    @property
    def is_fast(self):
        return self.energy_delta >= 0

    @property
    def duration_s(self):
        return self.duration_ms / 1000.0


@dataclass
class Species:
    """One Pokemon form. base_* are GO's own stats, not main-series stats."""

    template_id: str
    pokemon_id: str
    form: str | None
    dex: int
    types: tuple
    base_attack: int
    base_defense: int
    base_stamina: int
    fast_moves: list = field(default_factory=list)
    charged_moves: list = field(default_factory=list)
    elite_fast: list = field(default_factory=list)
    elite_charged: list = field(default_factory=list)
    shadow_available: bool = False

    @property
    def name(self):
        return self.form or self.pokemon_id

    def all_fast(self):
        return list(dict.fromkeys(self.fast_moves + self.elite_fast))

    def all_charged(self):
        return list(dict.fromkeys(self.charged_moves + self.elite_charged))


class GameMaster:
    def __init__(self, path=GAMEMASTER):
        self.path = Path(path)
        raw = json.loads(self.path.read_text())
        self._by_id = {t.get("templateId"): t.get("data", {}) for t in raw}

        self.type_chart = self._load_type_chart()
        self.cpm_table = self._load_cpm()
        self.species = self._load_species()
        self.moves = self._load_moves()

        battle = self._by_id["BATTLE_SETTINGS"]["battleSettings"]
        self.stab = battle["sameTypeAttackBonusMultiplier"]
        self.shadow_attack = battle["shadowPokemonAttackBonusMultiplier"]
        self.shadow_defense = battle["shadowPokemonDefenseBonusMultiplier"]
        # Seconds a raid boss waits between moves. A player waits none.
        self.enemy_attack_interval = battle["enemyAttackInterval"]
        self.energy_per_hp_lost = battle["energyDeltaPerHealthLost"]

        upgrades = self._by_id["POKEMON_UPGRADE_SETTINGS"]["pokemonUpgrades"]
        self.max_pokemon_level = upgrades["maxNormalUpgradeLevel"]
        self.levels_above_player = upgrades["allowedLevelsAbovePlayer"]
        self.upgrades_per_level = upgrades["upgradesPerLevel"]
        self.stardust_cost = upgrades["stardustCost"]
        self.candy_cost = upgrades["candyCost"]
        self.xl_candy_cost = upgrades["xlCandyCost"]
        self.xl_min_player_level = upgrades["xlCandyMinPlayerLevel"]
        self.xl_min_pokemon_level = upgrades["xlCandyMinPokemonLevel"]

        player = self._by_id["PLAYER_LEVEL_SETTINGS"]["playerLevel"]
        self.required_xp = player["requiredExperience"]
        # defaultLevelCap is the level XP alone reaches. Past it, levels also
        # need Level-Up Research, so the real ceiling is the length of the XP
        # table. Reading defaultLevelCap as "the cap" understates it by 10.
        self.xp_only_level_cap = player["defaultLevelCap"]
        self.trainer_level_cap = len(self.required_xp)
        self.milestone_levels = player["milestoneLevels"]

    # -- loaders ----------------------------------------------------------

    def _load_type_chart(self):
        chart = {}
        for attack_type in POKEMON_TYPES:
            data = self._by_id.get(f"POKEMON_TYPE_{attack_type}")
            scalars = data["typeEffective"]["attackScalar"]
            chart[attack_type] = dict(zip(POKEMON_TYPES, scalars))
        return chart

    def _load_cpm(self):
        return self._by_id["PLAYER_LEVEL_SETTINGS"]["playerLevel"]["cpMultiplier"]

    def _load_species(self):
        out = {}
        for template_id, data in self._by_id.items():
            match = _POKEMON_RE.match(template_id or "")
            if not match or "pokemonSettings" not in data:
                continue
            settings = data["pokemonSettings"]
            stats = settings.get("stats", {})
            if not stats.get("baseAttack"):
                continue
            types = tuple(
                t for t in (_strip_type(settings.get("type")),
                            _strip_type(settings.get("type2"))) if t
            )
            out[template_id] = Species(
                template_id=template_id,
                pokemon_id=settings["pokemonId"],
                form=settings.get("form"),
                dex=int(match.group(1)),
                types=types,
                base_attack=stats["baseAttack"],
                base_defense=stats["baseDefense"],
                base_stamina=stats["baseStamina"],
                fast_moves=settings.get("quickMoves", []),
                charged_moves=settings.get("cinematicMoves", []),
                elite_fast=settings.get("eliteQuickMove", []),
                elite_charged=settings.get("eliteCinematicMove", []),
                shadow_available="shadow" in settings,
            )
        return out

    def _load_moves(self):
        moves = {}
        for template_id, data in self._by_id.items():
            if not _MOVE_RE.match(template_id or "") or "moveSettings" not in data:
                continue
            m = data["moveSettings"]
            moves[m["movementId"]] = Move(
                move_id=m["movementId"],
                type=_strip_type(m["pokemonType"]),
                power=m.get("power", 0.0),
                energy_delta=m.get("energyDelta", 0),
                duration_ms=m.get("durationMs", 0),
                damage_window_ms=m.get("damageWindowStartMs", 0),
            )
        for template_id, data in self._by_id.items():
            if not _COMBAT_MOVE_RE.match(template_id or "") or "combatMove" not in data:
                continue
            c = data["combatMove"]
            move = moves.get(c["uniqueId"])
            if move is None:
                continue
            move.pvp_power = c.get("power", 0.0)
            move.pvp_energy_delta = c.get("energyDelta", 0)
            move.pvp_turns = c.get("durationTurns", 0)
        return moves

    # -- lookups ----------------------------------------------------------

    def effectiveness(self, attack_type, defender_types):
        """Product of per-type scalars. 1.6 / 1.0 / 0.625 / 0.390625 in GO."""
        row = self.type_chart[attack_type]
        result = 1.0
        for t in defender_types:
            result *= row[t]
        return result

    def unique_species(self):
        """Every distinct form, with the game master's duplicates collapsed.

        Most species ship twice, as BULBASAUR and BULBASAUR_NORMAL, with
        identical stats and movepools. Keep the shorter template id.
        """
        groups = {}
        for species in self.species.values():
            key = (species.pokemon_id, species.types,
                   species.base_attack, species.base_defense, species.base_stamina,
                   tuple(sorted(map(str, species.all_fast()))),
                   tuple(sorted(map(str, species.all_charged()))))
            current = groups.get(key)
            if current is None or len(species.template_id) < len(current.template_id):
                groups[key] = species
        return list(groups.values())

    def find(self, name):
        """Resolve a loose name to Species records. Prefers the base form."""
        key = name.upper().replace(" ", "_").replace("-", "_")
        exact = [s for s in self.species.values() if s.pokemon_id == key]
        if exact:
            base = [s for s in exact if s.template_id.endswith(key)]
            return base or exact
        return [s for s in self.species.values() if key in s.template_id]
