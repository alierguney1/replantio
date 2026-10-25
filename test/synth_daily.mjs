// Deterministic synthetic daily weather for fixtures, shaped like an
// Open-Meteo daily payload. NOT observations: a seeded generator that
// reproduces given monthly normals on average, with year-to-year anomalies
// (a per-year temperature offset and rain factor) and day-to-day AR(1)
// noise, so year-by-year, frost and chill code can be exercised offline.
// Monthly means are interpolated between mid-month anchors (a smooth annual
// cycle); each month's rain falls on its wet days.

export function mulberry32(a) {
  return function () {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | a) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

const MID = [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349];
const smooth = (arr, doy) => { // circular linear interpolation between mid-month anchors
  let i = MID.findIndex(m => m > doy) - 1;
  if (i === -2) i = 11;
  const j = (i + 1) % 12;
  const a = i < 0 ? MID[11] - 365 : MID[i], b = j === 0 && i === 11 ? MID[0] + 365 : MID[j];
  const ii = (i + 12) % 12;
  return arr[ii] + (arr[j] - arr[ii]) * (doy - a) / (b - a);
};

// normals: { tavg[12], tmin[12], prec[12] (mm/month), et0?[12] (mm/month) }
// opts: { years: [2015, ...], seed, sdYear (C), rainCv, sdDay (C), wetFrac,
//         yearOffsets?: {year: dT}, rainFactors?: {year: f}, extremes?: [{date, tmin}] }
export function synthDaily(normals, opts = {}) {
  const years = opts.years ?? [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024];
  const rnd = mulberry32(opts.seed ?? 7);
  const gauss = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());
  const sdYear = opts.sdYear ?? 0.6, rainCv = opts.rainCv ?? 0.22, sdDay = opts.sdDay ?? 2.0;
  const wetFrac = opts.wetFrac ?? 0.35;
  const out = { time: [], temperature_2m_mean: [], temperature_2m_min: [], temperature_2m_max: [],
    precipitation_sum: [], et0_fao_evapotranspiration: normals.et0 ? [] : undefined };
  const tavgAt = d => smooth(normals.tavg, d), tminAt = d => smooth(normals.tmin, d);
  let ar = 0;
  for (const y of years) {
    const dT = opts.yearOffsets?.[y] ?? gauss() * sdYear;
    const rf = opts.rainFactors?.[y] ?? Math.max(0.3, 1 + gauss() * rainCv);
    const leap = (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
    const nDays = leap ? 366 : 365;
    // pre-draw each month's wet days so the month total matches normal * rf
    const wet = Array.from({ length: nDays }, () => rnd() < wetFrac);
    const monthWet = Array(12).fill(0), monthOf = [];
    for (let d = 0; d < nDays; d++) {
      const m = new Date(Date.UTC(y, 0, 1 + d)).getUTCMonth();
      monthOf.push(m);
      if (wet[d]) monthWet[m]++;
    }
    const weights = wet.map(w => (w ? -Math.log(rnd() + 1e-12) : 0));
    const wsum = Array(12).fill(0);
    weights.forEach((w, d) => { wsum[monthOf[d]] += w; });
    for (let d = 0; d < nDays; d++) {
      const date = new Date(Date.UTC(y, 0, 1 + d));
      const iso = date.toISOString().slice(0, 10);
      const doy = d + 1 - (leap && d >= 59 ? 1 : 0);
      ar = 0.7 * ar + Math.sqrt(1 - 0.49) * gauss() * sdDay;
      const tm = tavgAt(doy) + dT + ar;
      const range = Math.max(2, 2 * (tavgAt(doy) - tminAt(doy)));
      let tn = tm - range / 2, tx = tm + range / 2;
      const ext = opts.extremes?.find(e => e.date === iso);
      if (ext) { tn = ext.tmin; tx = Math.max(tx, tn + 2); }
      const m = monthOf[d];
      const p = weights[d] && wsum[m] ? normals.prec[m] * rf * weights[d] / wsum[m] : 0;
      out.time.push(iso);
      out.temperature_2m_mean.push(+tm.toFixed(2));
      out.temperature_2m_min.push(+tn.toFixed(2));
      out.temperature_2m_max.push(+tx.toFixed(2));
      out.precipitation_sum.push(+p.toFixed(2));
      if (out.et0_fao_evapotranspiration) {
        const days = new Date(Date.UTC(y, m + 1, 0)).getUTCDate();
        out.et0_fao_evapotranspiration.push(+(normals.et0[m] / days).toFixed(3));
      }
    }
  }
  if (!out.et0_fao_evapotranspiration) delete out.et0_fao_evapotranspiration;
  return out;
}
