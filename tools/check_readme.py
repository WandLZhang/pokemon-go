"""Read-only consistency check: every README claim against data/."""
import csv, json, re, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent
readme = (root / "README.md").read_text()
rows = list(csv.DictReader((root / "data/box_list.csv").open()))
bag = json.loads((root / "data/bag.json").read_text())
tr = json.loads((root / "data/trainer.json").read_text())

fails = []
checked = {"pokemon": 0, "paths": 0}

# A Pokemon row names a species and a CP. Coverage rows end in %, skip those.
for line in readme.splitlines():
    m = re.match(r"^\| ([A-Z][a-z]+) (\d{2,4}) \|", line)
    if not m or "%" in line.split("|")[1]:
        continue
    sp, cp = m.groups()
    checked["pokemon"] += 1
    if not any(r["species"] == sp and r["cp"] == cp for r in rows):
        fails.append(f"README names {sp} {cp}, not in box_list.csv")

# A Layout path has an extension or a trailing slash. Command names don't.
for path in re.findall(r"^\| `([\w./-]+(?:\.\w+|/))` \|", readme, re.M):
    checked["paths"] += 1
    if not (root / path).exists():
        fails.append(f"Layout names {path}, which doesn't exist")

bag_total = sum(v["count"] for v in bag["items"].values())
for want in (f"{len(rows)} of {tr['pokemon_storage']}",
             f"{bag_total} of {bag['capacity']}",
             f"{tr['stardust']:,}"):
    if want not in readme:
        fails.append(f"state block missing {want!r}")

passes = bag["items"]["Premium Battle Pass"]["count"]
if f"{passes} Premium Battle Passes" not in readme:
    fails.append(f"pass count {passes} not in README")

# Sinnoh Stone count claimed must match the bag.
stones = bag["items"]["Sinnoh Stone"]["count"]
if f"you hold {stones}" not in readme:
    fails.append(f"Sinnoh Stone count {stones} not stated")

print(f"  checked {checked['pokemon']} Pokemon rows, {checked['paths']} paths")
print("\n".join("  " + f for f in fails) if fails
      else "  every README entity resolves against data/ and the tree")
sys.exit(1 if fails else 0)
