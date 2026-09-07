#!/usr/bin/env python3
"""Fetch authentic seed traits (storage behaviour, thousand seed weight)
from the Royal Botanic Gardens, Kew / SER Seed Information Database (SID)
for all species in data/species.json.

Source: Seed Information Database (SER / Kew RBG), CC BY 2.0.
Output: data/seed_traits.json
"""
import json, re, time, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SP_PATH = ROOT / "data" / "species.json"
OUT_PATH = ROOT / "data" / "seed_traits.json"

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
    # Maps (genus, epithet) -> list of species dicts
    taxa_map = {}
    for s in species_list:
        parts = s["sci"].strip().split()
        if len(parts) >= 2:
            genus, epithet = parts[0], parts[1].lower()
            taxa_map.setdefault((genus, epithet), []).append(s)

    unique_pairs = list(taxa_map.keys())
    print(f"Parsed {len(unique_pairs)} unique binomial pairs.")

    # 2. Batch query Kew species table
    matched_kew = {} # int_id -> (genus, epithet)
    pair_to_intid = {} # (genus, epithet) -> int_id

    batch_size = 40
    print("Matching binomials against Kew SID species backbone...")
    for i in range(0, len(unique_pairs), batch_size):
        chunk = unique_pairs[i:i + batch_size]
        clauses = [f"and(genus.eq.{g},epithet.eq.{e})" for g, e in chunk]
        url = f"{base_url}/species?or=({','.join(clauses)})&select=int_id,genus,epithet"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for row in data:
                    int_id = row.get("int_id")
                    g, e = row.get("genus"), (row.get("epithet") or "").lower()
                    if int_id:
                        matched_kew[int_id] = (g, e)
                        pair_to_intid[(g, e)] = int_id
        except Exception as ex:
            print(f"  Warning at batch {i}: {ex}")
            time.sleep(1)
        time.sleep(0.05)

    print(f"Successfully matched {len(pair_to_intid)} species in Kew SID.")

    # 3. Query storage_behaviour for all matched int_ids
    all_int_ids = list(matched_kew.keys())
    storage_results = {} # int_id -> normalized storage
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
        time.sleep(0.05)

    print(f"Found storage behaviour records for {len(storage_results)} taxa.")

    # 4. Query seed_weights for all matched int_ids
    weight_results = {} # int_id -> list of float weights in grams
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
        time.sleep(0.05)

    print(f"Found 1000-seed weight records for {len(weight_results)} taxa.")

    # 5. Build clean dataset keyed by EcoCrop species ID (int)
    out = {}
    for s in species_list:
        sp_id = s["id"]
        sci = s["sci"].strip()
        parts = sci.split()
        if len(parts) >= 2:
            genus, epithet = parts[0], parts[1].lower()
            int_id = pair_to_intid.get((genus, epithet))
            entry = {}
            if int_id:
                sb = storage_results.get(int_id)
                weights = weight_results.get(int_id)
                if sb:
                    entry["storage"] = sb
                if weights:
                    # round median/mean
                    weights.sort()
                    median_w = weights[len(weights) // 2]
                    entry["sw_1000g"] = round(median_w, 2)
                    entry["sw_g"] = round(median_w / 1000.0, 5)
                if entry:
                    entry["source"] = "Kew SID"

            if entry:
                out[str(sp_id)] = entry

    print(f"Generated seed traits dataset covering {len(out)} species.")
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print(f"Saved to {OUT_PATH} ({OUT_PATH.stat().st_size // 1024} KB)")

if __name__ == "__main__":
    main()
