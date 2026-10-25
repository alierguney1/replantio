// Climate risk from the daily record: what the 10-year normals hide.
// scoring.js rates every species on monthly NORMALS, which answers "can it
// grow here in an average year?". Restoration plantings fail in the other
// years: the drought summer after planting, the late frost on new shoots, the
// mild winter that never breaks a fruit tree's dormancy. The app already
// downloads ten years of DAILY ERA5 for the site; this module reads the days
// the normals average away. Everything here is display-side: scoreSpecies
// never reads it, so the suitability score and the ranking do not move.
//
// Variability over averages is an old lesson in climate impacts (Katz &
// Brown 1992, Climatic Change 21:289, "variability is more important than
// averages") and in tree distributions specifically (Zimmermann et al. 2009,
// PNAS 106:19723: climatic extremes improve predictions of tree species
// ranges beyond means).

import { aggregateClimate, scoreSpecies, daylength } from "./scoring.js";

const DAY_MS = 864e5;
const dayNum = s => Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10)) / DAY_MS;
const doyOf = d => Math.floor((d * DAY_MS - Date.UTC(new Date(d * DAY_MS).getUTCFullYear(), 0, 1)) / DAY_MS) + 1;
const median = v => {
  if (!v.length) return null;
  const s = [...v].sort((a, b) => a - b), h = (s.length - 1) / 2;
  return (s[Math.floor(h)] + s[Math.ceil(h)]) / 2;
};
// R type 7 (linear between order statistics), the default in R's quantile()
export function percentile(v, p) {
  if (!v.length) return null;
  const s = [...v].sort((a, b) => a - b), h = (s.length - 1) * p, lo = Math.floor(h);
  return s[lo] + (h - lo) * (s[Math.min(lo + 1, s.length - 1)] - s[lo]);
}

// Warmth-oriented calendar, the same rule koppenGeigerClass uses: summer is
// the warmer of AMJJAS / ONDJFM (Peel et al. 2007), so no latitude input and
// no hemisphere switch can misfile a site.
export function northernCalendar(tavg) {
  const half = idx => idx.reduce((a, i) => a + tavg[i], 0) / 6;
  return half([3, 4, 5, 6, 7, 8]) >= half([9, 10, 11, 0, 1, 2]);
}

// ---------------------------------------------------------------------------
// Year-by-year climates and suitability
// ---------------------------------------------------------------------------

// Per-calendar-year monthly climates from an Open-Meteo daily payload. Only
// complete years count (>= 365 days, every month with valid days): a
// truncated first or last year must never pose as a real dry year.
export function yearlyClimates(daily) {
  const time = daily?.time;
  if (!time?.length) return [];
  const byYear = new Map();
  for (let i = 0; i < time.length; i++) {
    const y = time[i].slice(0, 4);
    if (!byYear.has(y)) byYear.set(y, []);
    byYear.get(y).push(i);
  }
  const keys = Object.keys(daily).filter(k => Array.isArray(daily[k]) && daily[k].length === time.length);
  const out = [];
  for (const [y, ix] of byYear) {
    if (ix.length < 365) continue;
    const sub = {};
    for (const k of keys) sub[k] = ix.map(i => daily[k][i]);
    try {
      const a = aggregateClimate(sub);
      out.push({ year: +y, tavg: a.tavg, tmin: a.tmin, prec: a.prec, absMin: a.absMin,
        annualRain: a.annualRain, meanTemp: a.meanTemp });
    } catch { /* a month without valid days: not a scorable year */ }
  }
  return out.sort((a, b) => a.year - b.year);
}

// One site object per year: the analysed site with that year's own monthly
// weather swapped in. Everything else (pH, soil, slope, irrigation) is the
// site's, so a year can only fail on weather. Built once per rescore, not
// per species.
export function yearSites(site, years) {
  return years.map(y => ({ ...site, tavg: y.tavg, tmin: y.tmin, prec: y.prec, absMin: y.absMin, year: y.year }));
}

export const SUITABLE = 0.4; // grade(): "Suitable" starts above 0.4

// The same EcoCrop rules, applied to each year's own weather. A frequency over
// the record, not a probability: ten years cannot pin a tail. For annual crops
// each year is a season of its own; for perennials it reads as the share of
// years a new planting would have met inside its envelope, and a single
// frost-kill year is enough to lose established trees.
export function yearlyFit(sp, ysites, ev = null) {
  const years = [];
  let ok = 0;
  for (const s of ysites) {
    const r = scoreSpecies(sp, s, ev);
    const good = r.score > SUITABLE;
    if (good) ok++;
    years.push({ year: s.year, score: r.score, why: good ? null : limitingFactor(sp, r, s) });
  }
  return { ok, n: years.length, years };
}

// Which year-varying factor sank a year. Frost and the annual regime gate are
// multiplicative kills, temperature and rain the Liebig minimum. Site
// constants (pH, photoperiod, slope, soil) cannot explain one year failing
// when the next passes, so they are never named. Ties go to the most
// physical cause: frost, then rain, then temperature.
export function limitingFactor(sp, r, site) {
  const f = r.factors;
  const cands = [["frost", f.frost ?? 1], ["rain", f.rain], ["temp", f.temp], ["annual", f.annual ?? 1], ["chill", f.chill ?? 1]];
  let [k, v] = cands[0];
  for (const c of cands) if (c[1] < v) [k, v] = c;
  if (!(v < 1)) return null;
  const b = r.basis;
  if (k === "frost") return "frost";
  if (k === "chill") return "mild winter";
  if (k === "rain") return b && b.rain < sp.rain[1] ? "dry" : "wet";
  if (k === "temp") return b && b.temp < sp.temp[1] ? "cold" : "hot";
  const mean = site.tavg.reduce((a, x) => a + x, 0) / 12;
  return mean < sp.temp[0] ? "cold" : "hot";
}

// ---------------------------------------------------------------------------
// Frost calendar
// ---------------------------------------------------------------------------

// Last spring and first autumn frost from daily minima, 0 C on the 2 m daily
// minimum (the "light freeze" of US frost climatologies). Seasons are
// anchored on the warmest month of the normals: the last frost in the 182
// days before mid-warmest-month, the first in the 182 days after it. Only
// windows the record fully covers are counted. A season without frost reads
// as -Infinity (spring) / +Infinity (autumn), so medians fall out of plain
// order statistics. Offsets are days from the anchor.
//
// Scale honesty: reanalysis grid minima run warm against radiative valley
// frosts (scoring.js FROST_MARGIN); the dates are the grid's, and a frost
// pocket can freeze on nights the grid reads +2 C.
export function frostCalendar(daily, normalsTavg, thr = 0) {
  const time = daily?.time, tmin = daily?.temperature_2m_min;
  if (!time?.length || !Array.isArray(tmin) || normalsTavg?.length !== 12) return null;
  const d0 = dayNum(time[0]), d1 = dayNum(time[time.length - 1]);
  const val = new Float64Array(d1 - d0 + 1).fill(NaN);
  for (let i = 0; i < time.length; i++) if (tmin[i] != null) val[dayNum(time[i]) - d0] = tmin[i];
  const W = normalsTavg.indexOf(Math.max(...normalsTavg));
  const y0 = +time[0].slice(0, 4), y1 = +time[time.length - 1].slice(0, 4);
  const springs = [], autumns = [], seasons = [];
  for (let y = y0 - 1; y <= y1 + 1; y++) {
    const c = Date.UTC(y, W, 15) / DAY_MS;
    const sOk = c - 181 >= d0 && c <= d1, aOk = c + 1 >= d0 && c + 182 <= d1;
    let last = -Infinity, first = Infinity;
    // a frost is filed under the calendar year it fell in (a southern-type
    // spring runs July to January)
    const yearAt = off => new Date((c + (Number.isFinite(off) ? off : 0)) * DAY_MS).getUTCFullYear();
    if (sOk) {
      for (let d = c - 181; d <= c; d++) if (val[d - d0] <= thr) last = d - c;
      springs.push({ year: yearAt(last), off: last });
    }
    if (aOk) {
      for (let d = c + 1; d <= c + 182; d++) if (val[d - d0] <= thr) { first = d - c; break; }
      autumns.push({ year: yearAt(first), off: first });
    }
    if (sOk && aOk && Number.isFinite(last) && Number.isFinite(first)) seasons.push(first - last - 1);
  }
  if (!springs.length && !autumns.length) return null;
  const sF = springs.filter(s => Number.isFinite(s.off)), aF = autumns.filter(a => Number.isFinite(a.off));
  const latest = sF.reduce((m, s) => (m && m.off >= s.off ? m : s), null);
  const earliest = aF.reduce((m, a) => (m && m.off <= a.off ? m : a), null);
  const medOff = arr => {
    const m = median(arr.map(x => x.off));
    return m == null || !Number.isFinite(m) ? null : Math.round(m);
  };
  const out = {
    anchorMonth: W,
    springs: springs.length, springFrosts: sF.length,
    autumns: autumns.length, autumnFrosts: aF.length,
    lastSpring: { median: medOff(springs), latest: latest?.off ?? null, latestYear: latest?.year ?? null },
    firstAutumn: { median: medOff(autumns), earliest: earliest?.off ?? null, earliestYear: earliest?.year ?? null },
    // the frost-free run only where both ends exist in at least half the seasons
    season: seasons.length * 2 >= Math.max(springs.length, autumns.length) ? Math.round(median(seasons)) : null,
  };
  out.frostFree = !sF.length && !aF.length;
  // frost can strike in every month (high tropical mountains, tundra): no
  // frost-free season worth naming
  out.yearRound = out.season != null && out.season < 30;
  return out;
}

// Calendar day for a frost offset, on a non-leap reference year.
export function frostDate(anchorMonth, off) {
  if (off == null || !Number.isFinite(off)) return null;
  const d = new Date(Date.UTC(2023, anchorMonth, 15) + off * DAY_MS);
  return { month: d.getUTCMonth(), day: d.getUTCDate() };
}

// ---------------------------------------------------------------------------
// Winter chill (temperate fruit and nut trees)
// ---------------------------------------------------------------------------

// Hourly temperatures from daily extremes, Linvill (1990, HortScience
// 25:14-16): a sine from sunrise to sunset peaking two hours after solar
// noon, then logarithmic cooling through the night to the next day's
// minimum. Sunrise and sunset come from the Forsythe daylength already used
// for photoperiod (solar time; longitude and the equation of time shift
// clock hours, not chill totals). Near-polar days (daylength < 0.5 h or
// > 23.5 h) fall back to a plain diurnal cosine. Returns 24 values per day.
export function hourlyTemps(tmin, tmax, doy, lat) {
  const n = tmin.length, out = new Float64Array(n * 24);
  const dl = doy.map(d => Math.max(0, Math.min(24, daylength(lat, d))));
  const tss = i => tmin[i] + (tmax[i] - tmin[i]) * Math.sin(Math.PI * dl[i] / (dl[i] + 4));
  for (let i = 0; i < n; i++) {
    const D = dl[i], lo = tmin[i], hi = tmax[i];
    if (D < 0.5 || D > 23.5) {
      for (let h = 0; h < 24; h++) out[i * 24 + h] = lo + (hi - lo) * (1 - Math.cos(2 * Math.PI * (h - 5) / 24)) / 2;
      continue;
    }
    const sr = 12 - D / 2, ss = 12 + D / 2;
    const p = i > 0 ? i - 1 : i, q = i < n - 1 ? i + 1 : i;
    for (let h = 0; h < 24; h++) {
      let t;
      if (h < sr) { // before sunrise: yesterday's sunset curve cooling into today's minimum
        const night = Math.max(1, 24 - dl[p]), since = h + 24 - (12 + dl[p] / 2);
        t = tss(p) - (tss(p) - lo) * Math.min(1, Math.log(1 + since) / Math.log(1 + night));
      } else if (h <= ss) {
        t = lo + (hi - lo) * Math.sin(Math.PI * (h - sr) / (D + 4));
      } else { // after sunset: cooling toward tomorrow's minimum
        t = tss(i) - (tss(i) - tmin[q]) * Math.min(1, Math.log(1 + h - ss) / Math.log(1 + Math.max(1, 24 - D)));
      }
      out[i * 24 + h] = t;
    }
  }
  return out;
}

// Dynamic Model (Fishman, Erez & Couvillon 1987a,b; J. Theor. Biol. 124:473
// and 126:309): chill accrues as a thermally reversible intermediate that
// warm hours destroy, banked as a permanent "chill portion" once it reaches
// a critical level. Constants as distributed by Erez & Fishman and in chillR
// (Luedeling). Of the common chill models it best explained walnut phenology
// in a validation against historic records (Luedeling et al. 2009, Agric.
// For. Meteorol. 149:1854).
const E0 = 4153.5, E1 = 12888.8, A0 = 139500, A1 = 2.567e18, SLP = 1.6, TETMLT = 277;
const AA = A0 / A1, EE = E1 - E0;
export function chillPortions(hourly) {
  let x = 0, xiPrev = 0, cp = 0;
  for (let i = 0; i < hourly.length; i++) {
    const tk = hourly[i] + 273;
    const sr = Math.exp(SLP * TETMLT * (tk - TETMLT) / tk);
    const xi = sr / (1 + sr);
    const xs = AA * Math.exp(EE / tk);
    const ak1 = A1 * Math.exp(-E1 / tk);
    const s = x >= 1 ? x * (1 - xiPrev) : x; // a banked portion leaves (1 - xi) of the intermediate behind
    x = xs - (xs - s) * Math.exp(-ak1);
    if (x >= 1) cp += x * xi;
    xiPrev = xi;
  }
  return cp;
}

// Chilling Hours: hours between 0 and 7.2 C (Weinberger's 1950 45 F threshold,
// with the 0 C floor chillR uses). The unit most nursery catalogues still
// quote; it overstates warm-winter chill relative to the Dynamic Model, which
// is why both are shown.
export function chillingHours(hourly) {
  let n = 0;
  for (let i = 0; i < hourly.length; i++) if (hourly[i] >= 0 && hourly[i] <= 7.2) n++;
  return n;
}

// Winter chill per complete winter: 1 Nov - end of Feb on a northern-type
// calendar (the window of Luedeling, Zhang & Girvetz 2009, PLoS ONE 4:e6166),
// shifted by half a year (1 May - 31 Aug) on a southern-type one. Safe Winter
// Chill is their 10th percentile of winter totals: the chill a grower can
// count on in 9 winters of 10. With ~9-10 winters on record the 10th percentile sits near the
// poorest winter; it is reported as such, not as a fitted tail.
// tmax may be missing (older payloads): it is then rebuilt as 2*mean - min.
export function winterChill(daily, lat, normalsTavg) {
  const time = daily?.time, tmin = daily?.temperature_2m_min;
  const tmax = daily?.temperature_2m_max, tmean = daily?.temperature_2m_mean;
  if (!time?.length || !Array.isArray(tmin) || normalsTavg?.length !== 12 || lat == null) return null;
  const northern = northernCalendar(normalsTavg);
  const index = new Map();
  for (let i = 0; i < time.length; i++) index.set(dayNum(time[i]), i);
  let approxTmax = false;
  const hiOf = i => {
    if (tmax?.[i] != null) return tmax[i];
    approxTmax = true;
    return tmean?.[i] != null ? 2 * tmean[i] - tmin[i] : null;
  };
  const y0 = +time[0].slice(0, 4), y1 = +time[time.length - 1].slice(0, 4);
  const winters = [];
  for (let y = y0 - 1; y <= y1; y++) {
    const a = northern ? Date.UTC(y, 10, 1) / DAY_MS : Date.UTC(y, 4, 1) / DAY_MS;
    const b = northern ? Date.UTC(y + 1, 2, 1) / DAY_MS - 1 : Date.UTC(y, 8, 1) / DAY_MS - 1;
    const lo = [], hi = [], doy = [];
    let complete = true;
    for (let d = a; d <= b; d++) {
      const i = index.get(d);
      const h = i == null ? null : hiOf(i);
      if (i == null || tmin[i] == null || h == null) { complete = false; break; }
      lo.push(tmin[i]); hi.push(Math.max(h, tmin[i])); doy.push(doyOf(d));
    }
    if (!complete) continue;
    const hours = hourlyTemps(lo, hi, doy, lat);
    winters.push({ year: y, cp: chillPortions(hours), ch: chillingHours(hours) });
  }
  if (!winters.length) return null;
  const cps = winters.map(w => w.cp), chs = winters.map(w => w.ch);
  return {
    northern, approxTmax, n: winters.length, winters,
    safeCP: percentile(cps, 0.1), medianCP: median(cps),
    safeCH: percentile(chs, 0.1), medianCH: median(chs),
  };
}

// ---------------------------------------------------------------------------
// 2040s outlook: delta (change-factor) method
// ---------------------------------------------------------------------------

// Monthly means of any daily variable (nulls skipped).
export function monthlyMeans(daily, key) {
  const v = daily?.[key], time = daily?.time;
  if (!Array.isArray(v) || !time?.length) return null;
  const s = Array(12).fill(0), n = Array(12).fill(0);
  for (let i = 0; i < time.length; i++) {
    if (v[i] == null) continue;
    const m = +time[i].slice(5, 7) - 1;
    s[m] += v[i]; n[m]++;
  }
  return n.some(x => x === 0) ? null : s.map((x, m) => x / n[m]);
}

// Mean of each complete year's lowest daily minimum: a far steadier extreme
// to take a change from than one ten-year record low.
export function meanAnnualMin(daily) {
  const ys = yearlyClimates(daily).map(y => y.absMin).filter(v => v != null);
  return ys.length ? ys.reduce((a, b) => a + b, 0) / ys.length : null;
}

// The model's own 2015-2024 run is its baseline; only its CHANGE to the
// 2040s is applied to the observed ERA5 normals, additive for temperature and
// multiplicative for precipitation: the delta method used to downscale GCMs
// for EcoCrop studies (Ramirez-Villegas & Jarvis 2010, CIAT Decision and
// Policy Analysis Working Paper 1; Hay, Wilby & Leavesley 2000, J. Am. Water
// Resour. Assoc. 36:387). Comparing raw model output with ERA5 instead mixes
// the model's bias at one grid point (often degrees in relief) into what is
// shown as climate change.
// Precipitation guards: a ratio needs a baseline to divide by, so months with
// under 10 mm in the model baseline take the additive change instead, and
// ratios are bounded to [0.2, 5].
// obs: ERA5 normals (tavg, tmin, prec, absMin); base/fut: aggregateClimate of
// the model windows, each optionally carrying absMinMean and tmaxMean.
export function deltaFuture(obs, base, fut) {
  const dTavg = obs.tavg.map((_, m) => fut.tavg[m] - base.tavg[m]);
  const dTmin = obs.tmin.map((_, m) => fut.tmin[m] - base.tmin[m]);
  const dTmax = base.tmaxMean && fut.tmaxMean ? base.tmaxMean.map((b, m) => fut.tmaxMean[m] - b) : dTavg;
  const tavg = obs.tavg.map((t, m) => t + dTavg[m]);
  const tmin = obs.tmin.map((t, m) => t + dTmin[m]);
  const prec = obs.prec.map((p, m) => {
    const b = base.prec[m], f = fut.prec[m];
    if (b >= 10) return p * Math.min(5, Math.max(0.2, f / b));
    return Math.max(0, p + (f - b));
  });
  const coldest = obs.tmin.indexOf(Math.min(...obs.tmin));
  const dAbs = base.absMinMean != null && fut.absMinMean != null ? fut.absMinMean - base.absMinMean : dTmin[coldest];
  const annualRain = prec.reduce((a, b) => a + b, 0);
  const obsRain = obs.prec.reduce((a, b) => a + b, 0);
  const meanTemp = tavg.reduce((a, b) => a + b, 0) / 12;
  return {
    tavg, tmin, prec, annualRain, meanTemp,
    absMin: obs.absMin != null ? obs.absMin + dAbs : null,
    dT: dTavg.reduce((a, b) => a + b, 0) / 12,
    dP: obsRain > 0 ? annualRain / obsRain - 1 : null,
    dTavg, dTmin, dTmax, dAbsMin: dAbs,
  };
}

// The observed daily series with a monthly change added: the input for 2040s
// winter chill, so the projection keeps ERA5's real day-to-day weather.
export function shiftDaily(daily, dTmin, dTmax, dTavg) {
  const time = daily.time, m = time.map(t => +t.slice(5, 7) - 1);
  const add = (key, d) => Array.isArray(daily[key]) ? daily[key].map((v, i) => v == null ? v : v + d[m[i]]) : undefined;
  return { time, temperature_2m_min: add("temperature_2m_min", dTmin),
    temperature_2m_max: add("temperature_2m_max", dTmax), temperature_2m_mean: add("temperature_2m_mean", dTavg) };
}

// ---------------------------------------------------------------------------
// Climate-adjusted provenancing and terrain cells
// ---------------------------------------------------------------------------

// Environmental lapse rate of the ICAO standard atmosphere. Observed surface
// lapse rates run ~4-7 C/km by season and region (Rolland 2003, J. Climate
// 16:1032), so results are rounded and worded as approximate.
export const LAPSE_C_PER_M = 0.0065;

// Elevation drop whose present-day temperature matches the projected warming:
// the seed source a planting can borrow from today. Climate-adjusted
// provenancing mixes such pre-adapted seed into local seed (Prober et al.
// 2015, Front. Ecol. Evol. 3:65). Rounded to 50 m; null when there is no
// warming to adapt to.
export function elevationAnalogue(dT) {
  if (!(dT > 0.2)) return null;
  return Math.max(50, Math.round(dT / LAPSE_C_PER_M / 50) * 50);
}

// A terrain cell inside the drawn area: the analysed site's climate (ERA5,
// already downscaled by Open-Meteo to the centroid's elevation) shifted by the
// lapse rate for the cell's elevation difference, with the cell's own slope
// and aspect. Rain is held constant: orographic precipitation is not
// something a lapse rate knows.
export function cellSite(site, dz, terrain) {
  const dt = -LAPSE_C_PER_M * dz;
  return { ...site, tavg: site.tavg.map(t => t + dt), tmin: site.tmin.map(t => t + dt),
    absMin: site.absMin != null ? site.absMin + dt : null, terrain };
}

// Slope (degrees) and downslope aspect (compass degrees) for every node of a
// row-major elevation grid (row 0 = north), central differences inside and
// one-sided at the edges; dx/dy are node spacings in metres. Same conventions
// as the app's 3x3 DEM terrain probe.
export function gridTerrain(elev, cols, rows, dx, dy) {
  const at = (r, c) => elev[r * cols + c];
  const out = [];
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const c0 = Math.max(0, c - 1), c1 = Math.min(cols - 1, c + 1);
    const r0 = Math.max(0, r - 1), r1 = Math.min(rows - 1, r + 1);
    const gx = c1 > c0 ? (at(r, c1) - at(r, c0)) / ((c1 - c0) * dx) : 0; // uphill east
    const gy = r1 > r0 ? (at(r0, c) - at(r1, c)) / ((r1 - r0) * dy) : 0; // uphill north
    const slope = Math.atan(Math.hypot(gx, gy)) * 180 / Math.PI;
    const aspectDeg = Math.round((Math.atan2(-gx, -gy) * 180 / Math.PI + 360) % 360);
    out.push({ slope, aspectDeg });
  }
  return out;
}
