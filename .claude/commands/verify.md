---
description: Audit this repo's facts and constants with read-only agents, then fix what they find
---

Audit this repo for factual errors, then fix everything the audit finds.

Dispatch the agents below in parallel. Every one is **read-only** and reports
findings only. When they all return, you apply the fixes yourself. Reporting
without fixing isn't finishing.

There's no code here on purpose. Verify numbers by querying
`data/gamemaster.json` directly in a throwaway script, never by building a
tool. The engine that used to live here took seven correction commits in
twenty-six, which is why it's gone.

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
3. **Transcription drift.** `data/box_list.csv` comes from screenshots. A
   card stacks CP, sprite, name, HP bar, so a CP belongs to the row below it.
   The list view shows no IVs, candy, legacy moves, costumes or size, and
   `box_list.csv` has no form column, so regional variants collapse together.

## Agents

**A. Constants against the game master.** Scope: the Constants table, the
Formulas block and the Power-up costs table in `reference.md`. Check every
value against `data/gamemaster.json` directly. The power-up arrays index by
whole level and charge twice per level, so confirm the four totals. Confirm
the type multipliers against `POKEMON_TYPE_*.attackScalar`.

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

**D. Ranking math.** Scope: the DPS, CP and coverage figures quoted in
`README.md`. Recompute each from `data/gamemaster.json` and say which ones
move. The formulas are in `reference.md`. Compare the resulting DPS for a
well-known attacker against published lists and report the gap.

**E. Writing.** Scope: `README.md` and `reference.md`. Judge against the
owner's rules: always contract; ASD-STE100 one idea per sentence, active,
present tense; no negative setup then consequence; never the word "guard" or
"exactly"; no tilde meaning approximately; American spelling; no noun piles;
no AI slop; at most 1-2 em dashes per document; half the words. Report file,
line, the current text, and a concrete rewrite.

## Already fixed, don't re-report unless it regressed

These are fact errors in the docs. Code-bug entries were dropped with the
code.

- Power-up ceiling stated as trainer level + 2. It's + 10, since GO Beyond.
- The level 40 scroll reward called a Charged TM. It's an Elite Fast TM.
- Gifts counted against the item bag. They have their own storage.
- Candy for level 1 to 40 given as 248. The current game master says 304.
- Level 40 payout given as 136 items. It's 137.
- Level 30 to 50 given as 250,000 dust. It's 400,000.
- Trainer level cap cited to `defaultLevelCap`, which reads 70. The cap is 80.
- Ghost and Poison coverage given as 97%. They're 87% and 91%.
- Citing `gamepress.gg/pokemongo` and the 2019 GO Hub damage-mechanics page,
  which still prints the superseded 1.4x multipliers.
- Advice to evolve a Charmander into a Charizard already in the box, and to
  transfer the Salamence already fighting. Check every evolve row against
  what the box already holds.

## Known and accepted, don't report as bugs

- The DPS model gives neither side energy from damage taken, which costs 1 to
  6%, and applies no weather, friendship, Party Power, Mega bonus or dodging.
  `reference.md` declares both.
- Coverage scores each type against the best **same-type** attacker. That
  excludes the true strongest in 7 of 18 types, and `README.md` says so.
- `data/bag.json` marks two lines `derived` rather than observed.

## Sequence check

Read the "Do this next" steps as one argument before finishing. An early step
must not destroy an input a later step needs, and a step must not be listed
as actionable when the state says it's blocked. Both have happened here: a
transfer list and an evolve list naming the same Charmander, and an evolve
step ranked first while nothing in it was affordable.
