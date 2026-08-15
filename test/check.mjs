// Self-check for the scoring and growth engines. Run: node test/check.mjs
import assert from "node:assert";
import { readFileSync } from "node:fs";
import { trap, daylength, scoreSpecies, aggregateClimate, grade } from "../scoring.js";
import { CLASSES, height, dbhCm, co2eKgPerTree, crownDiameterM, crownDisplayM, standDisplay, maturityYears } from "../growth.js";

const species = JSON.parse(readFileSync(new URL("../data/species.json", import.meta.url)));
const by = sci => species.find(s => s.sci === sci);
const close = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: got ${a}, want ${b}±${tol}`);

// --- trapezoid
assert.equal(trap(5, 0, 10, 20, 30), 0.5);
assert.equal(trap(15, 0, 10, 20, 30), 1);
assert.equal(trap(25, 0, 10, 20, 30), 0.5);
assert.equal(trap(-1, 0, 10, 20, 30), 0);
assert.equal(trap(30, 0, 10, 20, 30), 0);

// --- daylength (verified anchors: equator/45N/70N, Forsythe p=0.8333)
close(daylength(0, 172), 12.121, 0.05, "equator Jun21");
close(daylength(45, 172), 15.618, 0.05, "45N Jun21");
close(daylength(45, 355), 8.763, 0.05, "45N Dec21");
assert.equal(daylength(70, 172), 24, "70N polar day");
assert.equal(daylength(70, 355), 0, "70N polar night");

// --- growth validation targets (research-verified anchors)
const euc = CLASSES.tropical_fast, oak = CLASSES.temperate_slow;
close(height(10, euc), 27.8, 0.3, "eucalyptus H(10)");
close(dbhCm(height(10, euc), euc), 19.9, 0.5, "eucalyptus DBH(10)");
close(height(10, oak), 4.6, 0.2, "oak H(10)");
const oakSp = { gclass: "temperate_slow", wood: "broadleaf" };
close(co2eKgPerTree(oakSp, 10), 21.5, 3, "oak CO2e(10) kg");
const eucSp = { gclass: "tropical_fast", wood: "broadleaf" };
const eucCo2 = co2eKgPerTree(eucSp, 10);
assert.ok(eucCo2 > 400 && eucCo2 < 800, `euc CO2e(10) plausible: ${eucCo2}`);
close(crownDiameterM(24, 19), 5.6, 0.4, "oak crown dia at D=24 H=19");
assert.ok(maturityYears(oak) > 60 && maturityYears(euc) < 25, "maturity ordering");

// --- climate aggregation
const days = { time: [], temperature_2m_mean: [], temperature_2m_min: [], precipitation_sum: [] };
for (const y of ["2020", "2021"]) for (let m = 1; m <= 12; m++) {
  days.time.push(`${y}-${String(m).padStart(2, "0")}-15`);
  days.temperature_2m_mean.push(10 + m);
  days.temperature_2m_min.push(5 + m);
  days.precipitation_sum.push(50);
}
const agg = aggregateClimate(days);
close(agg.tavg[0], 11, 0.01, "tavg Jan");
close(agg.prec[0], 50, 0.01, "prec Jan (per-year mean)");
close(agg.annualRain, 600, 0.1, "annual rain");
assert.equal(agg.absMin, 6);

// temp gaps must not swallow precipitation (audit #4)
const gappy = structuredClone(days);
gappy.time.push("2020-01-20"); gappy.temperature_2m_mean.push(null);
gappy.temperature_2m_min.push(null); gappy.precipitation_sum.push(40);
close(aggregateClimate(gappy).prec[0], 70, 0.01, "precip counted on null-temp day");

// a month with zero valid days must throw, not NaN-poison every score (audit #5)
const holey = { time: [], temperature_2m_mean: [], temperature_2m_min: [], precipitation_sum: [] };
for (let m = 1; m <= 12; m++) if (m !== 3) {
  holey.time.push(`2020-${String(m).padStart(2, "0")}-15`);
  holey.temperature_2m_mean.push(15); holey.temperature_2m_min.push(10); holey.precipitation_sum.push(50);
}
assert.throws(() => aggregateClimate(holey), /incomplete climate/, "missing month throws");

// --- suitability with fixture climates
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

const qr = by("Quercus robur"), eg = by("Eucalyptus grandis");
assert.ok(qr && eg, "key species present in dataset");
const qrBerlin = scoreSpecies(qr, berlin);
assert.ok(qrBerlin.score > 0.6, `oak in Berlin should be suitable: ${qrBerlin.score}`);
const egBerlin = scoreSpecies(eg, berlin);
assert.equal(egBerlin.score, 0, "E. grandis in Berlin killed by record low");
assert.equal(egBerlin.factors.frost, 0, "frost factor reports the kill");
const egSP = scoreSpecies(eg, saoPaulo);
assert.ok(egSP.score > 0.4, `E. grandis in Sao Paulo should rank: ${egSP.score}`);
assert.ok(qrBerlin.score > scoreSpecies(qr, saoPaulo).score, "oak prefers Berlin over Sao Paulo");

// missing soil -> ph factor null, not zero
const noSoil = scoreSpecies(qr, { ...berlin, ph: null });
assert.equal(noSoil.factors.ph, null);
assert.ok(noSoil.score > 0, "no-soil site still scores");

// audit #1: tropical species with NO cold data defaults to frost-tender
const at = by("Acacia tortilis");
assert.ok(at && at.ktmp == null && at.ktmpr == null, "A. tortilis has no cold data");
assert.equal(scoreSpecies(at, berlin).score, 0, "Sahel acacia must not rate in Berlin");
assert.ok(scoreSpecies(at, saoPaulo).factors.frost !== 0, "still fine where frost-free");

// audit #2: perennials must tolerate the annual regime, not just a summer window
const summerTourist = { temp: [12, 20, 30, 42], rain: [100, 200, 800, 1500], ph: null,
  ktmp: null, ktmpr: -60, photo: null, cycle: [90, 120], gclass: "tropical_fast", wood: "broadleaf" };
const st = scoreSpecies(summerTourist, berlin);
assert.equal(st.factors.annual, 0, "annual gate trips");
assert.equal(st.score, 0, "4-month window alone cannot qualify a tree in Berlin");

// audit #3: corrupt envelopes are excluded at build time
assert.equal(by("Faidherbia albida"), undefined, "inverted-envelope rows dropped");

// audit #9: unknown photoperiod reads as no-data, insensitive reads as pass
assert.equal(scoreSpecies(qr, berlin).factors.photo, null, "oak photoperiod unknown -> null");
const insensitive = species.find(s => Array.isArray(s.photo) && s.photo.length === 0);
assert.ok(insensitive, "known-insensitive species exist");
assert.equal(scoreSpecies(insensitive, saoPaulo).factors.photo, 1, "insensitive scores 1, not null");

// native-range layer (Kew WCVP)
const natives = JSON.parse(readFileSync(new URL("../data/natives.json", import.meta.url)));
const idOf = sci => String(species.find(s => s.sci === sci)?.id);
assert.ok(Object.keys(natives).length > 900, "native-range coverage");
assert.ok(natives[idOf("Eucalyptus grandis")].includes("AU"), "E. grandis native to AU");
assert.ok(!natives[idOf("Eucalyptus grandis")].includes("BR"), "E. grandis not native to BR");
assert.ok(natives[idOf("Quercus robur")].includes("DE"), "Q. robur native to DE");
const pear = natives[idOf("Pyrus pyrifolia")];
assert.ok(pear.includes("CN") && !pear.includes("BR"), "Chinese pear is Asian, not Brazilian");

// winter dormancy proxy: Chinese pear must fail in chill-free Cubatao-like climate
const pearSp = by("Pyrus pyrifolia");
assert.ok(pearSp?.decid, "pear is deciduous");
const cubatao = { ...saoPaulo, tavg: saoPaulo.tavg.map(v => v + 2.5), tmin: saoPaulo.tmin.map(v => v + 2.5), absMin: 8 };
assert.ok(scoreSpecies(pearSp, cubatao).score < 0.05, "no winter chill -> pear fails");
assert.ok(scoreSpecies(qr, berlin).factors.chill === 1, "oak in Berlin has real winter");

// display crowns widen with age (slenderness decline), biomass chain untouched
const cd20 = crownDisplayM(CLASSES.tropical_fast, 20);
const cd60 = crownDisplayM(CLASSES.tropical_fast, 60);
assert.ok(cd20 > 3.5 && cd20 < 5.5, `euc display crown at 20y plausible: ${cd20}`);
assert.ok(cd60 > 5 && cd60 < 8, `euc display crown at 60y plausible: ${cd60}`);
assert.ok(cd60 > cd20, "crowns keep widening with age");
close(co2eKgPerTree({ gclass: "temperate_slow", wood: "broadleaf" }, 10), 21.5, 3, "carbon anchor unmoved by crown fix");

// self-thinning display: density falls, surviving crowns widen, carbon untouched
const tm = CLASSES.tropical_medium;
const sd5 = standDisplay(tm, 5), sd30 = standDisplay(tm, 30), sd60 = standDisplay(tm, 60);
assert.ok(sd30.keep < sd5.keep && sd60.keep < sd30.keep, "stand keeps thinning with age");
const dens30 = sd30.keep * 1111;
assert.ok(dens30 > 100 && dens30 < 600, `30y density plausible: ${dens30.toFixed(0)}/ha`);
assert.ok(sd30.crown > crownDisplayM(tm, 30), "released crowns wider than plantation crowns");
assert.ok(sd30.crown > 8 && sd30.crown < 13, `30y display crown satellite-scale: ${sd30.crown.toFixed(1)} m`);
const cover30 = sd30.keep * 1111 * Math.PI * (sd30.crown / 2) ** 2 / 1e4;
assert.ok(cover30 > 0.8, `canopy stays closed after thinning: ${(cover30 * 100).toFixed(0)}%`);
close(co2eKgPerTree({ gclass: "temperate_slow", wood: "broadleaf" }, 10), 21.5, 3, "carbon anchor unmoved by thinning");

// habit expansion: non-tree species exist and are flagged
assert.ok(species.length > 2000, `all life forms present: ${species.length}`);
const okra = by("Abelmoschus esculentus");
assert.ok(okra && okra.tree === false && okra.porte === "herb", "okra is a flagged herb");
assert.ok(by("Quercus robur").tree === true, "oak stays a tree");

// agronomist regressions (field report, 2026-08): highland Bolivia and Bariloche
const cochabamba = { // ~2500 m semi-arid valley; ERA5 grid never records frost (absMin +1)
  lat: -17.39,
  tavg: [17, 16, 16, 16, 16, 15, 15, 16, 17, 19, 19, 17],
  tmin: [13, 12, 12, 11, 10, 9, 9, 9, 11, 12, 13, 13],
  prec: [190, 140, 95, 25, 6, 4, 4, 10, 20, 45, 90, 160],
  ph: null, absMin: 1,
};
const bariloche = {
  lat: -41.13,
  tavg: [16, 16, 13, 10, 6, 4, 3, 3, 5, 7, 11, 14],
  tmin: [10, 11, 9, 6, 4, 1, 0, 1, 1, 3, 6, 8],
  prec: [25, 25, 45, 90, 175, 190, 180, 140, 85, 55, 45, 35],
  ph: null, absMin: -8.9,
};
const jabo = by("Myrciaria cauliflora"), coca = by("Erythroxylum coca");
assert.ok(jabo && coca, "field-report species present");
const jaboCbba = scoreSpecies(jabo, cochabamba);
assert.equal(jaboCbba.factors.frost, 0.5, "grid frost margin penalizes jaboticaba at 2500 m");
assert.ok(jaboCbba.score <= 0.4, `jaboticaba must not rate suitable in highland Bolivia: ${jaboCbba.score}`);
assert.ok(scoreSpecies(coca, cochabamba).score <= 0.4, "coca stays marginal at best there");
assert.equal(scoreSpecies(jabo, bariloche).score, 0, "jaboticaba dead in Bariloche");
assert.equal(scoreSpecies(coca, bariloche).score, 0, "coca dead in Bariloche");
close(scoreSpecies(eg, saoPaulo).score, egSP.score, 0.001, "frost margin does not touch São Paulo eucalyptus");

// hardiness-vs-envelope contradictions (field report, Toronto 2026-08):
// EcoCrop's crop-oriented fields killed cold-hardy natives in their homeland
const toronto = {
  lat: 43.616,
  tavg: [-3.3, -3.1, 1.0, 6.3, 13.2, 18.9, 22.3, 21.7, 18.5, 11.9, 5.1, 0.5],
  tmin: [-6.8, -7.4, -3.0, 2.1, 8.7, 14.6, 17.9, 17.8, 14.6, 8.4, 1.8, -2.4],
  prec: [66, 59, 66, 99, 70, 93, 78, 70, 56, 83, 61, 72],
  ph: null, absMin: -26,
};
const winnipeg = {
  lat: 49.895,
  tavg: [-13.2, -13.9, -4.9, 3.1, 12.4, 18.8, 21.1, 19.9, 15.4, 6.5, -2.1, -10.0],
  tmin: [-17.5, -18.9, -10.0, -2.5, 6.3, 13.4, 16.1, 14.8, 10.9, 2.6, -5.5, -13.9],
  prec: [17, 16, 21, 45, 70, 83, 86, 76, 76, 48, 34, 29],
  ph: null, absMin: -38,
};
const maple = by("Acer saccharum"), sask = by("Aronia alnifolia");
assert.ok(maple && sask, "north-american natives present");
const NATIVE = { native: true };
assert.ok(scoreSpecies(maple, toronto, NATIVE).score >= 0.4, "sugar maple rates in Toronto with native evidence");
assert.equal(scoreSpecies(maple, toronto, NATIVE).factors.frost, 0.5, "hardiness contradiction demoted to half, not kill");
assert.ok(scoreSpecies(sask, winnipeg, NATIVE).score >= 0.6, "saskatoon rates in the town it is named after");
assert.ok(scoreSpecies(sask, winnipeg).score === 0, "without native evidence the annual gate still holds");
assert.ok(scoreSpecies(by("Erythroxylum coca"), winnipeg, NATIVE).score === 0, "evidence never revives a true climate kill");

// annual crops never meet the winter (Turkish field feedback, 2026-08):
// frost is tested on the growing window, not the year-round record low
const corn = by("Zea mays ssp. saccharata"); // 3-month cycle fits the frost-free window
const bean = by("Phaseolus vulgaris");
assert.ok(corn?.annual && bean?.annual, "sweet corn and bean carry the annual flag");
assert.equal(scoreSpecies(corn, winnipeg).factors.frost, 1, "sweet corn passes window frost in Winnipeg (absMin -38)");
assert.equal(scoreSpecies(bean, winnipeg).factors.frost, 1, "bean passes window frost too");
assert.ok(by("Solanum lycopersicum"), "tomato answers to its accepted name");

// wetland-on-a-hill (field report, 2026-08): obligate wetland species die on real slopes
const typha = by("Typha latifolia");
assert.ok(typha?.wet, "cattail is flagged obligate wetland");
const hill = { ...saoPaulo, terrain: { slope: 6, facing: "N" } };
const flat = { ...saoPaulo, terrain: { slope: 1, facing: null } };
assert.equal(scoreSpecies(typha, hill).score, 0, "cattail dies on a 6-degree hillside");
assert.equal(scoreSpecies(typha, hill).factors.drain, 0, "drainage factor reports the kill");
assert.equal(scoreSpecies(typha, flat).factors.drain, null, "flat ground leaves drainage unscored (water table unknowable)");
assert.ok(!by("Quercus robur").wet, "oak is not wetland-flagged");
close(scoreSpecies(qr, { ...berlin, terrain: { slope: 6 } }).score, qrBerlin.score, 0.001, "slope does not touch non-wetland species");

// perennial annual rain scoring (field report, Giresun/Mediterranean 2026-08):
// trees, shrubs and vines live on 12-month stored soil water, not cycle windows;
// sloped terrain sheds excess precipitation without root waterlogging.
const giresun = {
  lat: 40.85,
  tavg: [7.2, 7.5, 9.0, 12.5, 17.0, 21.5, 24.0, 24.2, 21.0, 16.8, 12.5, 9.0],
  tmin: [4.5, 4.8, 6.0, 9.2, 13.8, 18.0, 20.8, 21.0, 17.5, 13.5, 9.5, 6.2],
  prec: [127, 88, 124, 86, 120, 125, 125, 130, 134, 160, 106, 108],
  ph: 6.2, absMin: -6.0,
};
const hazel = by("Corylus avellana");
assert.ok(hazel, "hazelnut present");
const hazelSloped = scoreSpecies(hazel, { ...giresun, terrain: { slope: 10 } });
assert.ok(hazelSloped.factors.rain >= 0.6, `hazelnut on Giresun hillside scores high rain: ${hazelSloped.factors.rain}`);
assert.ok(hazelSloped.score >= 0.3, `hazelnut scores suitable in Giresun: ${hazelSloped.score}`);

// grading bands
assert.equal(grade(0.9), "Excellent");
assert.equal(grade(0.5), "Suitable");
assert.equal(grade(0), "Not suitable");

console.log("all checks passed");
console.log(`  oak@Berlin ${qrBerlin.score.toFixed(2)} | euc@Berlin ${egBerlin.score.toFixed(2)} | euc@SP ${egSP.score.toFixed(2)}`);
console.log(`  euc CO2e(10y) ${eucCo2.toFixed(0)} kg | oak CO2e(10y) ${co2eKgPerTree(oakSp, 10).toFixed(1)} kg`);
