#!/usr/bin/env python3
"""Build data/natives.json: the countries where each species.json taxon is native.

Sources (both cached under data/ on first run):
  WCVP    https://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip
          Kew's World Checklist of Vascular Plants, v16 (extracted 2026-06-04).
          wcvp_names.csv is the accepted-name backbone, wcvp_distribution.csv
          gives native/introduced status per TDWG WGSRPD level-3 region.
          Pipe-delimited. CC BY 3.0 -- note 3.0, not 4.0. Cite:
          Govaerts R (ed.). 2026. WCVP: World Checklist of Vascular Plants.
          Royal Botanic Gardens, Kew. https://doi.org/10.34885/egs6-cp24
  WGSRPD  https://raw.githubusercontent.com/tdwg/wgsrpd/master/level4/level4.dbf
          Attribute table of the level-4 shapefile: every level-4 area carries an
          ISO country code and the level-3 region it nests under, which is the
          published bridge from TDWG regions to countries. The repo carries no
          LICENSE file; TDWG publishes its site content under CC BY 4.0. Cite:
          Brummitt R.K. 2001. World Geographic Scheme for Recording Plant
          Distributions, ed. 2. Hunt Institute / TDWG.

Output is {"<species id>": ["AU", "PG", ...]} with ISO 3166-1 alpha-2 codes, so the
app can compare against the country code it gets from reverse geocoding. Species
with no WCVP match, or matched but with no native distribution, are left out
entirely -- absent means "unknown", not "not native anywhere".
"""
import collections, csv, difflib, io, json, pathlib, struct, sys, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECIES = ROOT / "data" / "species.json"
WCVP_ZIP = ROOT / "data" / "wcvp.zip"
LEVEL4 = ROOT / "data" / "wgsrpd_level4.dbf"
OUT = ROOT / "data" / "natives.json"

WCVP_URL = "https://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip"
LEVEL4_URL = "https://raw.githubusercontent.com/tdwg/wgsrpd/master/level4/level4.dbf"

# EcoCrop's spellings are decades old and full of typos, so an exact binomial
# lookup misses ~4% of the list. A near match is taken only when it is the sole
# candidate in the genus, or beats the runner-up by MARGIN -- 'Acacia anticeps'
# sits between the real anaticeps and anceps, and a guess there would invent a
# native range. Every non-exact match is printed for review.
FUZZ, MARGIN = 0.75, 0.10

# Corrections the automatic rule refuses because the runner-up is too close
# (mellifera vs umbellifera, cattleyanum vs ratterianum). Checked by hand.
ALIAS = {
    ("Acacia", "millifera"): ("Acacia", "mellifera"),
    ("Psidium", "cattleianum"): ("Psidium", "cattleyanum"),
}

# WGSRPD's ISO_Code column still carries a handful of withdrawn or non-ISO tokens.
# Remap them by level-4 area code (the level-3 region they sit in is too coarse --
# NLA holds Aruba, Bonaire and Curacao, which are three different countries now).
ISO_FIX = {
    "FRA-CI": ("JE", "GG"),  # Channel Is., filed under "UK" upstream
    "GRB-OO": ("GB",),       # "UK" is not an ISO 3166-1 code
    "IRE-NI": ("GB",),       # Northern Ireland
    "YUG-SE": ("RS",),       # "YU" retired with Yugoslavia
    "YUG-MN": ("ME",),
    "YUG-KO": ("XK",),       # user-assigned, but what geocoders return for Kosovo
    "LSI-ET": ("TL",),       # East Timor; "TP" was withdrawn in 2002
    "NLA-BO": ("BQ",),       # "AN" retired when the Antilles dissolved in 2010
    "NLA-CU": ("CW",),
    "LEE-NL": ("BQ", "SX"),  # Saba + St Eustatius, and Sint Maarten
    "SCS-SI": (),            # Spratly Is. -- disputed, no country to name
    "SCS-PI": (),            # Paracel Is.  -- ditto
}
RETIRED = {"UK", "AN", "YU", "TP", "SP", "PI"}  # must not survive ISO_FIX


def fetch(url, path):
    """Download to path unless it is already there. WCVP is ~84 MB."""
    if path.exists():
        return path
    print(f"downloading {url} -> {path.name}", flush=True)
    tmp = path.with_suffix(path.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as out:
        while chunk := r.read(1 << 20):
            out.write(chunk)
    tmp.rename(path)
    return path


def read_dbf(path):
    """Yield dBASE III records as dicts. Enough of the format for one flat table."""
    data = path.read_bytes()
    count, header_len, record_len = struct.unpack("<IHH", data[4:12])
    fields, off = [], 32
    while data[off] != 0x0D:
        name = data[off:off + 11].split(b"\0")[0].decode("ascii")
        fields.append((name, data[off + 16]))
        off += 32
    pos = header_len
    for _ in range(count):
        record, pos = data[pos:pos + record_len], pos + record_len
        if record[:1] == b"*":  # deleted
            continue
        at, row = 1, {}
        for name, length in fields:
            row[name] = record[at:at + length].decode("latin-1").strip()
            at += length
        yield row


def l3_to_iso(path):
    """TDWG level-3 region code -> sorted ISO 3166-1 alpha-2 codes it overlaps.

    41 of the 369 regions straddle a border (BOR is Brunei + Indonesia + Malaysia),
    and level 3 is as fine as WCVP records distribution, so those regions yield
    every country they touch. That errs towards calling a species native.
    """
    mapping = collections.defaultdict(set)
    for row in read_dbf(path):
        codes = ISO_FIX.get(row["Level4_cod"], (row["ISO_Code"],))
        mapping[row["Level3_cod"]].update(c for c in codes if c)
    stale = {c for codes in mapping.values() for c in codes} & RETIRED
    if stale:
        sys.exit(f"WGSRPD shipped unmapped legacy codes {sorted(stale)}; update ISO_FIX")
    return {k: sorted(v) for k, v in mapping.items()}


def binomial(sci):
    """'Acacia julifera ssp. julifera' -> ('Acacia', 'julifera').

    Drops authors, infraspecific ranks and the hybrid sign; matching the binomial
    is deliberate, since WCVP records the species-level range as the union of its
    subspecies. Returns None for genus-only entries and for hybrid formulas like
    'Annona cherimola x Annona squamosa' -- a cross has no native range of its
    own, and taking the first parent would invent one.
    """
    tokens = sci.replace("×", " ").split()
    for i, t in enumerate(tokens):
        if t == "x" and i + 1 < len(tokens) and tokens[i + 1][:1].isupper():
            return None
    tokens = [t.strip(".,") for t in tokens if t != "x"]
    if len(tokens) < 2 or tokens[1] in ("sp", "spp"):
        return None
    return tokens[0].capitalize(), tokens[1].lower()


def deslur(epithet):
    """caffra -> afra, caffer -> afer, caffrum -> afrum.

    The Madrid Code (IBC 2024) replaced the epithet 'caffr-', derived from a
    racial slur, across ~390 taxa; WCVP has adopted it, EcoCrop predates it.
    """
    return "af" + epithet[4:] if epithet.startswith("caff") else epithet


def wcvp_rows(zf, name):
    csv.field_size_limit(1 << 24)
    with zf.open(name) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, "utf-8", errors="replace"),
                                  delimiter="|")


def index_names(zf, genera):
    """One pass over wcvp_names.csv, keeping the genera we asked about.

    Returns (binomial -> name rows, every genus WCVP knows). Holding the whole
    1.4M-row file would cost hundreds of MB; the ~500 genera we care about fit
    comfortably.
    """
    index, all_genera = collections.defaultdict(list), set()
    for rec in wcvp_rows(zf, "wcvp_names.csv"):
        genus = rec["genus"]
        if not genus:
            continue
        all_genera.add(genus)
        if genus in genera and rec["species"]:
            index[(genus, rec["species"])].append(
                (rec["taxon_rank"], rec["taxon_status"],
                 rec["plant_name_id"], rec["accepted_plant_name_id"]))
    return index, all_genera


def accepted_id(rows):
    """Pick the accepted taxon for one binomial, and flag homonyms.

    A binomial shows up as the accepted species, as a synonym of something else,
    and as dozens of infraspecific names. Prefer the accepted species, then what
    the species-rank synonyms point at, then the infraspecific ones.
    """
    accepted = sorted(pid for rank, status, pid, _ in rows
                      if rank == "Species" and status == "Accepted")
    if accepted:
        return accepted[0], len(accepted) > 1
    for ranks in (("Species",), None):
        targets = [acc for rank, _, _, acc in rows
                   if acc and (ranks is None or rank in ranks)]
        if targets:
            return collections.Counter(targets).most_common(1)[0][0], False
    return None, False


def match(key, index, epithets):
    """Resolve one binomial to a key in `index`, tolerating EcoCrop's spellings."""
    genus, epithet = ALIAS.get(key, key)
    if (genus, epithet) in index:
        return (genus, epithet), "alias" if key != (genus, epithet) else "exact"
    fixed = deslur(epithet)
    if fixed != epithet and (genus, fixed) in index:
        return (genus, fixed), "madrid code"
    near = difflib.get_close_matches(epithet, epithets.get(genus, ()), n=2, cutoff=FUZZ)
    if not near:
        return None, "no candidate"
    scores = [difflib.SequenceMatcher(None, epithet, c).ratio() for c in near]
    if len(near) == 1 or scores[0] - scores[1] >= MARGIN:
        return (genus, near[0]), "spelling"
    return None, "ambiguous"


def native_areas(zf, ids):
    """plant_name_id -> TDWG level-3 codes where the taxon is native."""
    areas = collections.defaultdict(set)
    for rec in wcvp_rows(zf, "wcvp_distribution.csv"):
        if (rec["plant_name_id"] in ids and rec["introduced"] == "0"
                and rec["extinct"] == "0" and rec["location_doubtful"] == "0"):
            areas[rec["plant_name_id"]].add(rec["area_code_l3"])
    return areas


def by_genus(index):
    epithets = collections.defaultdict(set)
    for genus, epithet in index:
        epithets[genus].add(epithet)
    return epithets


def resolve(zf, keys):
    """binomial -> accepted plant_name_id, plus notes on how each was matched."""
    index, all_genera = index_names(zf, {g for g, _ in keys})
    epithets = by_genus(index)

    hits, notes, how, retry = {}, [], collections.Counter(), {}
    for key in keys:
        found, kind = match(key, index, epithets)
        if found is None and key[0] not in all_genera:
            retry[key] = difflib.get_close_matches(key[0], all_genera, n=5, cutoff=FUZZ)
            continue
        hits[key], how[kind] = found, how[kind] + 1
        if found and kind != "exact":
            notes.append((key, found, kind))

    if retry:  # second pass, only for the handful of misspelled genera
        extra, _ = index_names(zf, {g for cands in retry.values() for g in cands})
        extra_epithets = by_genus(extra)
        for key, cands in retry.items():
            # String distance alone will not do here -- Trewia is exactly as close
            # to Grewia as to Trevia. Keep only candidates that carry the epithet.
            found = [m for m in (match((g, key[1]), extra, extra_epithets)[0]
                                 for g in cands) if m]
            kind = ("genus" if len(found) == 1 else
                    "genus ambiguous" if found else "genus no candidate")
            hits[key], how[kind] = found[0] if len(found) == 1 else None, how[kind] + 1
            if len(found) == 1:
                index[found[0]] = extra[found[0]]
                notes.append((key, found[0], "genus"))

    resolved, homonyms = {}, []
    for key, found in hits.items():
        if found is None:
            continue
        pid, ambiguous = accepted_id(index[found])
        if pid:
            resolved[key] = pid
        if ambiguous:
            homonyms.append(found)
    return resolved, notes, how, homonyms


def main():
    fetch(LEVEL4_URL, LEVEL4)
    fetch(WCVP_URL, WCVP_ZIP)
    iso = l3_to_iso(LEVEL4)
    print(f"WGSRPD: {len(iso)} level-3 regions mapped to ISO codes")

    species = json.loads(SPECIES.read_text())
    keys = {s["id"]: binomial(s["sci"]) for s in species}
    wanted = {k for k in keys.values() if k}
    skipped = [s["sci"] for s in species if keys[s["id"]] is None]
    print(f"species.json: {len(species)} taxa -> {len(wanted)} distinct binomials "
          f"({len(skipped)} unusable: {', '.join(skipped)})")

    zf = zipfile.ZipFile(WCVP_ZIP)
    resolved, notes, how, homonyms = resolve(zf, wanted)
    print(f"WCVP names: {len(resolved)}/{len(wanted)} binomials resolved  {dict(how)}")
    for key, found, kind in sorted(notes):
        print(f"  {kind:14s} {key[0]} {key[1]} -> {found[0]} {found[1]}")
    if homonyms:
        print(f"  homonyms (>1 accepted species share a binomial, lowest id used): "
              f"{', '.join(f'{g} {e}' for g, e in sorted(homonyms))}")

    areas = native_areas(zf, set(resolved.values()))
    natives, no_dist, unmatched = {}, [], []
    for sp in species:
        pid = resolved.get(keys[sp["id"]]) if keys[sp["id"]] else None
        if pid is None:
            unmatched.append(sp["sci"])
            continue
        codes = sorted({c for l3 in areas.get(pid, ()) for c in iso.get(l3, ())})
        # [] = matched in WCVP but no native range recorded (cultigens like
        # Citrus); absent = no WCVP match at all (unknown). The UI shows them
        # differently.
        natives[str(sp["id"])] = codes
        if not codes:
            no_dist.append(sp["sci"])

    OUT.write_text(json.dumps(natives, separators=(",", ":"), sort_keys=True))
    total = len(species)
    print(f"\nwrote {OUT.relative_to(ROOT)}: {len(natives)}/{total} species "
          f"({100 * len(natives) / total:.1f}%), {OUT.stat().st_size / 1024:.0f} KB")
    print(f"  no WCVP match ({len(unmatched)}): {', '.join(sorted(unmatched))}")
    print(f"  matched, no native range ({len(no_dist)}): {', '.join(sorted(no_dist))}")


if __name__ == "__main__":
    main()
