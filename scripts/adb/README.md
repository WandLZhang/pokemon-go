# Phone capture over adb

Runbook for a coding agent on a Mac with the phone plugged in. The agent
here does two things a script can't: it reads pixel coordinates off a
screenshot, and it transcribes game screens into CSV.

The ranking engine runs elsewhere. This directory only gets data off the
phone.

## Setup, once

```sh
brew install --cask android-platform-tools
```

On the phone: Settings > About > tap Build number seven times, then
Developer options > USB debugging. Plug in over USB and accept the prompt.

```sh
scripts/adb/doctor.sh
```

Fix whatever it reports before going further. It checks the device, the
screen size, whether the screen is awake, both apps, and Extra Dim. Extra
Dim distorts color and it's the most common reason a Calcy scan fails.

Everything lands in `capture/`, which git ignores.

## What each screen gives you

The Pokemon list shows species, CP, and the shiny, lucky, shadow, favorite
and traded icons. It doesn't show IVs, level, or moves.

That's enough for most of the work. For raids, a perfect IV spread is worth
2.8 to 4.6% DPS over 0/0/0, while level 30 to 40 is worth 4.1 to 9.7%.
Species and level decide a raid attacker. IVs are a tiebreak.

PvP inverts this. Under a CP cap a low-attack spread often beats a hundo, so
PvP needs real IVs and CP tells you nothing.

So: screenshot the whole box first and cut it on species, then Calcy-scan
only what survives.

## Pass 1, the whole box

In Pokemon GO: Pokeball > Pokemon > sort by **Number**, scroll to the top.

Sort by Number, not CP. Number groups every copy of a species together, so
duplicates sit next to each other and the transfer list writes itself.

```sh
scripts/adb/capture_box.sh
```

It stops on its own when the list stops moving. About 27 frames for 325
Pokemon.

Then transcribe the frames to `data/box_list.csv` with these columns:

```
species,cp,shiny,lucky,shadow,purified,favorite
```

One row per Pokemon. Frames overlap on purpose, so deduplicate across the
seam. Species plus CP plus position in Number order is enough to tell two
copies apart. Where a frame is ambiguous, leave the row out and note it
rather than guessing.

## Pass 2, the item bag

Pokeball > Items, list view not grid, scroll to the top.

```sh
scripts/adb/capture_bag.sh
```

Transcribe into `data/bag.json`, matching the shape already there. Set
`complete` to `true` and drop `missing_from_screenshots` once the whole
scroll is captured.

## Pass 3, IVs for the keepers only

Only after the box list is ranked and a keep list exists.

Calcy reads one Pokemon at a time. Its floating button sits wherever it was
dragged, so there are no default coordinates.

```sh
# Open one Pokemon so the Calcy button is on screen.
scripts/adb/shot.sh calibrate
# Read the button position off capture/calibrate.png, then:
scripts/adb/calcy_scan.sh --button 980,1750 --count 60
```

Leave the phone alone while it runs. A stray touch desyncs the loop.

Appraise each Pokemon before scanning, or Calcy writes an IV range instead
of a number and the loader rejects the row.

Then export from Calcy's **History** screen, three-dot menu, and pull it:

```sh
scripts/adb/pull_calcy_csv.sh
# or, if you already know the path
scripts/adb/pull_calcy_csv.sh /sdcard/Download/calcy_export.csv
```

## Handing data back

Commit `data/box_list.csv`, `data/bag.json` and `capture/box.csv` and push.

Don't commit anything under `capture/`. The screenshots carry a trainer name
and a friend code, and `.gitignore` already excludes them.

## Scripts

| Script | Does |
|---|---|
| `doctor.sh` | Preflight. Run first |
| `shot.sh NAME` | One screenshot, for calibration |
| `scroll_capture.sh` | Screenshot a scrolling list. The other two wrap it |
| `capture_box.sh` | The Pokemon list |
| `capture_bag.sh` | The item bag |
| `calcy_scan.sh` | Tap Calcy across the box |
| `pull_calcy_csv.sh` | Find and pull the CSV export |

Set `ANDROID_SERIAL` when more than one device is attached. Set `OUT_ROOT`
to move the capture directory.
