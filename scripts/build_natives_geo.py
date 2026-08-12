#!/usr/bin/env python3
"""data/natives_geo.json - where a species is native in North America, drawn from
range maps instead of political regions.

  {"<species id>": "<0.5 degree grid, run-length encoded>"}

The country and level-3 layers (scripts/build_natives.py) answer "is it native to
Ontario", which for a province three times the size of France is not an answer.
WCVP records Amelanchier alnifolia -- our catalogue still calls it Aronia
alnifolia -- for all of Ontario, so the app calls the saskatoon native in
Toronto; the nearest ground Little drew it on is 275 km away, up the Ottawa
valley, and the bulk of the range is in the boreal northwest. Little's maps are
polygons, so the same question can be asked of the point the user is standing
on, at roughly 50 km.

Source
  USTreeAtlas  github.com/wpetry/USTreeAtlas, a public-domain clone of the USGS
               digitised "Atlas of United States Trees" (Elbert L. Little, Jr.,
               1971-1977). Little_datatable.csv maps Latin name -> file code;
               geojson/<code>.geojson is one FeatureCollection per species, in
               EPSG:4267 (NAD27) degrees. The NAD27/WGS84 shift is ~100 m, two
               orders of magnitude under the cell, so the coordinates are used
               as WGS84 unchanged. Cite: Little, E.L., Jr. 1971-1977. Atlas of
               United States trees. USDA Misc. Publ. 1146, 1293, 1314, 1361, 1410.

  Features carry CODE 1 (the species is there) and CODE 0 (it is not -- the
  interior gaps Little drew, a few of which are also rings of the CODE 1 polygon
  and a few of which are not). Both are honoured: presence fills, absence
  subtracts.

Matching to data/species.json is by binomial and, failing that, through WCVP
synonymy exactly as scripts/build_invasives.py does it -- our catalogue comes
from EcoCrop and carries pre-transfer names, so Aronia alnifolia only meets
Little's Amelanchier alnifolia after both sides resolve to the same accepted
taxon. A binomial that resolves to more than one accepted taxon is dropped
rather than guessed at: Eugenia aromatica is the clove to EcoCrop and a Florida
myrtle to O.Berg, and this layer exists to stop exactly that kind of range from
being handed to the wrong plant.

What this layer is not: Little mapped trees and large shrubs of North America
only, and mapped them fifty years ago from herbarium sheets and forest surveys.
Absence from the file means "Little drew no map here", never "not native". The
app must keep treating a missing species as unknown and fall back to the country
and level-3 layers.

Downloads are cached in /tmp. Rerun with:
    python3 scripts/build_natives_geo.py
"""
import collections, csv, io, json, math, pathlib, sys, time, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECIES = ROOT / "data" / "species.json"
WCVP_ZIP = ROOT / "data" / "wcvp.zip"
OUT = ROOT / "data" / "natives_geo.json"

CACHE = pathlib.Path("/tmp/replantio_little")
RAW = "https://raw.githubusercontent.com/wpetry/USTreeAtlas/master"
TABLE_URL = RAW + "/Little_datatable.csv"
GEOJSON_URL = RAW + "/geojson/%s.geojson"
WCVP_URL = "https://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip"

UA = {"User-Agent": "Replantio/1.0 (github.com/gdavidss/canopy; native range build)"}

# 0.5 degrees is ~55 km north-south and ~36 km east-west at 49N: fine enough to
# put Winnipeg and Toronto on different sides of a range edge, coarse enough that
# 1970s hand-digitised outlines are not being read for more precision than they
# have. Origin at (0, -180) keeps every row and column a two-digit base-36
# number for the whole of North America, which is what makes the encoding cheap.
CELL = 0.5
LAT0, LNG0 = 0.0, -180.0
BASE, WIDTH = 36, 2
LIMIT = BASE ** WIDTH          # 1296 rows/columns/run lengths, none of them close

# EcoCrop spellings that WCVP has never heard of either, so neither path can
# reach the map. Hand-checked one at a time; a near-match rule in their place
# would pair Platanus orientalis with occidentalis and hand an Old World plane
# tree the native range of an American one.
ALIAS = {
    ("Pinus", "ayachuite"): ("Pinus", "ayacahuite"),   # 'Pinus ayachuite var. Br.'
}

# Maps whose name still stands but whose species concept has been split since
# Little drew them, so the polygon and our catalogue entry are no longer the same
# plant. Name matching cannot see this -- both sides say the same words -- so it
# has to be a hand-checked list, keyed by Little's file code.
CONCEPT_SPLIT = {
    "prosjuli": ("Little's 'Prosopis juliflora' (1976) is the lumped mesquite of "
                 "the US southwest, since split into P. glandulosa and P. velutina; "
                 "P. juliflora now means the neotropical tree our catalogue carries, "
                 "which is not what this polygon covers"),
}

# Infraspecific ranks EcoCrop writes out, so 'Pinus strobus var. chiapensis' can
# be checked against its own accepted taxon instead of riding on P. strobus.
RANKS = {"ssp", "subsp", "var", "subvar", "f", "fo", "forma", "cv", "convar"}

# Printed on every run and enforced: the point of the layer is that these come
# out right, and a silent regression in them looks exactly like a correct build.
# Two of the four taxa are not in the catalogue; they are carried anyway, so the
# self-test keeps working whatever species.json does next.
PROBES = [
    ("Amelanchier alnifolia", "Toronto",   43.62,  -79.51, False),
    ("Amelanchier alnifolia", "Winnipeg",  49.90,  -97.10, True),
    ("Amelanchier alnifolia", "Vancouver", 49.30, -123.10, True),
    ("Acer saccharum",        "Toronto",   43.62,  -79.51, True),
    ("Acer saccharum",        "Calgary",   51.00, -114.10, False),
    ("Pseudotsuga menziesii", "Vancouver", 49.30, -123.10, True),
    ("Pseudotsuga menziesii", "Halifax",   44.60,  -63.60, False),
    ("Sequoia sempervirens",  "Eureka CA", 40.80, -124.20, True),
    ("Sequoia sempervirens",  "Toronto",   43.62,  -79.51, False),
]


# ----------------------------------------------------------------- fetching

def fetch(url, path, timeout=120, tries=3):
    """GET into the cache. Returns the path, or None once the retries are gone."""
    if path.exists() and path.stat().st_size:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
            if not body:
                raise ValueError("empty response")
            tmp = path.with_suffix(path.suffix + ".part")
            tmp.write_bytes(body)
            tmp.rename(path)
            return path
        except Exception as e:
            if attempt == tries - 1:
                print(f"  ! {url} failed ({e})", file=sys.stderr)
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


# -------------------------------------------------------------------- names

def binomial(sci):
    """'Pinus elliottii Engelm. var. elliottii' -> ('Pinus', 'elliottii').

    Same rule as scripts/build_natives.py: authors, infraspecific ranks and the
    hybrid sign go, and a hybrid formula ('Prunus x yedoensis' written out with
    both parents) resolves to nothing, because a cross has no range of its own.
    """
    tokens = sci.replace("×", " ").split()
    for i, t in enumerate(tokens):
        if t == "x" and i + 1 < len(tokens) and tokens[i + 1][:1].isupper():
            return None
    tokens = [t.strip(".,") for t in tokens if t != "x"]
    if len(tokens) < 2 or tokens[1] in ("sp", "spp"):
        return None
    return tokens[0].capitalize(), tokens[1].lower()


class Wcvp(NamedTuple):
    accepted: dict     # (genus, epithet)          -> accepted plant_name_id
    ambiguous: dict    # (genus, epithet)          -> the ids it could mean
    infra: dict        # (genus, epithet, infrasp) -> accepted plant_name_id
    species: dict      # plant_name_id             -> (genus, epithet) it belongs to


def resolve(rows):
    """One name's WCVP records -> (accepted id, every id it could mean).

    The accepted taxon wins; then whatever the same-rank synonyms point at; then
    anything else. Whichever tier answers first has to answer with one taxon: a
    binomial published twice by different authors is two plants, and picking one
    would be a coin toss over which continent's range to hand out.
    """
    tiers = [sorted({pid for rank, status, pid, _ in rows if status == "Accepted"}),
             sorted({a for _, _, _, a in rows if a})]
    for candidates in tiers:
        if candidates:
            return (candidates[0] if len(candidates) == 1 else None), candidates
    return None, []


def trinomial(sci):
    """'Pinus strobus var. chiapensis' -> ('Pinus', 'strobus', 'chiapensis').

    None when there is no infraspecific epithet to check, including the ones
    EcoCrop leaves unfinished ('Pinus ayachuite var. Br.').
    """
    key = binomial(sci)
    if not key:
        return None
    tokens = [t.strip(".,") for t in sci.replace("×", " ").split()]
    for i, token in enumerate(tokens[:-1]):
        if token.lower() in RANKS and tokens[i + 1].islower() and tokens[i + 1].isalpha():
            return key + (tokens[i + 1],)
    return None


def wcvp_index(keys, trinomials):
    """Everything this build needs out of WCVP, in one pass over wcvp_names.csv.

    Two names sharing an accepted id are the same plant, and that is how Aronia
    alnifolia finds Amelanchier alnifolia. `species` exists for the other
    direction: an infraspecific name has to be checked against the species its
    accepted taxon actually sits in, or Pinus strobus var. chiapensis -- a
    Chiapas cloud-forest pine, accepted as P. chiapensis -- inherits the range of
    the white pine of the Great Lakes.

    Only the genera asked about are held; a name transferred to some third genus
    neither list mentions comes back unknown, and the caller keeps the match
    rather than refusing what it cannot check.
    """
    blank = Wcvp({}, {}, {}, {})
    if not WCVP_ZIP.exists():
        print(f"downloading {WCVP_URL} -> {WCVP_ZIP.name} (~85 MB, first run only)")
        if not fetch(WCVP_URL, WCVP_ZIP, timeout=900):
            print("!! no WCVP; matching falls back to the literal binomial",
                  file=sys.stderr)
            return blank
    genera = {g for g, _ in keys} | {g for g, _, _ in trinomials}
    binomials = collections.defaultdict(list)
    infras = collections.defaultdict(list)
    species = {}
    csv.field_size_limit(1 << 24)
    try:
        with zipfile.ZipFile(WCVP_ZIP) as zf, zf.open("wcvp_names.csv") as f:
            for rec in csv.DictReader(io.TextIOWrapper(f, "utf-8", errors="replace"),
                                      delimiter="|"):
                if rec["genus"] not in genera or not rec["species"]:
                    continue
                row = (rec["taxon_rank"], rec["taxon_status"],
                       rec["plant_name_id"], rec["accepted_plant_name_id"])
                species[rec["plant_name_id"]] = (rec["genus"], rec["species"])
                if rec["infraspecies"]:
                    infras[(rec["genus"], rec["species"], rec["infraspecies"])].append(row)
                else:
                    binomials[(rec["genus"], rec["species"])].append(row)
    except Exception as e:
        print(f"!! WCVP unreadable ({e}); literal binomial only", file=sys.stderr)
        return blank

    out, ambiguous = {}, {}
    for key in keys:
        if key not in binomials:
            continue
        pid, candidates = resolve(binomials[key])
        if pid:
            out[key] = pid
        elif candidates:
            ambiguous[key] = candidates
    infra = {}
    for key in trinomials:
        if key in infras:
            pid, _ = resolve(infras[key])
            if pid:
                infra[key] = pid
    return Wcvp(out, ambiguous, infra, species)


# ------------------------------------------------------------- rasterising

def rings_of(geometry):
    """GeoJSON geometry -> [[exterior, hole, hole...], ...], one list per part."""
    kind, coords = geometry.get("type"), geometry.get("coordinates") or []
    if kind == "Polygon":
        return [coords]
    if kind == "MultiPolygon":
        return list(coords)
    return []


def fill(part, out):
    """Add every cell whose centre falls inside one polygon (rings after the first
    are holes, taken out by the even-odd rule).

    A scanline per grid row, with the edges bucketed by the rows they cross, so
    the cost is the number of edge-scanline crossings rather than edges x rows.
    Each part is filled on its own: Little's polygons overlap here and there, and
    even-odd across all of them at once would cancel the overlaps to nothing.
    """
    crossings = collections.defaultdict(list)
    for ring in part:
        for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
            if y0 == y1:
                continue
            lo, hi = (y0, y1) if y0 < y1 else (y1, y0)
            first = math.ceil((lo - LAT0) / CELL - 0.5)
            last = math.floor((hi - LAT0) / CELL - 0.5)
            for row in range(first, last + 1):
                yc = LAT0 + (row + 0.5) * CELL
                if lo <= yc < hi:   # half-open, so a vertex counts once
                    crossings[row].append(x0 + (x1 - x0) * (yc - y0) / (y1 - y0))

    for row, xs in crossings.items():
        xs.sort()
        for xa, xb in zip(xs[0::2], xs[1::2]):
            first = math.ceil((xa - LNG0) / CELL - 0.5)
            last = math.ceil((xb - LNG0) / CELL - 0.5) - 1
            for col in range(first, last + 1):
                out.add((row, col))


def trace(ring, out):
    """Add every cell the ring passes through.

    Interior filling alone loses a polygon narrower than a cell, and Little drew
    plenty of those -- riparian strips, single mountain ranges. Splitting each
    edge at the grid lines it crosses and taking the midpoint of each piece names
    the cells exactly, and costs one cell for the edges that cross nothing, which
    is most of them.
    """
    for (x0, y0), (x1, y1) in zip(ring, ring[1:]):
        dx, dy = x1 - x0, y1 - y0
        cuts = [0.0, 1.0]
        if dx:
            lo, hi = sorted(((x0 - LNG0) / CELL, (x1 - LNG0) / CELL))
            cuts += [((LNG0 + g * CELL) - x0) / dx
                     for g in range(math.floor(lo) + 1, math.floor(hi) + 1)]
        if dy:
            lo, hi = sorted(((y0 - LAT0) / CELL, (y1 - LAT0) / CELL))
            cuts += [((LAT0 + g * CELL) - y0) / dy
                     for g in range(math.floor(lo) + 1, math.floor(hi) + 1)]
        cuts.sort()
        for a, b in zip(cuts, cuts[1:]):
            t = (a + b) / 2
            out.add((math.floor((y0 + dy * t - LAT0) / CELL),
                     math.floor((x0 + dx * t - LNG0) / CELL)))


def rasterise(features):
    """The species' cells: presence interiors and outlines, minus absence
    interiors. Absence outlines are left in -- a gap Little drew is a statement
    about its middle, and shaving a 50 km ring off its rim would eat the range
    around it. Returns (cells, number of parts read)."""
    inside, edge, gaps, parts = set(), set(), set(), 0
    for feature in features:
        present = (feature.get("properties") or {}).get("CODE") != 0
        for part in rings_of(feature.get("geometry") or {}):
            if not part or len(part[0]) < 4:
                continue
            parts += 1
            if present:
                fill(part, inside)
                trace(part[0], edge)
            else:
                fill(part, gaps)
    return ((inside | edge) - gaps), parts


# ---------------------------------------------------------------- encoding

def b36(n):
    if not 0 <= n < LIMIT:
        sys.exit(f"grid index {n} does not fit in {WIDTH} base-{BASE} digits")
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    return digits[n // BASE] + digits[n % BASE]


def encode(cells):
    """cells -> 'RRC0NNC0NN;RRC0NN...' (see _grid in the output for the spec)."""
    by_row = collections.defaultdict(list)
    for row, col in cells:
        by_row[row].append(col)
    chunks = []
    for row in sorted(by_row):
        cols = sorted(by_row[row])
        runs, start, prev = [], cols[0], cols[0]
        for col in cols[1:]:
            if col == prev + 1:
                prev = col
                continue
            runs.append((start, prev - start + 1))
            start = prev = col
        runs.append((start, prev - start + 1))
        chunks.append(b36(row) + "".join(b36(s) + b36(n) for s, n in runs))
    return ";".join(chunks)


def contains(encoded, lat, lng):
    """The Python twin of the decoder the app will carry. Used for the probes, so
    they test the file that ships and not the polygons it came from."""
    row = math.floor((lat - LAT0) / CELL)
    col = math.floor((lng - LNG0) / CELL)
    for chunk in encoded.split(";"):
        if int(chunk[:WIDTH], BASE) != row:
            continue
        for i in range(WIDTH, len(chunk), 2 * WIDTH):
            start = int(chunk[i:i + WIDTH], BASE)
            length = int(chunk[i + WIDTH:i + 2 * WIDTH], BASE)
            if start <= col < start + length:
                return True
        return False
    return False


# -------------------------------------------------------------------- main

GRID_FORMAT = (
    "row = floor((lat - lat0) / cell), col = floor((lng - lng0) / cell). O valor "
    "de cada especie e uma string: linhas separadas por ';', em ordem crescente "
    "de row. Cada linha e o row em 2 digitos base 36 seguido de N corridas de 4 "
    "digitos - col inicial em 2 digitos base 36, comprimento em 2 digitos base 36 "
    "- em ordem crescente de col. A celula e nativa quando existe uma linha com "
    "aquele row e nela uma corrida com col_inicial <= col < col_inicial + "
    "comprimento; row ausente significa fora da area. Digitos base 36 sao "
    "0-9a-z, minusculos (parseInt(s, 36) em JS)."
)


def main():
    table = fetch(TABLE_URL, CACHE / "Little_datatable.csv")
    if not table:
        sys.exit("Little_datatable.csv did not download; nothing to build")
    little, dropped = {}, []
    for rec in csv.DictReader(table.open(encoding="utf-8-sig")):
        key = binomial(rec["Latin Name"].strip())
        code = (rec.get("SHP/*") or "").strip().lower()
        if not key or not code:
            continue
        if code in CONCEPT_SPLIT:
            dropped.append((key, code))
            continue
        little.setdefault(key, code)
    print(f"Little: {len(little)} species with a digitised map")
    for key, code in dropped:
        print(f"  dropped  {key[0]} {key[1]} ({code}): {CONCEPT_SPLIT[code]}")

    species = json.loads(SPECIES.read_text())
    keys = {s["id"]: binomial(s["sci"]) for s in species}
    infra_keys = {s["id"]: trinomial(s["sci"]) for s in species}
    ours = collections.defaultdict(list)
    for s in species:
        if keys[s["id"]]:
            ours[keys[s["id"]]].append(s["id"])
    print(f"species.json: {len(species)} taxa -> {len(ours)} distinct binomials, "
          f"{sum(1 for v in infra_keys.values() if v)} of them infraspecific")

    wcvp = wcvp_index(set(ours) | set(little) | set(ALIAS.values()),
                      {v for v in infra_keys.values() if v})
    accepted, ambiguous = wcvp.accepted, wcvp.ambiguous
    by_taxon = {}
    for key, code in little.items():          # accepted taxon -> Little map
        if key in accepted:
            by_taxon.setdefault(accepted[key], (key, code))
    print(f"WCVP: {sum(1 for k in ours if k in accepted)}/{len(ours)} of our "
          f"binomials and {sum(1 for k in little if k in accepted)}/{len(little)} "
          f"of Little's resolve to a single accepted taxon")

    # our binomial -> (Little binomial, file code), direct spelling first
    matched, how = {}, collections.Counter()
    for key in ours:
        look = ALIAS.get(key, key)
        if look in little:
            matched[key] = (look, little[look])
            how["alias" if look != key else "direct"] += 1
        elif accepted.get(look) in by_taxon:
            matched[key] = by_taxon[accepted[look]]
            how["synonym"] += 1
    print(f"matched {len(matched)} of our binomials to a Little map ("
          + ", ".join(f"{n} {kind}" for kind, n in sorted(how.items())) + ")")
    for key in sorted(k for k, v in matched.items() if k != v[0]):
        print(f"  {'alias  ' if key in ALIAS else 'synonym'} "
              f"{key[0]} {key[1]} -> {matched[key][0][0]} {matched[key][0][1]}")

    # A homonym only matters here when one of its readings owns a Little map:
    # that is the match being refused, and it is worth naming.
    refused = sorted(k for k, cands in ambiguous.items()
                     if k in ours and any(c in by_taxon for c in cands))
    for key in refused:
        maps = sorted(" ".join(by_taxon[c][0]) for c in ambiguous[key] if c in by_taxon)
        print(f"  ambiguous {key[0]} {key[1]}: {len(ambiguous[key])} accepted taxa "
              f"share the name, one of them {' / '.join(maps)} - left unmatched")

    # probe taxa ride along so the self-test runs even if the catalogue drops one
    wanted = {code for _, code in matched.values()}
    probe_codes = {}
    for name, _, _, _, _ in PROBES:
        key = binomial(name)
        found = little.get(key) or (by_taxon.get(accepted.get(key), (None, None))[1])
        probe_codes[name] = found
        if found:
            wanted.add(found)

    def grab(code):
        return code, fetch(GEOJSON_URL % code, CACHE / f"{code}.geojson")

    print(f"downloading {len(wanted)} range maps (cached in {CACHE})")
    with ThreadPoolExecutor(max_workers=8) as pool:
        paths = dict(pool.map(grab, sorted(wanted)))
    missing = sorted(c for c, p in paths.items() if not p)

    ranges, degenerate, empty = {}, [], []
    for code in sorted(wanted):
        if not paths[code]:
            continue
        try:
            data = json.loads(paths[code].read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            print(f"  ! {code}.geojson unreadable ({e})", file=sys.stderr)
            missing.append(code)
            continue
        cells, parts = rasterise(data.get("features") or [])
        if not cells:
            empty.append(code)
            continue
        ranges[code] = cells
        if len(cells) <= 2 or parts == 0:
            degenerate.append((code, len(cells), parts))

    entries, written, transferred = {}, set(), []
    for sid in sorted((sid for key in matched for sid in ours[key]), key=int):
        little_key, code = matched[keys[sid]]
        if code not in ranges:
            continue
        # An infraspecific name inherits the species' map only while it is still
        # in that species. Both sides are compared as the species their accepted
        # taxon sits in, so Pinus michoacana var. cornuta still matches Little's
        # Pinus michoacana (both are Pinus devoniana today) while Pinus strobus
        # var. chiapensis no longer matches his Pinus strobus.
        mine = wcvp.species.get(wcvp.infra.get(infra_keys[sid]))
        theirs = wcvp.species.get(accepted.get(little_key))
        if mine and theirs and mine != theirs:
            transferred.append((sid, mine, theirs))
            continue
        entries[str(sid)] = encode(ranges[code])
        written.add(code)

    if not entries:
        sys.exit("no species matched a usable Little map; refusing to write an "
                 "empty layer over the old one")
    shown = [c for code in written for c in ranges[code]]
    out = {
        "_sobre": (
            "Onde cada especie e nativa na America do Norte, por celula de 0,5 grau "
            "(~50 km), tirada dos mapas de distribuicao de Elbert L. Little Jr. "
            "(USGS, Atlas of United States Trees, 1971-1977). Serve para responder "
            "no ponto: a WCVP diz que a saskatoon e nativa de Ontario inteiro, os "
            "poligonos do Little poem o ponto mais proximo de Toronto a 275 km "
            "dali. Little mapeou arvores e arbustos grandes da America do Norte, "
            "e mapeou ha "
            "cinquenta anos: especie ausente daqui significa 'sem mapa', nunca "
            "'nao e nativa' - sem mapa, vale a camada de pais/regiao. Chaves com _ "
            "sao metadados."),
        "_fonte": (
            "Little, E.L., Jr. 1971-1977. Atlas of United States trees. USDA Misc. "
            "Publ. 1146, 1293, 1314, 1361, 1410. Poligonos digitalizados pelo USGS, "
            "dominio publico, via github.com/wpetry/USTreeAtlas (EPSG:4267/NAD27, "
            "usado como WGS84: a diferenca e de ~100 m, contra celulas de ~50 km). "
            "Sinonimia resolvida pela WCVP (Kew). Compilado em %s por "
            "scripts/build_natives_geo.py." % time.strftime("%Y-%m-%d")),
        "_grid": {
            "cell": CELL,
            "lat0": LAT0,
            "lng0": LNG0,
            "base": BASE,
            "digitos": WIDTH,
            "formato": GRID_FORMAT,
            "cobertura": ("celulas cujo centro cai dentro de um poligono de "
                          "presenca (CODE 1) mais as celulas tocadas pelo contorno "
                          "dele, menos as celulas cujo centro cai dentro de um "
                          "poligono de ausencia (CODE 0)"),
        },
        # The extent of what is in the file, so the app can tell "outside the
        # maps" from "inside them and not native" -- the first is a question for
        # the country layer, the second is an answer.
        "_dominio": {
            "lat": [LAT0 + min(r for r, _ in shown) * CELL,
                    LAT0 + (max(r for r, _ in shown) + 1) * CELL],
            "lng": [LNG0 + min(c for _, c in shown) * CELL,
                    LNG0 + (max(c for _, c in shown) + 1) * CELL],
            "sobre": ("Retangulo que cobre tudo o que existe neste arquivo. "
                      "Little so mapeou a America do Norte, entao um ponto fora "
                      "daqui nao tem resposta nesta camada, mesmo para uma "
                      "especie que esta aqui: a Dodonaea viscosa e nativa da "
                      "Australia e o mapa dela aqui e so a parte americana. Fora "
                      "do retangulo, vale a camada de pais/regiao. Dentro dele o "
                      "retangulo nao basta sozinho - e um retangulo, nao um "
                      "litoral."),
        },
    }
    metadata = len(out)
    out.update(entries)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
    size = OUT.stat().st_size
    print(f"\nwrote {OUT.relative_to(ROOT)}: {len(out) - metadata} species ids, "
          f"{len(written)} distinct maps, "
          f"{sum(len(ranges[c]) for c in written)} cells, {size / 1024:.0f} KB")
    for sid, mine, theirs in transferred:
        print(f"  not written: {sid} is {mine[0]} {mine[1]} today, and Little's "
              f"map is {theirs[0]} {theirs[1]}")
    if missing:
        print(f"  maps that did not download ({len(missing)}): {', '.join(missing)}")
    if empty:
        print(f"  maps that rasterised to nothing ({len(empty)}): {', '.join(empty)}")
    if degenerate:
        print("  maps small enough to be worth an eye: " + ", ".join(
            f"{c} ({n} cell{'s' if n != 1 else ''}, {p} parts)"
            for c, n, p in degenerate))
    if size > 300 * 1024:
        sys.exit(f"{size / 1024:.0f} KB is over the 300 KB budget for this layer")

    print("\nprobes (decoded from the encoding, not from the polygons):")
    ok = True
    for name, place, lat, lng, expect in PROBES:
        code = probe_codes.get(name)
        got = bool(code and code in ranges and contains(encode(ranges[code]), lat, lng))
        ok &= got == expect
        print(f"  {'ok  ' if got == expect else 'FAIL'} {name:24s} {place:10s} "
              f"{lat:6.2f},{lng:8.2f}  {'in ' if got else 'out'} "
              f"(expected {'in' if expect else 'out'})")
    if not ok:
        sys.exit("probe failed; the encoded ranges are wrong")


if __name__ == "__main__":
    main()
