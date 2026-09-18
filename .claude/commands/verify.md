---
description: Audit this repo's facts and constants with read-only agents, then fix what they find
---

Audit this repo for factual errors, then fix everything the audit finds.

Dispatch the agents below in parallel. Every one is **read-only** and reports
findings only. When they all return, you apply the fixes yourself and re-run
`python rank.py selftest`. Reporting without fixing isn't finishing.

## Output contract, every agent

A numbered list, most severe first. Each finding gives:

1. File and line number
2. The text as it currently reads, quoted
3. What's correct
4. The source URL checked against

End with one short paragraph naming what was checked and found correct. Don't
report a claim that checks out. Don't edit any file.

## Failure modes to hunt

Name these in every agent prompt. They produce nearly every error here.

1. **Main-series contamination.** Pokemon GO is its own game. Super effective
   is 1.6x, not 2x. There's no physical or special split. Base stats are GO's
   own, derived rather than copied. A move carries separate PvE and PvP power
   and energy. Bulbapedia's main-series pages will mislead you, so read the
   GO-specific page or the game master.
2. **Stale meta.** Niantic rebalances moves, stats and raid bosses most
   seasons. An article from 2024 can be flatly wrong today. Numbers come from
   the current game master, not a blog post. Read the current season off the
   top of `README.md` and pass it to each agent. GamePress shut its Pokemon GO
   wiki down, so every `gamepress.gg/pokemongo` link 404s.
3. **CSV misreads.** Calcy IV writes IV ranges where no appraisal was scanned,
   plus form, costume, shadow, lucky and gender columns that are easy to map
   to the wrong field. A parse that looks tidy can still be wrong.

## Agents

**A. Constants against the game master.** Scope: the Constants table and the
Formulas block in `reference.md`, plus `pogo/battle.py` and
`pogo/gamemaster.py`. Run `python rank.py constants` and check every printed
value against `data/gamemaster.json` directly. Confirm the type chart index
order in `POKEMON_TYPES` by spot-checking matchups no selftest covers.
Confirm the power-up cost arrays are indexed by whole level and charged twice
per level, and that the published anchors in `selftest` are the real published
figures rather than numbers reverse-engineered from this code.

**B. Off-game-master claims.** Scope: the Raid bosses table, the Items table,
and the "Rules that break main-series advice" list in `reference.md`. None of
these come from the game master, so each needs a live source. Check the tier
CPM and HP values, every item effect, and the gifts-and-stickers claim. Where
a source describes an older version of the game, say so.

**C. Trainer and bag arithmetic.** Scope: `README.md`. Recompute every sum.
Confirm 3,503,000 + 256,583 equals the stated total XP, that the XP-to-40
figure follows, and that the counted bag items, the gift exclusion and the
unaccounted remainder all reconcile against 571 / 550. Check the level 40
reward list and the power-up ceiling claim against a live source.

**D. Ranking math.** Scope: `pogo/battle.py` only. Check the damage formula,
the cycle DPS derivation, the TDO model and the boss construction against
published GO damage mechanics. Flag anywhere the code silently returns 0.0 or
None and the caller treats that as a real result. Say whether the DPS a
`counters` run reports for a well-known attacker matches published figures.

**E. Writing.** Scope: `README.md` and `reference.md`. Judge against the
owner's rules: always contract; ASD-STE100 one idea per sentence, active,
present tense; no negative setup then consequence; never the word "guard" or
"exactly"; no tilde meaning approximately; American spelling; no noun piles;
no AI slop; at most 1-2 em dashes per document; half the words. Report file,
line, the current text, and a concrete rewrite.

## Already fixed, don't re-report unless it regressed

- Power-up ceiling stated as trainer level + 2. It's + 10, since GO Beyond.
- The level 40 scroll reward called a Charged TM. It's an Elite Fast TM.
- Gifts counted against the item bag. They have their own storage.
- Duplicate `_NORMAL` forms listed twice in `counters` output.
- Power-up costs indexed per half-step instead of per whole level.
- Candy for level 1 to 40 given as 248. The current game master says 304.
- Level 40 payout given as 136 items. It's 137.
- Level 30 to 50 given as 250,000 dust. It's 400,000.
- Trainer level cap cited to `defaultLevelCap`, which reads 70. The cap is 80.
- `hit_points` missing the floor of 10, which zeroed Shedinja.
- `cycle_dps` rounding the fast-move count up. Energy carries over in raids.
- The boss taking no `enemyAttackInterval`, which cut TDO by 2 to 3 times.
- The boss solving for its best moveset per attacker instead of averaging.
- `_fmt_move` crashing on the nine integer move ids in the game master.
- `cpm` and `powerup_cost` accepting levels off the 0.5 grid.
- A boss with no moveset reported as "nothing could attack this boss".
- Citing `gamepress.gg/pokemongo` and the 2019 GO Hub damage-mechanics page,
  which still prints the superseded 1.4x multipliers.

## Known and accepted, don't report as bugs

- No energy from damage taken. Costs 1 to 6% of DPS, declared in
  `reference.md` and in the `battle.py` docstring.
- No weather, friendship, Party Power, Mega bonus or dodging.
- `counters` without `--box` lists forms you can't obtain, such as
  Eternamax Eternatus and Zen Darmanitan. `--box` avoids it.
