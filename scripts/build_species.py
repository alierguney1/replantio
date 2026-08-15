#!/usr/bin/env python3
"""Build data/species.json from the FAO EcoCrop database dump.

Source: https://raw.githubusercontent.com/OpenCLIM/ecocrop/main/EcoCrop_DB.csv
Keeps species with complete temperature, rainfall and soil pH envelopes.
Every field kept is documented in README.md; add columns here if the scoring
model grows.
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

# Curated metadata patches for major crops with incomplete EcoCrop dump fields.
# EcoCrop raw dump has complete envelopes for these flagship crops but empty LIFO fields.
SPECIES_PATCH = {
    2175: { # Zea mays (Maize / Corn)
        "lifo": "grass", "porte": "grass", "tree": False, "annual": True,
        "uses": ["environmental", "food", "forage", "materials"],
        "photo": ["short", "neutral"],
    },
    1265: { # Ipomoea batatas (Sweet Potato)
        "lifo": "herb, vine", "porte": "vine", "tree": False, "annual": True,
        "uses": ["food"], "photo": ["short"],
    },
    1884: { # Saccharum officinarum (Sugarcane)
        "lifo": "grass", "porte": "grass", "tree": False, "annual": False,
        "uses": ["food", "materials"], "photo": ["short", "neutral"],
    },
    1781: { # Pongamia pinnata (Indian beech / Millettia pinnata)
        "lifo": "tree", "porte": "tree", "tree": True, "wood": "broadleaf",
        "uses": ["environmental", "materials", "timber"],
    },
    8653: { # Pinus roxburghii (Chir pine)
        "lifo": "tree", "porte": "tree", "tree": True, "wood": "conifer",
        "uses": ["materials", "timber"],
    },
    6633: { # Hedysarum pallidum
        "lifo": "herb", "porte": "herb", "tree": False, "annual": False,
        "uses": ["forage"],
    },
    7651: { # Medicago intertexta (Calvary clover)
        "lifo": "herb", "porte": "herb", "tree": False, "annual": True,
        "uses": ["forage"],
    },
}

# Accepted binomial renames and orthographic standardizations from Kew WCVP
TAXONOMIC_RENAMES = {
    2662: "Acacia mellifera",
    347: "Falcataria falcata",
    354: "Aleurites moluccanus",
    3754: "Pachira quinata",
    3844: "Brassica rapa",
    2231: "Carya illinoinensis",
    2242: "Citrus aurantiifolia",
    4635: "Citrus × microcarpa",
    2263: "Diospyros nigra",
    2300: "Citrus japonica",
    6893: "Inga feuilleei",
    2475: "Luffa aegyptiaca",
    1379: "Solanum lycopersicum",
    1430: "Melaleuca leucadendra",
    7689: "Melilotus indicus",
    7937: "Neoglaziovia variegata",
    75061: "Attalea speciosa",
    8230: "Panax quinquefolius",
    1650: "Pennisetum polystachion",
    8660: "Pinus tabuliformis",
    1803: "Psidium cattleyanum",
    9922: "Coleus rotundifolius",
    10110: "Stipa Krylovii",
    10104: "Stipa baicalensis",
    10105: "Stipa breviflora",
    10106: "Stipa capillata",
    10107: "Stipa glareosa",
    10108: "Stipa gobica",
    10109: "Stipa grandis",
    10370: "Tetragonia tetragonoides",
    2095: "Trema orientale",
}

# Duplicate synonym entries merged into their accepted counterparts by Kew WCVP deduplication audit
EXCLUDED_DUPLICATE_IDS = {
    352, 505, 1110, 2071, 2090, 2334, 3578, 4055, 4185, 4564, 4768, 5101,
    5265, 5727, 5861, 5893, 6075, 6252, 7239, 7542, 7682, 8110, 8355, 8638,
    8654, 8657, 8955, 9287, 9645, 9868, 10816, 10955, 11291, 17655, 74984,
}

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
    keep = {
        "forest/wood": "timber", "environmental": "environmental",
        "cover crop": "environmental", "fruits & nuts": "fruit",
        "materials": "materials", "medicinals & aromatic": "medicinal",
        "ornamentals/turf": "ornamental", "forage/pasture": "forage",
        "food & beverage": "food", "cereals & pseudocereals": "food",
        "vegetables": "food", "pulses (grain legumes)": "food",
        "roots/tubers": "food",
    }
    return sorted({keep[t] for t in tags if t in keep})

def infer_habit(r, sci, famname, cat_raw, phys_raw, lispa_raw):
    """Infer life form and habit when EcoCrop LIFO is missing."""
    fam = (famname or "").split(":")[-1]
    phys = (phys_raw or "").lower()
    cat = (cat_raw or "").lower()

    if fam in CONIFER_FAM:
        return "tree", "tree", True, "conifer"
    if "gramineae" in fam.lower() or "poaceae" in fam.lower() or "cereals" in cat:
        return "grass", "grass", False, "broadleaf"
    if "tree" in phys or "tree" in (r.get("COMNAME") or "").lower() or sci.startswith("Pinus") or sci.startswith("Quercus"):
        return "tree", "tree", True, ("conifer" if fam in CONIFER_FAM else "broadleaf")
    if "vine" in phys or "climbing" in phys:
        return "vine", "vine", False, "broadleaf"
    if "shrub" in phys:
        return "shrub", "shrub", False, "broadleaf"
    return "herb", "herb", False, "broadleaf"

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
        code = int(r["EcoPortCode"])
        if code in EXCLUDED_DUPLICATE_IDS:
            continue
        patch = SPECIES_PATCH.get(code, {})

        lifo_raw = (patch.get("lifo") or r["LIFO"] or "").lower()
        inferred_lifo, inferred_porte, inferred_tree, inferred_wood = (
            infer_habit(r, r["ScientificName"], r["FAMNAME"], r["CAT"], r["PHYS"], r["LISPA"])
            if not lifo_raw.strip() else (None, None, None, None)
        )

        lifo_val = (patch.get("lifo") or r["LIFO"] or inferred_lifo or "").strip()
        if not lifo_val:
            continue  # no life form at all: unusable for the habit filter

        lifo_raw = lifo_val.lower()

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
        sci = TAXONOMIC_RENAMES.get(code, r["ScientificName"].strip())
        gclass, wood = growth_class(sci, r["FAMNAME"],
                                    (vals["TOPMN"] + vals["TOPMX"]) / 2, vals["KTMPR"])
        if "wood" in patch:
            wood = patch["wood"]
        elif inferred_wood:
            wood = inferred_wood

        porte = patch.get("porte") or next((c for c in ("tree", "shrub", "vine", "grass", "herb") if c in lifo_raw), None) or inferred_porte or "herb"
        is_tree = patch["tree"] if "tree" in patch else ("tree" in lifo_raw or bool(inferred_tree))
        is_annual = patch["annual"] if "annual" in patch else ("annual" in (r.get("LISPA") or "").lower())
        photo = patch.get("photo", photoperiod(r["PHOTO"]))
        use_list = patch.get("uses", uses(r["CAT"]))

        out.append({
            "id": code,
            "sci": sci,
            "common": names[0] if names else sci,
            "aka": names[1:],
            "family": (r["FAMNAME"] or "").split(":")[-1],
            "lifo": lifo_val,
            "uses": use_list,
            "temp": [vals["TMIN"], vals["TOPMN"], vals["TOPMX"], vals["TMAX"]],
            "rain": [vals["RMIN"], vals["ROPMN"], vals["ROPMX"], vals["RMAX"]],
            "ph": ph,
            "ktmp": vals["KTMP"],       # killing temp, early growth
            "ktmpr": vals["KTMPR"],      # killing temp, dormant season
            # obligate wetland: EcoCrop absolute drainage tolerates ONLY saturated soil
            **({"wet": True} if (r.get("DRAR") or r.get("DRA") or "").strip() == "poorly (saturated >50% of year)" else {}),
            # annual-capable: frost is tested on the growing window, not the winter
            **({"annual": True} if is_annual else {}),
            # shade-tolerant / understory: EcoCrop optimal light intensity includes shade
            **({"shade": True} if ("shade" in (r.get("LIOPMN") or "").lower() or "shade" in (r.get("LIOPMX") or "").lower()) else {}),
            "photo": photo,
            "cycle": cyc,
            "altmax": vals["ALTMX"],
            "gclass": gclass,
            "wood": wood,
            "decid": "deciduous" in (r["PHYS"] or "").lower(),
            "tree": is_tree,
            "porte": porte,
        })
    out.sort(key=lambda s: s["sci"])
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"{len(out)} species -> {OUT} ({OUT.stat().st_size // 1024} KB)")

if __name__ == "__main__":
    main()

