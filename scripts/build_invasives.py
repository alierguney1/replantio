#!/usr/bin/env python3
"""data/invasives.json - onde cada espécie é INVASORA, por país.

A regra do app é dura: espécie registrada como invasora no país analisado
nunca é recomendada. Este script monta a camada de dados dessa regra.

Fontes:
  1. GRIIS (Global Register of Introduced and Invasive Species), publicado
     pelo ISSG no GBIF como Darwin Core Archives, CC-BY. Uma checklist por
     país/território. Só entra quem o próprio GRIIS marca como invasora
     (isInvasive=invasive, ou degreeOfEstablishment invasive/widespread
     invasive). "introduzida"/"naturalizada" sozinha NÃO conta - a maioria
     das exóticas é inofensiva e barrar todas seria ruído.
  2. Instituto Hórus - Base de Dados Nacional de Espécies Exóticas
     Invasoras (bd.institutohorus.org.br), reforço para o Brasil. A base
     inteira é de exóticas invasoras no país, então toda planta de lá
     vira flag BR.

O casamento com data/species.json é por binômio normalizado ("Genus
epithet", sem autores, sem subsp./var.), com uma segunda passada pela
sinonímia da WCVP (mesmo arquivo que scripts/build_natives.py usa): o
catálogo vem do EcoCrop e carrega nomes antigos - Brachiaria decumbens,
Cassia siamea - enquanto o GRIIS usa os atuais - Urochloa decumbens,
Senna siamea. Sem esse passo, braquiária passaria batido no Brasil. Nada
de fuzzy: ou os dois nomes caem no mesmo táxon aceito, ou não casam.

Downloads ficam em /tmp (nada pesado entra no repo). Rodar de novo:
    python3 scripts/build_invasives.py
"""

import csv
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECIES_JSON = os.path.join(ROOT, "data", "species.json")
OUT_JSON = os.path.join(ROOT, "data", "invasives.json")
WCVP_ZIP = os.path.join(ROOT, "data", "wcvp.zip")   # gitignorado, cai do Kew
WCVP_URL = "https://sftp.kew.org/pub/data-repositories/WCVP/wcvp.zip"
CACHE = "/tmp/replantio_invasives"

ISSG_ORG = "cdef28b1-db4e-4c58-aa71-3c5238c2d0b5"  # Invasive Species Specialist Group
GBIF_DATASETS = "https://api.gbif.org/v1/organization/%s/publishedDataset?limit=1000" % ISSG_ORG
HORUS_API = "https://api-bd.institutohorus.org.br/api/Specie/getallwithcommomnames?page=1&pageSize=5000"

UA = {"User-Agent": "Replantio/1.0 (github.com/gdavidss/canopy; invasive-species data build)"}

# o rowType varia de archive pra archive (rs.tdwg.org/dwc/terms/Distribution
# num, rs.gbif.org/terms/1.0/Distribution noutro), então indexamos pelo
# último segmento da URI
DWC = "{http://rs.tdwg.org/dwc/text/}"
TAXON_ROW = "taxon"
PROFILE_ROW = "speciesprofile"
DIST_ROW = "distribution"

# valores que significam "é invasora aqui", vindos de isInvasive
INVASIVE_WORDS = {"invasive", "true", "yes", "y", "1", "invasora"}
# degreeOfEstablishment: só as duas categorias de invasão (D2 e E do Blackburn
# et al.). "established (category C3)" é naturalizada, não entra.
DEGREE_RE = re.compile(r"invasive", re.I)

# marcadores infraespecíficos e sujeira que aparecem no meio do nome
RANK_TOKENS = {"subsp", "ssp", "var", "subvar", "f", "fo", "forma", "cv",
               "convar", "nothosubsp", "nothovar", "sp", "spp", "cf", "aff",
               "×", "x", "agg", "sect", "ser"}


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def fetch(url, dest, timeout=120, tries=3):
    """GET com cache em disco. Devolve o caminho local ou None."""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
            if not body:
                raise ValueError("resposta vazia")
            tmp = dest + ".part"
            with open(tmp, "wb") as f:
                f.write(body)
            os.replace(tmp, dest)
            return dest
        except Exception as e:  # rede é rede: tenta de novo, depois desiste
            if attempt == tries - 1:
                log("  ! falhou %s (%s)" % (url, e))
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


# ---------------------------------------------------------------- nomes

def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


PARENS = re.compile(r"\([^)]*\)")


def binomial(name):
    """'Pinus elliottii Engelm. var. elliottii' -> 'Pinus elliottii'.

    Devolve None quando não dá pra extrair gênero + epíteto (nome só de
    gênero, híbrido, 'sp.'). Sem fuzzy: ou o binômio bate, ou não bate.
    """
    if not name:
        return None
    n = strip_accents(name)
    n = PARENS.sub(" ", n)          # autores entre parênteses
    n = n.replace("×", " × ").replace("×", " × ")
    toks = [t for t in re.split(r"[\s]+", n.strip()) if t]
    if len(toks) < 2:
        return None
    genus = toks[0].strip("×x").strip()
    if not re.fullmatch(r"[A-Z][a-z-]{2,}", genus):
        return None
    for t in toks[1:]:
        low = t.lower().rstrip(".")
        if low in RANK_TOKENS or t in ("×",):
            continue
        if t.endswith("."):         # abreviação de autor ou de rank
            continue
        if re.fullmatch(r"[a-z][a-z-]{2,}", t):
            return genus + " " + t
        # tudo que não é epíteto minúsculo (autor capitalizado, ano) encerra
        break
    return None


def species_binomial(sci):
    """Igual ao acima, mas híbrido declarado ('A x B') não casa com nada."""
    if " x " in sci or " × " in sci:
        return None
    return binomial(sci)


# --------------------------------------------------------------- GRIIS

def dwca_tables(zf):
    """meta.xml -> {rowType: (arquivo, delim, quote, skip, {termo: índice})}."""
    # alguns archives antigos empacotam tudo dentro de uma pasta
    meta_name = next((n for n in zf.namelist()
                      if n == "meta.xml" or n.endswith("/meta.xml")), None)
    if not meta_name:
        return {}
    prefix = meta_name[:-len("meta.xml")]
    try:
        meta = ET.fromstring(zf.read(meta_name))
    except ET.ParseError:
        return {}
    out = {}
    for node in meta:
        tag = node.tag.replace(DWC, "")
        if tag not in ("core", "extension"):
            continue
        loc = node.find(DWC + "files/" + DWC + "location")
        if loc is None or not loc.text:
            continue
        delim = (node.get("fieldsTerminatedBy") or "\\t")
        delim = delim.replace("\\t", "\t").replace("\\n", "\n") or "\t"
        quote = node.get("fieldsEnclosedBy") or ""
        skip = int(node.get("ignoreHeaderLines") or 0)
        idnode = node.find(DWC + "id") if tag == "core" else node.find(DWC + "coreid")
        fields = {"__id__": int(idnode.get("index")) if idnode is not None and idnode.get("index") else 0}
        for f in node.findall(DWC + "field"):
            term = (f.get("term") or "").rsplit("/", 1)[-1]
            if f.get("index") is not None:
                fields[term] = int(f.get("index"))
        row_type = (node.get("rowType") or "").rsplit("/", 1)[-1].lower()
        out[row_type] = (prefix + loc.text.strip(), delim, quote, skip, fields)
    return out


def read_table(zf, spec):
    """Gera dicts {termo: valor} para cada linha da tabela."""
    fname, delim, quote, skip, fields = spec
    try:
        raw = zf.read(fname)
    except KeyError:
        return
    text = raw.decode("utf-8", "replace")
    kw = dict(delimiter=delim)
    if quote:
        kw["quotechar"] = quote
    else:
        kw["quoting"] = csv.QUOTE_NONE
    reader = csv.reader(io.StringIO(text, newline=""), **kw)
    for i, row in enumerate(reader):
        if i < skip or not row:
            continue
        yield {term: (row[idx] if idx < len(row) else "")
               for term, idx in fields.items()}


def cc2(code):
    # GRIIS quirks: 'UK' is not ISO (use GB); 'IC' (Canary Is.) has no
    # country-level ISO home and is dropped deliberately.
    code = {'UK': 'GB'}.get(code, code) if isinstance(code, str) else code
    if code == 'IC':
        return None
    """'US', 'us', 'US-HI', 'ISO_3166-2:BR' -> 'US'/'BR'. Senão None."""
    if not code:
        return None
    c = code.strip().upper()
    c = c.rsplit(":", 1)[-1]          # ISO_3166-2:BR
    m = re.match(r"^([A-Z]{2})(?:-|$)", c)
    return m.group(1) if m else None


def parse_griis(path, title):
    """Devolve {ISO2: {binômio, ...}} das plantas invasoras do archive."""
    try:
        zf = zipfile.ZipFile(path)
    except Exception as e:
        log("  ! zip ruim %s (%s)" % (title, e))
        return {}
    with zf:
        tables = dwca_tables(zf)
        core = tables.get(TAXON_ROW)
        if not core:
            log("  ! sem core Taxon: %s" % title)
            return {}

        # id -> binômio, só Plantae
        taxa, invasive = {}, set()
        for row in read_table(zf, core):
            kingdom = (row.get("kingdom") or "").strip().lower()
            if kingdom and kingdom != "plantae":
                continue            # animais/fungos não interessam ao app
            b = binomial(row.get("scientificName") or row.get("acceptedNameUsage") or "")
            if not b:
                continue
            tid = row.get("__id__", "")
            taxa[tid] = b
            # archive sem extensão às vezes traz o flag no próprio core
            if (row.get("isInvasive") or "").strip().lower() in INVASIVE_WORDS:
                invasive.add(tid)

        if not taxa:
            return {}

        prof = tables.get(PROFILE_ROW)
        if prof:
            for row in read_table(zf, prof):
                if (row.get("isInvasive") or "").strip().lower() in INVASIVE_WORDS:
                    invasive.add(row.get("__id__", ""))

        # país + degreeOfEstablishment
        by_country = defaultdict(set)
        dist = tables.get(DIST_ROW)
        if dist:
            for row in read_table(zf, dist):
                tid = row.get("__id__", "")
                if tid not in taxa:
                    continue
                cc = cc2(row.get("countryCode") or row.get("locationID"))
                if not cc:
                    continue
                if (row.get("occurrenceStatus") or "").strip().lower() in (
                        "absent", "extinct", "excluded"):
                    continue
                # o USRIIS não usa isInvasive: a invasão vem do
                # degreeOfEstablishment (categorias D2 e E de Blackburn et al.)
                if (tid in invasive
                        or DEGREE_RE.search(row.get("degreeOfEstablishment") or "")
                        or (row.get("establishmentMeans") or "").strip().lower() == "invasive"):
                    by_country[cc].add(taxa[tid])
        else:
            # sem extensão Distribution não dá pra saber o país; o título
            # sozinho ("... - Bonaire") não vira ISO2 confiável, então pula
            log("  ~ sem Distribution, ignorado: %s" % title)
        return by_country


def griis_layer():
    """Baixa todas as checklists GRIIS e devolve {ISO2: {binômio}}."""
    meta_path = fetch(GBIF_DATASETS, os.path.join(CACHE, "griis_datasets.json"))
    if not meta_path:
        log("!! não deu pra listar os datasets GRIIS no GBIF")
        return {}, [], 0
    datasets = json.load(open(meta_path, encoding="utf-8"))["results"]
    jobs = []
    for d in datasets:
        url = next((e["url"] for e in d.get("endpoints", [])
                    if e.get("type") == "DWC_ARCHIVE"), None)
        if url:
            jobs.append((d["key"], d.get("title", d["key"]), url))
    log("GRIIS: %d datasets com Darwin Core Archive" % len(jobs))

    def grab(job):
        key, title, url = job
        return job, fetch(url, os.path.join(CACHE, "griis", key + ".zip"))

    got, failed = [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for (job, path) in pool.map(grab, jobs):
            (got if path else failed).append((job, path))
    log("GRIIS: %d baixados, %d falharam" % (len(got), len(failed)))

    by_country = defaultdict(set)
    for (key, title, url), path in got:
        for cc, names in parse_griis(path, title).items():
            by_country[cc] |= names
    return by_country, [t for (_, t, _), _ in failed], len(jobs)


# ---------------------------------------------------------------- Hórus

def horus_layer():
    """Plantas da base nacional do Instituto Hórus -> binômios (Brasil)."""
    path = fetch(HORUS_API, os.path.join(CACHE, "horus_species.json"), timeout=90)
    if not path:
        log("!! Instituto Hórus indisponível - Brasil fica só com GRIIS")
        return set()
    try:
        items = json.load(open(path, encoding="utf-8")).get("items", [])
    except Exception as e:
        log("!! JSON do Hórus ilegível (%s)" % e)
        return set()
    out = set()
    for it in items:
        if (it.get("kingdom") or "").strip().lower() != "plantae":
            continue
        b = binomial(it.get("scientific_name") or "")
        if b:
            out.add(b)
    log("Hórus: %d plantas invasoras no Brasil" % len(out))
    return out


# ----------------------------------------------------------------- WCVP

def wcvp_accepted(binomials):
    """binômio -> id do táxon aceito na WCVP. Dois nomes com o mesmo id são
    o mesmo bicho, e é assim que Brachiaria encontra Urochloa."""
    if not os.path.exists(WCVP_ZIP):
        log("WCVP: baixando o checklist do Kew (~90 MB, só na primeira vez)")
        if not fetch(WCVP_URL, WCVP_ZIP, timeout=900):
            log("!! sem WCVP - o casamento fica só no nome literal")
            return {}
    genera = {b.split()[0] for b in binomials}
    rows = defaultdict(list)
    csv.field_size_limit(1 << 24)
    try:
        with zipfile.ZipFile(WCVP_ZIP) as zf, zf.open("wcvp_names.csv") as f:
            for rec in csv.DictReader(io.TextIOWrapper(f, "utf-8", errors="replace"),
                                      delimiter="|"):
                if rec["genus"] in genera and rec["species"]:
                    rows[rec["genus"] + " " + rec["species"]].append(
                        (rec["taxon_rank"], rec["taxon_status"],
                         rec["plant_name_id"], rec["accepted_plant_name_id"]))
    except Exception as e:
        log("!! WCVP ilegível (%s) - casamento só no nome literal" % e)
        return {}

    out = {}
    for b in binomials:
        rs = rows.get(b)
        if not rs:
            continue
        # a espécie aceita ganha; senão, para onde os sinônimos de mesmo
        # rank apontam; por último os infraespecíficos
        acc = sorted(pid for rank, status, pid, _ in rs
                     if rank == "Species" and status == "Accepted")
        if acc:
            out[b] = acc[0]
            continue
        for ranks in (("Species",), None):
            targets = [a for rank, _, _, a in rs
                       if a and (ranks is None or rank in ranks)]
            if targets:
                out[b] = Counter(targets).most_common(1)[0][0]
                break
    log("WCVP: %d de %d binômios resolvidos a um táxon aceito" % (len(out), len(binomials)))
    return out


# ----------------------------------------------------------------- main

def main():
    species = json.load(open(SPECIES_JSON, encoding="utf-8"))
    index = defaultdict(list)          # binômio -> [ids]
    for s in species:
        b = species_binomial(s["sci"])
        if b:
            index[b].append(str(s["id"]))
    log("species.json: %d espécies, %d binômios indexáveis" % (len(species), len(index)))

    griis, failed, n_datasets = griis_layer()
    horus = horus_layer()
    if horus:
        griis["BR"] |= horus

    # sinonímia: táxon aceito -> ids do catálogo, para os nomes que as fontes
    # escrevem de outro jeito
    source_names = set().union(*griis.values()) if griis else set()
    accepted = wcvp_accepted(set(index) | source_names)
    by_taxon = defaultdict(set)
    for b, ids in index.items():
        if b in accepted:
            by_taxon[accepted[b]].update(ids)

    flags = defaultdict(set)           # id -> {ISO2}
    per_country, via_synonym = {}, set()
    for cc, names in griis.items():
        hits = set()
        for n in names:
            ids = set(index.get(n, ()))
            syn = by_taxon.get(accepted.get(n, ""), set()) - ids
            if syn:
                via_synonym.add(n)
            for sid in ids | syn:
                flags[sid].add(cc)
                hits.add(sid)
        per_country[cc] = len(hits)

    today = time.strftime("%Y-%m-%d")
    out = {
        "_sobre": ("Espécies do catálogo registradas como INVASORAS em cada país "
                   "(ISO 3166-1 alfa-2). Só entra quem a fonte marca como invasora - "
                   "exótica apenas introduzida ou naturalizada não entra. O app usa "
                   "isso para nunca recomendar plantio ecologicamente danoso. "
                   "Casamento por binômio; sinônimos podem faltar, então ausência "
                   "aqui não é atestado de segurança. Chaves com _ são metadados."),
        "_fontes": ("GRIIS - Global Register of Introduced and Invasive Species "
                    "(Invasive Species Specialist Group/IUCN, %d checklists no GBIF, "
                    "CC-BY) + Instituto Hórus, Base de Dados Nacional de Especies "
                    "Exoticas Invasoras (bd.institutohorus.org.br) para o Brasil. "
                    "Sinonímia resolvida pela WCVP (Kew). Compilado em %s por "
                    "scripts/build_invasives.py." % (n_datasets, today)),
    }
    for sid in sorted(flags, key=int):
        out[sid] = sorted(flags[sid])

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
        f.write("\n")

    size = os.path.getsize(OUT_JSON)
    pairs = sum(len(v) for v in flags.values())
    log("\ndata/invasives.json: %d espécies marcadas, %d pares espécie-país, "
        "%d países com pelo menos um flag (de %d checklists), %.1f KB"
        % (len(flags), pairs, sum(1 for n in per_country.values() if n),
           len(per_country), size / 1024))
    for cc in ("BR", "US"):
        log("  %s: %d espécies do catálogo" % (cc, per_country.get(cc, 0)))
    log("  %d nomes só casaram via sinonímia WCVP" % len(via_synonym))
    if failed:
        log("  archives que não baixaram (%d): %s" % (len(failed), "; ".join(failed[:10])))
    return out


if __name__ == "__main__":
    main()
