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
sourcing = json.load(open(ROOT / "data" / "sourcing.json"))

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

# PT name -> species ids (only names that resolve to exactly one species are usable)
by_name = {}
for sid, e in names.items():
    for nm in [e["nome"], *e.get("aka", [])]:
        by_name.setdefault(norm(nm).strip(), set()).add(int(sid))
uniq_names = sorted((n for n, ids in by_name.items() if len(ids) == 1 and len(n) >= 5),
                    key=len, reverse=True)

products = {}
stats = {"binomial": 0, "name": 0, "skipped": 0}
for f in sorted(glob.glob("/tmp/shop_*.json")):
    data = json.load(open(f))
    shop = data["shop"]
    for p in data.get("products", []):
        if p.get("kind") not in ("muda", "semente"):
            continue
        sids = []
        how = None
        if p.get("sci"):
            b = binom(p["sci"])
            if b in by_binom and len(by_binom[b]) == 1:
                sids, how = by_binom[b], "binomial"
        if not sids:
            # strict: the species name must BE the product's object, not a
            # substring ("Manga cv. Ananás" must not match abacaxi). Extract X
            # from "Muda(s)/Sementes de X", cut at (, -, "ou", digits; require
            # X == name exactly.
            t = norm(p.get("title", ""))
            m = re.search(r"(?:mudas?|sementes?)\s+de\s+(.*)", t)
            x = (m.group(1) if m else t)
            x = re.split(r"\(|\bou\b|\d| - |,", x)[0].strip()
            if x in by_name and len(by_name[x]) == 1:
                sids, how = [next(iter(by_name[x]))], "name"
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
