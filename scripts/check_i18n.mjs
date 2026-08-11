// Verifies every language dict covers the same keys as PT (the reference).
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
console.log(fail ? "i18n parity FAILED" : "i18n parity ok");
process.exit(fail);
