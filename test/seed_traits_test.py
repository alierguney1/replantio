#!/usr/bin/env python3
"""Pure-unit tests for scripts/fetch_seed_traits.py helpers (no network).

Run: python3 test/seed_traits_test.py
"""
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

from fetch_seed_traits import (  # noqa: E402
    clean_binomial,
    classify_dormancy,
    normalize_storage,
    upper_median,
)
from build_species import (  # noqa: E402
    p_ds_interval,
    P_DS_HALF_WIDTH,
)


def _sp(sci, family="", porte="tree"):
    return {"sci": sci, "family": family, "porte": porte}


def test_clean_binomial():
    assert clean_binomial("Quercus robur") == ("Quercus", "robur")
    assert clean_binomial("  Pinus   sylvestris  ") == ("Pinus", "sylvestris")
    # hybrids: the multiplication sign (and ASCII fallback) is skipped
    assert clean_binomial("Citrus \u00d7 microcarpa") == ("Citrus", "microcarpa")
    assert clean_binomial("Citrus x microcarpa") == ("Citrus", "microcarpa")
    # trinomials collapse to genus + epithet
    assert clean_binomial("Brassica oleracea var. capitata") == ("Brassica", "oleracea")
    assert clean_binomial("Zea mays ssp. saccharata") == ("Zea", "mays")
    # unparseable -> None
    assert clean_binomial("Abies") is None
    assert clean_binomial("") is None
    assert clean_binomial("   ") is None


def test_normalize_storage():
    assert normalize_storage("Orthodox") == "orthodox"
    assert normalize_storage("  RECALCITRANT (?)") == "recalcitrant"
    assert normalize_storage("Intermediate") == "intermediate"
    assert normalize_storage(None) is None
    assert normalize_storage("") is None
    assert normalize_storage("unknown behaviour") is None


def test_recalcitrant_py_suppression_kew_path():
    # Kew scarification-only cue suppressed on recalcitrant seed -> ND
    d, p, src = classify_dormancy(_sp("Inga vera", "Fabaceae"),
                                  kew_presow="Mechanical scarification",
                                  storage="recalcitrant")
    assert (d, p) == ("ND", "none"), (d, p)
    assert "PY suppressed" in src, src
    # Kew combinational cue keeps only the cold half on recalcitrant seed
    d, p, src = classify_dormancy(_sp("Inga vera", "Fabaceae"),
                                  kew_presow="Scarification followed by cold stratification",
                                  storage="recalcitrant")
    assert (d, p) == ("PD", "cold_stratification"), (d, p)
    assert "PY suppressed" in src, src
    # orthodox control keeps the PY component
    d, p, src = classify_dormancy(_sp("Inga vera", "Fabaceae"),
                                  kew_presow="Mechanical scarification",
                                  storage="orthodox")
    assert (d, p) == ("PY", "scarification"), (d, p)


def test_recalcitrant_py_suppression_family_path():
    # family PY prior suppressed when storage is recalcitrant (no Kew cue)
    d, p, src = classify_dormancy(_sp("Inga edulis", "Fabaceae"), storage="recalcitrant")
    assert (d, p) == ("ND", "none"), (d, p, src)
    # orthodox control keeps the family prior
    d, p, src = classify_dormancy(_sp("Inga edulis", "Fabaceae"), storage="orthodox")
    assert (d, p) == ("PY", "scarification"), (d, p, src)


def test_herb_malvaceae_ordering():
    # herbaceous Malvaceae are PY: the family cue outranks the herb default
    d, p, src = classify_dormancy(_sp("Abelmoschus esculentus", "Malvaceae", "herb"))
    assert (d, p) == ("PY", "scarification"), (d, p, src)
    assert src == "family_prior (Baskin & Baskin)", src
    # non-malvaceous herb stays ND
    d, p, src = classify_dormancy(_sp("Triticum aestivum", "Poaceae", "herb"))
    assert (d, p) == ("ND", "none"), (d, p, src)


def test_upper_median():
    assert upper_median([3, 1, 2]) == 2
    assert statistics.median([3, 1, 2]) == 2
    # even n: the upper-median convention differs from statistics.median
    assert upper_median([4, 1, 3, 2]) == 3
    assert statistics.median([4, 1, 3, 2]) == 2.5
    assert upper_median([10.5]) == 10.5


def test_p_ds_interval():
    # Empirical species tier: +-0.05
    assert p_ds_interval(0.95, "empirical_species") == (0.90, 1.00)
    assert p_ds_interval(0.05, "empirical_species") == (0.00, 0.10)
    assert p_ds_interval(0.50, "empirical_species") == (0.45, 0.55)

    # Genus homogeneous tier: +-0.11
    assert p_ds_interval(0.92, "genus_homogeneous") == (0.81, 1.00)
    assert p_ds_interval(0.08, "genus_homogeneous") == (0.00, 0.19)

    # Family prior tier: +-0.21
    assert p_ds_interval(0.08, "family_prior") == (0.00, 0.29)

    # Uncertain tiers: +-0.30
    assert p_ds_interval(0.35, "uncertain") == (0.05, 0.65)
    assert p_ds_interval(0.45, "uncertain_heterogeneous") == (0.15, 0.75)

    # Clamping checks at boundary extremes
    assert p_ds_interval(0.02, "empirical_species") == (0.00, 0.07)
    assert p_ds_interval(0.99, "genus_homogeneous") == (0.88, 1.00)

    # Unknown tier raises SystemExit
    try:
        p_ds_interval(0.5, "uncalibrated_tier", code=999)
        assert False, "Should raise SystemExit on unknown tier"
    except SystemExit as ex:
        assert "unknown p_ds tier" in str(ex)


if __name__ == "__main__":
    test_clean_binomial()
    test_normalize_storage()
    test_recalcitrant_py_suppression_kew_path()
    test_recalcitrant_py_suppression_family_path()
    test_herb_malvaceae_ordering()
    test_upper_median()
    test_p_ds_interval()
    print("all seed_traits unit tests passed")
