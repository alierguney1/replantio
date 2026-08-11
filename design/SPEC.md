# Espécies recomendadas · criteria row · implementation spec

Winner: `design/variant-d.html` (iterated from variant-b).
Screens: `final-1-default.png`, `final-2-open.png`, `final-3-filtered-closed.png`, `final-4-filtered-open.png`.

Replaces the `.filters` / `.filter select` block entirely. Three states:
1. **default**: one header line, `ESPÉCIES RECOMENDADAS` left, `317 espécies · critérios ▾` right. Nothing else. The list is the only focal element.
2. **constrained + closed**: same header (count turns accent, reads `31 de 317 · critérios`) plus a one-line summary of the active constraints.
3. **open**: four hairline rows, uppercase key column, options inline with the count each option would yield.

---

## 1. CSS

**Delete** from `style.css`:

```css
/* filter selects */
.filters { ... }
.filter label { ... }
.filter select { ... }
.filter select:focus { ... }
```

and (only wrapped the filters, now unused):

```css
.sp-chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 12px; }
```

Keep `.chip` and `.chip.more` (still used by "Mostrar mais" and "Mostrar mesmo assim").

**Add**:

```css
/* ---------- criteria row ---------- */
.sec-row { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin: 28px 0 10px; }
.sec-row .section-h { margin: 0; }

.crit-toggle {
  flex: 0 0 auto; font: inherit; font-size: 11px; color: var(--muted);
  background: none; border: 0; padding: 0; cursor: pointer; white-space: nowrap;
}
.crit-toggle b { font-family: var(--mono); font-weight: 500; font-variant-numeric: tabular-nums; color: var(--text); }
.crit-toggle.active b { color: var(--accent); }
.crit-toggle:hover { color: var(--text); }
.crit-toggle .car {
  display: inline-block; width: 0; height: 0; margin-left: 6px; vertical-align: 2px;
  border-left: 3.5px solid transparent; border-right: 3.5px solid transparent;
  border-top: 4px solid currentColor; opacity: .6; transition: transform .16s;
}
.crit-toggle[aria-expanded="true"] .car { transform: rotate(180deg); }

.crit-summary {
  display: block; width: 100%; text-align: left; font: inherit; font-size: 11px; line-height: 1.7;
  color: var(--muted); background: none; border: 0; padding: 0; margin: -4px 0 12px; cursor: pointer;
}
.crit-summary b { font-weight: 400; color: var(--text); }
.crit-summary .d { opacity: .4; margin: 0 2px; }
.crit-summary:hover b { color: var(--accent); }

.crit-panel { margin: 0 0 14px; }
.crit-panel[hidden] { display: none; }
.crit-row { display: flex; align-items: baseline; gap: 10px; padding: 8px 0; border-top: 1px solid var(--line); }
.crit-row:last-of-type { border-bottom: 1px solid var(--line); }
.crit-row .k {
  flex: 0 0 74px; font-size: 10px; text-transform: uppercase; letter-spacing: .6px;
  color: var(--muted); padding-top: 1px;
}
.crit-row .opts { display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 14px; row-gap: 4px; margin: -3px 0; }
.opt { font: inherit; font-size: 11.5px; background: none; border: 0; padding: 3px 0; margin: 0; color: var(--muted); cursor: pointer; }
.opt:hover { color: var(--text); }
.opt.on { color: var(--text); }
.opt.on.constrained { color: var(--accent); }
.opt .c { font-family: var(--mono); font-size: 9.5px; color: rgba(147, 160, 150, .7); margin-left: 4px; font-variant-numeric: tabular-nums; }
.opt[disabled] { opacity: .38; cursor: default; }

.crit-clear { display: block; margin: 9px 0 0 auto; font: inherit; font-size: 10.5px; color: var(--muted); background: none; border: 0; padding: 0; cursor: pointer; }
.crit-clear:hover { color: var(--text); }
```

Note: no separator glyphs between options. Spacing alone groups them, so a wrap can never orphan a `·` (that bug is visible in the earlier `variant-b.png`).

---

## 2. HTML the JS must produce

```html
<div class="sec-row">
  <div class="section-h">Espécies recomendadas</div>
  <button class="crit-toggle active" data-crit-toggle aria-expanded="false"><b>31</b> de 317 &middot; critérios<i class="car"></i></button>
</div>

<!-- only when constraints active AND panel closed -->
<button class="crit-summary" data-crit-toggle><b>nativas daqui</b> <span class="d">&middot;</span> <b>fruta</b> <span class="d">&middot;</span> <b>até 20 anos</b></button>

<div class="crit-panel" hidden>
  <div class="crit-row">
    <div class="k">Origem</div>
    <div class="opts">
      <button class="opt" data-f="origin" data-v="all">todas <span class="c">317</span></button>
      <button class="opt on constrained" data-f="origin" data-v="native" aria-pressed="true">nativas daqui</button>
    </div>
  </div>
  <!-- ... uso, maturidade, copa adulta ... -->
  <button class="crit-clear" data-crit-clear>limpar critérios</button>
</div>
<div id="sp-list">...</div>
```

Rules baked into the markup:
- the **selected** option carries `.on`, drops its `<span class="c">` count (it always equals the header count, so it is pure redundancy), and gets `aria-pressed="true"`;
- `.constrained` is added only when the selected option is **not** the first (default) one in its row: that is what turns it green;
- an option whose count is `0` and is not selected renders `disabled` (greys out, unclickable);
- toggle text: `<b>{n}</b> de {total} · critérios` when constrained, `<b>{total}</b> espécies · critérios` when not. `.active` on the toggle only when constrained.

---

## 3. JS

### 3a. module-level helpers (near `nearbyHere` / `USE_LABELS`)

```js
// class-level, so memoise per growth class
const MAT_CLS = {}, CROWN_CLS = {};
const matCls = g => MAT_CLS[g] ??= maturityYears(CLASSES[g]);
const crownCls = g => CROWN_CLS[g] ??= (() => {
  const cls = CLASSES[g], h = height(Math.min(maturityYears(cls), 120), cls);
  return crownDiameterM(dbhCm(h, cls), h);
})();

const critMatch = (s, c) => s.score > 0.05
  && (c.use === "all" || s.sp.uses.includes(c.use))
  && (!c.nativeOnly || nativeHere(s.sp) === true)
  && (!c.matMax || matCls(s.sp.gclass) <= c.matMax)
  && (!c.crownMin || crownCls(s.sp.gclass) >= c.crownMin);

const critState = () => ({ use: current.filter, nativeOnly: current.nativeOnly, matMax: current.matMax, crownMin: current.crownMin });
const critCount = over => current.scored.reduce((n, s) => n + (critMatch(s, { ...critState(), ...over }) ? 1 : 0), 0);

const CRIT_DIMS = () => [
  ...(current.cc ? [{
    key: "origin", label: "Origin", cur: current.nativeOnly ? "native" : "all",
    opts: [["all", tr("all origins")], ["native", tr("native here")]],
    over: v => ({ nativeOnly: v === "native" }),
  }] : []),
  {
    key: "use", label: "Use", cur: current.filter,
    opts: [["all", tr("all uses")], ...["timber", "fruit", "environmental", "medicinal", "forage"].map(u => [u, tr(USE_LABELS[u])])],
    over: v => ({ use: v }),
  },
  {
    key: "mat", label: "Maturity", title: tr("Time to max height"), cur: String(current.matMax ?? ""),
    opts: [["", tr("no limit")], ["20", tfmt("under {n} years", { n: 20 })], ["90", tfmt("under {n} years", { n: 90 })]],
    over: v => ({ matMax: v ? +v : null }),
  },
  {
    key: "crown", label: "Mature canopy", cur: String(current.crownMin ?? ""),
    opts: [["", tr("no minimum")], ["4", "&ge; 4 m"], ["5", "&ge; 5 m"]],
    over: v => ({ crownMin: v ? +v : null }),
  },
];

function critMarkup() {
  const dims = CRIT_DIMS();
  const n = critCount({});
  const total = critCount({ use: "all", nativeOnly: false, matMax: null, crownMin: null });
  const active = dims.flatMap(d => {
    const i = d.opts.findIndex(o => o[0] === d.cur);
    return i > 0 ? [d.opts[i][1]] : [];
  });

  const rows = dims.map(d => `<div class="crit-row">
    <div class="k"${d.title ? ` title="${d.title}"` : ""}>${tr(d.label)}</div>
    <div class="opts">${d.opts.map(([v, txt], i) => {
      const on = d.cur === v, c = on ? 0 : critCount(d.over(v));
      return `<button class="opt${on ? (i ? " on constrained" : " on") : (c ? "" : " zero")}" data-f="${d.key}" data-v="${v}"${on ? ' aria-pressed="true"' : ""}${!on && !c ? " disabled" : ""}>${txt}${on ? "" : `<span class="c">${c}</span>`}</button>`;
    }).join("")}</div></div>`).join("");

  return `<div class="sec-row">
      <div class="section-h">${tr("Recommended species")}</div>
      <button class="crit-toggle${active.length ? " active" : ""}" data-crit-toggle aria-expanded="${current.critOpen ? "true" : "false"}">${
        active.length ? tfmt("{n} of {t}", { n: `<b>${fmt(n)}</b>`, t: fmt(total) }) : tfmt("{n} species", { n: `<b>${fmt(total)}</b>` })
      } &middot; ${tr("criteria")}<i class="car"></i></button>
    </div>
    ${active.length && !current.critOpen ? `<button class="crit-summary" data-crit-toggle>${active.map(a => `<b>${a}</b>`).join(' <span class="d">&middot;</span> ')}</button>` : ""}
    <div class="crit-panel"${current.critOpen ? "" : " hidden"}>${rows}${
      active.length ? `<button class="crit-clear" data-crit-clear>${tr("clear criteria")}</button>` : ""
    }</div>`;
}
```

### 3b. in `renderResults()`

Delete `filterSel` and the `chips` template literal. Reuse `critMatch` for the pool so the counts and the list can never disagree:

```js
const pool = scored.filter(s => critMatch(s, critState()));
```

(`matureCrown` and the inline `dls`-scoped closure go away; `dls` is still needed for the readout.)

Replace these two lines of the panel template

```js
<div class="section-h">${tr("Recommended species")}</div>
<div class="sp-chips">${chips}</div>
```

with

```js
${critMarkup()}
```

### 3c. state + events

`current = { ..., critOpen: false }` at creation (app.js:382).

**Delete** the whole `content.addEventListener("change", ...)` block (app.js:499-509).

Add to the existing `content` click handler, above the `[data-toggle]` branch:

```js
if (e.target.closest("[data-crit-toggle]")) {
  current.critOpen = !current.critOpen;
  const p = content.querySelector(".crit-panel");
  p.hidden = !current.critOpen;
  content.querySelector(".crit-toggle").setAttribute("aria-expanded", String(current.critOpen));
  content.querySelector(".crit-summary")?.toggleAttribute("hidden", current.critOpen);
  return;
}
if (e.target.closest("[data-crit-clear]")) {
  current.filter = "all"; current.nativeOnly = false; current.matMax = null; current.crownMin = null;
  current.shown = 12; renderResults(); loadRowPhotos(); return;
}
const opt = e.target.closest(".opt[data-f]");
if (opt) {
  const v = opt.dataset.v;
  if (opt.dataset.f === "origin") current.nativeOnly = v === "native";
  if (opt.dataset.f === "use") current.filter = v;
  if (opt.dataset.f === "mat") current.matMax = v ? +v : null;
  if (opt.dataset.f === "crown") current.crownMin = v ? +v : null;
  current.shown = 12; renderResults(); loadRowPhotos(); return;
}
```

Toggling open/closed mutates the DOM in place rather than re-rendering, so the panel does not lose scroll position. Picking an option re-renders (as today), and `current.critOpen` keeps the panel open across the re-render.

### 3d. new PT keys

```js
"native here": "nativas daqui",
"all uses": "todos",
"Maturity": "Maturidade",
"no limit": "sem limite",
"no minimum": "sem mínimo",
"criteria": "critérios",
"clear criteria": "limpar critérios",
"{n} of {t}": "{n} de {t}",
"{n} species": "{n} espécies",
```

Existing keys reused unchanged: `Origin`, `Use`, `Mature canopy`, `all origins`, `under {n} years`, `Time to max height` (now only a `title` tooltip on the maturity key), and `USE_LABELS` through `tr()`.

`"Time to max height"` is too long for the 74px key column (it would wrap to three lines), which is why the visible label becomes `MATURIDADE` and the precise phrase moves to the tooltip.

---

## 4. Filter mapping

| filter | where it lives | interaction |
|---|---|---|
| Origem (`nativeOnly`) | row 1, rendered only when `current.cc` is known | two options, `todas` / `nativas daqui`; picking the second turns it green and adds it to the summary line |
| Uso (`filter`) | row 2, 6 options, wraps to two lines at 420px | single-select; `todos` returns to unfiltered |
| Maturidade (`matMax`) | row 3 | `sem limite` / `até 20 anos` / `até 90 anos` |
| Copa adulta (`crownMin`) | row 4 | `sem mínimo` / `≥ 4 m` / `≥ 5 m` |

Every non-selected option shows the count it would produce **given the other three filters as they stand**, so the user sees the cost of a click before making it, and an option that would empty the list is greyed out instead of leading to the "Nada passa do corte" dead end.
