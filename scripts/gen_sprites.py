#!/usr/bin/env python3
"""Generate one top-down sprite per species with gpt-image-1.

Usage:
  OPENAI_API_KEY=... python3 scripts/gen_sprites.py --ids 6054,1021   # specific
  OPENAI_API_KEY=... python3 scripts/gen_sprites.py --all --quality low

Resumable: skips ids that already have assets/sprites/{id}.png.
Output: 1024 PNG from the API, downscaled to 256px via sips.
"""
import argparse, base64, json, os, pathlib, subprocess, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "sprites"
OUT.mkdir(parents=True, exist_ok=True)
KEY = os.environ.get("OPENAI_API_KEY")
if not KEY:
    sys.exit("set OPENAI_API_KEY")

PALM_FAM = {"Palmae", "Arecaceae"}
CONIFER_FAM = {"Pinaceae", "Cupressaceae", "Taxaceae", "Podocarpaceae", "Araucariaceae"}

def prompt_for(sp):
    fam = sp["family"]
    porte = sp["porte"]
    hints = []
    if fam in PALM_FAM:
        hints.append("a palm: a radial star of long feathery fronds from a single point")
    elif fam in CONIFER_FAM:
        hints.append("a conifer: dense dark blue-green crown with visible radial branch whorls")
    elif porte == "tree":
        hints.append("a broadleaf tree crown of clumped foliage lobes"
                     + (", winter-deciduous open crown texture" if sp.get("decid") else ", dense evergreen texture"))
    elif porte == "shrub":
        hints.append("a shrub: low mounded clump of foliage, 1-3 m wide, slightly irregular")
    elif porte == "grass":
        hints.append("a grass tuft or clump seen from above, blades radiating outward")
    elif porte == "vine":
        hints.append("a sprawling vine mat of foliage with irregular runners")
    else:
        hints.append("a leafy herbaceous plant rosette seen from above")
    return (
        f"A single {sp['sci']} ({sp['common']}) plant photographed directly from above, "
        f"aerial nadir view as in satellite imagery: {hints[0]}. "
        "Botanically faithful foliage color and crown structure for this exact species. "
        "One plant only, centered, on a fully transparent background, soft neutral daylight "
        "from the northeast, muted natural colors (no neon green), photorealistic aerial "
        "texture, no ground, no shadow outside the crown, no text."
    )

def gen(sp, quality):
    body = json.dumps({
        "model": "gpt-image-1",
        "prompt": prompt_for(sp),
        "size": "1024x1024",
        "quality": quality,
        "background": "transparent",
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations", data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        j = json.load(r)
    raw = OUT / f"{sp['id']}.raw.png"
    final = OUT / f"{sp['id']}.png"
    raw.write_bytes(base64.b64decode(j["data"][0]["b64_json"]))
    subprocess.run(["sips", "-Z", "256", str(raw), "--out", str(final)],
                   check=True, capture_output=True)
    raw.unlink()
    return final.stat().st_size

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--quality", default="low", choices=["low", "medium", "high"])
    a = ap.parse_args()
    species = json.load(open(ROOT / "data" / "species.json"))
    if a.ids:
        want = {int(x) for x in a.ids.split(",")}
        todo = [s for s in species if s["id"] in want]
    elif a.all:
        todo = species
    else:
        sys.exit("--ids or --all")
    todo = [s for s in todo if not (OUT / f"{s['id']}.png").exists()]
    print(f"{len(todo)} to generate at quality={a.quality}")
    ok = fail = 0
    for i, sp in enumerate(todo):
        try:
            size = gen(sp, a.quality)
            ok += 1
            print(f"[{i+1}/{len(todo)}] {sp['id']} {sp['sci']} ok ({size//1024} KB)")
        except Exception as e:
            fail += 1
            print(f"[{i+1}/{len(todo)}] {sp['id']} {sp['sci']} FAIL {e}")
            time.sleep(5)
        time.sleep(1.2)  # stay friendly with image rate limits
    print(f"done: {ok} ok, {fail} failed")

if __name__ == "__main__":
    main()
