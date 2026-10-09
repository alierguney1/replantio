#!/usr/bin/env python3
"""Fetch authentic seed traits (storage behaviour, thousand seed weight, germination presow)
from the Royal Botanic Gardens, Kew / SER Seed Information Database (SID)
for all species in data/species.json.

Scientific Backbone:
- Continuous, evidence-calibrated Desiccation Sensitivity Probability (P_DS in [0, 1]).
- Explicit confidence tracking (empirical_species, genus_homogeneous, uncertain_heterogeneous, uncertain).
- Avoids crude majority voting in polymorphic families (Fabaceae, Arecaceae, Lauraceae) and
  heterogeneous genera (Acer, Dipterocarpus, Diospyros, Syzygium, Garcinia, Agathis, Magnolia).
- Prevents extreme threshold misfires by eliminating family-level TSW median imputation.
- Integrates Baskin & Baskin seed dormancy classification (ND, PD, PY, MPD, PY+PD)
  and concrete presowing treatment prescriptions.

Source: Seed Information Database (SER / Kew RBG), CC BY 2.0.
Output: data/seed_traits.json (+ data/seed_traits.meta.json run metadata)

Heuristic precedence for dormancy (documented limitation): direct Kew
presow cues > combinational genera > MPD genera > family cues > genus cues >
herb lifeform default > ND default. Kew-cued vs heuristic origin is not yet
recorded per entry (backlog: add dormancy_source).
Ecological flags (epicotyl_dormancy, serotinous, ectomycorrhizal, viviparous)
are interim author-curated name/family rules, pending trait-database sourcing;
scoring.js marks candidate uses as low-confidence.
p_ds point values per tier (0.95/0.50/0.05 empirical, 0.92/0.50/0.08
homogeneous genus, 0.08 family prior, 0.30-0.70 heterogeneous clamp, 0.35
data-free) are author priors, always paired with storage_confidence/source
labels — never presented as measurements.
"""
import json, re, time, urllib.request, pathlib
from collections import Counter
from statistics import median

ROOT = pathlib.Path(__file__).resolve().parent.parent
SP_PATH = ROOT / "data" / "species.json"
OUT_PATH = ROOT / "data" / "seed_traits.json"

HETEROGENEOUS_GENERA = {
    "Acer", "Dipterocarpus", "Diospyros", "Syzygium", "Garcinia",
    "Agathis", "Magnolia", "Citrus", "Coffea", "Hopea", "Shorea"
}

POLYMORPHIC_FAMILIES = {
    "Fabaceae", "Leguminosae", "Arecaceae", "Lauraceae", "Clusiaceae",
    "Dipterocarpaceae", "Ebenaceae", "Sapotaceae", "Myrtaceae"
}

COMBINATIONAL_GENERA = {"Caragana", "Cercis", "Rhus", "Tilia", "Ceanothus"}
MPD_GENERA = {"Fraxinus", "Ginkgo", "Taxus", "Ilex", "Magnolia", "Viburnum", "Hedera", "Panax"}
PY_FAMILIES = {"Fabaceae", "Leguminosae", "Malvaceae", "Cistaceae", "Bixaceae", "Nelumbonaceae", "Cannaceae"}
PD_FAMILIES = {
    "Pinaceae", "Cupressaceae", "Fagaceae", "Betulaceae", "Juglandaceae",
    "Rosaceae", "Sapindaceae", "Aceraceae", "Hippocastanaceae", "Araucariaceae"
}
ND_GENERA = {"Populus", "Salix", "Theobroma", "Swietenia", "Morus", "Ficus", "Casuarina"}

def get_anon_key():
    req = urllib.request.Request(
        "https://ser-sid.org/assets/index-BNtykY2s.js",
        headers={"User-Agent": "Mozilla/5.0 (Replantio Research)"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        js = r.read().decode("utf-8")
        return re.search(r"eyJ[a-zA-Z0-9_\-\.]+", js).group(0)

def normalize_storage(val):
    if not val:
        return None
    val = val.lower().strip()
    if "recalcitrant" in val:
        return "recalcitrant"
    if "intermediate" in val:
        return "intermediate"
    if "orthodox" in val:
        return "orthodox"
    return None

def clean_binomial(sci):
    parts = sci.strip().split()
    if len(parts) < 2:
        return None
    g = re.sub(r"[^a-zA-Z]", "", parts[0])
    e_idx = 1
    if parts[1] in ("×", "x", "X") and len(parts) >= 3:
        e_idx = 2
    e = re.sub(r"[^a-zA-Z]", "", parts[e_idx].lower())
    if g and e:
        return (g, e)
    return None

def classify_dormancy(s, kew_presow=None):
    b = clean_binomial(s["sci"])
    genus = b[0] if b else s["sci"].split()[0]
    fam = s.get("family") or ""
    porte = s.get("porte") or ""
    is_herb = porte in ("herb", "grass") or s.get("annual") == True

    # 1. Combinational dormancy (PY + PD) takes absolute precedence (Baskin & Baskin 2014)
    if genus in COMBINATIONAL_GENERA:
        return "PY+PD", "scarification_plus_cold_stratification"

    # 2. Morphophysiological dormancy (MPD)
    if genus in MPD_GENERA:
        return "MPD", "warm_plus_cold_stratification"

    # 3. Direct empirical cue from Kew germination tests
    if kew_presow:
        kp = kew_presow.lower()
        has_sc = any(w in kp for w in ("scarif", "chipped", "boiling", "scald", "acid", "nick"))
        has_ch = any(w in kp for w in ("stratifi", "chill", "cold", "moist"))
        if has_sc and has_ch:
            return "PY+PD", "scarification_plus_cold_stratification"
        if has_sc:
            return "PY", "scarification"
        if has_ch:
            return "PD", "cold_stratification"

    # 4. Functional & phylogenetic Baskin & Baskin classification.
    # Order matters: explicit genus/family cues outrank the herb lifeform
    # default (herbaceous Malvaceae are PY, not ND; Abelmoschus esculentus
    # was misclassified ND by the old order).
    if genus in ND_GENERA or genus in ("Eucalyptus", "Corymbia", "Melaleuca"):
        return "ND", "none"
    if fam in PY_FAMILIES or s.get("family") in ("Fabaceae", "Leguminosae"):
        return "PY", "scarification"
    if fam in PD_FAMILIES or genus in ("Pinus", "Picea", "Abies", "Larix", "Quercus", "Castanea", "Betula", "Alnus", "Prunus", "Malus"):
        return "PD", "cold_stratification"
    if is_herb:
        return "ND", "none"
    return "ND", "none"

def enrich_ecological_traits(s, entry):
    sci = s.get("sci", "")
    fam = s.get("family", "")
    b = clean_binomial(sci)
    genus = b[0] if b else sci.split()[0]
    if genus in ("Quercus", "Viburnum", "Paeonia", "Lilium") or fam == "Fagaceae":
        entry["epicotyl_dormancy"] = True
    if any(sci.startswith(x) for x in ("Pinus halepensis", "Pinus brutia", "Pinus radiata", "Pinus contorta", "Pinus banksiana", "Pinus rigida")) or "Banksia" in sci:
        entry["serotinous"] = True
    if fam in ("Dipterocarpaceae", "Fagaceae", "Betulaceae", "Pinaceae", "Nothofagaceae"):
        entry["ectomycorrhizal"] = True
    if genus in ("Rhizophora", "Avicennia", "Bruguiera", "Ceriops", "Kandelia") or fam in ("Rhizophoraceae", "Avicenniaceae"):
        entry["viviparous"] = True

def main():
    with open(SP_PATH) as f:
        species_list = json.load(f)
    print(f"Loaded {len(species_list)} species from {SP_PATH}")

    anon_key = get_anon_key()
    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "User-Agent": "Mozilla/5.0 (Replantio Research)"
    }
    base_url = "https://fyxheguykvewpdeysvoh.supabase.co/rest/v1"

    # 1. Parse binomials from species_list
    taxa_map = {}
    for s in species_list:
        b = clean_binomial(s["sci"])
        if b:
            taxa_map.setdefault(b, []).append(s)

    unique_pairs = list(taxa_map.keys())
    print(f"Parsed {len(unique_pairs)} unique binomial pairs.")

    # 2. Batch query Kew species table (batch size 25 prevents URL overflow)
    matched_kew = {} # int_id -> (genus, epithet)
    pair_to_intid = {} # (genus, epithet) -> int_id

    batch_size = 25
    print("Matching binomials against Kew SID species backbone...")
    for i in range(0, len(unique_pairs), batch_size):
        chunk = unique_pairs[i:i + batch_size]
        clauses = [f"and(genus.eq.{g},epithet.eq.{e})" for g, e in chunk]
        clause_str = ",".join(clauses)
        url = f"{base_url}/species?or=({clause_str})&select=int_id,genus,epithet"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for row in data:
                    int_id = row.get("int_id")
                    g = re.sub(r"[^a-zA-Z]", "", row.get("genus") or "")
                    e = re.sub(r"[^a-zA-Z]", "", (row.get("epithet") or "").lower())
                    if int_id and g and e:
                        matched_kew[int_id] = (g, e)
                        pair_to_intid[(g, e)] = int_id
        except Exception as ex:
            print(f"  Warning at batch {i}: {ex}")
            time.sleep(1)
        time.sleep(0.04)

    print(f"Successfully matched {len(pair_to_intid)} species in Kew SID.")

    # 3. Query storage_behaviour
    all_int_ids = list(matched_kew.keys())
    storage_results = {}
    id_batch_size = 100

    print("Fetching storage behaviour...")
    for i in range(0, len(all_int_ids), id_batch_size):
        chunk = all_int_ids[i:i + id_batch_size]
        id_str = ",".join(str(x) for x in chunk)
        url = f"{base_url}/storage_behaviour?species_id=in.({id_str})&select=species_id,storage_behaviour"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for row in data:
                    sid = row.get("species_id")
                    sb = normalize_storage(row.get("storage_behaviour"))
                    if sid and sb:
                        storage_results[sid] = sb
        except Exception as ex:
            print(f"  Warning at storage batch {i}: {ex}")
            time.sleep(1)
        time.sleep(0.04)

    print(f"Found storage behaviour records for {len(storage_results)} taxa.")

    # 4. Query seed_weights
    weight_results = {}
    print("Fetching 1000-seed weights...")
    for i in range(0, len(all_int_ids), id_batch_size):
        chunk = all_int_ids[i:i + id_batch_size]
        id_str = ",".join(str(x) for x in chunk)
        url = f"{base_url}/seed_weights?species_id=in.({id_str})&select=species_id,thousandseedweight"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for row in data:
                    sid = row.get("species_id")
                    w = row.get("thousandseedweight")
                    if sid and w is not None:
                        try:
                            val = float(w)
                            if val > 0:
                                weight_results.setdefault(sid, []).append(val)
                        except (ValueError, TypeError):
                            pass
        except Exception as ex:
            print(f"  Warning at weight batch {i}: {ex}")
            time.sleep(1)
        time.sleep(0.04)

    print(f"Found 1000-seed weight records for {len(weight_results)} taxa.")

    # 5. Query germination presow treatments
    presow_results = {}
    print("Fetching germination presowing treatments...")
    for i in range(0, len(all_int_ids), id_batch_size):
        chunk = all_int_ids[i:i + id_batch_size]
        id_str = ",".join(str(x) for x in chunk)
        url = f"{base_url}/germination?species_id=in.({id_str})&presow_treatment=neq.&select=species_id,presow_treatment"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for row in data:
                    sid = row.get("species_id")
                    pt = (row.get("presow_treatment") or "").strip()
                    if sid and pt:
                        presow_results[sid] = pt
        except Exception as ex:
            print(f"  Warning at germination batch {i}: {ex}")
            time.sleep(1)
        time.sleep(0.04)

    print(f"Found germination presow records for {len(presow_results)} taxa.")

    # 6. Build species-level empirical dataset
    out = {}
    genus_storage_obs = {}
    genus_weights_obs = {}

    for s in species_list:
        sp_id = s["id"]
        b = clean_binomial(s["sci"])
        if b:
            int_id = pair_to_intid.get(b)
            if int_id:
                genus = b[0]
                sb = storage_results.get(int_id)
                weights = weight_results.get(int_id)
                pt = presow_results.get(int_id)

                if sb:
                    genus_storage_obs.setdefault(genus, []).append(sb)
                if weights:
                    genus_weights_obs.setdefault(genus, []).extend(weights)

                entry = {}
                if sb:
                    entry["storage"] = sb
                    entry["p_ds"] = 0.95 if sb == "recalcitrant" else (0.50 if sb == "intermediate" else 0.05)
                    entry["storage_confidence"] = "empirical_species"
                    entry["source"] = "Kew SID (species)"

                if weights:
                    weights.sort()
                    median_w = round(weights[len(weights) // 2], 2)
                    entry["sw_1000g"] = median_w
                    entry["sw_g"] = round(median_w / 1000.0, 5)
                    entry["tsw_source"] = "species"

                dormancy, presow = classify_dormancy(s, pt)
                entry["dormancy"] = dormancy
                entry["presow"] = presow

                if entry:
                    out[str(sp_id)] = entry

    print(f"Direct species empirical matches from Kew SID: {len(out)} species.")

    # 7. Genus-Level Calibrated Probabilistic Imputation (Strict Anti-Bluffing Discipline)
    imputed_count = 0
    for s in species_list:
        sid = str(s["id"])
        entry = dict(out.get(sid, {}))
        b = clean_binomial(s["sci"])
        genus = b[0] if b else s["sci"].split()[0]
        fam = s.get("family") or ""

        # Dormancy always defined
        if "dormancy" not in entry:
            dormancy, presow = classify_dormancy(s)
            entry["dormancy"] = dormancy
            entry["presow"] = presow

        # Storage & P_DS imputation
        if "p_ds" not in entry:
            obs = genus_storage_obs.get(genus, [])
            if genus in HETEROGENEOUS_GENERA or (obs and len(set(obs)) > 1):
                # Genus has known desiccation heterogeneity: intermediate probability, marked uncertain
                recalc_ratio = sum(1 for x in obs if x == "recalcitrant") / len(obs) if obs else 0.45
                entry["p_ds"] = round(min(0.70, max(0.30, recalc_ratio)), 2)
                entry["storage"] = None # Never force false binary classification
                entry["storage_confidence"] = "uncertain_heterogeneous"
                entry["source"] = "Kew SID (genus, heterogeneous)"
                imputed_count += 1
            elif obs and len(obs) >= 2 and len(set(obs)) == 1:
                # Homogeneous genus with multiple concordant records
                dominant = obs[0]
                entry["storage"] = dominant
                entry["p_ds"] = 0.92 if dominant == "recalcitrant" else (0.50 if dominant == "intermediate" else 0.08)
                entry["storage_confidence"] = "genus_homogeneous"
                entry["source"] = "Kew SID (genus)"
                imputed_count += 1
            elif fam in ("Poaceae", "Brassicaceae", "Chenopodiaceae"):
                # Strictly orthodox family prior
                entry["storage"] = "orthodox"
                entry["p_ds"] = 0.08
                entry["storage_confidence"] = "family_prior"
                entry["source"] = "Taxonomic prior"
                imputed_count += 1
            else:
                # Insufficient data: do NOT assign family median or forced storage
                entry["storage"] = None
                entry["p_ds"] = 0.35 # Precautionary intermediate
                entry["storage_confidence"] = "uncertain"
                entry["source"] = "Uncertain / Insufficient data"

        # TSW Imputation: ONLY from conserved genera where variation is small (max/min < 4.0)
        # NEVER assign family-level medians (eliminates Fabaceae 0.8g vs 20,000g distortion)
        if "sw_1000g" not in entry:
            g_weights = genus_weights_obs.get(genus, [])
            if len(g_weights) >= 3:
                min_w, max_w = min(g_weights), max(g_weights)
                if min_w > 0 and (max_w / min_w) < 4.0:
                    med_w = round(median(g_weights), 2)
                    entry["sw_1000g"] = med_w
                    entry["sw_g"] = round(med_w / 1000.0, 5)
                    entry["tsw_source"] = "genus"
            # If genus variation is wide or missing, leave sw_1000g as None!

        enrich_ecological_traits(s, entry)
        out[sid] = entry

    print(f"Generated comprehensive seed traits dataset covering {len(out)} species ({imputed_count} genus/prior enriched).")
    if not pair_to_intid:
        raise SystemExit("No Kew SID matches at all — refusing to overwrite the vendored dataset with priors.")
    tmp = OUT_PATH.with_name(OUT_PATH.name + ".tmp")
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    tmp.replace(OUT_PATH)
    print(f"Saved to {OUT_PATH} ({OUT_PATH.stat().st_size // 1024} KB)")
    meta = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "species": len(out),
        "kew_matched": len(pair_to_intid),
        "storage_records": len(storage_results),
        "weight_records": len(weight_results),
        "presow_records": len(presow_results),
        "genus_prior_enriched": imputed_count,
        "script": "scripts/fetch_seed_traits.py",
    }
    with open(ROOT / "data" / "seed_traits.meta.json", "w") as f:
        json.dump(meta, f, indent=1, sort_keys=True)
    print(f"Run metadata: {meta}")

if __name__ == "__main__":
    main()
