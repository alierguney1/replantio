// Comprehensive real-world benchmark suite for the hybrid establishment strategy model
// Tests real-world ecological species across global biomes, verifying physiological constraints
// from Kew SID (recalcitrant, micro-seed, orthodox) and environmental aridity gates (ERA5 AI).

import assert from "node:assert";
import { readFileSync } from "node:fs";
import { establishmentStrategy, aridityClass } from "../scoring.js";
import { DICTS } from "../i18n.js";

const speciesList = JSON.parse(readFileSync(new URL("../data/species.json", import.meta.url)));
const spBySci = new Map(speciesList.map(s => [s.sci, s]));

console.log("=== REPLANTIO REAL-WORLD ESTABLISHMENT BENCHMARK SUITE ===");
console.log(`Loaded ${speciesList.length} species from species.json\n`);

// Fixture Sites
const SITE_HUMID = { ai: 1.15, annualRain: 1200, name: "Hamburg (Humid, AI=1.15)" };
const SITE_TROPICAL_WET = { ai: 1.60, annualRain: 1800, name: "Pará / Amazon (Humid, AI=1.60)" };
const SITE_SEMI_ARID = { ai: 0.24, annualRain: 320, name: "Konya (Semi-arid, AI=0.24)" };
const SITE_SEMI_ARID_IRRIGATED = { ai: 0.24, annualRain: 320, irrigated: true, name: "Konya Irrigated" };
const SITE_ARID = { ai: 0.12, annualRain: 150, name: "Almería (Arid, AI=0.12)" };

// --- 1. RECALCITRANT SEEDS (Kew SID: Desiccation-sensitive; die if dried/broadcast)
console.log("--- 1. Testing Recalcitrant Hardwood & Fruit Species ---");
const recalcitrantSpecies = [
  "Quercus robur",        // English Oak (acorns lose viability quickly upon drying)
  "Castanea sativa",      // Sweet Chestnut (large recalcitrant seed)
  "Eriobotrya japonica",  // Loquat (recalcitrant fleshy seed)
];

for (const sci of recalcitrantSpecies) {
  const sp = spBySci.get(sci);
  assert(sp, `Species ${sci} must exist in species.json`);
  assert.equal(sp.storage, "recalcitrant", `${sci} must be recorded as recalcitrant from Kew SID`);

  // Even on a humid site with plenty of rain, recalcitrant species cannot be direct-seeded safely on open ground
  const res = establishmentStrategy(sp, SITE_HUMID);
  assert.equal(res.method, "seedling", `${sci} must be seedling only`);
  assert.equal(res.directViable, false, `${sci} direct seeding must be unviable`);
  assert.equal(res.seedlingViable, true, `${sci} seedling planting must be viable`);
  assert.equal(res.labelKey, "Nursery seedlings (recalcitrant seed)");
  console.log(`  PASS: ${sci.padEnd(25)} -> ${res.labelKey} (1000-seed wt: ${sp.sw_1000g}g)`);
}

// --- 2. MICRO-SEEDED TREES (Kew SID: 1000-seed weight < 2g; negligible endosperm, easily choked by weeds)
console.log("\n--- 2. Testing Micro-Seeded Tree Species ---");
const microSeededSpecies = [
  "Eucalyptus grandis",     // Rose Gum (1000-seed wt ~1.4g -> 0.0014g/seed)
  "Betula pendula",         // Silver Birch (tiny winged achene ~0.3g/1000 seeds)
  "Paulownia tomentosa",    // Empress Tree (tiny winged seed ~0.15g/1000 seeds)
  "Populus nigra",          // Black Poplar (comose cottony seed ~0.4g/1000 seeds)
];

for (const sci of microSeededSpecies) {
  const sp = spBySci.get(sci);
  if (!sp) continue;
  if (sp.sw_1000g != null && sp.sw_1000g < 2.0) {
    const res = establishmentStrategy(sp, SITE_HUMID);
    assert.equal(res.method, "seedling", `${sci} must be seedling only`);
    assert.equal(res.directViable, false, `${sci} direct seeding must be unviable`);
    assert.equal(res.labelKey, "Nursery seedlings (micro-seed)");
    console.log(`  PASS: ${sci.padEnd(25)} -> ${res.labelKey} (1000-seed wt: ${sp.sw_1000g}g)`);
  }
}

// --- 3. PIONEER LEGUMES & RESTORATION DIRECT-SEEDING CANDIDATES (MUVUCA)
console.log("\n--- 3. Testing Pioneer Legumes / Direct-Seeding (Muvuca) Candidates ---");
const directSeedingTrees = [
  "Enterolobium cyclocarpum", // Guanacaste / Caro Caro (Orthodox, 703g/1000 seeds, vigorous pioneer)
  "Schizolobium parahybum",   // Guapuruvu (1417g/1000 seeds, classic Atlantic Forest direct-seeding pioneer)
  "Acacia mearnsii",          // Black Wattle (Orthodox, 13.5g/1000 seeds)
  "Senna spectabilis",        // Whitebark Senna (Orthodox, 27.2g/1000 seeds)
];

for (const sci of directSeedingTrees) {
  const sp = spBySci.get(sci);
  if (!sp) continue;

  // A. Under Humid Climate: Both methods viable!
  const resHumid = establishmentStrategy(sp, SITE_HUMID);
  assert.equal(resHumid.method, "both", `${sci} under humid climate must be viable for both`);
  assert.equal(resHumid.directViable, true);
  assert.equal(resHumid.seedlingViable, true);
  assert.equal(resHumid.labelKey, "Nursery seedlings · Direct seeding viable");
  console.log(`  PASS: [Humid Site]       ${sci.padEnd(25)} -> ${resHumid.labelKey}`);

  // B. Under Semi-Arid Climate (Konya AI=0.24, no irrigation): Aridity gate MUST block direct seeding!
  const resArid = establishmentStrategy(sp, SITE_SEMI_ARID);
  assert.equal(resArid.method, "seedling", `${sci} under semi-arid climate must require seedlings`);
  assert.equal(resArid.directViable, false);
  assert.equal(resArid.seedlingViable, true);
  assert.equal(resArid.labelKey, "Nursery seedlings (essential on arid sites)");
  console.log(`  PASS: [Semi-Arid Site]  ${sci.padEnd(25)} -> ${resArid.labelKey}`);

  // C. Under Semi-Arid WITH Irrigation: Direct seeding viability is restored
  const resIrr = establishmentStrategy(sp, SITE_SEMI_ARID_IRRIGATED);
  assert.equal(resIrr.method, "both", `${sci} with irrigation must restore direct seeding viability`);
  assert.equal(resIrr.directViable, true);
  console.log(`  PASS: [Irrigated Site]  ${sci.padEnd(25)} -> ${resIrr.labelKey}`);
}

// --- 4. HERBACEOUS SPECIES, GRASSES & COVER CROPS
console.log("\n--- 4. Testing Herbaceous Species & Cover Crops ---");
const herbSpecies = [
  "Trifolium repens",       // White Clover
  "Medicago sativa",        // Alfalfa / Lucerne
  "Zea mays",               // Maize
  "Avena sativa",           // Oats
  "Crotalaria juncea",      // Sunn Hemp (green manure)
  "Phaseolus vulgaris",     // Common Bean
];

for (const sci of herbSpecies) {
  const sp = spBySci.get(sci);
  if (!sp) continue;
  const res = establishmentStrategy(sp, SITE_HUMID);
  assert.equal(res.method, "direct_seeding", `${sci} must be direct seeding only`);
  assert.equal(res.directViable, true);
  assert.equal(res.seedlingViable, false);
  assert.equal(res.labelKey, "Direct seeding");
  console.log(`  PASS: ${sci.padEnd(25)} -> ${res.labelKey} (porte: ${sp.porte})`);
}

// --- 5. CLIMAX & SLOW HARDWOODS (Standard Nursery Seedlings)
console.log("\n--- 5. Testing Standard Climax Hardwoods & Conifers ---");
const standardTrees = [
  "Fagus sylvatica",        // European Beech
  "Pinus sylvestris",       // Scots Pine
  "Picea abies",            // Norway Spruce
  "Abies alba",             // Silver Fir
];

for (const sci of standardTrees) {
  const sp = spBySci.get(sci);
  if (!sp) continue;
  const res = establishmentStrategy(sp, SITE_HUMID);
  assert.equal(res.method, "seedling", `${sci} must standardly be seedling`);
  assert.equal(res.directViable, false);
  assert.equal(res.seedlingViable, true);
  console.log(`  PASS: ${sci.padEnd(25)} -> ${res.labelKey}`);
}

// --- 6. CATALOG-WIDE ROBUSTNESS & i18n INTEGRITY AUDIT
console.log("\n--- 6. Auditing Full 2,009 Species Catalog ---");
const methodCounts = { direct_seeding: 0, seedling: 0, both: 0 };
const labelCounts = {};

const ptDict = DICTS.pt;
const allLangs = Object.keys(DICTS);

for (const sp of speciesList) {
  // Test both humid and semi-arid contexts
  const stratHumid = establishmentStrategy(sp, SITE_HUMID);
  const stratArid = establishmentStrategy(sp, SITE_SEMI_ARID);

  assert(stratHumid && stratArid, `Species ${sp.sci} must return valid strategy`);
  assert(typeof stratHumid.directViable === "boolean");
  assert(typeof stratHumid.seedlingViable === "boolean");

  methodCounts[stratHumid.method] = (methodCounts[stratHumid.method] || 0) + 1;
  labelCounts[stratHumid.labelKey] = (labelCounts[stratHumid.labelKey] || 0) + 1;

  // Verify all returned labelKeys and noteKeys exist in all i18n dictionaries
  for (const lang of allLangs) {
    const dict = DICTS[lang];
    assert(stratHumid.labelKey in dict, `Missing labelKey "${stratHumid.labelKey}" in language "${lang}"`);
    assert(stratHumid.noteKey in dict, `Missing noteKey "${stratHumid.noteKey}" in language "${lang}"`);
    assert(stratArid.labelKey in dict, `Missing labelKey "${stratArid.labelKey}" in language "${lang}"`);
    assert(stratArid.noteKey in dict, `Missing noteKey "${stratArid.noteKey}" in language "${lang}"`);
  }
}

console.log("Catalog breakdown under humid conditions:");
for (const [k, v] of Object.entries(methodCounts)) {
  console.log(`  - ${k}: ${v} species (${(v / speciesList.length * 100).toFixed(1)}%)`);
}
console.log("\nEstablishment sub-labels across catalog:");
for (const [k, v] of Object.entries(labelCounts)) {
  console.log(`  - "${k}": ${v} species`);
}

console.log("\nALL ESTABLISHMENT BENCHMARKS PASSED SUCCESSFULLY!");
