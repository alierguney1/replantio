#!/usr/bin/env python3
"""Match crawled store products to species; write the `products` block of
data/sourcing.json. Inputs: /tmp/shop_*.json produced by the store crawlers
({"shop": id, "products": [{url,title,kind,sci,price}]}).

Matching order (strict to loose, never fuzzy):
1. binomial stated on the product page == species binomial (subsp/var stripped)
2. product title contains a Portuguese name (nome or aka) of exactly one species,
   on word boundaries, longest names first

Per species+shop keeps the cheapest product per kind (muda/semente).
"""
import glob, json, re, unicodedata, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
species = json.load(open(ROOT / "data" / "species.json"))
names = json.load(open(ROOT / "data" / "names_pt.json"))
names_tr = json.load(open(ROOT / "data" / "names_tr.json"))
sourcing = json.load(open(ROOT / "data" / "sourcing.json"))
shop_scope = {s["id"]: s.get("scope") for s in sourcing.get("shops", [])}

def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s)

def binom(s):
    m = re.match(r"([a-z]+) (x )?([a-z-]+)", norm(s))
    return f"{m.group(1)} {m.group(3)}" if m else None

by_binom = {}
for sp in species:
    b = binom(sp["sci"])
    if b: by_binom.setdefault(b, []).append(sp["id"])

# vernacular name -> species ids (only names that resolve to exactly one species are usable)
def name_index(d):
    idx = {}
    for sid, e in d.items():
        for nm in [e["nome"], *e.get("aka", [])]:
            idx.setdefault(norm(nm).strip(), set()).add(int(sid))
    return idx
by_name = name_index(names)
by_name_tr = name_index(names_tr)

products = {}
stats = {"binomial": 0, "binomial_embedded": 0, "name": 0, "skipped": 0}
for f in sorted(glob.glob("/tmp/shop_*.json") + glob.glob("/tmp/usshop_*.json") + glob.glob("/tmp/intl_*.json")):
    data = json.load(open(f))
    shop = data["shop"]
    for p in data.get("products", []):
        kind_map = {"seedling": "muda", "seed": "semente"}  # US kinds normalize to internal keys
        p["kind"] = kind_map.get(p.get("kind"), p.get("kind"))
        if p.get("kind") not in ("muda", "semente"):
            continue
        sids = []
        how = None
        slug = norm(re.sub(r"\.html?$", "", p["url"].rstrip("/").split("/")[-1]).replace("-", " "))
        title = norm(p.get("title", ""))
        if p.get("sci"):
            b = binom(p["sci"])
            if b in by_binom and len(by_binom[b]) == 1:
                sids, how = by_binom[b], "binomial"
        if not sids:
            # a known binomial hiding in the slug or title: exact word-pair
            # scan against our own species list, zero-guess precision
            for text in (slug, title):
                words = text.split()
                for i in range(len(words) - 1):
                    b = f"{words[i]} {words[i + 1]}"
                    if b in by_binom and len(by_binom[b]) == 1:
                        sids, how = by_binom[b], "binomial_embedded"
                        break
                if sids: break
        scope = shop_scope.get(shop)
        if not sids and scope == "BR":
            # strict: the species name must BE the product's object, not a
            # substring ("Manga cv. Ananás" must not match abacaxi). Extract X
            # from "Muda(s)/Sementes (de) X" in the title, else the URL slug;
            # cut at junk tokens; require X == name exactly.
            JUNK = r"\(|\bou\b|\bda\b|\bdo\b|\bpara\b|\bcom\b|\bcaixa\b|\bkit\b|\bund?\b|\bcm\b|\blitros?\b|\bfrutifer[ao]\b|\bornamental\b|\bnativ[ao]s?\b|\bverdadeir[ao]\b|\brar[ao]\b|\bexotic[ao]\b|\barvore\b|\bplanta\b|\benxertad[ao]\b|\badult[ao]\b|\bgrande\b|\bpequen[ao]\b|\d| - |,"
            for text in (title, slug):
                m = re.search(r"(?:mudas?|sementes?)\s+(?:de\s+)?(.*)", text)
                if not m: continue
                x = re.split(JUNK, m.group(1))[0].strip()
                if len(x) >= 5 and x in by_name and len(by_name[x]) == 1:
                    sids, how = [next(iter(by_name[x]))], "name"
                    break
        if not sids and scope == "TR":
            # Turkish puts the name BEFORE the kind word: "Ihlamur Fidanı",
            # "Domates Tohumu". Extract X before fidan*/tohum*; require X ==
            # a name from names_tr resolving to exactly one species. norm()
            # strips dotless ı on both sides, so "fidanı" -> "fidan".
            for text in (title, slug):
                m = re.search(r"^(.+?)\s+(?:fidan\w*|tohum\w*)\b", text)
                if not m: continue
                x = re.sub(r"\b(tuplu|asili|asisiz|bodur|yari|adet|koklu|acik|kok|luk|lu|cm|yas)\b|\d", " ", m.group(1))
                x = re.sub(r"\s+", " ", x).strip()
                if len(x) >= 4 and x in by_name_tr and len(by_name_tr[x]) == 1:
                    sids, how = [next(iter(by_name_tr[x]))], "name"
                    break
        if not sids:
            stats["skipped"] += 1
            continue
        stats[how] += 1
        sid = str(sids[0])
        slot = products.setdefault(sid, {}).setdefault(shop, {})
        kind = p["kind"]
        if kind not in slot or (p.get("price") or 9e9) < (slot[kind].get("price") or 9e9):
            slot[kind] = {"url": p["url"], **({"price": p["price"]} if p.get("price") else {})}

sourcing["products"] = products
sourcing["products_sobre"] = ("Links diretos de produto, casados por binomio declarado na pagina "
    "ou nome popular inequivoco; so lojas verificaveis (ML fora). Gerado por scripts/match_products.py")
json.dump(sourcing, open(ROOT / "data" / "sourcing.json", "w"), ensure_ascii=False, indent=1)
print("species with verified products:", len(products), "| match stats:", stats)
by_shop = {}
for v in products.values():
    for s in v: by_shop[s] = by_shop.get(s, 0) + 1
print("per shop:", by_shop)
