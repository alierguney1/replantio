#!/usr/bin/env python3
"""Build data/species.json from the FAO EcoCrop database dump.

Source: https://raw.githubusercontent.com/OpenCLIM/ecocrop/main/EcoCrop_DB.csv
Keeps woody species (life form contains 'tree') with complete temperature,
rainfall and soil pH envelopes. Every field kept is documented in README.md;
add columns here if the scoring model grows.
"""
import csv, json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "ecocrop_raw.csv"
OUT = ROOT / "data" / "species.json"

NUM = ["TOPMN", "TOPMX", "TMIN", "TMAX", "ROPMN", "ROPMX", "RMIN", "RMAX",
       "PHOPMN", "PHOPMX", "PHMIN", "PHMAX", "KTMP", "KTMPR", "GMIN", "GMAX", "ALTMX"]

# Growth-rate class by genus. Heuristic: pioneers/plantation species vs
# late-successional hardwoods; everything else defaults to medium.
# Edit freely; the growth model reads the class, not the genus.
FAST = {"Eucalyptus", "Acacia", "Cecropia", "Leucaena", "Gmelina", "Paulownia",
        "Populus", "Salix", "Casuarina", "Grevillea", "Melia", "Moringa",
        "Sesbania", "Calliandra", "Inga", "Gliricidia", "Erythrina", "Trema",
        "Musanga", "Ochroma", "Schizolobium", "Albizia", "Falcataria",
        "Ailanthus", "Robinia", "Alnus", "Betula", "Pinus", "Larix",
        "Pseudotsuga", "Corymbia", "Anadenanthera", "Guazuma", "Muntingia"}
SLOW = {"Quercus", "Fagus", "Swietenia", "Dipteryx", "Hymenaea", "Dalbergia",
        "Tabebuia", "Handroanthus", "Carya", "Taxus", "Podocarpus",
        "Araucaria", "Olea", "Ceratonia", "Adansonia", "Aspidosperma",
        "Astronium", "Peltogyne", "Guaiacum", "Diospyros", "Santalum",
        "Caesalpinia", "Cariniana", "Bertholletia", "Milicia", "Baillonella",
        "Entandrophragma", "Tieghemella", "Aquilaria", "Buxus", "Ilex"}
CONIFER_FAM = {"Pinaceae", "Cupressaceae", "Taxaceae", "Podocarpaceae",
               "Araucariaceae", "Taxodiaceae", "Cephalotaxaceae"}

def num(v):
    v = (v or "").strip()
    if v in ("", "NA"):
        return None
    try:
        return float(v)
    except ValueError:
        return None

def photoperiod(v):
    """'short day (<12 hours), neutral day (12-14 hours)' -> ['short','neutral'].
    None = unknown (no data); [] = known insensitive (tolerates all daylengths)."""
    v = (v or "").strip().lower()
    if not v or v == "na":
        return None
    if "not sensitive" in v:
        return []
    cats = [c for c in ("short", "neutral", "long") if c in v]
    if len(cats) == 3:
        return []
    return cats or None

def common_names(v):
    names = [n.strip() for n in (v or "").split(",") if n.strip()]
    clean = [n for n in names if n.isascii() and 2 < len(n) < 30]
    return (clean or names)[:4]

def uses(cat):
    tags = [t.strip() for t in (cat or "").split(",") if t.strip()]
    keep = {"forest/wood": "timber", "environmental": "environmental",
            "fruits & nuts": "fruit", "materials": "materials",
            "medicinals & aromatic": "medicinal", "ornamentals/turf": "ornamental",
            "forage/pasture": "forage", "food & beverage": "food"}
    return sorted({keep[t] for t in tags if t in keep})

def growth_class(sci, famname, topt_mid, ktmpr):
    genus = sci.split()[0]
    rate = "fast" if genus in FAST else "slow" if genus in SLOW else "medium"
    # deep-frost hardiness marks temperate species even when their optimum reads warm
    temperate = (ktmpr is not None and ktmpr <= -10) or topt_mid < 20
    zone = "temperate" if temperate else "tropical"
    family = (famname or "").split(":")[-1]
    return f"{zone}_{rate}", ("conifer" if family in CONIFER_FAM else "broadleaf")

def main():
    # ponytail: cp1252 per research; a few source bytes are pre-damaged, replace them
    rows = list(csv.DictReader(open(SRC, encoding="cp1252", errors="replace")))
    out = []
    for r in rows:
        lifo_raw = (r["LIFO"] or "").lower()
        if not lifo_raw.strip():
            continue  # no life form at all: unusable for the habit filter
        vals = {k: num(r[k]) for k in NUM}
        required = ["TOPMN", "TOPMX", "TMIN", "TMAX", "ROPMN", "ROPMX",
                    "RMIN", "RMAX"]
        if any(vals[k] is None for k in required):
            continue
        # a few EcoCrop rows have inverted/corrupt envelopes (e.g. Faidherbia
        # albida TMAX=13 < TOPMX=30); they would be unscorable, drop them
        t = [vals["TMIN"], vals["TOPMN"], vals["TOPMX"], vals["TMAX"]]
        rn = [vals["RMIN"], vals["ROPMN"], vals["ROPMX"], vals["RMAX"]]
        if sorted(t) != t or sorted(rn) != rn:
            continue
        # pH: absolute range required to score; optimal falls back to absolute
        ph = None
        if vals["PHMIN"] is not None and vals["PHMAX"] is not None:
            ph = [vals["PHMIN"], vals["PHOPMN"] or vals["PHMIN"],
                  vals["PHOPMX"] or vals["PHMAX"], vals["PHMAX"]]
            if sorted(ph) != ph:
                ph = None  # corrupt pH envelope: score pH as unknown instead
        names = common_names(r["COMNAME"])
        # GMIN/GMAX zeros are placeholders in the source
        cyc = [v if v else None for v in (vals["GMIN"], vals["GMAX"])]
        gclass, wood = growth_class(r["ScientificName"], r["FAMNAME"],
                                    (vals["TOPMN"] + vals["TOPMX"]) / 2, vals["KTMPR"])
        out.append({
            "id": int(r["EcoPortCode"]),
            "sci": r["ScientificName"].strip(),
            "common": names[0] if names else r["ScientificName"].strip(),
            "aka": names[1:],
            "family": (r["FAMNAME"] or "").split(":")[-1],
            "lifo": r["LIFO"],
            "uses": uses(r["CAT"]),
            "temp": [vals["TMIN"], vals["TOPMN"], vals["TOPMX"], vals["TMAX"]],
            "rain": [vals["RMIN"], vals["ROPMN"], vals["ROPMX"], vals["RMAX"]],
            "ph": ph,
            "ktmp": vals["KTMP"],       # killing temp, early growth
            "ktmpr": vals["KTMPR"],     # killing temp, dormant season
            "photo": photoperiod(r["PHOTO"]),
            "cycle": cyc,
            "altmax": vals["ALTMX"],
            "gclass": gclass,
            "wood": wood,
            "decid": "deciduous" in (r["PHYS"] or "").lower(),
            "tree": "tree" in lifo_raw,
            # single habit class for filtering; priority when multiple listed
            "porte": next((c for c in ("tree", "shrub", "vine", "grass", "herb") if c in lifo_raw), "herb"),
        })
    out.sort(key=lambda s: s["sci"])
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"{len(out)} species -> {OUT} ({OUT.stat().st_size // 1024} KB)")

if __name__ == "__main__":
    main()
