#!/usr/bin/env python3
"""Build the nativity layers for species.json: which countries, and where inside
the countries too big for that to mean anything.

  data/natives.json     {"<species id>": ["AU", "PG", ...]}  ISO 3166-1 alpha-2
  data/natives_l3.json  {"<species id>": ["BZL", "BZS", ...]} TDWG level-3 codes,
                        carried only for the nine countries in SUBNATIONAL
  data/l3_regions.json  {"BR": {"SP": "BZL", ...}, ...} ISO 3166-2 subdivision
                        code -> level-3 region, so a reverse geocode can reach
                        the level-3 layer

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

natives.json carries ISO 3166-1 alpha-2 codes, so the app can compare against the
country code it gets from reverse geocoding. Species with no WCVP match, or
matched but with no native distribution, are left out entirely -- absent means
"unknown", not "not native anywhere".

natives_l3.json is a strict refinement: it holds the same native areas one level
finer, for the countries where the country answer is too coarse to be worth
anything. A species listed there under BR always has BR in natives.json, and a
species native to BR always has at least one BZ* code here -- both files are the
same WCVP rows, collapsed differently. Species with no level-3 code in any of
those countries are absent, and the app falls back to the country layer.
"""
import collections, csv, difflib, io, json, pathlib, struct, sys, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECIES = ROOT / "data" / "species.json"
WCVP_ZIP = ROOT / "data" / "wcvp.zip"
LEVEL4 = ROOT / "data" / "wgsrpd_level4.dbf"
OUT = ROOT / "data" / "natives.json"
OUT_NATURALIZED = ROOT / "data" / "naturalized.json"
OUT_L3 = ROOT / "data" / "natives_l3.json"
OUT_REGIONS = ROOT / "data" / "l3_regions.json"

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

# Countries wide enough that "native here" stops being a fact about the place.
# Pau-brasil and the castanheira are both native to Brazil and have never shared a
# forest. For these, natives_l3.json keeps the level-3 codes WCVP already records
# instead of collapsing them; everywhere else level 3 is at or below country size,
# so splitting would only add bytes.
SUBNATIONAL = ("AR", "AU", "BR", "CA", "CN", "IN", "MX", "RU", "US")

# Level-4 area -> ISO 3166-2 subdivision code with the country prefix dropped,
# which is the form reverse geocoders hand back (Nominatim's ISO3166-2-lvl4,
# Google's administrative_area_level_1 short_name). WGSRPD's own level-4 suffixes
# look close enough to ISO to be a trap -- CHN-HB is Hebei where ISO CN-HB is
# Hubei, and BZN-RM is Roraima whose UF is RR -- so every one is written out.
# Several areas may share a subdivision (Puducherry is four exclaves); they just
# have to agree on the level-3 region, which subnational() enforces.
SUBDIVISIONS = {
    "AR": {  # ISO 3166-2:AR is single letters, and not the obvious ones
        "AGE-BA": "B", "AGE-CH": "H", "AGE-CN": "W", "AGE-CO": "X", "AGE-DF": "C",
        "AGE-ER": "E", "AGE-FO": "P", "AGE-LP": "L", "AGE-MI": "N", "AGE-SF": "S",
        "AGS-CB": "U", "AGS-NE": "Q", "AGS-RN": "R", "AGS-SC": "Z", "AGS-TF": "V",
        "AGW-CA": "K", "AGW-JU": "Y", "AGW-LR": "F", "AGW-ME": "M", "AGW-SA": "A",
        "AGW-SE": "G", "AGW-SJ": "J", "AGW-SL": "D", "AGW-TU": "T",
    },
    "AU": {
        "NSW-CT": "ACT", "NSW-NS": "NSW", "NTA-OO": "NT", "QLD-QU": "QLD",
        "SOA-OO": "SA", "TAS-OO": "TAS", "VIC-OO": "VIC", "WAU-WA": "WA",
    },
    "BR": {
        "BZC-DF": "DF", "BZC-GO": "GO", "BZC-MS": "MS", "BZC-MT": "MT",
        "BZE-AL": "AL", "BZE-BA": "BA", "BZE-CE": "CE", "BZE-MA": "MA",
        "BZE-PB": "PB", "BZE-PE": "PE", "BZE-PI": "PI", "BZE-RN": "RN",
        "BZE-SE": "SE", "BZE-FN": "PE",  # Fernando de Noronha is a PE district
        "BZL-ES": "ES", "BZL-MG": "MG", "BZL-RJ": "RJ", "BZL-SP": "SP",
        "BZL-TR": "ES",                  # Trindade is administered from Vitória
        "BZN-AC": "AC", "BZN-AM": "AM", "BZN-AP": "AP", "BZN-PA": "PA",
        "BZN-RM": "RR", "BZN-RO": "RO", "BZN-TO": "TO",  # RM is WGSRPD's Roraima
        "BZS-PR": "PR", "BZS-RS": "RS", "BZS-SC": "SC",
    },
    "CA": {
        "ABT-OO": "AB", "BRC-OO": "BC", "MAN-OO": "MB", "NBR-OO": "NB",
        "NSC-OO": "NS", "NUN-OO": "NU", "NWT-OO": "NT", "ONT-OO": "ON",
        "PEI-OO": "PE", "QUE-OO": "QC", "SAS-OO": "SK", "YUK-OO": "YT",
    },
    "CN": {
        "CHC-CQ": "CQ", "CHC-GZ": "GZ", "CHC-HU": "HB", "CHC-SC": "SC",
        "CHC-YN": "YN", "CHH-OO": "HI", "CHI-NM": "NM", "CHI-NX": "NX",
        "CHM-HJ": "HL", "CHM-JL": "JL", "CHM-LN": "LN", "CHN-BJ": "BJ",
        "CHN-GS": "GS", "CHN-HB": "HE", "CHN-SA": "SN", "CHN-SD": "SD",
        "CHN-SX": "SX", "CHN-TJ": "TJ", "CHQ-OO": "QH", "CHS-AH": "AH",
        "CHS-FJ": "FJ", "CHS-GD": "GD", "CHS-GX": "GX", "CHS-HE": "HA",
        "CHS-HK": "HK", "CHS-HN": "HN", "CHS-JS": "JS", "CHS-JX": "JX",
        "CHS-SH": "SH", "CHS-ZJ": "ZJ", "CHT-OO": "XZ", "CHX-OO": "XJ",
    },
    "IN": {
        "ASS-AS": "AS", "ASS-MA": "MN", "ASS-ME": "ML", "ASS-MI": "MZ",
        "ASS-NA": "NL", "ASS-TR": "TR", "EHM-AP": "AR", "EHM-SI": "SK",
        "IND-AP": "AP", "IND-BI": "BR", "IND-CH": "CH", "IND-CT": "CG",
        "IND-DE": "DL", "IND-GO": "GA", "IND-GU": "GJ", "IND-HA": "HR",
        "IND-JK": "JH", "IND-KE": "KL", "IND-KT": "KA", "IND-MP": "MP",
        "IND-MR": "MH", "IND-OR": "OD", "IND-PU": "PB", "IND-RA": "RJ",
        "IND-TN": "TN", "IND-UP": "UP", "IND-WB": "WB", "LDV-OO": "LD",
        "WHM-HP": "HP", "WHM-JK": "JK", "WHM-UT": "UK",
        "IND-DD": "DH", "IND-DM": "DH", "IND-DI": "DH",  # merged into one UT, 2020
        "IND-PO": "PY", "IND-KL": "PY", "IND-MH": "PY", "IND-YA": "PY",
    },
    "MX": {
        "MXC-DF": "CMX", "MXC-ME": "MEX", "MXC-MO": "MOR", "MXC-PU": "PUE",
        "MXC-TL": "TLA", "MXE-AG": "AGU", "MXE-CO": "COA", "MXE-CU": "CHH",
        "MXE-DU": "DUR", "MXE-GU": "GUA", "MXE-HI": "HID", "MXE-NL": "NLE",
        "MXE-QU": "QUE", "MXE-SL": "SLP", "MXE-TA": "TAM", "MXE-ZA": "ZAC",
        "MXG-VC": "VER", "MXN-BC": "BCN", "MXN-BS": "BCS", "MXN-SI": "SIN",
        "MXN-SO": "SON", "MXS-CL": "COL", "MXS-GR": "GRO", "MXS-JA": "JAL",
        "MXS-MI": "MIC", "MXS-NA": "NAY", "MXS-OA": "OAX", "MXT-CA": "CAM",
        "MXT-CI": "CHP", "MXT-QR": "ROO", "MXT-TB": "TAB", "MXT-YU": "YUC",
    },
    "US": {
        "ALA-OO": "AL", "ARI-OO": "AZ", "ARK-OO": "AR", "ASK-OO": "AK",
        "CAL-OO": "CA", "CNT-OO": "CT", "COL-OO": "CO", "DEL-OO": "DE",
        "FLA-OO": "FL", "GEO-OO": "GA", "HAW-HI": "HI", "IDA-OO": "ID",
        "ILL-OO": "IL", "INI-OO": "IN", "IOW-OO": "IA", "KAN-OO": "KS",
        "KTY-OO": "KY", "LOU-OO": "LA", "MAI-OO": "ME", "MAS-OO": "MA",
        "MIC-OO": "MI", "MIN-OO": "MN", "MNT-OO": "MT", "MRY-OO": "MD",
        "MSI-OO": "MS", "MSO-OO": "MO", "NCA-OO": "NC", "NDA-OO": "ND",
        "NEB-OO": "NE", "NEV-OO": "NV", "NWH-OO": "NH", "NWJ-OO": "NJ",
        "NWM-OO": "NM", "NWY-OO": "NY", "OHI-OO": "OH", "OKL-OO": "OK",
        "ORE-OO": "OR", "PEN-OO": "PA", "RHO-OO": "RI", "SCA-OO": "SC",
        "SDA-OO": "SD", "TEN-OO": "TN", "TEX-OO": "TX", "UTA-OO": "UT",
        "VER-OO": "VT", "VRG-OO": "VA", "WAS-OO": "WA", "WDC-OO": "DC",
        "WIS-OO": "WI", "WVA-OO": "WV", "WYO-OO": "WY",
    },
}

# Level-4 areas of a SUBNATIONAL country left out of l3_regions, and why. Most are
# one subdivision split across two level-3 regions: a state code alone cannot say
# which half you are standing in, and guessing would hand back a native range from
# the wrong side of the country. Anything in neither table stops the build, so a
# WGSRPD update cannot quietly drop a state.
SUBDIVISION_SKIP = {
    "ALU-OO": "Aleutian Is., part of US-AK -> ASK",
    "LAB-OO": "Labrador and Newfoundland are both CA-NL",
    "NFL-NE": "Newfoundland and Labrador are both CA-NL",
    "AND-AN": "Andaman and Nicobar Is. are both IN-AN",
    "NCB-OO": "Nicobar and Andaman Is. are both IN-AN",
    "EHM-DJ": "Darjiling is a district of IN-WB -> IND",
    "MXI-GU": "Guadalupe I., part of MX-BCN -> MXN",
    "MXI-RA": "Rocas Alijos, part of MX-BCS -> MXN",
    "MXI-RG": "Revillagigedo Is., part of MX-COL -> MXS",
    "NFK-LH": "Lord Howe I., part of AU-NSW -> NSW",
    "MAQ-OO": "Macquarie I., part of AU-TAS -> TAS",
    "QLD-CS": "Coral Sea Is., an external territory with no AU subdivision",
    "WAU-AC": "Ashmore-Cartier Is., an external territory with no AU subdivision",
}

# Subdivisions that did not exist when WGSRPD ed. 2 froze in 2001, filed under the
# level-3 region of the parent they were carved out of.
SUBDIVISION_EXTRA = {
    # Telangana from AP 2014 (ISO says TG but geocoders return TS: keep both), Ladakh from J&K 2019
    "IN": {"TG": "IND", "TS": "IND", "LA": "WHM"},
}

# Printed on every run: the sub-national split is the whole point of the second
# file, and a silent regression in it looks exactly like a correct build. Ranges
# cross-checked against Flora e Funga do Brasil and the Jepson eFlora.
SPOT_CHECK = [
    # Caesalpinia echinata rather than Paubrasilia, to exercise the synonym path
    (("Caesalpinia", "echinata"), {"BZE", "BZL"}, {"BZC", "BZN", "BZS"}),
    (("Araucaria", "angustifolia"), {"BZL", "BZS"}, {"BZN"}),
    (("Bertholletia", "excelsa"), {"BZN"}, {"BZE", "BZL", "BZS"}),
    (("Euterpe", "edulis"), {"BZE", "BZL", "BZS"}, {"BZN"}),
    (("Sequoia", "sempervirens"), {"CAL"}, {"FLA", "TEX", "WAS"}),
]


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


def subnational(path):
    """(level-3 codes inside SUBNATIONAL countries, {country: {subdivision: L3}}).

    The first is the filter for natives_l3.json, the second is the bridge from a
    reverse geocode to it. Russia gets the first and not the second: WGSRPD splits
    European Russia into five compass regions ("Central European Russia") that are
    not oblasts and nest no administrative units, so there is nothing to key ~50
    federal subjects on. Its level-3 codes are still recorded, in case a mapping
    for them ever lands.
    """
    rows = [r for r in read_dbf(path) if r["ISO_Code"] in SUBNATIONAL]
    codes = {r["Level3_cod"] for r in rows}

    regions = {}
    for row in rows:
        area, country = row["Level4_cod"], row["ISO_Code"]
        table = SUBDIVISIONS.get(country, {})
        if area not in table:
            if country in SUBDIVISIONS and area not in SUBDIVISION_SKIP:
                sys.exit(f"WGSRPD area {area} ({row['Level_4_Na']}, {country}) is in "
                         f"neither SUBDIVISIONS nor SUBDIVISION_SKIP")
            continue
        sub, l3 = table[area], row["Level3_cod"]
        held = regions.setdefault(country, {}).setdefault(sub, l3)
        if held != l3:
            sys.exit(f"{country}-{sub} spans {held} and {l3}; it belongs in "
                     f"SUBDIVISION_SKIP, not SUBDIVISIONS")
    for country, extra in SUBDIVISION_EXTRA.items():
        regions[country].update(extra)
    return codes, regions


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
    """plant_name_id -> (native, introduced) TDWG level-3 code sets. Introduced
    ranges become naturalized.json: establishment evidence for the frost demote
    (tea survives Rize winters its EcoCrop hardiness claims kill it), never an
    override of the invasive block."""
    areas = collections.defaultdict(set)
    intro = collections.defaultdict(set)
    for rec in wcvp_rows(zf, "wcvp_distribution.csv"):
        if (rec["plant_name_id"] in ids
                and rec["extinct"] == "0" and rec["location_doubtful"] == "0"):
            (areas if rec["introduced"] == "0" else intro)[rec["plant_name_id"]].add(rec["area_code_l3"])
    return areas, intro


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


def spot_check(resolved, areas, fine):
    """Print the sub-national range of the SPOT_CHECK taxa, and whether it holds up."""
    print("\nspot check (level-3 codes in the sub-national countries):")
    ok = True
    for key, present, absent in SPOT_CHECK:
        pid = resolved.get(key)
        got = sorted(areas.get(pid, frozenset()) & fine) if pid else []
        bad = sorted((present - set(got)) | (absent & set(got)))
        ok &= not bad and bool(got)
        print(f"  {'ok ' if not bad and got else 'FAIL'} {key[0] + ' ' + key[1]:26s} "
              f"{' '.join(got) or '(nothing)'}"
              f"{'   wrong: ' + ' '.join(bad) if bad else ''}")
    return ok


def main():
    fetch(LEVEL4_URL, LEVEL4)
    fetch(WCVP_URL, WCVP_ZIP)
    iso = l3_to_iso(LEVEL4)
    fine, regions = subnational(LEVEL4)
    print(f"WGSRPD: {len(iso)} level-3 regions mapped to ISO codes; "
          f"{len(fine)} of them inside the {len(SUBNATIONAL)} sub-national countries")

    species = json.loads(SPECIES.read_text())
    keys = {s["id"]: binomial(s["sci"]) for s in species}
    wanted = {k for k in keys.values() if k}
    skipped = [s["sci"] for s in species if keys[s["id"]] is None]
    print(f"species.json: {len(species)} taxa -> {len(wanted)} distinct binomials "
          f"({len(skipped)} unusable: {', '.join(skipped)})")

    zf = zipfile.ZipFile(WCVP_ZIP)
    # The spot-check taxa ride along through name resolution and the distribution
    # pass; the ones outside species.json simply never reach an output file.
    extra = {k for k, _, _ in SPOT_CHECK} - wanted
    resolved, notes, how, homonyms = resolve(zf, wanted | extra)
    hit = sum(1 for k in wanted if k in resolved)
    print(f"WCVP names: {hit}/{len(wanted)} binomials resolved  {dict(how)} "
          f"(tallies include {len(extra)} spot-check taxa outside species.json)")
    for key, found, kind in sorted(notes):
        print(f"  {kind:14s} {key[0]} {key[1]} -> {found[0]} {found[1]}")
    if homonyms:
        print(f"  homonyms (>1 accepted species share a binomial, lowest id used): "
              f"{', '.join(f'{g} {e}' for g, e in sorted(homonyms))}")

    areas, intro = native_areas(zf, set(resolved.values()))
    natives, naturalized, fine_natives, no_dist, unmatched = {}, {}, {}, [], []
    for sp in species:
        pid = resolved.get(keys[sp["id"]]) if keys[sp["id"]] else None
        if pid is None:
            unmatched.append(sp["sci"])
            continue
        codes = sorted({c for l3 in areas.get(pid, ()) for c in iso.get(l3, ())})
        if nz := sorted({c for l3 in intro.get(pid, ()) for c in iso.get(l3, ())}):
            naturalized[str(sp["id"])] = nz  # non-empty only: absence means "not recorded"
        # [] = matched in WCVP but no native range recorded (cultigens like
        # Citrus); absent = no WCVP match at all (unknown). The UI shows them
        # differently.
        natives[str(sp["id"])] = codes
        if not codes:
            no_dist.append(sp["sci"])
        # No empty lists here: nothing to say about a species that reaches none of
        # the nine countries, and the country layer already covers it.
        if detail := sorted(areas.get(pid, frozenset()) & fine):
            fine_natives[str(sp["id"])] = detail

    for path, obj in ((OUT, natives), (OUT_NATURALIZED, naturalized), (OUT_L3, fine_natives), (OUT_REGIONS, regions)):
        path.write_text(json.dumps(obj, separators=(",", ":"), sort_keys=True))
    print(f"wrote {OUT_NATURALIZED.relative_to(ROOT)}: {len(naturalized)}/{len(species)} species, "
          f"{OUT_NATURALIZED.stat().st_size / 1024:.0f} KB")

    total = len(species)
    print(f"\nwrote {OUT.relative_to(ROOT)}: {len(natives)}/{total} species "
          f"({100 * len(natives) / total:.1f}%), {OUT.stat().st_size / 1024:.0f} KB")
    print(f"  no WCVP match ({len(unmatched)}): {', '.join(sorted(unmatched))}")
    print(f"  matched, no native range ({len(no_dist)}): {', '.join(sorted(no_dist))}")

    per_country = collections.Counter()
    for detail in fine_natives.values():
        per_country.update({c for l3 in detail for c in iso[l3] if c in SUBNATIONAL})
    print(f"\nwrote {OUT_L3.relative_to(ROOT)}: {len(fine_natives)}/{total} species "
          f"({100 * len(fine_natives) / total:.1f}%), {OUT_L3.stat().st_size / 1024:.0f} KB")
    print("  species with level-3 detail per country: " + ", ".join(
        f"{c} {per_country[c]}" for c in SUBNATIONAL))
    print(f"wrote {OUT_REGIONS.relative_to(ROOT)}: " + ", ".join(
        f"{c} {len(subs)}" for c, subs in sorted(regions.items())) +
        f"  ({', '.join(c for c in SUBNATIONAL if c not in regions)}: no usable "
        f"subdivision bridge, level-3 only)")

    if not spot_check(resolved, areas, fine):
        sys.exit("spot check failed; the level-3 output is wrong")


if __name__ == "__main__":
    main()
