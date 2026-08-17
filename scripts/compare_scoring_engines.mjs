#!/usr/bin/env node
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import {
  trap,
  daylength,
  monthlyDaylengths,
  scoreSpecies as scoreSpeciesV2,
  grade as gradeV2,
  gradeColor as gradeColorV2,
  usdaTextureClass,
  faoTextureCategory,
  saxtonRawlsHydrology
} from "../scoring.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const species = JSON.parse(readFileSync(resolve(__dirname, "../data/species.json"), "utf8"));

// ---------------------------------------------------------------------------
// Upstream (Origin / gdavidss) Scoring Engine Implementation (Faithful Replica)
// ---------------------------------------------------------------------------
function dayClassesOrigin(d) {
  const c = [];
  if (d < 12.5) c.push("short");
  if (d >= 11.5 && d <= 14.5) c.push("neutral");
  if (d > 13.5) c.push("long");
  return c;
}

export function scoreSpeciesOrigin(sp, site, ev = null) {
  const [gmin, gmax] = sp.cycle ?? [null, null];
  const G = gmin == null && gmax == null ? 12 :
    Math.max(1, Math.min(12, Math.round(((gmin ?? gmax) + (gmax ?? gmin)) / 60)));

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
      if (m > bestScore || (m === bestScore && t > temp)) { bestScore = m; temp = t; rain = r; best = s; }
      if (G === 12) break;
    }
  }

  let annual = trap(site.tavg.reduce((a, b) => a + b, 0) / 12, ...sp.temp) > 0 ? 1 : 0;
  if (!annual && ev?.native) annual = 1;

  const kt = sp.ktmpr ?? sp.ktmp ?? (sp.gclass?.startsWith("tropical") ? 0 : null);
  const FROST_MARGIN = 4;
  let frost;
  if (kt == null) frost = null;
  else if (sp.annual && G < 12) {
    let wmin = Infinity;
    for (let k = 0; k < G; k++) wmin = Math.min(wmin, site.tmin[(best + k) % 12]);
    frost = wmin < kt + 4 ? 0 : 1;
  } else {
    frost = (Math.min(...site.tmin) < kt + 4 || (site.absMin != null && site.absMin < kt) ? 0 :
      (site.absMin != null && site.absMin - FROST_MARGIN <= kt ? 0.5 : 1));
  }
  if (frost === 0 && (ev?.native || ev?.countryNative)) frost = 0.5;

  const ph = sp.ph && site.ph != null ? trap(site.ph, ...sp.ph) : null;

  const drain = sp.wet
    ? (site.terrain?.slope != null ? (site.terrain.slope >= 4 ? 0 : null) : null)
    : null;

  let chill = null;
  if (sp.decid && sp.gclass?.startsWith("temperate")) {
    const coldest = Math.min(...site.tavg);
    chill = coldest <= 10 ? 1 : coldest >= 16 ? 0 : (16 - coldest) / 6;
  }

  let photo = sp.photo == null ? null : 1;
  if (sp.photo?.length) {
    const dls = monthlyDaylengths(site.lat);
    const here = new Set();
    for (let k = 0; k < G; k++) dayClassesOrigin(dls[(best + k) % 12]).forEach(c => here.add(c));
    photo = sp.photo.some(c => here.has(c)) ? 1 : 0.5;
  }

  const score = Math.min(temp, rain, ph ?? 1, chill ?? 1) * (frost ?? 1) * (photo ?? 1) * (drain ?? 1) * annual;

  const tri = (x, a, b, c, d) => trap(x, a, (b + c) / 2, (b + c) / 2, d);
  let tsum = 0, rtot = 0;
  for (let k = 0; k < G; k++) { const m = (best + k) % 12; tsum += site.tavg[m]; rtot += site.prec[m]; }
  const fits = [tri(tsum / G, ...sp.temp), tri(rtot, ...sp.rain)];
  if (sp.ph && site.ph != null) fits.push(tri(site.ph, ...sp.ph));
  const fit = fits.reduce((a, b) => a + b, 0) / fits.length;

  return { score, fit, factors: { temp, rain, ph, frost, photo, annual, chill, drain }, window: { start: best, months: Gt } };
}

// ---------------------------------------------------------------------------
// 20 Global Benchmark Sites with Comprehensive Climate, Soil & Terrain
// ---------------------------------------------------------------------------
export const SITES = [
  {
    id: "konya_tr",
    name: "Konya, Central Anatolia, Turkey",
    lat: 37.87,
    lon: 32.49,
    elevation: 1020,
    biome: "Semi-arid continental steppe",
    terrain: { slope: 1.2, aspect: 180 },
    tavg: [0.0, 1.5, 6.0, 11.5, 16.5, 21.0, 24.5, 24.2, 19.5, 13.5, 7.0, 2.0],
    tmin: [-4.5, -3.5, 0.5, 5.0, 9.5, 13.5, 16.5, 16.2, 11.5, 6.5, 1.0, -2.5],
    prec: [36.0, 31.0, 33.0, 42.0, 45.0, 24.0, 8.0, 6.0, 14.0, 31.0, 35.0, 44.0], // 349 mm
    et0: [22.0, 30.0, 62.0, 98.0, 145.0, 182.0, 210.0, 195.0, 138.0, 82.0, 38.0, 21.0],
    absMin: -24.0,
    ph: 7.8,
    soil: {
      effectivePh: 7.8,
      sandPct: 22.0, siltPct: 45.0, clayPct: 33.0, somPct: 1.4, socGKg: 8.1,
      bdodGCm3: 1.40, cecCmolKg: 24.0, cfvoPct: 5.0, maxDepthCm: 120,
      usdaTexture: "Clay Loam", faoTexture: "medium", awcMm: 142.0
    },
    soilTexture: "medium",
    rad: 4.8,
    keySpeciesToCheck: ["Balanites aegyptiaca", "Prunus dulcis", "Elaeagnus angustifolia", "Pinus nigra", "Juglans regia", "Robinia pseudoacacia"]
  },
  {
    id: "rize_tr",
    name: "Rize, Eastern Black Sea, Turkey",
    lat: 41.02,
    lon: 40.52,
    elevation: 120,
    biome: "Temperate Humid Rainforest / Subtropical Steep Hills",
    terrain: { slope: 15.0, aspect: 350 }, // 15 deg north-facing mountain slope
    tavg: [7.0, 7.2, 8.5, 12.5, 16.8, 21.0, 23.5, 23.8, 20.5, 16.5, 12.5, 9.0],
    tmin: [4.0, 4.0, 5.5, 9.0, 13.5, 17.5, 20.5, 21.0, 17.5, 13.5, 9.5, 6.0],
    prec: [168.8, 113.7, 152.6, 98.1, 123.4, 160.6, 183.1, 224.1, 252.7, 278.4, 179.8, 163.7], // 2099 mm
    et0: [29.8, 37.5, 53.5, 77.3, 94.8, 102.5, 104.9, 92.9, 75.0, 53.3, 39.5, 27.8],
    absMin: -4.0,
    ph: 4.8,
    soil: {
      effectivePh: 4.8,
      sandPct: 40.0, siltPct: 35.0, clayPct: 25.0, somPct: 3.8, socGKg: 22.0,
      bdodGCm3: 1.20, cecCmolKg: 18.0, cfvoPct: 5.0, maxDepthCm: 140,
      usdaTexture: "Loam", faoTexture: "medium", awcMm: 178.0
    },
    soilTexture: "medium",
    rad: 3.6,
    keySpeciesToCheck: ["Camellia sinensis", "Corylus avellana", "Castanea sativa", "Coffea excelsa", "Phoenix dactylifera"]
  },
  {
    id: "seville_es",
    name: "Seville, Andalusia, Spain",
    lat: 37.38,
    lon: -5.98,
    elevation: 20,
    biome: "Hot-summer Mediterranean",
    terrain: { slope: 1.5, aspect: 180 },
    tavg: [10.5, 12.7, 14.6, 17.3, 21.7, 25.4, 29.0, 29.1, 24.8, 20.7, 14.8, 12.1],
    tmin: [6.5, 8.3, 9.7, 12.1, 15.6, 18.9, 21.8, 22.4, 19.2, 16.0, 10.9, 8.4],
    prec: [66.0, 50.0, 36.0, 54.0, 31.0, 10.0, 2.0, 5.0, 27.0, 68.0, 91.0, 99.0], // 539 mm
    et0: [42.0, 58.0, 95.0, 132.0, 185.0, 215.0, 240.0, 222.0, 155.0, 102.0, 55.0, 38.0],
    absMin: -0.4,
    ph: 7.2,
    soil: {
      effectivePh: 7.2,
      sandPct: 35.0, siltPct: 38.0, clayPct: 27.0, somPct: 1.6, socGKg: 9.3,
      bdodGCm3: 1.35, cecCmolKg: 20.0, cfvoPct: 2.0, maxDepthCm: 150,
      usdaTexture: "Clay Loam", faoTexture: "medium", awcMm: 155.0
    },
    soilTexture: "medium",
    rad: 5.2,
    keySpeciesToCheck: ["Olea europaea", "Ceratonia siliqua", "Ficus carica", "Quercus ilex", "Pinus pinea", "Larix decidua"]
  },
  {
    id: "berlin_de",
    name: "Berlin, Brandenburg, Germany",
    lat: 52.52,
    lon: 13.40,
    elevation: 40,
    biome: "Central European Temperate Maritime-Continental",
    terrain: { slope: 1.0, aspect: 180 },
    tavg: [0.6, 1.5, 4.9, 9.4, 14.4, 17.5, 19.5, 19.2, 14.9, 10.2, 5.3, 1.7],
    tmin: [-2.5, -2.2, 0.9, 4.4, 9.0, 12.4, 14.5, 14.2, 10.7, 6.7, 2.5, -1.0],
    prec: [43.0, 37.0, 41.0, 36.0, 54.0, 69.0, 56.0, 58.0, 45.0, 44.0, 45.0, 55.0], // 583 mm
    et0: [15.0, 24.0, 48.0, 78.0, 115.0, 130.0, 135.0, 118.0, 72.0, 40.0, 18.0, 12.0],
    absMin: -18.5,
    ph: 5.9,
    soil: {
      effectivePh: 5.9,
      sandPct: 65.0, siltPct: 23.0, clayPct: 12.0, somPct: 2.2, socGKg: 12.8,
      bdodGCm3: 1.45, cecCmolKg: 14.0, cfvoPct: 3.0, maxDepthCm: 150,
      usdaTexture: "Sandy Loam", faoTexture: "light", awcMm: 118.0
    },
    soilTexture: "light",
    rad: 3.1,
    keySpeciesToCheck: ["Pinus sylvestris", "Quercus robur", "Fagus sylvatica", "Robinia pseudoacacia", "Terminalia brownii"]
  },
  {
    id: "manaus_br",
    name: "Manaus, Amazonas, Brazil",
    lat: -3.10,
    lon: -60.02,
    elevation: 80,
    biome: "Equatorial Amazon Rainforest",
    terrain: { slope: 2.0, aspect: 180 },
    tavg: [26.2, 26.1, 26.3, 26.5, 26.8, 27.0, 27.2, 27.8, 28.2, 28.1, 27.6, 26.8],
    tmin: [23.1, 23.0, 23.2, 23.4, 23.6, 23.5, 23.3, 23.5, 23.8, 23.9, 23.7, 23.4],
    prec: [280.0, 290.0, 320.0, 260.0, 180.0, 95.0, 60.0, 50.0, 85.0, 130.0, 190.0, 240.0], // 2180 mm
    et0: [105.0, 98.0, 108.0, 102.0, 110.0, 115.0, 125.0, 135.0, 140.0, 138.0, 122.0, 112.0],
    absMin: 18.0,
    ph: 4.6,
    soil: {
      effectivePh: 4.6,
      sandPct: 20.0, siltPct: 20.0, clayPct: 60.0, somPct: 2.5, socGKg: 14.5,
      bdodGCm3: 1.25, cecCmolKg: 8.5, cfvoPct: 0.0, maxDepthCm: 200,
      usdaTexture: "Clay", faoTexture: "heavy", awcMm: 165.0
    },
    soilTexture: "heavy",
    rad: 4.6,
    keySpeciesToCheck: ["Hevea brasiliensis", "Theobroma cacao", "Bertholletia excelsa", "Euterpe oleracea", "Malus domestica"]
  },
  {
    id: "sao_paulo_br",
    name: "São Paulo, SP, Brazil",
    lat: -23.55,
    lon: -46.63,
    elevation: 760,
    biome: "Humid Subtropical Plateau",
    terrain: { slope: 4.0, aspect: 0 },
    tavg: [22.5, 22.8, 22.0, 20.0, 17.5, 16.2, 16.0, 17.0, 18.2, 19.8, 20.8, 21.8],
    tmin: [19.0, 19.2, 18.5, 16.2, 13.5, 12.0, 11.5, 12.2, 13.8, 15.5, 16.8, 18.0],
    prec: [240.0, 220.0, 160.0, 85.0, 60.0, 50.0, 45.0, 40.0, 75.0, 130.0, 145.0, 210.0], // 1460 mm
    et0: [130.0, 118.0, 110.0, 88.0, 68.0, 58.0, 62.0, 75.0, 85.0, 105.0, 115.0, 128.0],
    absMin: 3.5,
    ph: 5.4,
    soil: {
      effectivePh: 5.4,
      sandPct: 30.0, siltPct: 30.0, clayPct: 40.0, somPct: 2.8, socGKg: 16.2,
      bdodGCm3: 1.30, cecCmolKg: 15.0, cfvoPct: 2.0, maxDepthCm: 160,
      usdaTexture: "Clay", faoTexture: "heavy", awcMm: 150.0
    },
    soilTexture: "heavy",
    rad: 4.4,
    keySpeciesToCheck: ["Araucaria angustifolia", "Eucalyptus grandis", "Coffea arabica", "Musa acuminata"]
  },
  {
    id: "barrow_us",
    name: "Utqiaġvik (Barrow), Alaska, USA",
    lat: 71.29,
    lon: -156.78,
    elevation: 5,
    biome: "Arctic Polar Tundra / Continuous Permafrost",
    terrain: { slope: 0.5, aspect: 180 },
    tavg: [-25.0, -26.5, -24.5, -16.0, -5.5, 2.0, 4.5, 4.0, 0.5, -8.0, -17.5, -22.5],
    tmin: [-29.0, -30.5, -28.5, -20.0, -8.5, -0.5, 1.5, 1.2, -1.5, -11.0, -21.0, -26.0],
    prec: [8.0, 6.0, 6.0, 5.0, 6.0, 12.0, 25.0, 30.0, 20.0, 15.0, 10.0, 8.0], // 151 mm
    et0: [0.0, 0.0, 2.0, 10.0, 25.0, 45.0, 55.0, 40.0, 15.0, 2.0, 0.0, 0.0],
    absMin: -45.0,
    ph: 5.5,
    soil: {
      effectivePh: 5.5,
      sandPct: 45.0, siltPct: 40.0, clayPct: 15.0, somPct: 12.0, socGKg: 69.6,
      bdodGCm3: 1.10, cecCmolKg: 28.0, cfvoPct: 0.0, maxDepthCm: 25, // Frozen permafrost barrier
      usdaTexture: "Loam", faoTexture: "medium", awcMm: 45.0
    },
    soilTexture: "medium",
    rad: 2.1,
    keySpeciesToCheck: ["Salix pulchra", "Betula nana", "Picea glauca", "Malus domestica"]
  },
  {
    id: "riyadh_sa",
    name: "Riyadh, Saudi Arabia",
    lat: 24.68,
    lon: 46.72,
    elevation: 610,
    biome: "Hyper-arid Hot Desert",
    terrain: { slope: 0.8, aspect: 180 },
    tavg: [14.5, 17.5, 22.0, 28.0, 34.0, 37.0, 38.5, 38.0, 34.5, 28.5, 21.5, 16.0],
    tmin: [9.0, 11.5, 15.5, 21.0, 26.5, 28.5, 30.0, 29.5, 26.0, 20.5, 15.0, 10.5],
    prec: [12.0, 8.0, 22.0, 25.0, 5.0, 0.0, 0.0, 0.0, 0.0, 2.0, 8.0, 12.0], // 94 mm
    et0: [85.0, 110.0, 165.0, 210.0, 275.0, 310.0, 320.0, 300.0, 245.0, 175.0, 115.0, 80.0],
    absMin: 2.0,
    ph: 8.6, // Highly alkaline calcareous soil
    soil: {
      effectivePh: 8.6,
      sandPct: 88.0, siltPct: 8.0, clayPct: 4.0, somPct: 0.2, socGKg: 1.2,
      bdodGCm3: 1.60, cecCmolKg: 4.5, cfvoPct: 15.0, maxDepthCm: 100,
      usdaTexture: "Sand", faoTexture: "light", awcMm: 42.0
    },
    soilTexture: "light",
    rad: 6.2,
    keySpeciesToCheck: ["Phoenix dactylifera", "Acacia tortilis", "Prosopis cineraria", "Ziziphus spina-christi", "Fagus sylvatica"]
  },
  {
    id: "niamey_ne",
    name: "Niamey, Sahel, Niger",
    lat: 13.51,
    lon: 2.11,
    elevation: 220,
    biome: "Tropical Semi-arid Sahelian Savanna",
    terrain: { slope: 1.0, aspect: 180 },
    tavg: [24.5, 27.5, 31.5, 34.5, 34.0, 31.5, 28.5, 27.5, 28.5, 31.0, 28.5, 25.0],
    tmin: [16.5, 19.5, 23.5, 27.0, 27.5, 25.5, 23.5, 22.8, 23.5, 24.0, 19.5, 16.8],
    prec: [0.0, 0.0, 2.0, 6.0, 32.0, 75.0, 140.0, 175.0, 90.0, 15.0, 0.0, 0.0], // 535 mm
    et0: [140.0, 155.0, 205.0, 225.0, 220.0, 185.0, 160.0, 145.0, 155.0, 175.0, 150.0, 135.0],
    absMin: 12.0,
    ph: 6.2,
    soil: {
      effectivePh: 6.2,
      sandPct: 78.0, siltPct: 12.0, clayPct: 10.0, somPct: 0.5, socGKg: 2.9,
      bdodGCm3: 1.55, cecCmolKg: 6.0, cfvoPct: 4.0, maxDepthCm: 120,
      usdaTexture: "Loamy Sand", faoTexture: "light", awcMm: 68.0
    },
    soilTexture: "light",
    rad: 5.8,
    keySpeciesToCheck: ["Faidherbia albida", "Adansonia digitata", "Balanites aegyptiaca", "Parkia biglobosa", "Picea abies"]
  },
  {
    id: "bogota_co",
    name: "Bogotá, Cundinamarca, Colombia",
    lat: 4.71,
    lon: -74.07,
    elevation: 2600,
    biome: "Tropical High-Andes Montane (Altiplano / Cloud Plateau)",
    terrain: { slope: 2.5, aspect: 180 },
    tavg: [13.5, 13.8, 14.0, 14.2, 14.2, 13.8, 13.5, 13.5, 13.6, 13.8, 13.8, 13.5], // Constant cool spring
    tmin: [6.0, 6.8, 7.5, 8.5, 8.5, 8.0, 7.5, 7.2, 7.0, 7.8, 8.0, 6.8],
    prec: [35.0, 45.0, 70.0, 110.0, 105.0, 55.0, 45.0, 45.0, 60.0, 120.0, 110.0, 60.0], // 860 mm
    et0: [85.0, 82.0, 88.0, 80.0, 82.0, 78.0, 82.0, 85.0, 86.0, 82.0, 78.0, 82.0],
    absMin: -2.0, // Rare radiative ground frosts in dry nights
    ph: 5.2,
    soil: {
      effectivePh: 5.2,
      sandPct: 35.0, siltPct: 45.0, clayPct: 20.0, somPct: 4.5, socGKg: 26.1,
      bdodGCm3: 1.15, cecCmolKg: 22.0, cfvoPct: 2.0, maxDepthCm: 150,
      usdaTexture: "Loam", faoTexture: "medium", awcMm: 165.0
    },
    soilTexture: "medium",
    rad: 4.2,
    keySpeciesToCheck: ["Solanum tuberosum", "Alnus acuminata", "Quercus humboldtii", "Coffea arabica", "Theobroma cacao"]
  },
  {
    id: "mumbai_in",
    name: "Mumbai, Maharashtra, India",
    lat: 19.07,
    lon: 72.87,
    elevation: 15,
    biome: "Tropical Wet-and-Dry Coastal Monsoon",
    terrain: { slope: 1.0, aspect: 270 },
    tavg: [24.2, 25.0, 27.2, 29.5, 31.0, 29.8, 28.0, 27.5, 28.0, 29.0, 27.8, 25.5],
    tmin: [17.5, 18.5, 21.0, 24.5, 27.0, 26.5, 25.5, 25.0, 25.0, 24.0, 21.5, 18.8],
    prec: [0.5, 0.2, 0.5, 1.5, 15.0, 520.0, 750.0, 560.0, 320.0, 65.0, 10.0, 1.5], // 2244 mm (4-month deluge, 7-month drought)
    et0: [115.0, 125.0, 160.0, 180.0, 195.0, 140.0, 115.0, 110.0, 125.0, 145.0, 130.0, 115.0],
    absMin: 11.0,
    ph: 6.8,
    soil: {
      effectivePh: 6.8,
      sandPct: 25.0, siltPct: 30.0, clayPct: 45.0, somPct: 1.8, socGKg: 10.4,
      bdodGCm3: 1.35, cecCmolKg: 35.0, cfvoPct: 3.0, maxDepthCm: 140,
      usdaTexture: "Clay", faoTexture: "heavy", awcMm: 160.0
    },
    soilTexture: "heavy",
    rad: 5.1,
    keySpeciesToCheck: ["Mangifera indica", "Tectona grandis", "Cocos nucifera", "Azadirachta indica", "Pinus sylvestris"]
  },
  {
    id: "zermatt_ch",
    name: "Zermatt / Valais, Switzerland",
    lat: 45.98,
    lon: 7.74,
    elevation: 1620,
    biome: "Inner-Alpine Mountain Slope (High Elevation)",
    terrain: { slope: 25.0, aspect: 160 }, // 25 deg steep mountain slope
    tavg: [-4.0, -3.2, 0.5, 4.5, 9.2, 13.0, 15.2, 14.6, 11.2, 6.5, 0.8, -3.0],
    tmin: [-8.0, -7.5, -4.0, -0.5, 3.8, 7.2, 9.0, 8.8, 6.0, 2.0, -3.0, -6.8],
    prec: [45.0, 38.0, 42.0, 50.0, 68.0, 75.0, 70.0, 78.0, 55.0, 58.0, 62.0, 52.0], // 693 mm
    et0: [12.0, 18.0, 38.0, 62.0, 95.0, 115.0, 122.0, 108.0, 72.0, 42.0, 18.0, 10.0],
    absMin: -22.0,
    ph: 5.8,
    soil: {
      effectivePh: 5.8,
      sandPct: 55.0, siltPct: 32.0, clayPct: 13.0, somPct: 3.5, socGKg: 20.3,
      bdodGCm3: 1.30, cecCmolKg: 16.0, cfvoPct: 35.0, maxDepthCm: 35, // Shallow stony alpine regolith
      usdaTexture: "Sandy Loam", faoTexture: "light", awcMm: 38.0
    },
    soilTexture: "light",
    rad: 3.8,
    keySpeciesToCheck: ["Larix decidua", "Pinus cembra", "Picea abies", "Olea europaea", "Quercus ilex"]
  },
  {
    id: "antalya_tr",
    name: "Antalya Taurus Mountains, Turkey",
    lat: 36.85,
    lon: 30.50,
    elevation: 850,
    biome: "Mediterranean Karstic Steep Mountain Slope",
    terrain: { slope: 22.0, aspect: 190 }, // 22 deg steep south-facing limestone slope
    tavg: [6.5, 7.8, 10.5, 14.5, 19.2, 24.0, 27.5, 27.2, 23.0, 17.5, 12.0, 8.0],
    tmin: [2.5, 3.5, 5.5, 9.0, 13.0, 17.5, 21.0, 20.8, 17.0, 12.5, 7.5, 4.0],
    prec: [195.0, 140.0, 85.0, 52.0, 28.0, 8.0, 2.0, 3.0, 18.0, 75.0, 130.0, 210.0], // 946 mm
    et0: [35.0, 48.0, 82.0, 118.0, 165.0, 198.0, 215.0, 195.0, 145.0, 95.0, 52.0, 32.0],
    absMin: -6.5,
    ph: 7.6,
    soil: {
      effectivePh: 7.6,
      sandPct: 30.0, siltPct: 40.0, clayPct: 30.0, somPct: 2.2, socGKg: 12.8,
      bdodGCm3: 1.38, cecCmolKg: 26.0, cfvoPct: 45.0, maxDepthCm: 25, // Shallow stony karstic soil
      usdaTexture: "Clay Loam", faoTexture: "medium", awcMm: 32.0
    },
    soilTexture: "medium",
    rad: 5.4,
    keySpeciesToCheck: ["Cedrus libani", "Pinus brutia", "Quercus coccifera", "Ceratonia siliqua", "Juglans regia"]
  },
  {
    id: "fairbanks_us",
    name: "Fairbanks, Alaska, USA",
    lat: 64.84,
    lon: -147.72,
    elevation: 140,
    biome: "Subarctic Boreal Taiga Forest",
    terrain: { slope: 1.5, aspect: 180 },
    tavg: [-22.5, -18.5, -10.5, 0.5, 9.5, 15.5, 17.0, 13.5, 7.0, -3.5, -15.5, -21.0],
    tmin: [-27.5, -24.5, -18.0, -6.5, 3.0, 9.5, 11.5, 8.5, 2.0, -8.0, -20.5, -26.0],
    prec: [12.0, 10.0, 9.0, 8.0, 15.0, 35.0, 55.0, 48.0, 32.0, 22.0, 18.0, 16.0], // 280 mm
    et0: [2.0, 5.0, 18.0, 48.0, 92.0, 125.0, 130.0, 95.0, 48.0, 15.0, 3.0, 1.0],
    absMin: -48.0,
    ph: 6.2,
    soil: {
      effectivePh: 6.2,
      sandPct: 35.0, siltPct: 55.0, clayPct: 10.0, somPct: 4.8, socGKg: 27.8,
      bdodGCm3: 1.25, cecCmolKg: 18.0, cfvoPct: 5.0, maxDepthCm: 80,
      usdaTexture: "Silt Loam", faoTexture: "medium", awcMm: 125.0
    },
    soilTexture: "medium",
    rad: 2.8,
    keySpeciesToCheck: ["Picea mariana", "Picea glauca", "Betula neoalaskana", "Populus tremuloides", "Quercus robur"]
  },
  {
    id: "perth_au",
    name: "Perth, Western Australia",
    lat: -31.95,
    lon: 115.86,
    elevation: 30,
    biome: "Mediterranean Sandy Plain / Swan Coastal Plain",
    terrain: { slope: 1.0, aspect: 0 },
    tavg: [24.8, 25.2, 23.5, 20.0, 16.5, 14.0, 13.2, 13.8, 15.5, 18.0, 20.8, 23.0],
    tmin: [17.8, 18.2, 16.5, 13.5, 10.5, 8.5, 7.8, 8.2, 9.5, 11.5, 14.0, 16.0],
    prec: [15.0, 12.0, 18.0, 38.0, 85.0, 135.0, 145.0, 115.0, 60.0, 38.0, 22.0, 10.0], // 693 mm
    et0: [210.0, 185.0, 155.0, 105.0, 72.0, 55.0, 58.0, 72.0, 95.0, 138.0, 175.0, 205.0],
    absMin: 0.5,
    ph: 6.2,
    soil: {
      effectivePh: 6.2,
      sandPct: 92.0, siltPct: 5.0, clayPct: 3.0, somPct: 0.8, socGKg: 4.6,
      bdodGCm3: 1.58, cecCmolKg: 3.8, cfvoPct: 1.0, maxDepthCm: 180,
      usdaTexture: "Sand", faoTexture: "light", awcMm: 48.0
    },
    soilTexture: "light",
    rad: 5.6,
    keySpeciesToCheck: ["Eucalyptus gomphocephala", "Corymbia calophylla", "Banksia attenuata", "Olea europaea", "Picea abies"]
  },
  {
    id: "nairobi_ke",
    name: "Nairobi, Kenya",
    lat: -1.29,
    lon: 36.82,
    elevation: 1795,
    biome: "East African Tropical Highland Plateau",
    terrain: { slope: 2.0, aspect: 0 },
    tavg: [19.2, 20.0, 20.2, 19.5, 18.2, 16.8, 16.0, 16.5, 18.2, 19.5, 19.0, 18.8],
    tmin: [12.5, 13.0, 14.0, 14.5, 13.5, 11.5, 10.5, 10.8, 11.5, 13.0, 13.5, 13.0],
    prec: [55.0, 50.0, 95.0, 215.0, 150.0, 35.0, 18.0, 22.0, 30.0, 55.0, 145.0, 90.0], // 960 mm (Bimodal)
    et0: [125.0, 128.0, 135.0, 110.0, 98.0, 85.0, 82.0, 88.0, 112.0, 125.0, 105.0, 115.0],
    absMin: 5.0,
    ph: 5.8,
    soil: {
      effectivePh: 5.8,
      sandPct: 15.0, siltPct: 25.0, clayPct: 60.0, somPct: 3.2, socGKg: 18.6,
      bdodGCm3: 1.22, cecCmolKg: 25.0, cfvoPct: 2.0, maxDepthCm: 180, // Fertile volcanic red clay (Nitisol)
      usdaTexture: "Clay", faoTexture: "heavy", awcMm: 175.0
    },
    soilTexture: "heavy",
    rad: 5.2,
    keySpeciesToCheck: ["Coffea arabica", "Croton megalocarpus", "Grevillea robusta", "Persea americana", "Malus domestica"]
  },
  {
    id: "shanghai_cn",
    name: "Shanghai / Yangtze Delta, China",
    lat: 31.23,
    lon: 121.47,
    elevation: 10,
    biome: "East Asian Humid Subtropical Alluvial Plain",
    terrain: { slope: 0.5, aspect: 180 },
    tavg: [4.8, 6.5, 10.2, 15.8, 21.0, 24.8, 28.8, 28.5, 24.5, 19.2, 13.5, 7.5],
    tmin: [1.8, 3.2, 6.8, 12.0, 17.5, 21.8, 25.8, 25.5, 21.2, 15.5, 9.8, 4.0],
    prec: [60.0, 65.0, 95.0, 90.0, 105.0, 175.0, 160.0, 155.0, 125.0, 65.0, 55.0, 45.0], // 1195 mm
    et0: [35.0, 45.0, 72.0, 105.0, 135.0, 138.0, 172.0, 160.0, 115.0, 82.0, 52.0, 38.0],
    absMin: -6.0,
    ph: 6.8,
    soil: {
      effectivePh: 6.8,
      sandPct: 15.0, siltPct: 65.0, clayPct: 20.0, somPct: 2.1, socGKg: 12.2,
      bdodGCm3: 1.32, cecCmolKg: 18.0, cfvoPct: 0.0, maxDepthCm: 180, // Deep alluvial silt loam
      usdaTexture: "Silt Loam", faoTexture: "medium", awcMm: 195.0
    },
    soilTexture: "medium",
    rad: 3.9,
    keySpeciesToCheck: ["Ginkgo biloba", "Cinnamomum camphora", "Metasequoia glyptostroboides", "Camellia sinensis", "Hevea brasiliensis"]
  },
  {
    id: "buenos_aires_ar",
    name: "Buenos Aires / Pampas, Argentina",
    lat: -34.60,
    lon: -58.38,
    elevation: 25,
    biome: "Temperate Humid Grassland / Pampas",
    terrain: { slope: 0.5, aspect: 0 },
    tavg: [25.0, 23.8, 21.5, 17.5, 14.0, 11.2, 10.8, 12.5, 14.8, 18.0, 21.0, 23.5],
    tmin: [19.5, 18.8, 16.5, 13.0, 9.8, 7.5, 7.0, 8.2, 10.2, 13.0, 15.8, 18.0],
    prec: [120.0, 115.0, 135.0, 105.0, 85.0, 60.0, 55.0, 65.0, 75.0, 120.0, 110.0, 105.0], // 1050 mm
    et0: [165.0, 135.0, 115.0, 75.0, 48.0, 35.0, 38.0, 52.0, 78.0, 112.0, 145.0, 170.0],
    absMin: -2.5,
    ph: 6.6,
    soil: {
      effectivePh: 6.6,
      sandPct: 20.0, siltPct: 55.0, clayPct: 25.0, somPct: 3.5, socGKg: 20.3,
      bdodGCm3: 1.25, cecCmolKg: 26.0, cfvoPct: 0.0, maxDepthCm: 180, // Deep fertile Mollisol
      usdaTexture: "Silt Loam", faoTexture: "medium", awcMm: 190.0
    },
    soilTexture: "medium",
    rad: 4.5,
    keySpeciesToCheck: ["Erythrina crista-galli", "Phytolacca dioica", "Prosopis alba", "Eucalyptus camaldulensis", "Picea abies"]
  },
  {
    id: "reykjavik_is",
    name: "Reykjavik, Iceland",
    lat: 64.14,
    lon: -21.94,
    elevation: 30,
    biome: "Subpolar Oceanic / Volcanic Andosol",
    terrain: { slope: 2.0, aspect: 180 },
    tavg: [0.0, 0.2, 1.0, 3.5, 6.8, 10.0, 11.5, 11.0, 8.0, 4.5, 1.8, 0.2],
    tmin: [-2.8, -2.5, -2.0, 0.5, 3.8, 7.2, 9.0, 8.5, 5.5, 2.0, -0.8, -2.5],
    prec: [85.0, 80.0, 82.0, 60.0, 50.0, 50.0, 52.0, 65.0, 75.0, 85.0, 80.0, 90.0], // 854 mm
    et0: [8.0, 12.0, 25.0, 48.0, 82.0, 105.0, 110.0, 88.0, 52.0, 25.0, 10.0, 6.0],
    absMin: -16.0,
    ph: 6.0,
    soil: {
      effectivePh: 6.0,
      sandPct: 45.0, siltPct: 40.0, clayPct: 15.0, somPct: 6.5, socGKg: 37.7,
      bdodGCm3: 0.95, cecCmolKg: 32.0, cfvoPct: 15.0, maxDepthCm: 100, // Volcanic Andosol
      usdaTexture: "Loam", faoTexture: "medium", awcMm: 160.0
    },
    soilTexture: "medium",
    rad: 2.3,
    keySpeciesToCheck: ["Betula pubescens", "Sorbus aucuparia", "Salix caprea", "Larix sibirica", "Olea europaea"]
  },
  {
    id: "kyoto_jp",
    name: "Kyoto, Kansai, Japan",
    lat: 35.01,
    lon: 135.76,
    elevation: 60,
    biome: "Temperate East Asian Humid Forest Basin",
    terrain: { slope: 3.0, aspect: 180 },
    tavg: [4.5, 5.5, 9.0, 14.5, 19.5, 23.5, 27.5, 28.5, 24.5, 18.5, 12.5, 7.0],
    tmin: [1.2, 1.8, 4.5, 9.5, 14.8, 19.5, 23.8, 24.5, 20.5, 14.0, 8.2, 3.2],
    prec: [55.0, 68.0, 115.0, 130.0, 155.0, 220.0, 240.0, 160.0, 180.0, 120.0, 75.0, 52.0], // 1570 mm
    et0: [32.0, 42.0, 70.0, 102.0, 132.0, 135.0, 165.0, 160.0, 112.0, 78.0, 48.0, 32.0],
    absMin: -6.5,
    ph: 5.6,
    soil: {
      effectivePh: 5.6,
      sandPct: 35.0, siltPct: 40.0, clayPct: 25.0, somPct: 3.8, socGKg: 22.0,
      bdodGCm3: 1.20, cecCmolKg: 20.0, cfvoPct: 5.0, maxDepthCm: 160,
      usdaTexture: "Loam", faoTexture: "medium", awcMm: 175.0
    },
    soilTexture: "medium",
    rad: 3.8,
    keySpeciesToCheck: ["Cryptomeria japonica", "Chamaecyparis obtusa", "Acer palmatum", "Ginkgo biloba", "Hevea brasiliensis"]
  }
];

// ---------------------------------------------------------------------------
// Benchmark Execution & Metric Computation
// ---------------------------------------------------------------------------
console.log(`Starting comparative benchmark across ${SITES.length} global sites on ${species.length} species...`);

const results = [];

for (const site of SITES) {
  const siteResults = {
    id: site.id,
    name: site.name,
    biome: site.biome,
    climate_summary: {
      annualRain: site.prec.reduce((a, b) => a + b, 0),
      meanTemp: +(site.tavg.reduce((a, b) => a + b, 0) / 12).toFixed(1),
      absMin: site.absMin,
      slope: site.terrain?.slope ?? 0,
      ph: site.soil.effectivePh,
      texture: site.soil.usdaTexture,
      faoTexture: site.soil.faoTexture,
      depthCm: site.soil.maxDepthCm
    },
    counts: {
      origin: { suitable: 0, very_suitable: 0, total_pass: 0 },
      v2: { suitable: 0, very_suitable: 0, total_pass: 0 }
    },
    species_scores: []
  };

  const speciesEvaluated = [];

  for (const sp of species) {
    const resOrig = scoreSpeciesOrigin(sp, site);
    const resV2 = scoreSpeciesV2(sp, site);

    const isTreeOrPerennial = sp.porte === "tree" || sp.tree || !sp.annual;

    if (resOrig.score >= 0.4) siteResults.counts.origin.suitable++;
    if (resOrig.score >= 0.6) siteResults.counts.origin.very_suitable++;
    if (resOrig.score > 0) siteResults.counts.origin.total_pass++;

    if (resV2.score >= 0.4) siteResults.counts.v2.suitable++;
    if (resV2.score >= 0.6) siteResults.counts.v2.very_suitable++;
    if (resV2.score > 0) siteResults.counts.v2.total_pass++;

    speciesEvaluated.push({
      sci: sp.sci,
      common: sp.common,
      tree: sp.tree || sp.porte === "tree",
      annual: sp.annual,
      decid: sp.decid,
      gclass: sp.gclass,
      orig: {
        score: +resOrig.score.toFixed(3),
        fit: +resOrig.fit.toFixed(3),
        factors: resOrig.factors,
        grade: gradeV2(resOrig.score)
      },
      v2: {
        score: +resV2.score.toFixed(3),
        fit: +resV2.fit.toFixed(3),
        factors: resV2.factors,
        grade: gradeV2(resV2.score),
        window: resV2.window
      },
      delta: +(resV2.score - resOrig.score).toFixed(3)
    });
  }

  // Sort by score & fit for Trees
  const treesOrig = speciesEvaluated.filter(s => s.tree).sort((a, b) => (b.orig.score - a.orig.score) || (b.orig.fit - a.orig.fit));
  const treesV2 = speciesEvaluated.filter(s => s.tree).sort((a, b) => (b.v2.score - a.v2.score) || (b.v2.fit - a.v2.fit));

  // Discrepancies & Flagged Species
  // 1. High in Origin, Zero/Low in v2 (Origin False Positive or v2 Strict Gate)
  const originHighV2Low = speciesEvaluated
    .filter(s => s.orig.score >= 0.6 && s.v2.score < 0.3)
    .sort((a, b) => (b.orig.score - a.orig.score));

  // 2. Zero/Low in Origin, High in v2 (Origin False Negative or v2 Perennial Recovery)
  const originLowV2High = speciesEvaluated
    .filter(s => s.orig.score < 0.3 && s.v2.score >= 0.6)
    .sort((a, b) => (b.v2.score - a.v2.score));

  siteResults.top_trees_origin = treesOrig.slice(0, 10);
  siteResults.top_trees_v2 = treesV2.slice(0, 10);
  siteResults.origin_high_v2_low = originHighV2Low.slice(0, 10);
  siteResults.origin_low_v2_high = originLowV2High.slice(0, 10);

  // Key species ground truth review
  siteResults.key_species_review = site.keySpeciesToCheck.map(name => {
    const found = speciesEvaluated.find(s => s.sci.toLowerCase() === name.toLowerCase());
    return {
      sci: name,
      found: !!found,
      orig_score: found?.orig?.score ?? null,
      orig_factors: found?.orig?.factors ?? null,
      v2_score: found?.v2?.score ?? null,
      v2_factors: found?.v2?.factors ?? null,
      delta: found ? +(found.v2.score - found.orig.score).toFixed(3) : null
    };
  });

  results.push(siteResults);
}

// Write out JSON artifact
const jsonOutPath = resolve(__dirname, "../data/scoring_comparison_20_biomes.json");
writeFileSync(jsonOutPath, JSON.stringify(results, null, 2), "utf8");
console.log(`Saved detailed benchmark JSON to ${jsonOutPath}`);

// Generate high-level statistical summary
console.log("\n================================================================================");
console.log("             GLOBAL 20-BIOME BENCHMARK SUMMARY TABLE                            ");
console.log("================================================================================");
console.log(String("Site Name").padEnd(36) + " | Orig Pass | v2 Pass | Orig>=0.6 | v2>=0.6 | Top Divergence");
console.log("-".repeat(95));

for (const r of results) {
  const topDiv = r.origin_high_v2_low[0]?.sci ?? r.origin_low_v2_high[0]?.sci ?? "Aligned";
  console.log(
    r.name.slice(0, 35).padEnd(36) + " | " +
    String(r.counts.origin.total_pass).padStart(9) + " | " +
    String(r.counts.v2.total_pass).padStart(7) + " | " +
    String(r.counts.origin.very_suitable).padStart(9) + " | " +
    String(r.counts.v2.very_suitable).padStart(7) + " | " +
    topDiv
  );
}
console.log("================================================================================\n");
