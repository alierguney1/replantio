#!/usr/bin/env python3
"""Harvest the reference climate ranges Carvalho published for each species.

Paulo Ernani Ramalho de Carvalho, "Especies Arbóreas Brasileiras" (Embrapa
Florestas, 5 vols) and the Circular Técnica series behind it state, for every
species, the range of annual rainfall, annual mean temperature, coldest-month
mean temperature and absolute minimum recorded across the species' Brazilian
occurrence area. That is the closest thing to an independent, expert-curated
envelope that exists for the Brazilian flora, and it is public: Embrapa's
Infoteca serves the PDFs without a login.

This finds the right PDF per species, extracts the CLIMA block and pulls the
numbers, so the fitted envelopes can be checked against something that was not
built from GBIF. Needs `pdftotext` (poppler).
"""
import pathlib
import re
import subprocess
import sys
import urllib.parse
import urllib.request

CACHE = pathlib.Path(__file__).resolve().parent.parent / "data" / "cache" / "carvalho"
BASE = "https://www.infoteca.cnptia.embrapa.br"
UA = {"User-Agent": "Mozilla/5.0 (canopy-envelope-prototype)"}

# Carvalho files by common name, so the queries carry both. The scientific names
# he used predate several transfers (Tabebuia -> Handroanthus, Chorisia -> Ceiba).
QUERIES = {
    "Handroanthus impetiginosus": ["Ipe-roxo Tabebuia impetiginosa avellanedae"],
    "Cariniana estrellensis": ["Jequitiba-branco Cariniana estrellensis"],
    "Cecropia pachystachya": ["Embauba Cecropia pachystachya"],
    "Anadenanthera colubrina": ["Angico-branco Anadenanthera colubrina"],
    "Copaifera langsdorffii": ["Copaiba Copaifera langsdorffii"],
    "Aspidosperma polyneuron": ["Peroba-rosa Aspidosperma polyneuron"],
    "Luehea divaricata": ["Acoita-cavalo Luehea divaricata"],
    "Trema micrantha": ["Grandiuva Trema micrantha"],
    "Schinus terebinthifolia": ["Aroeira-vermelha Schinus terebinthifolius"],
    "Ceiba speciosa": ["Paineira Chorisia speciosa"],
}

LABELS = [
    ("rain", r"Precipita[çc][ãa]o pluvial m[ée]dia anual"),
    ("temp", r"Temperatura m[ée]dia anual"),
    ("tcold", r"Temperatura m[ée]dia do m[êe]s mais frio"),
    ("thot", r"Temperatura m[ée]dia do m[êe]s mais quente"),
    ("tabsmin", r"Temperatura m[íi]nima absoluta"),
    ("frost", r"N[úu]mero de geadas"),
    ("koppen", r"Tipos clim[áa]ticos"),
]


def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read() if binary else r.read().decode("utf-8", "replace")


def candidates(query, limit=6):
    url = f"{BASE}/infoteca/simple-search?" + urllib.parse.urlencode({"query": query})
    html = get(url)
    return re.findall(r'href="(/infoteca/handle/doc/\d+)"[^>]*>([^<]*)', html)[:limit]


def pdf_for(handle):
    html = get(BASE + handle)
    m = re.search(r'(/infoteca/bitstream/doc/\d+/\d+/[^"]+\.pdf)', html)
    return BASE + urllib.parse.quote(m.group(1), safe="/") if m else None


def text_of(url):
    CACHE.mkdir(parents=True, exist_ok=True)
    name = re.sub(r"\W+", "_", url.split("/doc/")[-1])
    pdf, txt = CACHE / f"{name}.pdf", CACHE / f"{name}.txt"
    if not txt.exists():
        if not pdf.exists():
            pdf.write_bytes(get(url, binary=True))
        subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)
    return txt.read_text("utf-8", "replace")


NEXT_LABEL = re.compile(
    r"Temperatura|Precipita|Regime de|Defici[êe]ncia|N[úu]mero de geadas|"
    r"Tipos clim|Solos|Ocorr[êe]ncia|Aspectos|Caracter[íi]sticas", re.I)


def clima(text):
    """Pull the labelled climate lines. pdftotext -layout keeps two columns on
    the same physical line, so grab a window after the label and cut at the next
    label rather than at the newline."""
    flat = re.sub(r"[ \t]+", " ", text)
    out = {}
    for key, label in LABELS:
        m = re.search(label + r"\s*:?\s*(.{0,300})", flat, re.S | re.I)
        if not m:
            continue
        v = re.sub(r"\s+", " ", m.group(1))
        nxt = NEXT_LABEL.search(v)
        out[key] = (v[:nxt.start()] if nxt else v).strip(" .;:")
    return out


def main():
    want = sys.argv[1:] or list(QUERIES)
    for sci in want:
        print(f"\n{'=' * 78}\n{sci}")
        for query in QUERIES.get(sci, [sci]):
            for handle, title in candidates(query):
                try:
                    url = pdf_for(handle)
                    if not url:
                        continue
                    c = clima(text_of(url))
                except Exception as e:  # a missing or scanned PDF is not fatal
                    print(f"  [{handle}] {title.strip()[:60]}: {type(e).__name__}")
                    continue
                if "temp" not in c and "rain" not in c:
                    continue
                print(f"  [{title.strip()[:64]}] {url}")
                for k, _ in LABELS:
                    if c.get(k):
                        print(f"    {k:8s} {c[k][:180]}")


if __name__ == "__main__":
    main()
