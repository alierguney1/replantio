#!/usr/bin/env python3
"""Check the fitted envelopes against two independent references.

1. Carvalho (Embrapa Florestas). For the ten target species, the ranges of
   annual rainfall, annual mean temperature, coldest-month mean and absolute
   minimum that Carvalho reports across each species' Brazilian occurrence
   area. Harvested by scripts/fetch_carvalho.py and transcribed below with the
   source document, so the comparison is auditable. Carvalho's numbers are
   station extremes over Brazil, so the honest expectation is that his range is
   wider than a p2-p98 quantile band but geographically narrower, since the
   fits also see Paraguay, Bolivia, Argentina and Mexico.

2. FAO EcoCrop itself. Ten Brazilian native trees that DO have a curated
   EcoCrop envelope were fitted blind by the same pipeline. That is the only
   apples-to-apples test available: same shape, same consumer (scoring.js),
   one side expert-curated and one side occurrence-derived.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Transcribed from the Embrapa Infoteca PDFs fetch_carvalho.py downloads into
# data/cache/carvalho. temp/tcold in C, rain in mm, tabsmin in C.
# None = Carvalho does not state it (or no circular exists for the species).
CARVALHO = {}

HOTTEST_ANNUAL_MEAN = 31.0  # WorldClim bio1 global max is 30.99 C


def overlap(a, b):
    """Jaccard overlap of two [lo, hi] intervals."""
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    if hi <= lo:
        return 0.0
    union = max(a[1], b[1]) - min(a[0], b[0])
    return (hi - lo) / union


def verdict(fit, ref, tol):
    """How the fitted absolute range compares with a reference range."""
    if ref is None:
        return "no reference"
    o = overlap(fit, ref)
    lo_gap, hi_gap = fit[0] - ref[0], fit[1] - ref[1]
    tag = ("agrees" if o >= 0.6 else "partial" if o >= 0.3 else "disagrees")
    return (f"{tag} (overlap {o:.2f}, low edge {lo_gap:+.0f}, "
            f"high edge {hi_gap:+.0f}{tol})")


def main():
    proto = json.loads((ROOT / "data" / "envelopes_proto.json").read_text())
    ecocrop = {s["sci"]: s for s in
               json.loads((ROOT / "data" / "species.json").read_text())}
    fits = {r["sci"]: r for r in proto["species"]}

    print("=" * 100)
    print("A. Fitted vs FAO EcoCrop, blind, on ten Brazilian natives EcoCrop covers")
    print("=" * 100)
    print(f"{'species':<26} {'source':<8} {'temp abs':>14} {'temp opt':>14} "
          f"{'rain abs':>14} {'rain opt':>14}")
    tw, rw, contained, nonbinding = [], [], 0, 0
    n = 0
    for sci, r in fits.items():
        e = ecocrop.get(sci)
        if not e or "temp" not in r:
            continue
        n += 1
        t_eco_abs = f"{e['temp'][0]:.0f}-{e['temp'][3]:.0f}"
        t_eco_opt = f"{e['temp'][1]:.0f}-{e['temp'][2]:.0f}"
        r_eco_abs = f"{e['rain'][0]:.0f}-{e['rain'][3]:.0f}"
        r_eco_opt = f"{e['rain'][1]:.0f}-{e['rain'][2]:.0f}"
        print(f"{sci:<26} {'ecocrop':<8} "
              f"{t_eco_abs:>14} "
              f"{t_eco_opt:>14} "
              f"{r_eco_abs:>14} "
              f"{r_eco_opt:>14}")
        t_fit_abs = f"{r['temp'][0]:.0f}-{r['temp'][3]:.0f}"
        t_fit_opt = f"{r['temp'][1]:.0f}-{r['temp'][2]:.0f}"
        r_fit_abs = f"{r['rain'][0]:.0f}-{r['rain'][3]:.0f}"
        r_fit_opt = f"{r['rain'][1]:.0f}-{r['rain'][2]:.0f}"
        print(f"{'':<26} {'fitted':<8} "
              f"{t_fit_abs:>14} "
              f"{t_fit_opt:>14} "
              f"{r_fit_abs:>14} "
              f"{r_fit_opt:>14}"
              f"   n={r['n_cells']}")
        et, ft = (e["temp"][0], e["temp"][3]), (r["temp"][0], r["temp"][3])
        er, fr = (e["rain"][0], e["rain"][3]), (r["rain"][0], r["rain"][3])
        tw.append((ft[1] - ft[0]) / (et[1] - et[0]))
        rw.append((fr[1] - fr[0]) / (er[1] - er[0]))
        inside = ft[0] >= et[0] - 0.5 and ft[1] <= et[1] + 0.5
        contained += inside
        nonbinding += e["temp"][3] > HOTTEST_ANNUAL_MEAN
        print(f"{'':<26} temp overlap {overlap(et, ft):.2f}, rain overlap "
              f"{overlap(er, fr):.2f}, fitted temp range is "
              f"{tw[-1]:.2f}x EcoCrop's, rain {rw[-1]:.2f}x"
              f"{', fit sits inside EcoCrop' if inside else ''}")
    if n:
        print(f"\n  {n} species compared. Fitted absolute temperature range is on "
              f"average {sum(tw) / n:.2f}x EcoCrop's, rainfall {sum(rw) / n:.2f}x.")
        print(f"  {contained}/{n} fitted envelopes sit entirely inside the curated one.")
        print(f"  {nonbinding}/{n} curated envelopes have an upper temperature bound "
              f"above {HOTTEST_ANNUAL_MEAN} C, the hottest annual mean on Earth, so "
              f"that bound can never exclude a site. No fitted envelope can do that.")

    print()
    print("=" * 100)
    print("B. Fitted vs Carvalho, Especies Arboreas Brasileiras / Circular Tecnica")
    print("=" * 100)
    if not CARVALHO:
        print("  (no references transcribed yet, run scripts/fetch_carvalho.py)")
        return
    for sci, ref in CARVALHO.items():
        r = fits.get(sci)
        if not r or "temp" not in r:
            print(f"{sci:<28} no fit")
            continue
        ft = (r["temp"][0], r["temp"][3])
        fr = (r["rain"][0], r["rain"][3])
        print(f"\n{sci}  ({ref['doc']})")
        print(f"  temp  Carvalho {ref['temp'][0]}-{ref['temp'][1]} C   "
              f"fitted p2-p98 {ft[0]:.1f}-{ft[1]:.1f} C   "
              f"observed {r['temp_full_range'][0]}-{r['temp_full_range'][1]}")
        print(f"        {verdict(ft, ref['temp'], ' C')}")
        print(f"  rain  Carvalho {ref['rain'][0]}-{ref['rain'][1]} mm  "
              f"fitted p2-p98 {fr[0]:.0f}-{fr[1]:.0f} mm  "
              f"observed {r['rain_full_range'][0]}-{r['rain_full_range'][1]}")
        print(f"        {verdict(fr, ref['rain'], ' mm')}")
        if ref.get("tabsmin") is not None:
            print(f"  cold  Carvalho absolute minimum {ref['tabsmin']} C   "
                  f"fitted ktmpr {r['ktmpr']} C   (bio6 p5 {r['bio6_p5']}, "
                  f"coldest cell bio6 {r['bio6_min']})")
        if ref.get("note"):
            print(f"  note  {ref['note']}")


if __name__ == "__main__":
    sys.exit(main())
