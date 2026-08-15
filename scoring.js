// EcoCrop suitability engine, adapted for perennials.
// Model: trapezoidal membership per factor, min() combination (Liebig),
// best growing-season window over 12 candidate start months (Hijmans/dismo,
// DIVA-GIS). Perennial adaptations, documented in README.md:
//   - temperature scored on window-mean temp (OpenCLIM perennial variant),
//   - frost kill tested year-round against KTMPR (dormant-season hardiness),
//   - photoperiod scored from computed daylength (extension; not in dismo).

export function trap(x, a, b, c, d) {
  if (x <= a || x >= d) return 0;
  if (x < b) return (x - a) / (b - a);
  if (x <= c) return 1;
  return (d - x) / (d - c);
}

// Forsythe/CBM daylength (hours) at latitude (deg) and day of year. p=0.8333
// is the US-standard sunrise/sunset definition (sun upper limb + refraction).
export function daylength(lat, doy, p = 0.8333) {
  const theta = 0.2163108 + 2 * Math.atan(0.9671396 * Math.tan(0.00860 * (doy - 186)));
  const phi = Math.asin(0.39795 * Math.cos(theta));
  const rad = Math.PI / 180;
  let a = (Math.sin(p * rad) + Math.sin(lat * rad) * Math.sin(phi)) /
          (Math.cos(lat * rad) * Math.cos(phi));
  a = Math.max(-1, Math.min(1, a)); // clamps polar day/night
  return 24 - (24 / Math.PI) * Math.acos(a);
}

const MID_DOY = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349];

export function monthlyDaylengths(lat) {
  return MID_DOY.map(d => daylength(lat, d));
}

// Aggregate Open-Meteo daily arrays into monthly climate normals.
export function aggregateClimate(daily) {
  const sum = Array(12).fill(0), n = Array(12).fill(0);
  const tminSum = Array(12).fill(0), precSum = Array(12).fill(0);
  const years = Array.from({ length: 12 }, () => new Set());
  let absMin = Infinity;
  for (let i = 0; i < daily.time.length; i++) {
    const m = +daily.time[i].slice(5, 7) - 1;
    precSum[m] += daily.precipitation_sum[i] ?? 0; // precip counts even when temp has gaps
    years[m].add(daily.time[i].slice(0, 4));
    const t = daily.temperature_2m_mean[i];
    if (t == null) continue;
    sum[m] += t; n[m]++;
    tminSum[m] += daily.temperature_2m_min[i] ?? t;
    if (daily.temperature_2m_min[i] != null) absMin = Math.min(absMin, daily.temperature_2m_min[i]);
  }
  if (n.some(v => v === 0)) throw new Error("incomplete climate series (a month has no valid days)");
  const tavg = sum.map((s, m) => s / n[m]);
  const tmin = tminSum.map((s, m) => s / n[m]);
  const prec = precSum.map((s, m) => s / years[m].size); // mean monthly total, mm
  const meanOf = arr => {
    const v = (arr ?? []).filter(x => x != null);
    return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
  };
  const radMJ = meanOf(daily.shortwave_radiation_sum);
  return {
    tavg, tmin, prec,
    absMin: absMin === Infinity ? null : absMin,
    annualRain: prec.reduce((a, b) => a + b, 0),
    meanTemp: tavg.reduce((a, b) => a + b, 0) / 12,
    rad: radMJ == null ? null : radMJ / 3.6, // kWh/m2/day
    rh: meanOf(daily.relative_humidity_2m_mean),
    cloud: meanOf(daily.cloud_cover_mean),
  };
}

function dayClasses(d) {
  // half-hour tolerance on the EcoCrop category boundaries so equatorial
  // ~12.1h days still count as "short day (<12h)"
  const c = [];
  if (d < 12.5) c.push("short");
  if (d >= 11.5 && d <= 14.5) c.push("neutral");
  if (d > 13.5) c.push("long");
  return c;
}

// site: {tavg[12], tmin[12], prec[12], ph|null, lat}
// ev (optional): { native: true } = the species' own mapped/regional native
// range covers this exact site, which is evidence the regime is survivable
// even where EcoCrop's crop-oriented fields say otherwise.
export function scoreSpecies(sp, site, ev = null) {
  const [gmin, gmax] = sp.cycle ?? [null, null];
  const G = gmin == null && gmax == null ? 12 :
    Math.max(1, Math.min(12, Math.round(((gmin ?? gmax) + (gmax ?? gmin)) / 60)));
  // A TREE declaring deep dormant hardiness (KTMPR <= -10) does not grow
  // through its winter: its TEMPERATURE is scored on the growing season
  // (months averaging >= 5 C, capped by its own cycle), otherwise a
  // 12-month mean blends saskatoon's Winnipeg summers with -20 C januaries
  // and kills it in the town it was named after. Its RAIN is the full year
  // (temperate trees live on stored/annual water, and sugar maple's 6-month
  // envelope would starve in Toronto on window rain alone). Herbaceous
  // hardy crops keep the classic cycle-window scoring.
  const dormantTree = sp.tree && (sp.ktmpr ?? 99) <= -10;
  let Gt = G;
  if (dormantTree) {
    const warm = site.tavg.filter(t => t >= 5).length;
    Gt = Math.min(G, Math.max(3, warm));
    if (G === 12) Gt = Math.min(12, Math.max(3, warm));
  }

  let temp = 0, rain = 0, best = 0, bestScore = -1;
  if (dormantTree) { // annual rain, warm-season temperature, decoupled
    rain = trap(site.prec.reduce((a, b) => a + b, 0), ...sp.rain);
    for (let s = 0; s < 12; s++) {
      let tsum = 0;
      for (let k = 0; k < Gt; k++) tsum += site.tavg[(s + k) % 12];
      const t = trap(tsum / Gt, ...sp.temp);
      if (t > bestScore) { bestScore = t; temp = t; best = s; }
    }
  } else {
    for (let s = 0; s < 12; s++) {
      let tsum = 0, rtot = 0;
      for (let k = 0; k < G; k++) {
        const m = (s + k) % 12;
        tsum += site.tavg[m];
        rtot += site.prec[m];
      }
      const t = trap(tsum / G, ...sp.temp);
      const r = trap(rtot, ...sp.rain);
      const m = Math.min(t, r);
      // ties broken by temperature so an all-zero-rain site still reports the
      // real growing window (else annuals get frost-tested on january)
      if (m > bestScore || (m === bestScore && t > temp)) { bestScore = m; temp = t; rain = r; best = s; }
      if (G === 12) break; // all windows identical for full-year perennials
    }
  }

  // A perennial lives through the whole year, not just its best window:
  // the annual regime must sit inside the absolute temperature envelope.
  let annual = trap(site.tavg.reduce((a, b) => a + b, 0) / 12, ...sp.temp) > 0 ? 1 : 0;
  // native right here beats the envelope: the regime is survivable by observation
  if (!annual && ev?.native) annual = 1;

  // Frost semantics:
  // 1. Annual crops live only during their growing window and never meet the winter.
  // 2. Perennials are tested against dormant-season hardiness (KTMPR) for winter extremes.
  // 3. Tropical perennials without cold data default to frost-tender (0 C).
  // 4. Temperate perennials lacking KTMPR leave winter hardiness unscored (null);
  //    we never test succulent shoot KTMP against winter 10-year record lows.
  const FROST_MARGIN = 4;
  let frost = null;
  if (sp.annual && G < 12) {
    const kt = sp.ktmp ?? sp.ktmpr ?? (sp.gclass?.startsWith("tropical") ? 0 : null);
    if (kt != null) {
      let wmin = Infinity;
      for (let k = 0; k < G; k++) wmin = Math.min(wmin, site.tmin[(best + k) % 12]);
      frost = wmin < kt + 4 ? 0 : 1;
    }
  } else {
    const kt = sp.ktmpr ?? (sp.gclass?.startsWith("tropical") ? 0 : null);
    if (kt != null) {
      const minMonthly = Math.min(...site.tmin);
      if (minMonthly < kt + 4 || (site.absMin != null && site.absMin < kt - FROST_MARGIN)) {
        // Monthly winter is chronically too cold OR 10-year record low severely undercuts hardiness: absolute kill
        frost = 0;
      } else if (site.absMin != null && site.absMin - FROST_MARGIN <= kt) {
        // 10-year grid minimum is within margin of kill threshold: takes a half penalty with caveat
        frost = 0.5;
      } else {
        frost = 1;
      }
    }
  }

  // EcoCrop hardiness fields are unreliable for wild cold-climate trees
  // (sugar maple carries KTMPR -18 and would die in Toronto): when the
  // species is native to this exact site, a frost kill demotes to a half
  // penalty instead, and the card says which field we distrusted.
  if (frost === 0 && ev?.native) frost = 0.5;

  const ph = sp.ph && site.ph != null ? trap(site.ph, ...sp.ph) : null;

  // Obligate wetland species (EcoCrop absolute drainage = saturated only:
  // duckweed, cattail, mangroves) cannot live on drained ground. A real
  // slope from the DEM is the one drainage signal we can trust from space;
  // flat ground stays unscored (null) because we cannot see the water table.
  const drain = sp.wet
    ? (site.terrain?.slope != null ? (site.terrain.slope >= 4 ? 0 : null) : null)
    : null;

  // Winter dormancy proxy: EcoCrop has no chill-hours field, so temperate
  // deciduous species (which need cold to break dormancy and fruit) are
  // penalized where the coldest month stays warm. Full credit at <= 10 C,
  // zero at >= 16 C, linear between. Catches e.g. Asian pear in the tropics.
  let chill = null;
  if (sp.decid && sp.gclass?.startsWith("temperate")) {
    const coldest = Math.min(...site.tavg);
    chill = coldest <= 10 ? 1 : coldest >= 16 ? 0 : (16 - coldest) / 6;
  }

  // photo: null = unknown (not scored), [] = known insensitive, else categories
  let photo = sp.photo == null ? null : 1;
  if (sp.photo?.length) {
    const dls = monthlyDaylengths(site.lat);
    const here = new Set();
    for (let k = 0; k < G; k++) dayClasses(dls[(best + k) % 12]).forEach(c => here.add(c));
    photo = sp.photo.some(c => here.has(c)) ? 1 : 0.5;
  }

  const score = Math.min(temp, rain, ph ?? 1, chill ?? 1) * (frost ?? 1) * (photo ?? 1) * (drain ?? 1) * annual;

  // Tie-breaker: EcoCrop plateaus leave many species at the same score, so
  // also measure how close the site sits to each envelope's center
  // (triangular membership peaking at the optimal-range midpoint).
  const tri = (x, a, b, c, d) => trap(x, a, (b + c) / 2, (b + c) / 2, d);
  let tsum = 0, rtot = 0;
  for (let k = 0; k < G; k++) { const m = (best + k) % 12; tsum += site.tavg[m]; rtot += site.prec[m]; }
  const fits = [tri(tsum / G, ...sp.temp), tri(rtot, ...sp.rain)];
  if (sp.ph && site.ph != null) fits.push(tri(site.ph, ...sp.ph));
  const fit = fits.reduce((a, b) => a + b, 0) / fits.length;

  return { score, fit, factors: { temp, rain, ph, frost, photo, annual, chill, drain }, window: { start: best, months: Gt } };
}

export function grade(s) {
  if (s <= 0) return "Not suitable";
  if (s <= 0.2) return "Very marginal";
  if (s <= 0.4) return "Marginal";
  if (s <= 0.6) return "Suitable";
  if (s <= 0.8) return "Very suitable";
  return "Excellent";
}

export function gradeColor(s) {
  if (s > 0.8) return "#63c987";
  if (s > 0.6) return "#a9cd72";
  if (s > 0.4) return "#d9c46a";
  if (s > 0.2) return "#d79a63";
  return "#d4756f";
}
