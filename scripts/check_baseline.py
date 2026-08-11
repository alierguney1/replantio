#!/usr/bin/env python3
"""Is a WorldClim-fitted envelope on the same scale as a Canopy site reading?

The envelopes come from WorldClim 2.1, which is a 1970-2000 normal. The site
panel comes from Open-Meteo ERA5, 2015-2024, which app.js queries at line 357.
Those are two different climates 30 years apart, sampled by two different
models. If the offset is material then every occurrence-derived envelope is
being compared against a site that has already moved, and the whole shortlist
drifts one way. This measures the offset at real Brazilian restoration sites.
"""
import json
import math
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fit_envelopes import load_bioclim

SITES = [
    ("Sao Paulo SP", -23.55, -46.63),
    ("Campinas SP", -22.90, -47.06),
    ("Curitiba PR", -25.43, -49.27),
    ("Belo Horizonte MG", -19.92, -43.94),
    ("Brasilia DF", -15.79, -47.88),
    ("Cuiaba MT", -15.60, -56.10),
    ("Ilheus BA", -14.79, -39.05),
    ("Petrolina PE", -9.39, -40.50),
    ("Manaus AM", -3.12, -60.02),
    ("Belem PA", -1.46, -48.50),
    ("Porto Alegre RS", -30.03, -51.23),
    ("Serra do Mar SP", -23.85, -45.90),
]


def era5(lat, lon):
    url = ("https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode({
        "latitude": f"{lat:.4f}", "longitude": f"{lon:.4f}",
        "start_date": "2015-01-01", "end_date": "2024-12-31",
        "daily": "temperature_2m_mean,temperature_2m_min,precipitation_sum",
        "timezone": "auto"}))
    for attempt in range(6):  # the free archive tier throttles hard
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                d = json.loads(r.read())["daily"]
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            time.sleep(20 * (attempt + 1))
    t = [x for x in d["temperature_2m_mean"] if x is not None]
    p = [x for x in d["precipitation_sum"] if x is not None]
    # monthly mean of daily minima, per calendar month, then the coldest month:
    # that is exactly what scoring.js compares against KTMPR.
    bym = {}
    for day, v in zip(d["time"], d["temperature_2m_min"]):
        if v is not None:
            bym.setdefault(day[5:7], []).append(v)
    coldest = min(statistics.mean(v) for v in bym.values())
    # the 10-year record low: scoring.js tests this against KTMPR directly
    record = min(v for v in d["temperature_2m_min"] if v is not None)
    years = len({day[:4] for day in d["time"]})
    return statistics.mean(t), sum(p) / years, coldest, record


def grid_bias(grids, step=4.0, batch=10):
    """Same comparison over a coarse grid of Brazilian land points.

    Twelve cities is an anecdote. The archive API takes comma-separated
    coordinates, so a few dozen points cost a handful of calls and turn the
    offset into something you can put a number on.
    """
    pts = []
    lat = -33.0
    while lat <= 5.0:
        lon = -74.0
        while lon <= -34.0:
            row, col = grids[1].index(lat, lon)
            b1, r1 = grids[1].at(row, col, 0)
            b12, _ = grids[12].at(row, col, 0)
            # a hyper-arid cell makes the percentage meaningless (and bio12 can
            # be 0 on the Atacama edge of the lattice)
            if not (math.isnan(b1) or math.isnan(b12)) and b12 >= 100:
                pts.append((lat, lon, b1, b12))
            lon += step
        lat += step
    dt, dp = [], []
    for i in range(0, len(pts), batch):
        chunk = pts[i:i + batch]
        url = ("https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode({
            "latitude": ",".join(f"{p[0]:.4f}" for p in chunk),
            "longitude": ",".join(f"{p[1]:.4f}" for p in chunk),
            "start_date": "2015-01-01", "end_date": "2024-12-31",
            "daily": "temperature_2m_mean,precipitation_sum", "timezone": "GMT"}))
        for attempt in range(6):
            try:
                with urllib.request.urlopen(url, timeout=300) as r:
                    res = json.loads(r.read())
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or attempt == 5:
                    raise
                time.sleep(20 * (attempt + 1))
        for (lat, lon, b1, b12), d in zip(chunk, res if isinstance(res, list) else [res]):
            dd = d["daily"]
            t = [x for x in dd["temperature_2m_mean"] if x is not None]
            p = [x for x in dd["precipitation_sum"] if x is not None]
            if not t:
                continue
            dt.append(statistics.mean(t) - b1)
            dp.append(100 * (sum(p) / 10 - b12) / b12)
        time.sleep(3)
    print(f"\ngrid check, {len(dt)} Brazilian land points on a {step} deg lattice")
    print(f"  temp   ERA5 minus WorldClim: mean {statistics.mean(dt):+.2f} C, "
          f"median {statistics.median(dt):+.2f}, "
          f"p10 {sorted(dt)[len(dt) // 10]:+.2f}, p90 {sorted(dt)[-len(dt) // 10]:+.2f}")
    print(f"  precip ERA5 minus WorldClim: mean {statistics.mean(dp):+.1f}%, "
          f"median {statistics.median(dp):+.1f}%, "
          f"p10 {sorted(dp)[len(dp) // 10]:+.1f}%, p90 {sorted(dp)[-len(dp) // 10]:+.1f}%")


def main():
    grids = load_bioclim("5m")
    print(f"{'site':<18} {'WCbio1':>7} {'ERA5T':>7} {'dT':>6} "
          f"{'WCbio12':>8} {'ERA5P':>7} {'dP%':>7} {'WCbio6':>7} "
          f"{'ERA5tmin':>9} {'d6':>6} {'ERA5rec':>8} {'rec-b6':>7}")
    dt, dp, dt6, drec = [], [], [], []
    for name, lat, lon in SITES:
        row, col = grids[1].index(lat, lon)
        b1, _ = grids[1].at(row, col, 2)
        b6, _ = grids[6].at(row, col, 2)
        b12, _ = grids[12].at(row, col, 2)
        t, p, c, rec = era5(lat, lon)
        dt.append(t - b1)
        dp.append(100 * (p - b12) / b12)
        dt6.append(c - b6)
        drec.append(rec - b6)
        print(f"{name:<18} {b1:7.1f} {t:7.1f} {t - b1:+6.1f} {b12:8.0f} "
              f"{p:7.0f} {100 * (p - b12) / b12:+6.1f}% {b6:7.1f} {c:9.1f} "
              f"{c - b6:+6.1f} {rec:8.1f} {rec - b6:+7.1f}")
        time.sleep(2)  # free tier, be polite
    print(f"\nmean offset ERA5 2015-2024 minus WorldClim 1970-2000: "
          f"temp {statistics.mean(dt):+.2f} C (median {statistics.median(dt):+.2f}), "
          f"precip {statistics.mean(dp):+.1f}%, "
          f"coldest-month mean min {statistics.mean(dt6):+.2f} C")
    print(f"10-year absolute record low minus WorldClim bio6: "
          f"mean {statistics.mean(drec):+.2f} C, "
          f"range {min(drec):+.1f} to {max(drec):+.1f}. "
          f"This is the gap a KTMPR derived from bio6 has to cover, because "
          f"scoring.js tests site.absMin (a record low) against it.")
    if "--grid" in sys.argv:
        grid_bias(grids)


if __name__ == "__main__":
    main()
