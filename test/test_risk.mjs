// Climate-risk layer (risk.js): year-by-year fit, frost calendar, winter
// chill, delta-method 2040s, provenancing and terrain cells.
// Run: node test/test_risk.mjs
import assert from "node:assert";
import { readFileSync } from "node:fs";
import { scoreSpecies, aggregateClimate } from "../scoring.js";
import {
  percentile, northernCalendar, yearlyClimates, yearSites, yearlyFit, limitingFactor, SUITABLE,
  frostCalendar, frostDate, hourlyTemps, chillPortions, chillingHours, winterChill,
  monthlyMeans, meanAnnualMin, deltaFuture, shiftDaily, LAPSE_C_PER_M, elevationAnalogue, cellSite, gridTerrain,
} from "../risk.js";
import { synthDaily } from "./synth_daily.mjs";

const species = JSON.parse(readFileSync(new URL("../data/species.json", import.meta.url)));
const by = sci => species.find(s => s.sci === sci);
const close = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: got ${a}, want ${b}±${tol}`);

// a daily payload from a function of the date
function series(from, to, fn) {
  const out = { time: [], temperature_2m_mean: [], temperature_2m_min: [], temperature_2m_max: [], precipitation_sum: [] };
  for (let t = Date.UTC(...from); t <= Date.UTC(...to); t += 864e5) {
    const d = new Date(t), iso = d.toISOString().slice(0, 10);
    const v = fn(d, iso);
    out.time.push(iso);
    out.temperature_2m_min.push(v.tmin);
    out.temperature_2m_max.push(v.tmax ?? v.tmin + 10);
    out.temperature_2m_mean.push(v.tmean ?? (v.tmin + (v.tmax ?? v.tmin + 10)) / 2);
    out.precipitation_sum.push(v.p ?? 1);
  }
  return out;
}

// fixture normals (same values as test/check.mjs)
const berlin = {
  lat: 52.5,
  tavg: [0.6, 1.5, 4.9, 9.4, 14.4, 17.5, 19.5, 19.2, 14.9, 10.2, 5.3, 1.7],
  tmin: [-2.5, -2.2, 0.9, 4.4, 9.0, 12.4, 14.5, 14.2, 10.7, 6.7, 2.5, -1.0],
  prec: [43, 37, 41, 36, 54, 69, 56, 58, 45, 44, 45, 55],
  ph: 6.0, absMin: -15,
};
const saoPaulo = {
  lat: -23.5,
  tavg: [22.1, 22.4, 21.7, 20.1, 17.6, 16.5, 16.1, 17.5, 18.4, 19.4, 20.4, 21.4],
  tmin: [18.0, 18.2, 17.6, 15.8, 13.0, 11.8, 11.3, 12.4, 13.5, 14.8, 15.9, 17.2],
  prec: [240, 215, 160, 75, 60, 50, 45, 40, 80, 125, 145, 200],
  ph: 5.3, absMin: 3,
};
const malatya = {
  lat: 38.4498,
  tavg: [1.7, 4.5, 8.8, 14.9, 19.8, 26.2, 29.5, 30, 25.3, 18.1, 10, 4],
  tmin: [-1.4, 0.8, 4.1, 9.4, 14, 19.8, 22.8, 23.5, 19.5, 13.4, 6.4, 1.2],
  prec: [72, 42, 80, 38, 47, 7, 0, 2, 4, 21, 48, 54],
  ph: null, absMin: -12.5,
};

// --- helpers
assert.equal(percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.1), 1.9, "R type-7 10th percentile");
assert.equal(percentile([5], 0.1), 5);
assert.equal(percentile([], 0.1), null);
assert.equal(northernCalendar(berlin.tavg), true, "Berlin keeps a northern calendar");
assert.equal(northernCalendar(saoPaulo.tavg), false, "São Paulo is southern by warmth, no latitude needed");

// --- scoreSpecies exposes the climate it scored (dormant trees read the full year)
{
  const oak = by("Quercus robur"), maple = by("Acer saccharum");
  const annual = berlin.prec.reduce((a, b) => a + b, 0);
  const r = scoreSpecies(oak, berlin);
  close(r.basis.rain, annual, 1e-9, "dormant oak is scored on annual rain, and basis says so");
  assert.ok(r.window.months < 12, "while its temperature window is the warm season");
  // sugar maple: the old strip summed the 6-month window (326 mm), drawing the
  // tick OUTSIDE its 500 mm minimum while the scorer read 583 mm
  const m = scoreSpecies(maple, berlin);
  close(m.basis.rain, annual, 1e-9, "sugar maple basis is the scored annual rain");
  assert.ok(m.basis.rain > maple.rain[0], "so its strip tick lands inside the envelope");
  const bean = by("Phaseolus vulgaris"), b = scoreSpecies(bean, berlin);
  let wr = 0; for (let k = 0; k < b.window.months; k++) wr += berlin.prec[(b.window.start + k) % 12];
  close(b.basis.rain, wr, 1e-9, "a short-cycle crop's basis is its window rain");
  let wt = 0; for (let k = 0; k < b.window.months; k++) wt += berlin.tavg[(b.window.start + k) % 12];
  close(b.basis.temp, wt / b.window.months, 1e-9, "basis temperature is the window mean");
  // apricot (KTMPR -5, 180-240 day cycle) is a window species: the irrigated
  // score lifts rain to its optimum, the basis keeps the rain that falls
  const irr = scoreSpecies(by("Prunus armeniaca"), { ...malatya, irrigated: true }, { countryNative: true });
  let iw = 0; for (let k = 0; k < irr.window.months; k++) iw += malatya.prec[(irr.window.start + k) % 12];
  assert.equal(irr.factors.rain, 1, "irrigation lifts the rain factor");
  close(irr.basis.rain, iw, 1e-9, "basis is rain that falls, before the irrigation lift");
}

// --- yearlyClimates: complete calendar years only
{
  const d = synthDaily(berlin, { years: [2015, 2016, 2017], seed: 3 });
  // truncate the last year: 2017 must be dropped, never posed as a dry year
  const cut = d.time.indexOf("2017-06-30");
  const trunc = Object.fromEntries(Object.entries(d).map(([k, v]) => [k, v.slice(0, cut + 1)]));
  const ys = yearlyClimates(trunc);
  assert.deepEqual(ys.map(y => y.year), [2015, 2016], "a truncated year is skipped");
  const full = yearlyClimates(d);
  assert.equal(full.length, 3);
  const agg = aggregateClimate(d);
  close(full.reduce((a, y) => a + y.annualRain, 0) / 3, agg.annualRain, 0.01, "years average back to the normals");
  close(full.reduce((a, y) => a + y.meanTemp, 0) / 3, agg.meanTemp, 0.01, "temperatures too");
  assert.ok(full.every(y => y.absMin >= agg.absMin), "each year's low is no lower than the record low");
  assert.equal(yearlyClimates({}).length, 0);
}

// --- year-by-year fit: a drought year and a frost year are named for what they are
{
  const years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024];
  // Malatya apricot, rainfed: the 416 mm normals already zero the rain factor;
  // year by year it must fail on rain, never on a site constant
  const d = synthDaily(malatya, { years, seed: 11 });
  const ys = yearlyClimates(d);
  assert.equal(ys.length, 10);
  const apricot = by("Prunus armeniaca");
  const site = { ...malatya, ...aggregateClimate(d) };
  const rainfed = yearlyFit(apricot, yearSites(site, ys), { countryNative: true });
  assert.equal(rainfed.n, 10);
  assert.ok(rainfed.ok <= 2, `rainfed Malatya apricot fits few years: ${rainfed.ok}`);
  assert.ok(rainfed.years.filter(y => y.why).every(y => y.why === "dry"), "failing years are dry years");
  const irrigated = yearlyFit(apricot, yearSites({ ...site, irrigated: true }, ys), { countryNative: true });
  assert.ok(irrigated.ok >= 9, `irrigation carries the apricot through the dry years: ${irrigated.ok}`);

  // a probe with a narrow rain band; one year at 40% rain, one with a -25 C night
  const probe = { sci: "probe", temp: [5, 10, 24, 35], rain: [450, 520, 900, 1400], ph: null,
    ktmpr: -18, ktmp: -3, photo: null, cycle: [null, null], gclass: "temperate_medium", wood: "broadleaf",
    tree: true, decid: true };
  const db = synthDaily(berlin, { years, seed: 5, sdYear: 0, rainCv: 0, rainFactors: { 2018: 0.4 },
    extremes: [{ date: "2021-02-10", tmin: -25 }] });
  const yb = yearlyClimates(db);
  const fit = yearlyFit(probe, yearSites({ ...berlin, ...aggregateClimate(db) }, yb));
  const why = Object.fromEntries(fit.years.map(y => [y.year, y.why]));
  assert.equal(why[2018], "dry", "the 40%-rain year fails dry");
  assert.equal(why[2021], "frost", "the -25 C night fails on frost");
  assert.equal(fit.ok, 8, "the other eight years fit");
  assert.ok(fit.years.every(y => (y.score > SUITABLE) === (y.why === null)), "a reason exactly when a year fails");
  // the normals score never moves: yearlyFit is display-side only
  const before = scoreSpecies(probe, berlin).score;
  yearlyFit(probe, yearSites(berlin, yb));
  assert.equal(scoreSpecies(probe, berlin).score, before);
}

// --- limitingFactor directions
{
  const sp = { rain: [400, 600, 900, 1200], temp: [5, 12, 24, 32] };
  const site = { tavg: Array(12).fill(15) };
  const R = (factors, basis) => ({ factors: { frost: 1, annual: 1, chill: null, temp: 1, rain: 1, ...factors }, basis });
  assert.equal(limitingFactor(sp, R({ rain: 0.2 }, { rain: 450, temp: 15 }), site), "dry");
  assert.equal(limitingFactor(sp, R({ rain: 0.2 }, { rain: 1150, temp: 15 }), site), "wet");
  assert.equal(limitingFactor(sp, R({ temp: 0.1 }, { rain: 700, temp: 6 }), site), "cold");
  assert.equal(limitingFactor(sp, R({ temp: 0.1 }, { rain: 700, temp: 31 }), site), "hot");
  assert.equal(limitingFactor(sp, R({ frost: 0, rain: 0 }, { rain: 450, temp: 15 }), site), "frost", "frost wins ties: it kills");
  assert.equal(limitingFactor(sp, R({ chill: 0.3 }, { rain: 700, temp: 15 }), site), "mild winter");
  assert.equal(limitingFactor(sp, R({}, { rain: 700, temp: 15 }), site), null, "nothing year-varying failed");
}

// --- frost calendar: last spring and first autumn frost
{
  // northern-type: frost on 10 Apr and 20 Oct every year, 2015-2020
  const nh = series([2015, 0, 1], [2020, 11, 31], d => {
    const md = d.toISOString().slice(5, 10);
    return { tmin: md === "04-10" || md === "10-20" ? -1 : 5 };
  });
  const f = frostCalendar(nh, berlin.tavg);
  assert.equal(f.anchorMonth, 6, "anchored on July, Berlin's warmest month");
  assert.deepEqual(frostDate(f.anchorMonth, f.lastSpring.median), { month: 3, day: 10 }, "last spring frost 10 Apr");
  assert.deepEqual(frostDate(f.anchorMonth, f.firstAutumn.median), { month: 9, day: 20 }, "first autumn frost 20 Oct");
  assert.equal(f.season, 192, "frost-free days strictly between 10 Apr and 20 Oct");
  assert.equal(f.frostFree, false);
  assert.equal(f.yearRound, false);
  assert.equal(f.springs, 6, "six complete springs on record");
  // one late year sets the latest date and its year
  const late = series([2015, 0, 1], [2020, 11, 31], d => {
    const md = d.toISOString().slice(5, 10), y = d.getUTCFullYear();
    return { tmin: md === "04-10" || md === "10-20" || (y === 2017 && md === "05-03") ? -1 : 5 };
  });
  const fl = frostCalendar(late, berlin.tavg);
  assert.deepEqual(frostDate(fl.anchorMonth, fl.lastSpring.latest), { month: 4, day: 3 }, "latest spring frost 3 May");
  assert.equal(fl.lastSpring.latestYear, 2017);
  assert.deepEqual(frostDate(fl.anchorMonth, fl.lastSpring.median), { month: 3, day: 10 }, "the median ignores one outlier");

  // southern-type (São Paulo calendar): frosts on 20 Aug (spring) and 10 May (autumn)
  const sh = series([2015, 0, 1], [2020, 11, 31], d => {
    const md = d.toISOString().slice(5, 10);
    return { tmin: md === "08-20" || md === "05-10" ? -0.5 : 8 };
  });
  const fs = frostCalendar(sh, saoPaulo.tavg);
  assert.equal(fs.anchorMonth, 1, "anchored on February, São Paulo's warmest month");
  assert.deepEqual(frostDate(fs.anchorMonth, fs.lastSpring.median), { month: 7, day: 20 }, "southern last frost 20 Aug");
  assert.deepEqual(frostDate(fs.anchorMonth, fs.firstAutumn.median), { month: 4, day: 10 }, "southern first frost 10 May");
  assert.ok(fs.season > 250 && fs.season < 270, `southern frost-free run ~263 d: ${fs.season}`);

  // tropical: never a frost
  const trop = series([2015, 0, 1], [2018, 11, 31], () => ({ tmin: 19 }));
  const ft = frostCalendar(trop, saoPaulo.tavg);
  assert.equal(ft.frostFree, true);
  assert.equal(ft.lastSpring.median, null);
  assert.equal(ft.season, null);

  // occasional frost: median spring is frost-free, the one frost still reported
  const rare = series([2015, 0, 1], [2020, 11, 31], d => ({ tmin: d.toISOString().slice(0, 10) === "2018-02-14" ? -2 : 6 }));
  const fr = frostCalendar(rare, berlin.tavg);
  assert.equal(fr.springFrosts, 1);
  assert.equal(fr.lastSpring.median, null, "a typical spring here has no frost");
  assert.equal(fr.lastSpring.latestYear, 2018);
  assert.equal(fr.frostFree, false);

  // tundra-like: frost in every month
  const cold = series([2015, 0, 1], [2018, 11, 31], d => ({ tmin: d.getUTCDate() % 3 === 0 ? -3 : 1 }));
  assert.equal(frostCalendar(cold, berlin.tavg).yearRound, true, "no frost-free season worth naming");
  assert.equal(frostCalendar({}, berlin.tavg), null);
}

// --- Linvill hourly curve
{
  const H = hourlyTemps([2, 4, 2], [12, 14, 12], [80, 81, 82], 45);
  const day = Array.from(H.slice(24, 48));
  const sr = Math.round(12 - 12.2 / 2);
  close(day[sr], 4, 0.6, "minimum near sunrise");
  assert.equal(day.indexOf(Math.max(...day)), 14, "maximum at 14:00 solar");
  close(Math.max(...day), 14, 1e-6, "reaches the daily maximum");
  assert.ok(day.every(t => t >= 2 - 1e-9 && t <= 14 + 1e-9), "stays within the neighbouring extremes");
  for (let h = 1; h < 72; h++) assert.ok(Math.abs(H[h] - H[h - 1]) < 3.5, `no jumps at hour ${h}`);
  // polar night falls back to a bounded diurnal curve
  const P = hourlyTemps([-20], [-12], [355], 75);
  assert.ok(Array.from(P).every(t => t >= -20 && t <= -12));
}

// --- Dynamic Model: documented behaviour (Fishman et al. 1987; Luedeling 2009)
{
  const flat = (t, h) => new Float64Array(h).fill(t);
  assert.equal(chillPortions(flat(6, 28)), 0, "at 6 C the first portion is not banked before hour 29");
  close(chillPortions(flat(6, 29)), 0.981, 0.002, "first portion at hour 29");
  const rate = t => chillPortions(flat(t, 1000));
  assert.ok(rate(6) > rate(2) && rate(8) > rate(12) && rate(6) > rate(0), "effective chill peaks around 6-8 C");
  assert.equal(rate(16), 0, "warm hours bank nothing");
  assert.ok(rate(-5) < 0.5, "deep cold barely chills");
  // negation: warm afternoons destroy the unbanked intermediate
  const mix = []; for (let d = 0; d < 40; d++) { for (let i = 0; i < 18; i++) mix.push(6); for (let i = 0; i < 6; i++) mix.push(20); }
  assert.ok(chillPortions(Float64Array.from(mix)) < chillPortions(flat(6, 40 * 18)), "warm spells negate chill");
  assert.equal(chillingHours(Float64Array.from([-1, 0, 3, 7.2, 7.3, 12])), 3, "chilling hours count 0-7.2 C");
}

// --- winter chill per winter, Safe Winter Chill
{
  const years = [2015, 2016, 2017, 2018, 2019, 2020];
  const d = synthDaily(berlin, { years, seed: 21 });
  const w = winterChill(d, berlin.lat, berlin.tavg);
  assert.equal(w.northern, true);
  assert.equal(w.n, 5, "five complete Nov-Feb winters in six calendar years");
  assert.ok(w.safeCP <= w.medianCP && w.safeCH <= w.medianCH, "safe chill sits below the median");
  assert.ok(w.medianCP > 40 && w.medianCP < 110, `a Berlin-like winter holds tens of chill portions: ${w.medianCP.toFixed(0)}`);
  assert.equal(w.approxTmax, false);
  // warmer winters chill less: São Paulo-like climate is near zero
  const sp = winterChill(synthDaily(saoPaulo, { years, seed: 22 }), saoPaulo.lat, saoPaulo.tavg);
  assert.equal(sp.northern, false, "southern winter window (May-Aug)");
  assert.equal(sp.n, 6);
  assert.ok(sp.medianCP < w.medianCP / 2, `subtropical winters chill far less: ${sp.medianCP.toFixed(1)}`);
  // +2 C everywhere costs chill in a mild winter
  const warmer = winterChill(shiftDaily(d, Array(12).fill(2), Array(12).fill(2), Array(12).fill(2)), berlin.lat, berlin.tavg);
  assert.ok(warmer.medianCP !== w.medianCP, "warming changes winter chill");
  // older payloads without tmax rebuild it from mean and min
  const noMax = { ...d, temperature_2m_max: undefined };
  const wn = winterChill(noMax, berlin.lat, berlin.tavg);
  assert.equal(wn.approxTmax, true);
  close(wn.medianCP, w.medianCP, 6, "the 2*mean-min rebuild stays close");
  assert.equal(winterChill({}, 50, berlin.tavg), null);
}

// --- delta method: the model's bias never reaches the projection
{
  const obs = { ...berlin };
  // a model running 2 C warm and 30% wet over its own baseline years
  const base = { tavg: berlin.tavg.map(t => t + 2), tmin: berlin.tmin.map(t => t + 2), prec: berlin.prec.map(p => p * 1.3), absMinMean: -10 };
  const fut = { tavg: base.tavg.map(t => t + 1.5), tmin: base.tmin.map(t => t + 1.8), prec: base.prec.map(p => p * 0.9), absMinMean: -8 };
  const f = deltaFuture(obs, base, fut);
  f.tavg.forEach((t, m) => close(t, berlin.tavg[m] + 1.5, 1e-9, `month ${m} warms by the model's change only`));
  f.tmin.forEach((t, m) => close(t, berlin.tmin[m] + 1.8, 1e-9, `tmin month ${m}`));
  f.prec.forEach((p, m) => close(p, berlin.prec[m] * 0.9, 1e-9, `rain month ${m} scales by the model's ratio`));
  close(f.dT, 1.5, 1e-9, "annual warming");
  close(f.dP, -0.1, 1e-9, "annual rain change");
  close(f.absMin, -15 + 2, 1e-9, "record low shifts by the change in mean annual minima");
  // a near-dry baseline month takes the additive change, ratios stay bounded
  const dry = { ...obs, prec: [...berlin.prec.slice(0, 11), 2] };
  const b2 = { ...base, prec: [...base.prec.slice(0, 10), 50, 4] };
  const f2 = { ...fut, prec: [...fut.prec.slice(0, 10), 500, 9] };
  const g = deltaFuture(dry, b2, f2);
  close(g.prec[11], 2 + 5, 1e-9, "baseline under 10 mm: additive change");
  close(g.prec[10], 45 * 5, 1e-9, "a tenfold ratio is capped at 5x");
  // without annual minima the coldest month's tmin change shifts the record low
  const h = deltaFuture(obs, { ...base, absMinMean: null }, fut);
  close(h.absMin, -15 + 1.8, 1e-9);
  // monthlyMeans / meanAnnualMin on a payload
  const d = synthDaily(berlin, { years: [2015, 2016], seed: 9 });
  const mm = monthlyMeans(d, "temperature_2m_max");
  assert.equal(mm.length, 12);
  assert.ok(mm[6] > mm[0], "July tmax above January");
  const yl = yearlyClimates(d);
  close(meanAnnualMin(d), (yl[0].absMin + yl[1].absMin) / 2, 1e-9);
  // shiftDaily keeps real day-to-day weather, adds the monthly change
  const s = shiftDaily(d, Array(12).fill(1), Array(12).fill(2), Array(12).fill(1.5));
  close(s.temperature_2m_min[40] - d.temperature_2m_min[40], 1, 1e-9);
  close(s.temperature_2m_max[200] - d.temperature_2m_max[200], 2, 1e-9);
}

// --- provenancing and terrain cells
{
  assert.equal(LAPSE_C_PER_M, 0.0065);
  assert.equal(elevationAnalogue(1.3), 200, "1.3 C is ~200 m of standard-atmosphere lapse");
  assert.equal(elevationAnalogue(2.0), 300);
  assert.equal(elevationAnalogue(0.1), null, "no warming, no analogue");
  assert.equal(elevationAnalogue(null), null);
  const c = cellSite(berlin, 200, { slope: 12, aspectDeg: 180 });
  close(c.tavg[6], berlin.tavg[6] - 1.3, 1e-9, "200 m higher is 1.3 C cooler");
  close(c.absMin, berlin.absMin - 1.3, 1e-9);
  assert.equal(c.prec, berlin.prec, "rain held constant");
  assert.equal(c.terrain.slope, 12);
  // a plane rising 10% to the east: ~5.7 deg, draining west (270)
  const cols = 4, rows = 3, dx = 100, dy = 100;
  const elev = []; for (let r = 0; r < rows; r++) for (let k = 0; k < cols; k++) elev.push(500 + 10 * k);
  const g = gridTerrain(elev, cols, rows, dx, dy);
  g.forEach(t => { close(t.slope, Math.atan(0.1) * 180 / Math.PI, 1e-9, "uniform slope"); assert.equal(t.aspectDeg, 270, "faces west"); });
  // rising to the north: faces south (180)
  const n = []; for (let r = 0; r < rows; r++) for (let k = 0; k < cols; k++) n.push(500 + 20 * (rows - 1 - r));
  assert.equal(gridTerrain(n, cols, rows, dx, dy)[5].aspectDeg, 180, "north-rising plane faces south");
  // a warm-climate tree gains suitability downhill and loses it uphill
  const euc = by("Eucalyptus grandis");
  const sp0 = scoreSpecies(euc, saoPaulo).score;
  assert.ok(scoreSpecies(euc, cellSite(saoPaulo, 900, null)).score < sp0, "900 m up is colder for eucalyptus");
}

console.log("all risk checks passed");
