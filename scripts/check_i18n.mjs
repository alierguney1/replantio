// Verifies every language dict covers the same keys as PT (the reference),
// and that every literal key app.js translates exists in PT at all: parity
// alone cannot see a key that is missing from every dictionary (an untranslated
// aria-label shipped that way).
import { readFileSync } from "node:fs";
import { DICTS } from "../i18n.js";
const ref = Object.keys(DICTS.pt);
let fail = 0;
for (const [lang, dict] of Object.entries(DICTS)) {
  if (lang === "pt") continue;
  const missing = ref.filter(k => !(k in dict));
  const extra = Object.keys(dict).filter(k => !(k in DICTS.pt));
  if (missing.length) { console.log(`${lang}: MISSING ${missing.length}:`, missing.slice(0, 5)); fail = 1; }
  if (extra.length) { console.log(`${lang}: extra ${extra.length}:`, extra.slice(0, 5)); }
}
// literal keys: tr("..."), tfmt("...", ...), and the criteria-row labels app.js
// passes through tr(d.label)
const app = readFileSync(new URL("../app.js", import.meta.url), "utf8");
const used = new Set();
for (const m of app.matchAll(/\b(?:tr|tfmt)\(\s*"((?:[^"\\]|\\.)*)"/g)) used.add(JSON.parse(`"${m[1]}"`));
for (const m of app.matchAll(/\blabel: "((?:[^"\\]|\\.)*)"/g)) used.add(JSON.parse(`"${m[1]}"`));
const untranslated = [...used].filter(k => !(k in DICTS.pt));
if (untranslated.length) { console.log(`app.js: ${untranslated.length} keys in no dictionary:`, untranslated.slice(0, 5)); fail = 1; }
console.log(fail ? "i18n parity FAILED" : `i18n parity ok (${used.size} app.js keys covered)`);
process.exit(fail);
