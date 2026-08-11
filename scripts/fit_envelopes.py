#!/usr/bin/env python3
"""Fit EcoCrop-shaped climate envelopes for species FAO EcoCrop never covered.

Prototype for the Brazilian native species base (STRATEGY.md item 3). EcoCrop
carries 2,568 species and 61 of them are Brazilian native trees, which is not a
species base. The rest of Brazil's restoration flora has no curated envelope
anywhere, so this derives one from where the tree actually grows:

    GBIF occurrences -> WorldClim 2.1 normals at those points -> quantiles
    -> [absmin, optmin, optmax, absmax], the shape scoring.js already eats.

Sources (all cached under data/cache on first run):
  GBIF       api.gbif.org/v1, keyless. species/match for the taxon key (gated on
             rank == SPECIES, the same gate app.js already applies), then
             occurrence/search paged for georeferenced records.
  WorldClim  geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_<res>_bio.zip,
             1970-2000 normals. bio1 annual mean temp, bio6 min temp of the
             coldest month, bio12 annual precipitation. LZW float32 GeoTIFF on a
             plain WGS84 grid, which Pillow reads without GDAL.
             NOTE: WorldClim is free for academic and non-commercial use only.
             A commercial Canopy needs CHELSA (CC BY 4.0) instead; the sampler
             is one class and the grid geometry is the same.
  WCVP       data/wcvp.zip, already vendored for data/natives.json. Used here to
             mask occurrences down to the countries where Kew records the
             species as native, which is what keeps Schinus terebinthifolia from
             being fitted to Florida.

Provenance matters and is recorded per species: EcoCrop envelopes are
expert-curated physiological limits, these are observed realized-niche
quantiles. They are not the same kind of number. See the calibration mode
(--set calib) for how far apart they sit on species that have both.

Usage:
    python3 scripts/fit_envelopes.py                  # the 10 target species
    python3 scripts/fit_envelopes.py --set calib      # EcoCrop cross-check
    python3 scripts/fit_envelopes.py --res 10m --cap 2000
"""
import argparse
import collections
import json
import math
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_natives as bn  # read_dbf/l3_to_iso/binomial/resolve/native_areas

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
OUT = ROOT / "data" / "envelopes_proto.json"

WC_URL = "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_{res}_bio.zip"
GBIF = "https://api.gbif.org/v1"
UA = {"User-Agent": "canopy-envelope-prototype/0.1 (github.com/canopy; contact: dev)"}

# Atlantic Forest + Cerrado restoration workhorses. None of them is in EcoCrop.
TARGETS = [
    "Handroanthus impetiginosus",
    "Cariniana estrellensis",
    "Cecropia pachystachya",
    "Anadenanthera colubrina",
    "Copaifera langsdorffii",
    "Aspidosperma polyneuron",
    "Luehea divaricata",
    "Trema micrantha",
    "Schinus terebinthifolia",
    "Ceiba speciosa",
]

# Held-out calibration: Brazilian native trees that DO have a curated EcoCrop
# envelope in data/species.json. Fit them blind, then compare. Chosen to span
# the ecological range: Araucaria is a narrow subtropical conifer, Guazuma a
# wide pioneer, Bertholletia an Amazon endemic, Euterpe edulis an Atlantic
# Forest understorey palm.
CALIB = [
    "Araucaria angustifolia",
    "Bertholletia excelsa",
    "Cedrela odorata",
    "Ceiba pentandra",
    "Enterolobium cyclocarpum",
    "Euterpe edulis",
    "Genipa americana",
    "Guazuma ulmifolia",
    "Hymenaea courbaril",
    "Schizolobium parahybum",
]

# Fossils and living collections are not evidence about climate: a fossil point
# carries the wrong climate entirely, and a LIVING_SPECIMEN is a botanic garden
# accession sitting wherever the garden is. Everything else is kept.
BASIS = ["PRESERVED_SPECIMEN", "HUMAN_OBSERVATION", "MACHINE_OBSERVATION",
         "MATERIAL_SAMPLE", "MATERIAL_CITATION", "OBSERVATION", "OCCURRENCE"]

# hasGeospatialIssue=false already drops the fatal ones; these are the flags
# GBIF classes as merely suspicious but which put the point in the wrong climate.
BAD_ISSUES = {
    "COUNTRY_COORDINATE_MISMATCH", "PRESUMED_SWAPPED_COORDINATE",
    "PRESUMED_NEGATED_LATITUDE", "PRESUMED_NEGATED_LONGITUDE",
    "COORDINATE_INVALID", "COORDINATE_OUT_OF_RANGE", "ZERO_COORDINATE",
    "COORDINATE_REPROJECTION_FAILED", "COORDINATE_REPROJECTION_SUSPICIOUS",
}
NOT_WILD = {"INTRODUCED", "INTRODUCEDASSISTEDCOLONISATION", "CULTIVATED",
            "MANAGED", "NATURALISED", "NATURALIZED", "INVASIVE", "VAGRANT"}
NOT_WILD_DEGREE = {"CULTIVATED", "MANAGED", "CAPTIVE", "RELEASED"}

MAX_UNCERTAINTY_M = 20_000   # a point vaguer than one climate cell says nothing
MIN_DECIMALS = 2             # 0.01 deg ~ 1.1 km; whole degrees are placeholders
MAX_OFFSET = 100_000         # GBIF refuses offset + limit beyond this
PAGE = 300                   # GBIF occurrence/search page cap


# --------------------------------------------------------------------------
# HTTP

def get_json(url, params=None, tries=5, timeout=45):
    """GET with retry.

    A short timeout on purpose: GBIF answers a 300-record page in about a
    second, so a request still open after 45 s is a dead connection, not a slow
    one, and waiting the default out costs minutes per stalled page.
    """
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)


def fetch(url, path):
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  downloading {path.name} ...", end="", flush=True)
    tmp = path.with_suffix(path.suffix + ".part")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r, open(tmp, "wb") as out:
        while chunk := r.read(1 << 20):
            out.write(chunk)
    tmp.rename(path)
    print(f" {path.stat().st_size / 1e6:.0f} MB")
    return path


# --------------------------------------------------------------------------
# WorldClim

class Bioclim:
    """One WorldClim bioclim band, sampled by lat/lon.

    The rasters are plain equirectangular WGS84: a tiepoint at (-180, 90) and a
    constant pixel scale, so the transform is arithmetic and needs no GDAL.
    Pillow decodes the LZW float32 strips; the tags are read back and asserted
    rather than assumed.
    """

    def __init__(self, path):
        im = Image.open(path)
        tags = im.tag_v2
        sx, sy = tags[33550][0], tags[33550][1]
        _, _, _, x0, y0, _ = tags[33922]
        assert im.mode == "F" and abs(sx - sy) < 1e-12, f"unexpected grid in {path}"
        self.x0, self.y0, self.sx, self.sy = x0, y0, sx, sy
        self.a = np.array(im, dtype=np.float32)
        nodata = tags.get(42113)
        if nodata is not None:
            self.a[self.a <= float(nodata) * 0.999] = np.nan
        self.h, self.w = self.a.shape

    def index(self, lat, lon):
        return (int((self.y0 - lat) / self.sy), int((lon - self.x0) / self.sx))

    def at(self, row, col, ring=0):
        """Value at a cell, else the nearest valid cell within `ring` cells.

        Coastal occurrences land in a sea cell often enough to matter: a
        mangrove or restinga point at 5 arcmin is routinely one cell offshore.
        Snapping to the nearest land cell recovers it; refusing to snap would
        throw away exactly the coastal Atlantic Forest records that matter most.
        """
        if not (0 <= row < self.h and 0 <= col < self.w):
            return np.nan, -1
        v = self.a[row, col]
        if not np.isnan(v):
            return float(v), 0
        for r in range(1, ring + 1):
            lo_r, hi_r = max(0, row - r), min(self.h, row + r + 1)
            lo_c, hi_c = max(0, col - r), min(self.w, col + r + 1)
            block = self.a[lo_r:hi_r, lo_c:hi_c]
            if np.isnan(block).all():
                continue
            # nearest valid cell inside the ring, by grid distance
            rows, cols = np.where(~np.isnan(block))
            d = (rows + lo_r - row) ** 2 + (cols + lo_c - col) ** 2
            k = int(np.argmin(d))
            return float(block[rows[k], cols[k]]), r
        return np.nan, -1


def load_bioclim(res, bands=(1, 6, 12)):
    zpath = CACHE / f"wc2.1_{res}_bio.zip"
    fetch(WC_URL.format(res=res), zpath)
    out = {}
    with zipfile.ZipFile(zpath) as zf:
        for b in bands:
            name = f"wc2.1_{res}_bio_{b}.tif"
            tif = CACHE / name
            if not tif.exists():
                tif.write_bytes(zf.read(name))
            out[b] = Bioclim(tif)
    return out


# --------------------------------------------------------------------------
# GBIF

def gbif_match(name):
    """Resolve a name to a GBIF backbone species key.

    Gated on rank == SPECIES: GBIF silently falls back to a genus match, which
    would fit an envelope to the whole genus. README.md already flags this trap
    for the nearby-occurrence check; it is far more damaging here.
    Synonyms are followed to the accepted usage so that, say, Schinus
    terebinthifolius and terebinthifolia collapse to one key.
    """
    m = get_json(f"{GBIF}/species/match", {"name": name, "kingdom": "Plantae",
                                           "strict": "false"})
    if m.get("matchType") in (None, "NONE") or m.get("rank") != "SPECIES":
        return None, f"no species-rank match (matchType={m.get('matchType')}, " \
                     f"rank={m.get('rank')})"
    key = m.get("acceptedUsageKey") or m.get("usageKey")
    return {"key": key, "name": m.get("species") or m.get("canonicalName"),
            "matchType": m.get("matchType"), "status": m.get("status"),
            "confidence": m.get("confidence"), "family": m.get("family")}, None


KEEP_FIELDS = ("decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters",
               "countryCode", "basisOfRecord", "year", "issues",
               "establishmentMeans", "degreeOfEstablishment", "datasetKey",
               "institutionCode", "coordinatePrecision")


def gbif_occurrences(key, cap):
    """Up to `cap` georeferenced records, sampled across the whole result set.

    Paging straight from offset 0 does not give the first `cap` records of a
    random sample, it gives whatever GBIF's internal ordering puts first, which
    tracks dataset ingestion and so over-represents whichever herbarium
    published in bulk. Spreading the pages evenly over the offset range costs
    the same number of calls and samples the whole set instead.
    """
    base = {"taxonKey": key, "hasCoordinate": "true", "hasGeospatialIssue": "false",
            "occurrenceStatus": "PRESENT", "basisOfRecord": BASIS, "limit": 1}
    total = get_json(f"{GBIF}/occurrence/search", base)["count"]
    reach = min(total, MAX_OFFSET)
    npages = max(1, math.ceil(min(cap, reach) / PAGE))
    span = max(0, reach - PAGE)
    offsets = sorted({int(round(i * span / max(1, npages - 1))) for i in range(npages)}) \
        if npages > 1 else [0]

    seen, rows = set(), []
    for off in offsets:
        page = get_json(f"{GBIF}/occurrence/search",
                        dict(base, limit=PAGE, offset=off))
        for r in page.get("results", []):
            k = r.get("key")
            if k in seen:
                continue
            seen.add(k)
            rows.append({f: r.get(f) for f in KEEP_FIELDS})
        if len(rows) >= cap:
            break
    return total, rows[:cap]


def cached_occurrences(sci, key, cap):
    path = CACHE / "gbif" / f"{key}_{cap}.json"
    if path.exists():
        d = json.loads(path.read_text())
        return d["total"], d["records"]
    total, rows = gbif_occurrences(key, cap)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"sci": sci, "key": key, "total": total,
                                "records": rows}))
    return total, rows


# --------------------------------------------------------------------------
# Native-range mask (reuses the WCVP pipeline behind data/natives.json)

MASK_CACHE = CACHE / "native_mask.json"


def native_countries(names):
    """binomial -> ISO country codes where WCVP records the species as native.

    Cached, because resolving names means a full pass over a 300 MB CSV inside
    data/wcvp.zip and that is four minutes whether you ask about 10 species or
    400. At 400 species it is amortised; at 10 it dominates the run.
    """
    have = json.loads(MASK_CACHE.read_text()) if MASK_CACHE.exists() else {}
    todo = [n for n in names if n not in have]
    if todo:
        bn.fetch(bn.LEVEL4_URL, bn.LEVEL4)
        bn.fetch(bn.WCVP_URL, bn.WCVP_ZIP)
        iso = bn.l3_to_iso(bn.LEVEL4)
        keys = {n: bn.binomial(n) for n in todo}
        zf = zipfile.ZipFile(bn.WCVP_ZIP)
        resolved, _, _, _ = bn.resolve(zf, {k for k in keys.values() if k})
        areas = bn.native_areas(zf, set(resolved.values()))
        for name, key in keys.items():
            pid = resolved.get(key)
            have[name] = sorted({c for l3 in areas.get(pid, ()) for c in iso.get(l3, ())}) \
                if pid else None
        MASK_CACHE.parent.mkdir(parents=True, exist_ok=True)
        MASK_CACHE.write_text(json.dumps(have, indent=1, sort_keys=True))
    return {n: set(have[n]) for n in names if have.get(n)}


# --------------------------------------------------------------------------
# Cleaning

DEC = re.compile(r"\.(\d+)")


def decimals(v):
    m = DEC.search(f"{v!r}")
    return len(m.group(1)) if m else 0


def clean(rows, native=None):
    """Filter raw occurrences to points that can carry climate information."""
    drop = collections.Counter()
    kept = []
    for r in rows:
        lat, lon = r.get("decimalLatitude"), r.get("decimalLongitude")
        if lat is None or lon is None:
            drop["no coordinate"] += 1
        elif abs(lat) > 90 or abs(lon) > 180 or (lat == 0 and lon == 0):
            drop["impossible coordinate"] += 1
        elif set(r.get("issues") or ()) & BAD_ISSUES:
            drop["geospatial issue flag"] += 1
        elif min(decimals(lat), decimals(lon)) < MIN_DECIMALS:
            drop["coordinate too coarse"] += 1
        elif (r.get("coordinateUncertaintyInMeters") or 0) > MAX_UNCERTAINTY_M:
            drop["uncertainty > 20 km"] += 1
        elif str(r.get("establishmentMeans") or "").upper().replace(" ", "") in NOT_WILD:
            drop["introduced/cultivated"] += 1
        elif str(r.get("degreeOfEstablishment") or "").upper().replace(" ", "") \
                in NOT_WILD_DEGREE:
            drop["introduced/cultivated"] += 1
        elif native is not None and r.get("countryCode") not in native:
            drop["outside native range"] += 1
        else:
            kept.append(r)
            continue
    return kept, drop


def thin(rows, mode, grid):
    """One record per cell. Duplicates inside a cell add no climate information
    and are pure sampling bias: a roadside tree next to a university gets 300
    records, a tree in the Jalapao gets one. Standard SDM thinning."""
    out, seen = [], set()
    for r in rows:
        lat, lon = r["decimalLatitude"], r["decimalLongitude"]
        if mode == "5km":
            k = (round(lat / 0.05), round(lon / 0.05))
        else:
            k = grid.index(lat, lon)
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


# --------------------------------------------------------------------------
# Fitting

def q(v, p):
    return float(np.percentile(v, p))


def envelope(vals, abs_lo=2, abs_hi=98, opt_lo=25, opt_hi=75, ndigits=0):
    e = [q(vals, abs_lo), q(vals, opt_lo), q(vals, opt_hi), q(vals, abs_hi)]
    e = [round(x, ndigits) for x in e]
    for i in range(1, 4):  # quantiles are monotone, rounding can tie them
        e[i] = max(e[i], e[i - 1])
    return e


# WorldClim has no absolute-extreme variable, and scoring.js runs two frost
# tests: the dismo one (coldest monthly mean minimum within 4 C of KTMPR) and a
# record-low one (the observed 10-year minimum under KTMPR outright). bio6 is a
# mean of daily minima, so neither test can read it directly. scripts/
# check_baseline.py measured both gaps at 12 Brazilian sites against the same
# Open-Meteo ERA5 series app.js queries:
#   10-year record low  = 1.62 * bio6 - 14.3   (R2 0.79, RMSE 1.5 C, n=12)
#   ERA5 coldest monthly mean min = bio6 + 1.9
# so the two thresholds a species must clear at the cold edge of its own range
# are 1.62*p5 - 14.3 and (p5 + 1.9) - 4. KTMPR is the lower of them. This is the
# weakest link in the pipeline: it is a 12-point regression standing in for a
# variable the raster does not carry.
def ktmpr_from_bio6(p5):
    return round(min(1.616 * p5 - 14.32, p5 - 2.06) * 2) / 2


def quality(n_cells, n_raw, drop, spread_deg, native_known):
    """A flag the UI can show next to an occurrence-derived envelope.

    Nothing here is a statement about the tree. It is a statement about how much
    evidence the envelope rests on, which is the thing a user planting 10,000
    seedlings is entitled to see.
    """
    reasons = []
    if n_cells < 20:
        return "insufficient", ["fewer than 20 independent climate cells"]
    if n_cells < 60:
        reasons.append(f"only {n_cells} independent climate cells")
    if spread_deg < 3:
        reasons.append(f"occurrences span only {spread_deg:.1f} deg of latitude")
    if not native_known:
        reasons.append("no WCVP native range, occurrences unmasked")
    frac_out = drop.get("outside native range", 0) / max(1, n_raw)
    if frac_out > 0.3:
        reasons.append(f"{100 * frac_out:.0f}% of records fell outside the "
                       f"native range (introduced or invasive population)")
    if not reasons:
        return "good", reasons
    return ("fair" if n_cells >= 60 and spread_deg >= 3 else "poor"), reasons


# --------------------------------------------------------------------------

def fit_species(sci, grids, cap, dedupe, mask, ring):
    t0 = time.time()
    rec = {"sci": sci}
    m, err = gbif_match(sci)
    if err:
        return dict(rec, error=err)
    rec["gbif"] = m
    total, raw = cached_occurrences(sci, m["key"], cap)

    native = mask.get(sci)
    kept, drop = clean(raw, native)
    grid = grids[1]
    thinned = thin(kept, dedupe, grid)
    alt = thin(kept, "5km" if dedupe == "cell" else "cell", grid)

    vals, snapped, offgrid = collections.defaultdict(list), 0, 0
    countries = collections.Counter()
    lats = []
    for r in thinned:
        lat, lon = r["decimalLatitude"], r["decimalLongitude"]
        row, col = grid.index(lat, lon)
        got = {}
        worst = 0
        for b, g in grids.items():
            v, ringused = g.at(row, col, ring)
            if np.isnan(v):
                worst = -1
                break
            worst = max(worst, ringused)
            got[b] = v
        if worst < 0:
            offgrid += 1
            continue
        snapped += worst > 0
        for b, v in got.items():
            vals[b].append(v)
        countries[r.get("countryCode") or "??"] += 1
        lats.append(lat)

    n = len(vals[1])
    rec.update({
        "n_gbif_total": total, "n_fetched": len(raw), "n_clean": len(kept),
        "n_cells": n, "n_alt_dedupe": len(alt), "dropped": dict(drop),
        "snapped_to_land": snapped, "no_climate_cell": offgrid,
        "top_countries": countries.most_common(6),
        "native_countries": sorted(native) if native else None,
        "seconds": round(time.time() - t0, 1),
    })
    if n < 20:
        rec["quality"], rec["quality_notes"] = "insufficient", \
            [f"only {n} independent climate cells"]
        return rec

    t, p, c = np.array(vals[1]), np.array(vals[12]), np.array(vals[6])
    spread = (max(lats) - min(lats)) if lats else 0.0
    rec["temp"] = envelope(t, ndigits=1)
    rec["rain"] = envelope(p, ndigits=0)
    rec["ktmpr"] = ktmpr_from_bio6(q(c, 5))
    rec["ktmpr_naive_p5_minus_4"] = round(q(c, 5) - 4, 1)
    rec["bio6_p5"] = round(q(c, 5), 1)
    rec["bio6_min"] = round(float(c.min()), 1)
    rec["temp_full_range"] = [round(float(t.min()), 1), round(float(t.max()), 1)]
    rec["rain_full_range"] = [round(float(p.min())), round(float(p.max()))]
    rec["temp_median"] = round(float(np.median(t)), 1)
    rec["rain_median"] = round(float(np.median(p)))
    rec["quality"], rec["quality_notes"] = quality(n, len(raw), drop, spread,
                                                   native is not None)
    rec["n_occurrences"] = n
    rec["provenance"] = "gbif+worldclim quantiles"
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="target", choices=["target", "calib", "both"])
    ap.add_argument("--res", default="5m", choices=["5m", "10m"])
    ap.add_argument("--cap", type=int, default=2000)
    ap.add_argument("--dedupe", default="cell", choices=["cell", "5km"])
    ap.add_argument("--ring", type=int, default=2,
                    help="cells to search for land when a point falls in the sea")
    ap.add_argument("--no-mask", action="store_true",
                    help="skip the WCVP native-range mask (to measure its effect)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    names = {"target": TARGETS, "calib": CALIB, "both": TARGETS + CALIB}[args.set]
    t0 = time.time()
    print(f"WorldClim {args.res} bio1/bio6/bio12")
    grids = load_bioclim(args.res)
    print(f"  grid {grids[1].w}x{grids[1].h}, cell {grids[1].sx:.4f} deg "
          f"(~{grids[1].sx * 111:.0f} km at the equator)")

    mask = {}
    if not args.no_mask:
        print("WCVP native ranges (reusing the data/natives.json pipeline)")
        mask = native_countries(names)
        print(f"  {len(mask)}/{len(names)} species have a native country list")

    out = []
    for sci in names:
        r = fit_species(sci, grids, args.cap, args.dedupe, mask, args.ring)
        out.append(r)
        if "error" in r:
            print(f"\n{sci}: FAILED, {r['error']}")
            continue
        print(f"\n{sci} -> {r['gbif']['name']} ({r['gbif']['matchType']}, "
              f"key {r['gbif']['key']})")
        print(f"  gbif {r['n_gbif_total']} records, fetched {r['n_fetched']}, "
              f"clean {r['n_clean']}, cells {r['n_cells']} "
              f"({args.dedupe} dedupe; {r['n_alt_dedupe']} the other way)")
        if r["dropped"]:
            print("  dropped: " + ", ".join(f"{k} {v}" for k, v in
                                            sorted(r["dropped"].items())))
        if r.get("snapped_to_land") or r.get("no_climate_cell"):
            print(f"  coastal: {r['snapped_to_land']} snapped to land, "
                  f"{r['no_climate_cell']} had no land cell within {args.ring}")
        print("  " + ", ".join(f"{c}:{n}" for c, n in r["top_countries"]))
        if r["quality"] == "insufficient":
            print(f"  QUALITY insufficient: {'; '.join(r['quality_notes'])}")
            continue
        print(f"  temp {r['temp']} C   (observed {r['temp_full_range']})")
        print(f"  rain {r['rain']} mm  (observed {r['rain_full_range']})")
        print(f"  ktmpr {r['ktmpr']} C (bio6 p5 {r['bio6_p5']}, min {r['bio6_min']})")
        print(f"  quality {r['quality']}"
              + (f": {'; '.join(r['quality_notes'])}" if r["quality_notes"] else ""))

    payload = {
        "generated_by": "scripts/fit_envelopes.py",
        "method": ("GBIF occurrences masked to the WCVP native range, thinned to "
                   f"one record per {args.dedupe}, sampled against WorldClim 2.1 "
                   f"{args.res} 1970-2000 normals (bio1, bio6, bio12); "
                   "temp/rain = [p2, p25, p75, p98], ktmpr = p5(bio6) - 4"),
        "provenance": "occurrence-derived, NOT expert-curated: do not present "
                      "these next to FAO EcoCrop envelopes without a source tag",
        "climate_baseline": "WorldClim 2.1, 1970-2000",
        "worldclim_licence": "free for academic and non-commercial use only",
        "resolution": args.res,
        "native_mask": not args.no_mask,
        "species": out,
    }
    pathlib.Path(args.out).write_text(json.dumps(payload, indent=1))
    ok = sum(1 for r in out if r.get("quality") in ("good", "fair"))
    print(f"\nwrote {args.out}: {len(out)} species, {ok} usable, "
          f"{time.time() - t0:.0f} s total")


if __name__ == "__main__":
    main()
