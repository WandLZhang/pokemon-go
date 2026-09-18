"""Read a Calcy IV CSV export into rows this repo can rank.

Calcy lets you customize which columns it writes, so nothing here assumes a
fixed header. Each required field is matched against a list of candidate
names. When a match fails the loader prints every header it saw and stops,
rather than ranking a box it misread.
"""

import csv
import logging
import re
from dataclasses import dataclass

log = logging.getLogger(__name__)

# First candidate that matches a header wins. Matching is case-insensitive
# and ignores spaces, underscores and punctuation.
COLUMNS = {
    "species": ["pokemon", "species", "name", "pokemonname"],
    "nickname": ["nickname", "customname", "displayname"],
    "cp": ["cp", "combatpower"],
    "hp": ["hp", "hitpoints"],
    "level": ["level", "lvl", "pokemonlevel"],
    "iv_attack": ["atkiv", "attackiv", "ivattack", "ivatk", "attack"],
    "iv_defense": ["defiv", "defenseiv", "ivdefense", "ivdef", "defense"],
    "iv_stamina": ["staiv", "stamiv", "staminaiv", "ivstamina", "ivsta",
                   "hpiv", "stamina"],
    "fast_move": ["fastmove", "quickmove", "move1", "fastattack"],
    "charged_move": ["chargemove", "chargedmove", "move2", "chargeattack"],
    "form": ["form", "variant", "costume"],
    "shadow": ["shadow", "shadowpurified", "shadowstatus"],
    "lucky": ["lucky"],
    "shiny": ["shiny"],
    "favorite": ["favorite", "favourite"],
}
REQUIRED = ["species", "cp", "iv_attack", "iv_defense", "iv_stamina"]


class BoxParseError(Exception):
    pass


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _map_headers(headers):
    normalized = {_norm(h): h for h in headers}
    mapping = {}
    for field, candidates in COLUMNS.items():
        for candidate in candidates:
            if candidate in normalized:
                mapping[field] = normalized[candidate]
                break
    missing = [f for f in REQUIRED if f not in mapping]
    if missing:
        raise BoxParseError(
            f"Calcy CSV is missing required columns {missing}.\n"
            f"Headers seen: {sorted(headers)}\n"
            f"Mapped so far: {mapping}\n"
            f"Add the missing columns in Calcy IV under "
            f"Settings > Detailed Output Customization, or extend "
            f"COLUMNS in pogo/box.py."
        )
    return mapping


def _number(value):
    """Calcy writes '13' or a range like '12-14' when appraisal is missing."""
    if value is None:
        return None, False
    text = str(value).strip()
    if not text:
        return None, False
    if re.fullmatch(r"\d+(\.\d+)?", text):
        return float(text), True
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)", text)
    if match:
        low, high = float(match.group(1)), float(match.group(2))
        return (low + high) / 2.0, False
    return None, False


def _truthy(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "x"}


@dataclass
class BoxEntry:
    species: str
    nickname: str | None
    cp: int | None
    hp: int | None
    level: float | None
    ivs: tuple
    iv_exact: bool
    fast_move: str | None
    charged_move: str | None
    form: str | None
    shadow: bool
    lucky: bool
    shiny: bool
    favorite: bool
    raw: dict


def load(path):
    """Parse the CSV. Returns (entries, fuzzy) where fuzzy lacks exact IVs."""
    with open(path, newline="", encoding="utf-8-sig") as handle:
        sample = handle.read(8192)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        headers = reader.fieldnames or []
        mapping = _map_headers(headers)
        log.info("calcy csv headers=%s mapping=%s", headers, mapping)

        entries, fuzzy = [], []
        for line_no, row in enumerate(reader, start=2):
            if not any((v or "").strip() for v in row.values()):
                continue
            ivs, exact = [], True
            for field in ("iv_attack", "iv_defense", "iv_stamina"):
                value, is_exact = _number(row.get(mapping[field]))
                ivs.append(0 if value is None else int(round(value)))
                exact = exact and is_exact
            cp, _ = _number(row.get(mapping.get("cp")))
            hp, _ = _number(row.get(mapping.get("hp")))
            level, _ = _number(row.get(mapping.get("level")))
            entry = BoxEntry(
                species=(row.get(mapping["species"]) or "").strip(),
                nickname=(row.get(mapping.get("nickname")) or "").strip() or None,
                cp=int(cp) if cp is not None else None,
                hp=int(hp) if hp is not None else None,
                level=level,
                ivs=tuple(ivs),
                iv_exact=exact,
                fast_move=(row.get(mapping.get("fast_move")) or "").strip() or None,
                charged_move=(row.get(mapping.get("charged_move")) or "").strip() or None,
                form=(row.get(mapping.get("form")) or "").strip() or None,
                shadow=_truthy(row.get(mapping.get("shadow"))),
                lucky=_truthy(row.get(mapping.get("lucky"))),
                shiny=_truthy(row.get(mapping.get("shiny"))),
                favorite=_truthy(row.get(mapping.get("favorite"))),
                raw=dict(row),
            )
            log.debug("row %d parsed: %s", line_no, entry)
            entries.append(entry)
            if not exact:
                fuzzy.append(entry)

    log.info("parsed %d entries, %d without exact IVs", len(entries), len(fuzzy))
    return entries, fuzzy


def resolve(gm, entry):
    """Match a CSV row to a game master Species. Returns None when unsure."""
    candidates = gm.find(entry.species)
    if not candidates:
        return None
    if entry.form:
        form_key = re.sub(r"[^A-Z0-9]", "", entry.form.upper())
        for species in candidates:
            if form_key and form_key in re.sub(r"[^A-Z0-9]", "", species.template_id):
                return species
    base = [s for s in candidates
            if s.template_id.endswith(s.pokemon_id)
            or s.template_id.endswith(s.pokemon_id + "_NORMAL")]
    return (base or candidates)[0]
