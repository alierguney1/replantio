#!/usr/bin/env python3
"""Audit data/species.json for synonym duplicates: two catalog entries that are
the same plant under different binomials.

The catalog is stitched from EcoCrop, Carvalho, Orwa and friends, and those
sources do not agree on nomenclature. Acca sellowiana and Feijoa sellowiana
both landed in the base and both surfaced to the user as "goiabeira-serrana".
This finds the rest of that family of mistake by pushing every `sci` through
the Kew WCVP checklist (data/wcvp.zip) and grouping on the accepted taxon id:
two names with the same accepted id are the same plant.

Four rules keep it honest:

  * infraspecific names resolve to THEIR OWN accepted taxon, never to the
    parent species. Pinus caribaea ssp. bahamensis / caribaea / hondurensis
    are three accepted varieties, three ids, three legitimate entries. An
    infraspecific entry only lands with the plain species when WCVP says that
    infraspecific name is a synonym of it.
  * only Accepted, Synonym and Orthographic rows are evidence of identity.
    Illegitimate, Invalid and Misapplied names carry an accepted id too, and
    following it merges plants that are not the same: WCVP hangs the
    illegitimate "Bombacopsis quinata Dugand" off Bombax ceiba, which would
    otherwise read as a duplicate.
  * a name whose synonym rows disagree (Festuca arundinacea points at three
    different accepted taxa depending on the author) is reported, not voted on.
  * anything WCVP cannot place - cultivars ("cv. Nandi"), cultivar groups
    ("Pak Choi"), provenance notes ("island provenances"), ploidy races
    ("(tetraploid)"), hybrid formulas ("A x B"), misspellings - is reported
    instead of being guessed into a group.

Groups are split by what they mean for the catalog. A group of different
binomials at species rank is a straight duplicate. A group that is one crop's
cultivar groups (broccoli, cabbage and kale all sink into Brassica oleracea)
is WCVP lumping, not a catalog bug, and both entries should stay. Read the
`same display name` flag first: that is the symptom the user sees.

Read-only: touches no data file. Exits 1 when a merge candidate exists.

Usage:
    python3 scripts/audit_duplicates.py           # full report
    python3 scripts/audit_duplicates.py --json    # same, machine-readable
    python3 scripts/audit_duplicates.py --quiet   # merge candidates only
"""

import collections
import csv
import difflib
import io
import json
import os
import re
import sys
import unicodedata
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SPECIES_JSON = os.path.join(DATA, "species.json")
WCVP_ZIP = os.path.join(DATA, "wcvp.zip")
WCVP_URL = "https://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip"

# derived files keyed by species id: a removal has to be replayed through
# whatever builds them
DERIVED = [("natives", "natives.json"), ("natives_l3", "natives_l3.json"),
           ("names_pt", "names_pt.json"), ("invasives", "invasives.json"),
           ("natives_geo", "natives_geo.json")]

# the climate envelope - the expensive half of an entry
ENVELOPE = ("temp", "rain", "ph", "ktmp", "ktmpr", "photo", "cycle", "altmax",
            "gclass", "wet")

# WCVP statuses that establish identity. Illegitimate/Invalid/Misapplied names
# also carry an accepted id, but it is not a claim that the two names are the
# same plant, so they only ever count as a hint in the report.
SOLID = {"Accepted", "Artificial Hybrid", "Local Biotype"}   # self-accepted
IDENTITY = {"Synonym", "Orthographic"}                       # point elsewhere

RANK_TOKENS = {"ssp", "subsp", "sp", "var", "subvar", "v", "f", "fo", "forma",
               "form", "nothosubsp", "nothovar", "convar", "cv", "grex", "gr",
               "group", "cultivar", "race", "provenance"}
# ranks that name a botanical infraspecies; cv./grex/group are horticultural
# and never resolve in WCVP
BOTANICAL_RANKS = {"ssp", "subsp", "sp", "var", "subvar", "v", "f", "fo",
                   "forma", "form", "nothosubsp", "nothovar"}

PARENS = re.compile(r"\([^)]*\)")
AUTHOR_IN_PARENS = re.compile(r"^\(\s*[A-Z][^)]*\)$")

# This snapshot of wcvp.zip carries none of the slur-derived epithets: grep it
# for "caffra" and you get nothing, while Sclerocarya caffra Sond. sits there
# as "Sclerocarya afra Sond." and Acacia caffra as "Acacia afra". 300-odd names
# are affected, accepted names and their synonyms alike, so it is a deliberate
# substitution rather than a corrupt download - but note the published IBC 2024
# replacements are affra/affrum/affer, with two f's, and this file uses one.
#
# Either way the catalog still spells them the old way, so those names miss
# silently - here and in build_natives / build_invasives / build_names_pt /
# build_natives_geo. Only tried as a fallback, because Portulacaria afra and
# Artemisia afra are real "afra" names that must keep matching themselves.
SNAPSHOT_EPITHETS = {"caffra": "afra", "caffrum": "afrum", "caffer": "afer"}
# Latin gender and the spelling wobble that comes with hand-typed catalogues:
# moluccana/moluccanus, indica/indicus, orientalis/orientale, burmanni/burmannii
GENDER_TAIL = re.compile(r"(us|um|a|is|e|os|on|or|ii|i)$")


def log(msg):
    sys.stderr.write(msg + "\n")


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def norm(s):
    return re.sub(r"\s+", " ", strip_accents(s).lower()).strip()


def loose(epithet):
    """Epithet -> a key that ignores Latin gender and doubled letters. Only
    used to *suggest* a spelling, never to merge on its own."""
    e = GENDER_TAIL.sub("", norm(epithet)).replace("y", "i")
    e = re.sub(r"([a-z])\1+", r"\1", e)
    return e


# --------------------------------------------------------------- name parsing

class Parsed:
    def __init__(self, genus=None, epithet=None, infra=None, infra_abbrev=False,
                 reason=None, note=None):
        self.genus = genus
        self.epithet = epithet
        self.infra = infra                # infraspecific epithet, rank-agnostic
        self.infra_abbrev = infra_abbrev  # abbreviated, e.g. "var. perei."
        self.reason = reason              # set when we refuse to resolve it
        self.note = note                  # what we dropped, for the report

    @property
    def species_key(self):
        return norm("%s %s" % (self.genus, self.epithet))

    @property
    def infra_key(self):
        return norm("%s %s %s" % (self.genus, self.epithet, self.infra))


def parse_sci(sci):
    """'Pinus caribaea ssp. hondurensis' -> genus / epithet / infraspecies.

    Returns a Parsed with .reason set when the string is not a plain botanical
    name. Those get reported rather than guessed at.
    """
    raw = sci.strip()

    # ", island provenances" / ", mosambicensis type": a seed-lot note bolted
    # onto a species name. Cutting it would merge entries the catalog keeps
    # apart on purpose.
    if "," in raw:
        return Parsed(reason="provenance-note", note=raw.split(",", 1)[1].strip())

    # parentheses: "(L.) Merr." is an author, "(tetraploid)" is a ploidy race
    for m in re.findall(r"\([^)]*\)", raw):
        if not AUTHOR_IN_PARENS.match(m.strip()):
            return Parsed(reason="infraspecific-note", note=m.strip("() "))
    s = PARENS.sub(" ", raw).replace("×", " × ")

    toks = [t for t in re.split(r"\s+", strip_accents(s).strip()) if t]
    if len(toks) < 2:
        return Parsed(reason="genus-only")
    genus = toks[0]
    if not re.fullmatch(r"[A-Z][a-z-]{2,}", genus):
        return Parsed(reason="unparseable-genus")
    rest = toks[1:]

    # "Fragaria x ananassa" is a nothospecies with a real WCVP name;
    # "Annona cherimola x Annona squamosa" is a formula and has none
    hybrid_at = [i for i, t in enumerate(rest) if t in ("x", "X", "×")]
    if hybrid_at:
        if hybrid_at[0] == 0:
            rest = rest[1:]
        else:
            return Parsed(reason="hybrid-formula", note=raw)
    if not rest:
        return Parsed(reason="genus-only")

    epithet = rest[0]
    if not re.fullmatch(r"[a-z][a-z-]{1,}\.?", epithet):
        return Parsed(reason="unparseable-epithet", note=epithet)
    epithet, rest = epithet.rstrip("."), rest[1:]
    if not rest:
        return Parsed(genus, epithet)

    for i, t in enumerate(rest):                 # a rank marker in the tail
        low = t.lower().rstrip(".")
        if low not in RANK_TOKENS:
            continue
        after = rest[i + 1:]
        if not after:
            return Parsed(reason="rank-without-epithet", note=raw)
        if low not in BOTANICAL_RANKS:
            return Parsed(reason="cultivar", note=" ".join([t] + after))
        infra = after[0]
        if not re.fullmatch(r"[a-z][a-z-]{1,}\.?", infra):
            # "var. Br.", "var. Murray": a cultivar or a collector
            return Parsed(reason="cultivar", note=" ".join([t] + after))
        if len(after) > 1 and re.fullmatch(r"[a-z][a-z-]+", after[1]):
            return Parsed(reason="informal-race", note=" ".join(after))
        return Parsed(genus, epithet, infra.rstrip("."),
                      infra_abbrev=infra.endswith("."))

    # no rank marker: trailing authors ("Portulaca quadrifida L.") or a
    # cultivar group ("Brassica rapa Pak Choi")
    if all("." in t for t in rest):
        return Parsed(genus, epithet, note="authors: " + " ".join(rest))
    return Parsed(reason="cultivar", note=" ".join(rest))


# ------------------------------------------------------------------- WCVP

def wcvp_genera():
    """Every genus name in the checklist, so a catalog genus that matches none
    of them ("Stripa" for Stipa) can be reported as the typo it is."""
    csv.field_size_limit(1 << 24)
    out = set()
    with zipfile.ZipFile(WCVP_ZIP) as zf, zf.open("wcvp_names.csv") as f:
        for rec in csv.DictReader(io.TextIOWrapper(f, "utf-8", errors="replace"),
                                  delimiter="|"):
            out.add(norm(rec["genus"]))
    out.discard("")
    return out


def wcvp_rows(genera):
    """wcvp_names.csv rows for the genera the catalog uses, keyed as
    "genus species" and "genus species infraspecies"."""
    if not os.path.exists(WCVP_ZIP):
        sys.exit("missing %s - grab it from %s" % (WCVP_ZIP, WCVP_URL))
    csv.field_size_limit(1 << 24)
    by_species, by_infra = collections.defaultdict(list), collections.defaultdict(list)
    with zipfile.ZipFile(WCVP_ZIP) as zf, zf.open("wcvp_names.csv") as f:
        for rec in csv.DictReader(io.TextIOWrapper(f, "utf-8", errors="replace"),
                                  delimiter="|"):
            if not rec["species"] or norm(rec["genus"]) not in genera:
                continue
            row = (rec["taxon_status"], rec["plant_name_id"],
                   rec["accepted_plant_name_id"], rec["taxon_name"])
            key = norm(rec["genus"] + " " + rec["species"])
            if rec["infraspecies"]:
                by_infra[key + " " + norm(rec["infraspecies"])].append(row)
            else:
                by_species[key].append(row)
    return by_species, by_infra


def wcvp_names_for(ids):
    """id -> (taxon_name, rank, status). A second pass, because an accepted
    name can sit in a genus the catalog never mentions: Brachiaria resolves
    into Urochloa."""
    out = {}
    if not ids:
        return out
    csv.field_size_limit(1 << 24)
    with zipfile.ZipFile(WCVP_ZIP) as zf, zf.open("wcvp_names.csv") as f:
        for rec in csv.DictReader(io.TextIOWrapper(f, "utf-8", errors="replace"),
                                  delimiter="|"):
            if rec["plant_name_id"] in ids:
                out[rec["plant_name_id"]] = (rec["taxon_name"],
                                             rec["taxon_rank"],
                                             rec["taxon_status"])
    return out


def pick_accepted(rows):
    """Rows sharing a name -> (accepted id, why, weak candidates).

    Self-accepted rows win. Otherwise the synonym and orthographic rows have
    to agree unanimously. Everything else is reported: `weak` carries the ids
    that illegitimate/invalid/misapplied rows point at, so the report can show
    what was rejected.
    """
    solid = sorted(pid for status, pid, _, _ in rows if status in SOLID)
    if solid:
        return solid[0], "accepted", []
    targets = {a for status, _, a, _ in rows if status in IDENTITY and a}
    weak = sorted({a for status, _, a, _ in rows
                   if status not in IDENTITY and status not in SOLID and a})
    if len(targets) == 1:
        return targets.pop(), "synonym", weak
    if len(targets) > 1:
        return None, "ambiguous-synonym", sorted(targets)
    return None, ("unreliable-status-only" if weak else "unplaced"), weak


def snapshot_alias(key):
    """The same key with the slur-derived epithets swapped for what this
    snapshot calls them. None when nothing changes."""
    parts = [SNAPSHOT_EPITHETS.get(t, t) for t in key.split()]
    out = " ".join(parts)
    return out if out != key else None


def resolve(p, by_species, by_infra):
    """Parsed -> (accepted id, how, weak candidates). An infraspecific name
    resolves on its own key only; falling back to the parent species would
    collapse exactly the distinctions we are told to keep."""
    if p.infra:
        rows, how = by_infra.get(p.infra_key), "infraspecific"
        if not rows:
            alias = snapshot_alias(p.infra_key)
            if alias and by_infra.get(alias):
                rows, how = by_infra[alias], "infraspecific-snapshot-epithet"
        if not rows and p.infra_abbrev:
            # "var. perei." -> pereirae, but only when the prefix is unique
            hits = [k for k in by_infra if k.startswith(p.infra_key)]
            roots = {pick_accepted(by_infra[k])[0] for k in hits}
            if hits and len(roots) == 1 and None not in roots:
                rows, how = by_infra[hits[0]], "infraspecific-abbrev"
        if not rows:
            return None, "infraspecific-not-in-wcvp", []
    else:
        rows, how = by_species.get(p.species_key), "species"
        if not rows:
            alias = snapshot_alias(p.species_key)
            if alias and by_species.get(alias):
                rows, how = by_species[alias], "species-snapshot-epithet"
        if not rows:
            return None, "species-not-in-wcvp", []
    aid, why, weak = pick_accepted(rows)
    return aid, (how if aid else why), weak


def suggest_spelling(p, by_species, by_infra, genera):
    """A name WCVP does not have -> the name it was probably meant to be.
    Gender-blind key first (moluccana -> moluccanus), then difflib. A genus the
    checklist has never heard of gets corrected first ("Stripa" -> Stipa).
    Suggestions are reported for a human to confirm; nothing merges on one."""
    genus = norm(p.genus)
    if genus not in genera:
        near = difflib.get_close_matches(genus, list(genera), n=2, cutoff=0.9)
        if len(near) != 1:
            return None
        genus = near[0]
    pool = by_infra if p.infra else by_species
    prefix = ("%s %s " % (genus, p.epithet)) if p.infra else (genus + " ")
    tails = {k[len(prefix):]: k for k in pool if k.startswith(prefix)}
    if not tails:
        return "%s %s" % (genus, p.epithet) if genus != norm(p.genus) else None
    target = p.infra if p.infra else p.epithet
    same = [k for tail, k in tails.items() if loose(tail) == loose(target)]
    if len(same) == 1:
        return same[0]
    close = difflib.get_close_matches(norm(target), list(tails), n=2, cutoff=0.88)
    return tails[close[0]] if len(close) == 1 else None


# --------------------------------------------------------------- the catalog

def filled(sp):
    """How much of an entry is populated. False and 0 are real values."""
    return sum(1 for k, v in sp.items()
               if k not in ("id", "sci") and v not in (None, "", [], {}))


def envelope(sp):
    return sum(1 for k in ENVELOPE if sp.get(k) not in (None, "", [], {}))


def load_refs():
    """species id -> derived files that mention it."""
    refs = collections.defaultdict(list)
    for label, fname in DERIVED:
        path = os.path.join(DATA, fname)
        if not os.path.exists(path):
            continue
        for k in json.load(open(path, encoding="utf-8")):
            if not k.startswith("_"):
                refs[str(k)].append(label)
    path = os.path.join(DATA, "sourcing.json")
    if os.path.exists(path):
        for k in json.load(open(path, encoding="utf-8")).get("products", {}):
            refs[str(k)].append("sourcing")
    return refs


def load_pt():
    """species id -> the Portuguese name the app shows. This is where a
    duplicate becomes visible: two rows, one name."""
    path = os.path.join(DATA, "names_pt.json")
    if not os.path.exists(path):
        return {}
    return {str(k): v.get("nome") for k, v in
            json.load(open(path, encoding="utf-8")).items()
            if not k.startswith("_")}


def display_collisions(members, pt):
    """Names two members of a group both show to the user."""
    seen = collections.defaultdict(list)
    for sp, _ in members:
        # dedup per entry: plenty of rows carry the same string in `common` and
        # in names_pt, and that is one entry showing one name, not a collision
        labels = {norm(l) for l in (pt.get(str(sp["id"])), sp.get("common"))
                  if l and norm(l) != norm(sp["sci"])}
        for label in labels:
            seen[label].append(sp["id"])
    return {label: sorted(ids) for label, ids in seen.items() if len(ids) > 1}


# --------------------------------------------------------------- the audit

def base_binomial(sp, parsed):
    p = parsed[str(sp["id"])]
    return p.species_key if p.genus else norm(sp["sci"])


def classify(members, parsed, name, rank):
    """A group of same-taxon entries -> what it means for the catalog.

    merge         different binomials for one taxon: the Acca/Feijoa bug, one
                  entry should go
    infraspecific one binomial, the catalog keeps varieties or cultivar groups
                  WCVP sinks into the species: normally all stay
    lumped        WCVP folded named crops into one hybrid taxon (grapefruit and
                  sweet orange both into Citrus × aurantium): a taxonomic
                  opinion about cultivated plants, not a catalog bug
    """
    bases = {base_binomial(sp, parsed) for sp, _ in members}
    if len(bases) == 1:
        return "infraspecific"
    if "×" in name:
        return "lumped"
    return "merge"


def audit():
    species = json.load(open(SPECIES_JSON, encoding="utf-8"))
    parsed = {str(sp["id"]): parse_sci(sp["sci"]) for sp in species}
    genera = {norm(p.genus) for p in parsed.values() if p.genus}
    log("species.json: %d entries, %d genera" % (len(species), len(genera)))
    known = wcvp_genera()
    # a genus the checklist does not have is a typo; load the genus it was
    # probably meant to be as well, so its names can at least be suggested
    typos = {}
    for g in sorted(genera - known):
        near = difflib.get_close_matches(g, list(known), n=2, cutoff=0.9)
        if len(near) == 1:
            typos[g] = near[0]
    if typos:
        log("genera not in WCVP: %s" % ", ".join("%s -> %s" % kv
                                                 for kv in typos.items()))
    by_species, by_infra = wcvp_rows(genera | set(typos.values()))
    log("WCVP: %d genera, %d species keys, %d infraspecific keys"
        % (len(known), len(by_species), len(by_infra)))

    groups = collections.defaultdict(list)
    unresolved = []
    for sp in species:
        p = parsed[str(sp["id"])]
        if p.reason:
            unresolved.append([sp, p.reason, p.note, [], None])
            continue
        aid, how, weak = resolve(p, by_species, by_infra)
        if aid:
            groups[aid].append((sp, how))
        else:
            hint = None
            if how.endswith("not-in-wcvp"):
                hint = suggest_spelling(p, by_species, by_infra, known)
            unresolved.append([sp, how, p.note, weak, hint])
    log("resolved %d entries to %d taxa; %d unresolved"
        % (sum(len(v) for v in groups.values()), len(groups), len(unresolved)))

    # a name we could not resolve may still collide with one we could: chase
    # the rejected candidates and the suggested spellings
    for u in unresolved:
        cands = set(u[3])
        rows = (by_infra if u[4] and u[4].count(" ") > 1 else by_species).get(u[4] or "")
        if rows:
            aid, _, _ = pick_accepted(rows)
            if aid:
                cands.add(aid)
        u[3] = sorted(cands)

    dupes = {aid: m for aid, m in groups.items() if len(m) > 1}
    suspects = [u for u in unresolved if any(c in groups for c in u[3])]
    names = wcvp_names_for(set(dupes) | {c for u in suspects for c in u[3]})
    return parsed, groups, dupes, suspects, unresolved, names


def keep(members, accepted_name, refs):
    """Which entry to keep: the accepted binomial, then a shop that sells it,
    then the fuller envelope."""
    def score(item):
        sp = item[0]
        return (norm(sp["sci"]) == norm(accepted_name),
                "sourcing" in refs.get(str(sp["id"]), []),
                envelope(sp), filled(sp), -sp["id"])
    return max(members, key=score)[0]["id"]


def report(as_json=False, quiet=False):
    parsed, groups, dupes, suspects, unresolved, names = audit()
    refs, pt = load_refs(), load_pt()

    out = []
    for aid, members in dupes.items():
        name, rank, _ = names.get(aid, ("?", "?", "?"))
        kind = classify(members, parsed, name, rank)
        out.append({
            "accepted_id": aid, "accepted_name": name, "accepted_rank": rank,
            "kind": kind,
            "keep": keep(members, name, refs) if kind == "merge" else None,
            "same_display_name": display_collisions(members, pt),
            "members": [{
                "id": sp["id"], "sci": sp["sci"], "common": sp["common"],
                "pt": pt.get(str(sp["id"])), "matched_as": how,
                "filled": filled(sp), "envelope": envelope(sp),
                "refs": refs.get(str(sp["id"]), []),
            } for sp, how in sorted(members, key=lambda m: m[0]["id"])],
        })
    order = {"merge": 0, "lumped": 1, "infraspecific": 2}
    out.sort(key=lambda g: (order[g["kind"]], g["accepted_name"]))

    sus = [{
        "id": sp["id"], "sci": sp["sci"], "common": sp["common"],
        "reason": why, "suggested": hint,
        "collides_with": [{"accepted_name": names.get(c, ("?",))[0],
                           "entries": [{"id": s["id"], "sci": s["sci"]}
                                       for s, _ in groups.get(c, [])]}
                          for c in cands if c in groups],
    } for sp, why, note, cands, hint in suspects]

    if as_json:
        json.dump({
            "duplicate_groups": out,
            "unresolved_but_colliding": sus,
            "unresolved": [{"id": sp["id"], "sci": sp["sci"], "reason": why,
                            "note": note, "suggested": hint}
                           for sp, why, note, _, hint in unresolved],
        }, sys.stdout, ensure_ascii=False, indent=1)
        sys.stdout.write("\n")
        return sum(1 for g in out if g["kind"] == "merge")

    def show(g):
        print("\n%s  [WCVP %s, %s]" % (g["accepted_name"], g["accepted_id"],
                                       g["accepted_rank"]))
        for m in g["members"]:
            label = m["pt"] or m["common"]
            print("  %-6s %-40s %-24s fields=%-3d env=%-2d %s%s"
                  % (m["id"], m["sci"], (label or "")[:24], m["filled"],
                     m["envelope"], ",".join(m["refs"]) or "-",
                     "   <- keep" if m["id"] == g["keep"] else ""))
        for label, ids in g["same_display_name"].items():
            print("       ! both show as %r: %s"
                  % (label, ", ".join(str(i) for i in ids)))
        if g["keep"] and not any(norm(m["sci"]) == norm(g["accepted_name"])
                                for m in g["members"]):
            print("       > no member carries the accepted binomial: rename the"
                  " kept entry to %r" % g["accepted_name"])
        if g["accepted_rank"] in ("Form", "Variety", "Subspecies"):
            print("       ? accepted taxon is infraspecific: check these are"
                  " not cultivar groups WCVP chose to lump")

    merges = [g for g in out if g["kind"] == "merge"]
    print("\n=== %d MERGE CANDIDATES: one plant, two binomials ===" % len(merges))
    for g in merges:
        show(g)

    if not quiet:
        lump = [g for g in out if g["kind"] == "lumped"]
        print("\n\n=== %d LUMPED BY WCVP: distinct crops folded into one taxon."
              " Keep both unless the display names collide ===" % len(lump))
        for g in lump:
            show(g)

        infra = [g for g in out if g["kind"] == "infraspecific"]
        print("\n\n=== %d INFRASPECIFIC SPLITS: one binomial, the catalog keeps"
              " varieties WCVP sinks into the species ===" % len(infra))
        for g in infra:
            show(g)

        print("\n\n=== %d UNRESOLVED NAMES THAT WOULD COLLIDE once fixed"
              " (needs a human) ===" % len(sus))
        for s in sus:
            print("\n  %-6s %-40s %s" % (s["id"], s["sci"], s["reason"]))
            if s["suggested"]:
                print("       probably meant: %s" % s["suggested"])
            for c in s["collides_with"]:
                print("       -> %s: %s" % (c["accepted_name"],
                                            ", ".join("%s %s" % (e["id"], e["sci"])
                                                      for e in c["entries"])))

        print("\n\n=== %d UNRESOLVED, by reason (never grouped) ===" % len(unresolved))
        for why, n in collections.Counter(u[1] for u in unresolved).most_common():
            print("  %-26s %d" % (why, n))
        for sp, why, note, _, hint in sorted(unresolved, key=lambda u: (u[1], u[0]["sci"])):
            extra = note or ""
            if hint:
                extra = "probably: %s" % hint
            print("  %-26s %-6s %-40s %s" % (why, sp["id"], sp["sci"], extra))

    print("\n%d merge candidates, %d lumped, %d infraspecific splits, "
          "%d unresolved (%d of them colliding)"
          % (len(merges), sum(1 for g in out if g["kind"] == "lumped"),
             sum(1 for g in out if g["kind"] == "infraspecific"),
             len(unresolved), len(sus)))
    return len(merges)


def main():
    n = report(as_json="--json" in sys.argv, quiet="--quiet" in sys.argv)
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
