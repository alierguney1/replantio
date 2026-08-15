#!/usr/bin/env python3
"""Build data/names_pt.json: the Portuguese common name of each species.json taxon.

Two sources, in this order:

  FFB   https://ipt.jbrj.gov.br/jbrj/archive.do?r=lista_especies_flora_brasil
        Flora e Funga do Brasil, the Darwin Core archive published by the Jardim
        Botanico do Rio de Janeiro (extracted 2026-08-01). taxon.txt is the
        accepted-name backbone plus every synonym; vernacularname.txt carries
        18,956 vernacular records, 17,194 of them tagged PORTUGUES, each bound to
        a taxonID and often to a locality. CC BY 4.0. Cite: Flora e Funga do
        Brasil. Jardim Botanico do Rio de Janeiro. https://floradobrasil.jbrj.gov.br
        The archive is ~20 MB and is NOT kept in the repo -- it caches in
        /tmp/replantio-ffb/ and re-downloads if that is gone.

  CURATED  the table at the bottom of this file. FFB only covers plants recorded
        in Brazil, and most of the EcoCrop base is imported crops; it also picks
        an arbitrary one of the names it records, so 'curi' comes out ahead of
        'pinheiro-do-parana' for Araucaria angustifolia. Every line in CURATED is
        a name written by hand and overrides FFB. Keyed by the `sci` string
        exactly as species.json spells it, which is EcoCrop's decades-old
        spelling: Tabebuia serratifolia, not Handroanthus serratifolius.

Output is {"<species id>": {"nome": "ipe-amarelo", "aka": ["pau-d'arco"]}}. A
species with no confident name is left out entirely, and the app falls back to
the binomial -- absent means "we do not know", never a guess and never the
English trade name that species.json's `common` field holds.

Run:  python3 scripts/build_names_pt.py
"""
import collections, csv, itertools, json, pathlib, re, sys, unicodedata, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECIES = ROOT / "data" / "species.json"
OUT = ROOT / "data" / "names_pt.json"

CACHE = pathlib.Path("/tmp/replantio-ffb")
FFB_URL = "https://ipt.jbrj.gov.br/jbrj/archive.do?r=lista_especies_flora_brasil"

# Ranks that name a plant a user could plant. GENERO and up are too coarse to
# carry a species name; the infraspecific ranks do carry one, but a subspecies
# name attached to the species is a weaker claim -- 'teosinte' is recorded for
# Zea mays subsp. mexicana and is not what a Brazilian calls Zea mays.
RANK_WEIGHT = {"ESPECIE": 1.0, "SUB_ESPECIE": 0.55, "VARIEDADE": 0.55, "FORMA": 0.5}

# locality values that mean "the whole country" rather than one state
NATIONWIDE = {"brasil", "brazil", "brasil-todo", "todo-o-brasil"}

APOSTROPHES = str.maketrans({"`": "'", "’": "'", "´": "'", "‘": "'",
                             "“": "", "”": "", '"': ""})

# Latin inflections. Only consulted when a candidate is a single word spelled
# character for character like the genus or the epithet, which is the one case
# where FFB has handed back the scientific name instead of a common one. A
# Brazilian says 'acacia' with an accent and 'jauari' with none, so the accents
# and the ending together separate 'acácia' and 'jauari' (keep) from 'guajava'
# (drop). Latinised genus names that Brazilians really do use as words --
# casuarina, melaleuca, macadâmia -- survive this and should.
LATIN_ENDING = re.compile(r"(us|um|is|ae|ii|a|ana|ata|ica|ina|osa|oides|"
                          r"ensis|ense|folia|folius|florus|flora)$")


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def normalise(name):
    """'Angelim  preto' -> 'angelim-preto'. None if the string is not a name.

    Brazilian vernacular plant names are conventionally hyphenated, and FFB is
    already 99% hyphenated, so the space cases are typing slips, not real
    orthography. Rejects the handful of rows that hold a collector citation, a
    digit, or two spellings joined by a slash ('cumixa/cumicha') -- 8 rows.
    """
    s = name.translate(APOSTROPHES).strip().lower()
    s = re.sub(r"\s*\([^)]*\)", "", s)
    if "/" in s or re.search(r"\d", s):
        return None
    s = re.sub(r"[\s–—_]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s if re.fullmatch(r"[a-zà-ÿ'\-]{3,}", s) else None


def is_latin(name, key):
    """True if this 'common name' is really the scientific name.

    Two shapes show up in FFB: the whole binomial respelled ('sesbania-
    grandiflora', 'cordia-africana'), and the bare epithet left in place of a
    name ('guajava'). Everything else is treated as Portuguese, because the
    Portuguese name for an imported tree very often is its Latinised genus and
    dropping those would cost more real names than it saves.
    """
    genus, epithet = strip_accents(key[0]), strip_accents(key[1])
    words = strip_accents(name).split("-")
    if genus in words and epithet in words:
        return True
    return name in (key[0], key[1]) and bool(LATIN_ENDING.search(name))


def fetch_ffb():
    CACHE.mkdir(parents=True, exist_ok=True)
    taxon, vern = CACHE / "taxon.txt", CACHE / "vernacularname.txt"
    if not (taxon.exists() and vern.exists()):
        zpath = CACHE / "ffb.zip"
        if not zpath.exists():
            print("downloading Flora e Funga do Brasil (~20 MB)...", file=sys.stderr)
            urllib.request.urlretrieve(FFB_URL, zpath)
        with zipfile.ZipFile(zpath) as z:
            z.extract("taxon.txt", CACHE)
            z.extract("vernacularname.txt", CACHE)
    return taxon, vern


def read_tsv(path):
    # quoting=QUOTE_NONE: authorship strings carry unbalanced quotes
    with open(path, encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)


def load_ffb():
    taxon_path, vern_path = fetch_ffb()
    taxon = {r["id"]: r for r in read_tsv(taxon_path)}

    synonyms = collections.defaultdict(set)   # accepted id -> ids sunk into it
    for tid, r in taxon.items():
        a = r["acceptedNameUsageID"]
        if a and a != tid and a in taxon:
            synonyms[a].add(tid)

    vern = collections.defaultdict(list)
    english = collections.Counter()
    portuguese = collections.Counter()
    for i, r in enumerate(read_tsv(vern_path)):
        words = re.split(r"[\s\-]+", r["vernacularName"].lower())
        if r["language"] == "PORTUGUES":
            r["order"] = i
            vern[r["id"]].append(r)
            portuguese.update(words)
        elif r["language"] == "INGLES":
            english.update(words)

    # FFB files some plainly English names under PORTUGUES ('arabian-coffee' on
    # Coffea arabica). A word that recurs in its English rows and barely shows up
    # in its Portuguese ones is a reliable tell, and the archive supplies the
    # list: at pt <= 3 the only real Portuguese word caught is 'timor'.
    stop_words = {w for w, c in english.items()
                  if c >= 2 and portuguese[w] <= 3 and len(w) >= 3}

    index = collections.defaultdict(set)      # (genus, epithet) -> taxon ids
    for tid, r in taxon.items():
        if r["kingdom"] != "Plantae" or r["taxonRank"] not in RANK_WEIGHT:
            continue
        g, e = r["genus"].strip().lower(), r["specificEpithet"].strip().lower()
        if g and e and g != "na":
            index[(g, e)].add(tid)

    return taxon, synonyms, vern, index, stop_words


def binomial(sci):
    """'Zea mays ssp. mays' -> ('zea', 'mays'). Names are matched at species
    rank: a Brazilian calls Brassica oleracea var. acephala 'couve' whether or
    not the label says var. acephala."""
    s = re.sub(r"\s*(subsp\.|ssp\.|var\.|f\.)\s+\S+", "", sci)
    s = s.replace("×", "").replace(" x ", " ")
    parts = s.split()
    if len(parts) < 2 or parts[1].lower() in ("sp.", "spp."):
        return None
    return (parts[0].lower(), parts[1].lower().rstrip("."))


def ffb_names(sp, taxon, synonyms, vern, index, stop_words):
    """Portuguese names FFB records for this species, best first.

    FFB records one row per name per taxon, so there is no usage frequency to
    rank by; the only signals in the archive are which record the name hangs off
    (the species itself beats a variety of it, and beats a name inherited
    through a synonym), whether the locality says the whole country, and the
    order the compilers listed them in. Good enough to pick a real name, not
    good enough to always pick the famous one -- that is what CURATED is for.
    """
    key = binomial(sp["sci"])
    if not key:
        return []
    weights = {tid: 1.0 for tid in index.get(key, ())}
    for tid in list(weights):                        # synonym -> accepted name
        accepted = taxon[tid]["acceptedNameUsageID"]
        if accepted in taxon:
            weights.setdefault(accepted, 0.9)
    for tid in list(weights):                        # accepted name -> synonyms
        if taxon[tid]["taxonomicStatus"] == "NOME_ACEITO":
            for s in synonyms.get(tid, ()):
                weights.setdefault(s, 0.6)

    genus, epithet = strip_accents(key[0]), strip_accents(key[1])
    scored = {}
    for tid, weight in weights.items():
        weight *= RANK_WEIGHT.get(taxon[tid]["taxonRank"], 0.5)
        for row in vern.get(tid, []):
            name = normalise(row["vernacularName"])
            if not name or is_latin(name, key) or set(strip_accents(name).split("-")) & stop_words:
                continue
            score = 40 * weight
            if strip_accents(row["locality"].strip().lower()) in NATIONWIDE:
                score += 12
            score -= 2 * name.count("-")             # 'aroeira' over 'aroeira-da-praia'
            score -= 0.001 * row["order"]
            scored[name] = max(scored.get(name, -1e9), score)

    # FFB spells the same name both ways ('ipe-roxo' and 'ipe-roxo' with the
    # circumflex) on one plant often enough to matter. Same name, so keep the
    # spelling that carries the accents.
    merged = {}
    for name in sorted(scored, key=lambda n: -scored[n]):
        bare = strip_accents(name)
        if bare in merged:
            kept = merged[bare]
            if sum(c != strip_accents(c) for c in name) > sum(c != strip_accents(c) for c in kept):
                merged[bare] = name
        else:
            merged[bare] = name
    order = {n: i for i, n in enumerate(sorted(scored, key=lambda n: -scored[n]))}
    return sorted(merged.values(), key=lambda n: order[n])


def main():
    species = json.load(open(SPECIES, encoding="utf-8"))
    taxon, synonyms, vern, index, stop_words = load_ffb()

    unknown = sorted(set(CURATED) - {s["sci"] for s in species})
    if unknown:
        sys.exit("CURATED keys absent from species.json: " + ", ".join(unknown))
    for sci, name in sorted(CURATED.items()):
        # only the binomial shape: 'casuarina' is a hand-written line and is
        # what a Brazilian says, so the bare-Latin-word rule does not apply
        key = binomial(sci)
        words = strip_accents(name.split("|")[0]).split("-")
        if key and all(strip_accents(w) in words for w in key):
            sys.exit(f"CURATED name for {sci} is the scientific name: {name}")

    out = {}
    counts = collections.Counter()
    for sp in species:
        if sp["sci"] in DROP:
            continue
        names = [n for n in ffb_names(sp, taxon, synonyms, vern, index, stop_words)
                 if n not in FOREIGN]
        curated = CURATED.get(sp["sci"])
        if curated:
            counts["hand"] += 1
            nome, *rest = curated.split("|")
            # a bare line inherits FFB's alternates, which are real records; a
            # line with any '|' is the whole answer, so a trailing '|' means
            # "this name and nothing else" for the species where FFB's other
            # records name a different plant (boldo for Vernonia amygdalina)
            aka = [a for a in rest if a] if rest else [n for n in names if n != nome]
        elif names:
            counts["ffb"] += 1
            nome, aka = names[0], names[1:]
        elif GENUS_NAME.get(sp["sci"].split()[0]):
            counts["genus"] += 1
            nome, aka = GENUS_NAME[sp["sci"].split()[0]], []
        else:
            continue
        entry = {"nome": nome}
        aka = [a for a in aka if a not in FOREIGN][:3]
        if aka:
            entry["aka"] = aka
        out[str(sp["id"])] = entry

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, sort_keys=True,
                  separators=(",", ":"))
        f.write("\n")
    print(f"{len(out)} of {len(species)} species named: {counts['hand']} hand-written, "
          f"{counts['ffb']} from FFB, {counts['genus']} named for their genus. "
          f"{OUT.stat().st_size // 1024} KB", file=sys.stderr)


# A handful of rows FFB tags PORTUGUES that are plainly not, and that the
# derived stop-word list misses because each word occurs exactly once.
FOREIGN = {
    "lettuce", "lechuga", "laitue", "lattuga", "starfruit", "grosella-roja",
    "redcurrant", "caballo", "tampala", "chili-chili", "kikuyo", "durian",
    "paraseriante", "papaya", "mango", "kaki", "kiwi-ouro", "blimbing",
    "velvet-tamarind", "dogwood", "palo-hediondo", "tocorito", "chirivia",
    "caimitillo", "whitania", "erythrina-do-alto", "kudsú-tropical", "mirtilo-highbush",
    "falsa",            # FFB's whole record for Grewia asiatica; means nothing alone
}

# Where the Portuguese name is a genus name and every species in the genus
# answers to it. Used only when FFB has nothing, so it never displaces a real
# species-level record: a Brazilian calls Eucalyptus dundasii a eucalipto, and
# 'eucalipto' over the binomial is the whole point of this file.
GENUS_NAME = {
    "Abies": "abeto", "Acacia": "acácia", "Agave": "agave", "Albizia": "albízia",
    "Aloe": "babosa", "Amaranthus": "caruru", "Arachis": "amendoim",
    "Bambusa": "bambu", "Brachiaria": "braquiária", "Casuarina": "casuarina",
    "Corymbia": "eucalipto", "Crotalaria": "crotalária", "Cupressus": "cipreste",
    "Dendrocalamus": "bambu", "Dioscorea": "cará", "Eucalyptus": "eucalipto",
    "Ficus": "figueira", "Fragaria": "morango", "Juglans": "nogueira",
    "Leucaena": "leucena", "Melaleuca": "melaleuca", "Mentha": "hortelã",
    "Musa": "banana", "Ocimum": "manjericão", "Phyllostachys": "bambu",
    "Picea": "pícea", "Pinus": "pinheiro", "Populus": "álamo",
    "Quercus": "carvalho", "Ribes": "groselha", "Rubus": "amora-preta",
    "Salix": "salgueiro", "Sesbania": "sesbânia", "Stylosanthes": "estilosantes",
    "Thymus": "tomilho", "Toona": "cedro-australiano", "Trifolium": "trevo",
    "Urochloa": "braquiária", "Vaccinium": "mirtilo", "Vicia": "ervilhaca",
}

# Names written by hand, `sci` exactly as species.json spells it -> the name,
# then any alternates, pipe-separated; a line with no alternates keeps FFB's.
# These override FFB. Rules followed: a name only goes in if it is the name a
# Brazilian would use for that species (not a translation, not a
# transliteration); where a species has a fruit name and a tree name and both
# are current, the one people say goes first and the other into aka; when the
# species-level name was not certain, the line was left out and the app falls
# back to the binomial.
CURATED = {
    # verification-pass corrections (2026-08-11): wrong-species names caught by QA
    "Psidium friedrichsthalianum": "araçá-da-costa-rica|goiaba-da-costa-rica",
    "Vaccinium macrocarpon": "cranberry|oxicoco",
    "Canna edulis": "biri|achira",
    "Satureja montana": "segurelha-de-inverno",
    "Chenopodium quinoa": "quinoa|quinua|espinafre-do-peru",
    "Theobroma bicolor": "cacau-do-peru|cacau-branco",
    "Cymbopogon martini var. motia": "palmarosa",
    "Cymbopogon martini var. sofia": "palmarosa",
    # --- Brazilian natives: FFB has a name but not the one people use --------
    "Acrocomia aculeata": "macaúba|mucajá|bocaiúva|coco-babão",
    "Aiphanes aculeata": "pupunha-brava|chica-chica",       # not Bactris, do not call it pupunha
    "Anacardium occidentale": "cajueiro|caju|castanha-de-caju",
    "Araucaria angustifolia": "araucária|pinheiro-do-paraná|pinheiro-brasileiro",
    "Attalea funifera": "piaçava|piaçaba",
    "Bertholletia excelsa": "castanha-do-pará|castanheira|castanha-do-brasil",
    "Calophyllum brasiliense": "guanandi|jacareúba|landim",
    "Ceiba pentandra": "sumaúma|samaúma",
    "Conocarpus erectus": "mangue-de-botão|amora-do-mar",    # mangue-negro is Avicennia
    "Erythrina poeppigiana": "eritrina",        # FFB spells it 'erythrina-do-alto'
    "Eugenia uniflora": "pitanga|pitangueira",
    "Euterpe edulis": "juçara|palmito-juçara|içara",
    "Ilex paraguariensis": "erva-mate|mate|congonha",
    "Inga edulis": "ingá-cipó|ingá-de-metro|ingá-doce",
    "Jatropha curcas": "pinhão-manso|pião-branco",
    "Laguncularia racemosa": "mangue-branco|tinteiro",
    "Mimosa scabrella": "bracatinga|bracaatinga",
    "Myroxylon balsamum": "bálsamo|cabreúva",
    "Myroxylon balsamum var. perei.": "bálsamo|cabreúva",
    "Ochroma pyramidale": "pau-de-balsa|pau-balsa",
    "Attalea speciosa": "babaçu|coco-babaçu",
    "Parkinsonia aculeata": "turco|cina-cina|espinho-de-turco",
    "Phytolacca dioica": "bela-sombra|umbu|maria-mole",
    "Terminalia catappa": "amendoeira-da-praia|castanhola|chapéu-de-sol",
    "Psidium friedrichsthalianum": "araçá|",     # FFB says araçá-boi, which is Eugenia stipitata
    "Senna spectabilis": "canafístula|",
    "Spondias cytherea": "cajá-manga|cajarana|cajá-açu",
    "Spondias mombin": "cajá|taperebá|cajá-mirim",
    "Tabebuia serratifolia": "ipê-amarelo|pau-d'arco-amarelo",
    "Vernonia amygdalina": "boldo-africano|",    # boldo alone is Plectranthus

    # --- Brazilian natives FFB records no name for ---------------------------
    "Arachis pintoi": "amendoim-forrageiro",
    "Avicennia germinans": "mangue-preto|siriúba",
    "Caryocar nuciferum": "piquiá",
    "Cephaelis ipecacuanha": "poaia|ipeca",
    "Cyphomandra betacea": "tomate-de-árvore|tamarilho",
    "Erythroxylum coca": "coca",
    "Gliricidia sepium": "gliricídia",
    "Muntingia calabura": "calabura",
    "Neoglaziovia variegata": "caroá",
    "Physalis peruviana": "fisális",
    "Rhizophora mangle": "mangue-vermelho|mangue-sapateiro",
    "Schizolobium parahybum": "guapuruvu|ficheira",
    "Stevia rebaudiana": "estévia",

    # --- weeds, forages and cover crops --------------------------------------
    "Axonopus compressus": "grama-tapete|grama-sempre-verde",
    "Bidens pilosa": "picão-preto|picão|carrapicho-de-agulha",
    "Bougainvillea glabra": "primavera|três-marias|buganvília",
    "Bromus unioloides": "cevadilha",
    "Calopogonium mucunoides": "calopogônio",
    "Cassia occidentalis": "fedegoso|mangirioba",
    "Crotalaria juncea": "crotalária|cânhamo-da-índia",
    "Cynodon dactylon": "grama-seda|capim-de-burro|grama-bermuda",
    "Cyperus rotundus": "tiririca|tiririca-roxa",
    "Eichhornia crassipes": "aguapé|baronesa|jacinto-d'água",
    "Glycine wightii": "soja-perene",
    "Heteropogon contortus": "capim-rabo-de-burro",
    "Macroptilium atropurpureum": "siratro",
    "Macroptilium lathyroides": "feijão-de-rola",
    "Mucuna pruriens": "mucuna|café-berão",
    "Mucuna pruriens var utilis": "mucuna-preta|mucuna",
    "Paspalum dilatatum": "capim-melador|capim-mimoso",
    "Portulaca oleracea": "beldroega",
    "Pueraria lobata": "kudzu",
    "Pueraria phaseoloides": "kudzu-tropical|puerária",
    "Solanum nigrum": "erva-moura|maria-pretinha",
    "Sorghum x drummondii": "capim-sudão",
    "Stylosanthes guianensis var. guianensis": "estilosantes",
    "Stylosanthes guianensis var. intermedia": "estilosantes",
    "Trifolium incarnatum": "trevo-encarnado",
    "Trifolium pratense": "trevo-vermelho",
    "Trifolium repens": "trevo-branco",
    "Talinum triangulare": "major-gomes|cariru",
    "Urena lobata": "guaxima|malva-roxa",
    "Xanthosoma sagittifolium": "taioba|mangará",

    # --- fruit ---------------------------------------------------------------
    "Annona atemoya": "atemoia",
    "Annona muricata": "graviola|graveóla",
    "Citrus aurantiifolia": "limão-galego|lima-ácida",
    "Citrus aurantium": "laranja-azeda|laranja-amarga",
    "Citrus aurantium ssp. bergamia": "bergamota|bergamoteira",
    "Citrus deliciosa": "mexerica|bergamota|tangerina",
    "Citrus grandis": "pomelo|toranja",
    "Citrus limon": "limão-siciliano|limão",
    "Citrus × microcarpa": "calamondim|quincã",
    "Citrus medica": "cidra|cidreira",
    "Citrus paradisi": "toranja|pomelo",
    "Citrus reticulata": "tangerina|mexerica|bergamota",
    "Citrus sp.": "citros",
    "Citrus unshiu": "tangerina-satsuma|satsuma",
    "Fragaria x ananassa": "morango|morangueiro",
    "Malus domestica": "maçã|macieira",
    "Musa balbisiana": "banana",
    "Musa sp.": "banana",
    "Musa textilis": "abacá",
    "Passiflora edulis": "maracujá|maracujá-azedo",
    "Passiflora edulis var. edulis": "maracujá-roxo|maracujá",
    "Passiflora edulis var. flavicarpa": "maracujá-amarelo|maracujá-azedo",
    "Passiflora laurifolia": "maracujá-laranja|maracujazinho",
    "Passiflora mollissima": "maracujá-banana|curuba",
    "Prunus amygdalus": "amêndoa|amendoeira",
    "Prunus persica": "pêssego|pessegueiro|nectarina",
    "Prunus salicina": "ameixa-japonesa|ameixa",
    "Pyrus communis": "pera|pereira",
    "Pyrus pyrifolia": "pera-japonesa|pera-nashi",
    "Rubus occidentalis": "framboesa-preta",
    "Vaccinium angustifolium": "mirtilo",
    "Vitis labrusca": "uva-americana|uva-isabel",
    "Vitis vinifera": "uva|videira|parreira",
    "Ziziphus mauritiana": "jujuba|maçã-de-pobre",

    # --- vegetables, grains and spices ---------------------------------------
    "Allium ampeloprasum": "alho-poró|alho-porro",
    "Anethum graveolens": "endro|aneto",
    "Amaranthus hypochondriacus": "amaranto",
    "Beta vulgaris": "beterraba|beterraba-de-mesa",
    "Beta vulgaris var. cicla": "acelga|beterraba-branca",
    "Beta vulgaris var. crassa": "beterraba|beterraba-de-mesa",
    "Beta vulgaris var. flavescens": "acelga|beterraba-branca",
    "Beta vulgaris var. saccharifera": "beterraba-açucareira|beterraba",
    "Brassica rapa": "nabo|nabo-forrageiro",
    "Brassica chinensis": "couve-chinesa|pak-choi",
    "Brassica napus": "canola|colza",
    "Brassica napus var. napobrassica": "rutabaga|nabo-sueco",
    "Brassica oleracea var. acephala": "couve|couve-manteiga",
    "Brassica oleracea var. botrytis": "couve-flor|",
    "Brassica oleracea var. capitata": "repolho|couve-repolho",
    "Brassica oleracea var. gemmifera": "couve-de-bruxelas|",
    "Brassica oleracea var. gongyloides": "couve-rábano|",
    "Brassica oleracea var. italica": "brócolis|brócolos",
    "Brassica rapa Gaisin gr.": "couve-chinesa|",
    "Brassica rapa Pak Choi": "pak-choi|couve-chinesa",
    "Brassica rapa var. rapifera": "nabo|nabo-redondo",
    "Cajanus cajan": "feijão-guandu|guandu|andu",
    "Capsicum baccatum var. pendulum": "pimenta-dedo-de-moça|cumari",
    "Capsicum frutescens": "pimenta-malagueta|malagueta",
    "Coffea excelsa": "café",
    "Colocasia esculenta": "inhame|taro",
    "Colocasia esculenta var. antiquorum": "inhame|taro",
    "Cucurbita moschata": "abóbora|jerimum|abóbora-menina",
    "Cucurbita pepo": "abobrinha|mogango",
    "Curcuma longa": "açafrão-da-terra|cúrcuma",
    "Curcuma zedoaria": "zedoária",
    "Cymbopogon citratus": "capim-santo|capim-cidreira|capim-limão",
    "Emilia sonchifolia": "serralhinha|falsa-serralha",
    "Eruca sativa": "rúcula|pinchão",
    "Eugenia aromatica": "cravo-da-índia|craveiro-da-índia",
    "Fagopyrum esculentum": "trigo-sarraceno|mourisco",
    "Helianthus tuberosus": "tupinambo|alcachofra-de-jerusalém",
    "Ipomoea aquatica": "corriola-d'água|campainha-d'água",
    "Ipomoea aquatica var. reptans": "corriola-d'água|campainha-d'água",
    "Ipomoea batatas": "batata-doce|batata",
    "Lactuca sativa var. capitata": "alface|alface-repolhuda",
    "Solanum lycopersicum": "tomate|tomateiro",
    "Mentha piperita": "hortelã-pimenta",
    "Mentha pulegium": "poejo",
    "Mentha spicata var. crispa": "hortelã|hortelã-crespa",
    "Marrubium vulgare": "marroio|marroio-branco",
    "Nicotiana rustica": "fumo-bravo",
    "Pastinaca sativa": "pastinaca|cherovia",
    "Poa trivialis": "poa-comum|",
    "Ocimum americanum": "alfavaca",
    "Ocimum basilicum": "manjericão|alfavaca",
    "Opuntia ficus-indica": "palma-forrageira|palma|figo-da-índia",
    "Oryza glaberrima": "arroz-africano",
    "Phaseolus vulgaris": "feijão|feijão-comum|feijão-carioca",
    "Piper betle": "bétel",
    "Raphanus sativus": "rabanete|rábano",
    "Raphanus sativus var. oleiferus": "nabo-forrageiro|",
    "Ricinus communis": "mamona|carrapateira",
    "Saccharum officinarum": "cana-de-açúcar|cana",
    "Salvia officinalis": "sálvia|sálvia-comum",
    "Setaria italica": "painço",
    "Solanum aethiopicum": "jiló|jiloeiro",
    "Solanum muricatum": "pepino-doce",
    "Triticum spelta": "espelta",
    "Vigna radiata": "feijão-mungo|feijão-moyashi",
    "Zea mays": "milho|milho-verde",
    "Zea mays ssp. mays": "milho|milho-verde",
    "Zea mays ssp. saccharata": "milho-doce|milho-verde",

    # --- planted timber and ornamentals --------------------------------------
    "Attalea speciosa": "babaçu|palmeira-babaçu",
    "Calotropis procera": "flor-de-seda|algodão-de-seda|ciúme",
    "Caryota urens": "palmeira-rabo-de-peixe|palmeira-toddy",
    "Cassia fistula": "chuva-de-ouro|cássia-imperial",
    "Casuarina equisetifolia": "casuarina|casuarina-da-praia",
    "Chrysophyllum cainito": "caimito|caimiteiro|abiu-roxo",
    "Ficus benghalensis": "figueira-de-bengala|bargá",
    "Ficus elastica": "falsa-seringueira|figueira-elástica",
    "Lonchocarpus nicou": "timbó|nicou",
    "Michelia champaca": "magnólia-amarela|champá",
    "Neoglaziovia variegata": "caroá|carauá",
    "Pouteria sapota": "sapota|mamei",
    "Samanea saman": "bordão-de-velho|árvore-da-chuva",
    "Vitex agnus-castus": "agnocasto|pimenteiro-silvestre",
    "Grevillea robusta": "grevílea|grevilha",
    "Khaya anthotheca": "mogno-africano",
    "Khaya senegalensis": "mogno-africano|caoba",
    "Melaleuca quinquenervia": "melaleuca",
    "Moringa oleifera": "moringa|moringueiro|acácia-branca",
    "Pinus elliottii ssp. elliottii": "pinus|pinheiro",
    "Pinus excelsa": "pinheiro-do-butão|",
    "Pinus taeda": "pinus|pinheiro",
    "Sambucus cerulea": "sabugueiro",
    "Swietenia mahogani": "mogno-das-antilhas",
}

# Homonyms: EcoCrop means one plant, the FFB record with that binomial is
# another, so the name FFB returns belongs to the wrong tree.
DROP = {
    "Terminalia tomentosa",   # EcoCrop's is the Indian timber; FFB's is a
                              # synonym of the Amazonian Terminalia corrugata
}

if __name__ == "__main__":
    main()
