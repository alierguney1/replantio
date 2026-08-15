// EcoCrop suitability engine, adapted for perennials.
// Model: trapezoidal membership per factor, min() combination (Liebig),
// best growing-season window over 12 candidate start months (Hijmans/dismo,
// DIVA-GIS). Perennial adaptations, documented in README.md:
//   - temperature scored on window-mean temp (OpenCLIM perennial variant),
//   - frost kill tested year-round against KTMPR (dormant-season hardiness),
//   - active-growth frost tested against KTMP during the growing window,
//   - sloped terrain gravity drainage modeled for excess precipitation,
//   - topographic solar radiation calculated on inclined slopes,
//   - photoperiod scored from computed daylength (extension; not in dismo),
//   - growing season water deficit and FAO-56 irrigation requirement calculated.

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

export const MID_DOY = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349];

export function monthlyDaylengths(lat) {
  return MID_DOY.map(d => daylength(lat, d));
}

// Topographic solar radiation ratio on inclined surfaces (Duffie & Beckman 2013, Swift 1976).
// Computes daily integrated beam radiation ratio Rb = I_slope / I_flat, coupled with
// Liu & Jordan (1960) isotropic sky-view diffuse (1+cos beta)/2 and ground albedo (1-cos beta)/2.
export function slopeSolarFactor(latDeg, slopeDeg, aspectDeg, doy) {
  if (slopeDeg == null || slopeDeg < 1.0 || aspectDeg == null || latDeg == null) return 1.0;
  const rad = Math.PI / 180;
  const phi = latDeg * rad;
  const beta = slopeDeg * rad;
  // standard solar azimuth gamma: South = 0, East = -pi/2, West = +pi/2, North = +/-pi
  const gamma = (aspectDeg - 180) * rad;
  const delta = 0.409 * Math.sin((2 * Math.PI / 365) * doy - 1.39);

  // Horizontal sunset hour angle
  const tanTan = -Math.tan(phi) * Math.tan(delta);
  let ws = 0;
  if (tanTan <= -1) ws = Math.PI; // polar day
  else if (tanTan >= 1) ws = 0;   // polar night
  else ws = Math.acos(tanTan);

  if (ws <= 0) return 0;

  const I_flat = 2 * (ws * Math.sin(phi) * Math.sin(delta) + Math.cos(phi) * Math.cos(delta) * Math.sin(ws));
  if (I_flat <= 1e-6) return 0;

  const A = Math.sin(delta) * (Math.sin(phi) * Math.cos(beta) - Math.cos(phi) * Math.sin(beta) * Math.cos(gamma));
  const B = Math.cos(delta) * (Math.cos(phi) * Math.cos(beta) + Math.sin(phi) * Math.sin(beta) * Math.cos(gamma));
  const C = Math.cos(delta) * Math.sin(beta) * Math.sin(gamma);

  const Ramp = Math.hypot(B, C);
  const psi = Math.atan2(C, B);

  let w1 = -ws, w2 = ws;
  if (Ramp > 1e-6) {
    const x = -A / Ramp;
    if (x >= 1) return 0; // never illuminated by direct beam
    if (x > -1) {
      const deltaW = Math.acos(x);
      w1 = Math.max(-ws, psi - deltaW);
      w2 = Math.min(ws, psi + deltaW);
    }
  }

  let I_slope = 0;
  if (w2 > w1) {
    I_slope = A * (w2 - w1) + B * (Math.sin(w2) - Math.sin(w1)) - C * (Math.cos(w2) - Math.cos(w1));
  }
  I_slope = Math.max(0, I_slope);

  const Rb = I_slope / I_flat;
  const kb = 0.70, kd = 0.30, rho = 0.20;
  const Fsky = (1 + Math.cos(beta)) / 2;
  const Fground = (1 - Math.cos(beta)) / 2;

  return Math.max(0.05, kb * Rb + kd * Fsky + rho * Fground);
}

export function monthlySlopeSolarFactors(latDeg, slopeDeg, aspectDeg) {
  if (slopeDeg == null || slopeDeg < 1.0 || aspectDeg == null || latDeg == null) return Array(12).fill(1.0);
  return MID_DOY.map(d => slopeSolarFactor(latDeg, slopeDeg, aspectDeg, d));
}

// UNEP / FAO Aridity Index (AI = P / ET0) classification
export const ARIDITY_CLASSES = [
  { max: 0.05, label: "Hyper-arid" },
  { max: 0.20, label: "Arid" },
  { max: 0.50, label: "Semi-arid" },
  { max: 0.65, label: "Dry sub-humid" },
  { max: Infinity, label: "Humid" },
];

export function aridityClass(ai) {
  if (ai == null || !Number.isFinite(ai) || ai < 0) return null;
  return ARIDITY_CLASSES.find(c => ai < c.max)?.label ?? "Humid";
}

// Aggregate Open-Meteo daily arrays into monthly climate normals.
export function aggregateClimate(daily) {
  const sum = Array(12).fill(0), n = Array(12).fill(0);
  const tminSum = Array(12).fill(0), precSum = Array(12).fill(0), et0Sum = Array(12).fill(0);
  const years = Array.from({ length: 12 }, () => new Set());
  let absMin = Infinity;
  const hasET0 = Array.isArray(daily.et0_fao_evapotranspiration);

  for (let i = 0; i < daily.time.length; i++) {
    const m = +daily.time[i].slice(5, 7) - 1;
    precSum[m] += daily.precipitation_sum[i] ?? 0; // precip counts even when temp has gaps
    if (hasET0) et0Sum[m] += daily.et0_fao_evapotranspiration[i] ?? 0;
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
  const et0 = hasET0 ? et0Sum.map((s, m) => s / years[m].size) : null;
  const meanOf = arr => {
    const v = (arr ?? []).filter(x => x != null);
    return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null;
  };
  const radMJ = meanOf(daily.shortwave_radiation_sum);
  const annualRain = prec.reduce((a, b) => a + b, 0);
  const annualET0 = et0 ? et0.reduce((a, b) => a + b, 0) : null;
  const waterBalance = annualET0 != null ? annualRain - annualET0 : null;
  const ai = annualET0 != null && annualET0 > 0 ? annualRain / annualET0 : null;

  return {
    tavg, tmin, prec, et0,
    absMin: absMin === Infinity ? null : absMin,
    annualRain,
    annualET0,
    waterBalance,
    ai,
    aridity: aridityClass(ai),
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

// ---------------------------------------------------------------------------
// Perennial Hydrology & Slope Drainage (FAO Soils Bulletin 52 / Darcy Flux)
// Flat land (<2 deg) accumulates standing water when rain > ROPMX.
// Sloped terrain (>2 deg) accelerates lateral surface/subsurface gravity drainage,
// expanding the upper precipitation tolerance band (RMAX - ROPMX).
// ---------------------------------------------------------------------------
const SLOPE_FLAT_DEG = 2.0;         // Threshold below which drainage is flat/unrelieved
const SLOPE_MAX_DEG = 16.0;         // Gravitational drainage benefit plateau (~28% gradient)
const MAX_SLOPE_DRAIN_FACTOR = 1.0; // Expands upper tolerance band (RMAX - ROPMX) by up to +100%

/**
 * Calculates rain score for perennials on sloped terrain.
 * On flat ground, excess precipitation above ROPMX saturates soil toward RMAX.
 * On hillsides, lateral gravity drainage expands the (RMAX - ROPMX) tolerance band proportionally.
 */
function scorePerennialRain(annualRain, [rmin, ropmn, ropmx, rmax], slope) {
  if (annualRain <= ropmx) {
    return trap(annualRain, rmin, ropmn, ropmx, rmax);
  }
  const deg = slope ?? 0;
  const slopeProgress = deg > SLOPE_FLAT_DEG
    ? Math.min(1.0, (deg - SLOPE_FLAT_DEG) / (SLOPE_MAX_DEG - SLOPE_FLAT_DEG))
    : 0;
  const effectiveRmax = ropmx + (rmax - ropmx) * (1 + slopeProgress * MAX_SLOPE_DRAIN_FACTOR);
  return trap(annualRain, rmin, ropmn, ropmx, effectiveRmax);
}

// site: {tavg[12], tmin[12], prec[12], et0[12]|null, ph|null, lat, terrain}
// ev (optional): { native: true } = the species' own mapped/regional native
// range covers this exact site, which is evidence the regime is survivable
// even where EcoCrop's crop-oriented fields say otherwise.
export function scoreSpecies(sp, site, ev = null) {
  const [gmin, gmax] = sp.cycle ?? [null, null];
  const G = gmin == null && gmax == null ? 12 :
    Math.max(1, Math.min(12, Math.round(((gmin ?? gmax) + (gmax ?? gmin)) / 60)));
  const isPerennial = !sp.annual;
  // A dormant/deciduous perennial does not grow through its winter: its TEMPERATURE
  // is scored on the growing season (months averaging >= 5 C, capped by its cycle),
  // otherwise a 12-month mean blends saskatoon's Winnipeg summers with -20 C januaries.
  // Its RAIN is the full hydrological year (perennials survive on stored soil water
  // replenished year-round). Herbaceous annual crops keep cycle-window scoring.
  const isDormant = isPerennial && (sp.decid || (sp.ktmpr ?? 99) <= -10);
  let Gt = G;
  if (isDormant) {
    const warm = site.tavg.filter(t => t >= 5).length;
    Gt = Math.min(G, Math.max(3, warm));
    if (G === 12) Gt = Math.min(12, Math.max(3, warm));
  }

  let temp = 0, rain = 0, best = 0, bestScore = -1, bestDist = Infinity;
  const toptMid = (sp.temp[1] + sp.temp[2]) / 2;
  if (isPerennial) {
    // Perennials score rain on annual precipitation adjusted for hillside gravity drainage
    const annualRain = site.prec.reduce((a, b) => a + b, 0);
    rain = scorePerennialRain(annualRain, sp.rain, site.terrain?.slope);

    const sMax = Gt === 12 ? 1 : 12;
    for (let s = 0; s < sMax; s++) {
      let tsum = 0;
      for (let k = 0; k < Gt; k++) tsum += site.tavg[(s + k) % 12];
      const mean = tsum / Gt;
      const t = trap(mean, ...sp.temp);
      const dist = Math.abs(mean - toptMid);
      if (t > bestScore || (t === bestScore && dist < bestDist)) {
        bestScore = t; temp = t; best = s; bestDist = dist;
      }
    }
  } else {
    for (let s = 0; s < 12; s++) {
      let tsum = 0, rtot = 0;
      for (let k = 0; k < G; k++) {
        const m = (s + k) % 12;
        tsum += site.tavg[m];
        rtot += site.prec[m];
      }
      const mean = tsum / G;
      const t = trap(mean, ...sp.temp);
      const r = trap(rtot, ...sp.rain);
      const m = Math.min(t, r);
      const dist = Math.abs(mean - toptMid);
      // ties broken by thermal optimum midpoint so an all-zero-rain site or plateau
      // reports the true biological growing window instead of winter or extreme heat
      if (m > bestScore || (m === bestScore && dist < bestDist)) {
        bestScore = m; temp = t; rain = r; best = s; bestDist = dist;
      }
      if (G === 12) break; // all windows identical for full-year perennials
    }
  }

  // A perennial lives through the whole year, not just its best window:
  // the annual regime must sit inside the absolute temperature envelope.
  // Annual crops live only during their G-month window and are exempt.
  let annual = (sp.annual && G < 12) ? 1 : (trap(site.tavg.reduce((a, b) => a + b, 0) / 12, ...sp.temp) > 0 ? 1 : 0);
  // native right here beats the envelope: the regime is survivable by observation
  if (!annual && ev?.native) annual = 1;

  // ---------------------------------------------------------------------------
  // Frost & Freezing Semantics (Dual-Stage Physiological Model):
  // 1. Annual crops live only inside their growing window and never meet winter.
  //    Tested on growing-window months against KTMP (or KTMPR).
  // 2. Perennials experience two distinct vulnerability stages:
  //    a) Dormant Winter Hardiness (KTMPR): Tested against 10-year record low (absMin)
  //       and chronic winter monthly minima. Tropical perennials default to 0 C.
  //    b) Active-Season Shoot Sensitivity (KTMP): Succulent new spring/summer growth
  //       is tested against growing-window monthly minima.
  // ---------------------------------------------------------------------------
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
    // Stage 1: Dormant winter extreme tolerance (KTMPR)
    const ktr = sp.ktmpr ?? (sp.gclass?.startsWith("tropical") ? 0 : null);
    if (ktr != null) {
      const minMonthly = Math.min(...site.tmin);
      if (minMonthly < ktr + 4 || (site.absMin != null && site.absMin < ktr)) {
        // Winter is chronically below hardiness OR record low cuts under kill threshold:
        frost = 0;
      } else if (site.absMin != null && site.absMin - FROST_MARGIN <= ktr) {
        // Record low sits within FROST_MARGIN of hardiness: radiative frost caveat penalty
        frost = 0.5;
      } else {
        frost = 1;
      }
    }

    // Stage 2: Active growing-season frost risk for succulent new growth (KTMP)
    if (frost !== 0 && sp.ktmp != null) {
      let wmin = Infinity;
      for (let k = 0; k < Gt; k++) wmin = Math.min(wmin, site.tmin[(best + k) % 12]);
      if (wmin < sp.ktmp) {
        // Late spring or early autumn frost threatens active vegetative shoots
        frost = Math.min(frost ?? 1, 0.5);
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
    for (let k = 0; k < Gt; k++) dayClasses(dls[(best + k) % 12]).forEach(c => here.add(c));
    photo = sp.photo.some(c => here.has(c)) ? 1 : 0.5;
  }

  // Shade-preferring / understory species: in intense direct open sun,
  // delicate understory crops (cocoa, cardamom, vanilla, ginseng) suffer
  // photo-inhibition and leaf scorch unless intercropped with nurse trees
  // (Beer et al. 1998, Somarriba et al. 2012; 15-20% open-sun seedling stress).
  let shade = null;
  if (sp.shade) {
    const effRad = site.radSlope ?? site.rad;
    if (effRad != null && effRad >= 5.2 && (site.cloud == null || site.cloud < 50)) {
      shade = 0.85; // soft penalty in unshaded high-radiation open fields
    } else {
      shade = 1.0;
    }
  }

  const score = Math.min(temp, rain, ph ?? 1, chill ?? 1) * (frost ?? 1) * (photo ?? 1) * (drain ?? 1) * (shade ?? 1) * annual;

  // Tie-breaker: EcoCrop plateaus leave many species at the same score, so
  // also measure how close the site sits to each envelope's center
  // (triangular membership peaking at the optimal-range midpoint).
  const tri = (x, a, b, c, d) => trap(x, a, (b + c) / 2, (b + c) / 2, d);
  let tsum = 0;
  for (let k = 0; k < Gt; k++) tsum += site.tavg[(best + k) % 12];
  const rainVal = isPerennial ? site.prec.reduce((a, b) => a + b, 0) : (() => {
    let r = 0;
    for (let k = 0; k < G; k++) r += site.prec[(best + k) % 12];
    return r;
  })();
  const fits = [tri(tsum / Gt, ...sp.temp), tri(rainVal, ...sp.rain)];
  if (sp.ph && site.ph != null) fits.push(tri(site.ph, ...sp.ph));
  const fit = fits.reduce((a, b) => a + b, 0) / fits.length;

  // ---------------------------------------------------------------------------
  // Growing-Season Water Deficit & Irrigation Guidance (FAO-56 Dual-Crop Method)
  // Quantifies supplementary irrigation needed (mm/month) to overcome rainfed deficit:
  // Deficit = max(0, ETc - P_window), where ETc = ET0 * Kc.
  // ---------------------------------------------------------------------------
  let wRain = 0, wET0 = 0;
  for (let k = 0; k < Gt; k++) {
    const m = (best + k) % 12;
    wRain += site.prec[m];
    if (site.et0) wET0 += site.et0[m];
  }

  let deficit = null;
  let irrigation = null;
  if (site.et0) {
    // Habit- and cycle-derived crop coefficient (Kc) approximation (FAO-56):
    const cropKc = sp.porte === "tree" ? 0.95 :
      sp.porte === "shrub" ? 0.85 :
      sp.cycle?.[1] > 180 ? 1.05 : 0.90;
    const cropET = wET0 * cropKc;
    deficit = Math.max(0, Math.round(cropET - wRain));
    // Recommend irrigation if growing window deficit exceeds 30 mm (mm/month rate)
    irrigation = deficit > 30 ? Math.round(deficit / Gt) : 0;
  }

  return {
    score,
    fit,
    factors: { temp, rain, ph, frost, photo, annual, chill, drain, shade },
    window: { start: best, months: Gt, deficit, irrigation }
  };
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
