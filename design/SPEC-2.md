# Painel direito · passe estético · implementation spec

Winner: **`design/panel-a.html`** ("placa de instrumento"), after 7 iteration rounds.
Rejected: `panel-b.html` (warm notebook: muddy greens, 6px radius loses the glass, ruled stats add ink)
and `panel-c.html` (deep glass: circular thumbs read as avatars, recessed plates reintroduce
boxes-in-boxes, hairline-less rows lose all scanning rhythm). Two ideas were harvested from B and
are in this spec: the **two-column site readout** and the **full-bleed specimen photo**.

Final screenshots

| file | state |
|---|---|
| `panel-a-2-open.png` | default, first card open (the money shot) |
| `panel-a-2-list.png` | all cards closed: the ledger rhythm |
| `panel-a-2-crit.png` | criteria panel open |
| `panel-a-2-filt.png` | constrained (`31 de 374`) + summary line |
| `panel-a-2-map.png` / `panel-a-2-onmap.png` | clipped/scrolling, panel meeting the map |
| `panel-b-col.png`, `panel-c-col.png` | the two rejected directions |

The criteria-row structure from `SPEC.md` is untouched. Everything below is finish.

---

## 0. The thesis, in one paragraph

The old panel was a flat rectangle holding rounded boxes inside a rounded box, with two levels of
text, three saturated data hues at three different chromas, no macro spacing, and its one genuinely
beautiful thing (the climate figure) undersold. The new panel is **one continuous surface**: rows are
separated by hairlines, never by borders, so criteria and species read as a single ledger. Type gets
**three** levels instead of two. Headings drop from weight 600 to 500, because light-on-dark type
optically gains weight and 600 was the main reason the panel felt heavy. The climate figure becomes
**one figure with one month axis**: temperature above the spine, rain hanging below it. Light comes
from above: a dark halo ring outside the panel so its edge survives bright satellite imagery, a
hairline of glass inside, one contact shadow and one ambient shadow.

Rules honoured: no lone-number tiles (every numeral is on a line with its label, or is a labelled
data mark inside a figure); no coloured left borders anywhere; IBM Plex Sans + Mono kept (see §13);
one focal element per section; no em dashes.

---

## 1. `:root`: replace the whole block

Keeps every existing token name so the rest of the app keeps working; **adds** `--faint`, `--line-2`,
`--amber`, `--water`, `--warn` and the spacing scale.

```css
:root {
  --glass: rgba(12, 16, 13, 0.84);
  --line: rgba(255, 255, 255, 0.072);
  --line-2: rgba(255, 255, 255, 0.13);
  /* three levels of ink, not two */
  --text: #e8ede8;
  --muted: #99a69c;
  --faint: #6b786f;
  /* data hues, brought to one common low chroma */
  --accent: #63c987;
  --accent-dim: rgba(99, 201, 135, 0.16);
  --amber: #d7a463;
  --water: #79a6c6;
  --warn: #e0827b;
  --radius: 14px;
  /* vertical rhythm: the panel only ever uses these */
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px; --s5: 22px; --s6: 32px; --s7: 44px;
  --pad: 22px;
  color-scheme: dark;
  --mono: "IBM Plex Mono", ui-monospace, SFMono-Regular, monospace;
  font-family: "IBM Plex Sans", system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
```

**Deleted token:** `--glass-soft` (its only user was `.sp`, which loses its background in §7).

**Two deliberate app-wide side effects.** `--accent` moves from `#55d97c` (electric mint) to `#63c987`,
and `--line` from `.09` to `.072`. Both are used by the top bar, so the brand mark, the armed draw
button and the pill borders cool and soften very slightly. That is the point: the three data hues
could not be reconciled while the green stayed at that chroma. If the owner wants the top bar frozen,
scope the two tokens to the panel by moving them into a `#panel { }` block instead.

---

## 2. The container

Replace `#panel` and `#panel-content`, and add the scrollbar + fade rules.

```css
#panel {
  position: fixed; top: 16px; right: 16px; z-index: 1000;
  max-height: calc(100vh - 32px);
  width: 420px; max-width: calc(100vw - 32px);
  border: 0; border-radius: 20px;
  background:
    linear-gradient(180deg, rgba(255,255,255,.05) 0, rgba(255,255,255,.012) 120px, rgba(255,255,255,0) 300px),
    var(--glass);
  backdrop-filter: blur(30px) saturate(1.25); -webkit-backdrop-filter: blur(30px) saturate(1.25);
  box-shadow:
    0 0 0 1px rgba(0,0,0,.55),                /* dark halo: the edge survives bright imagery */
    inset 0 0 0 1px rgba(255,255,255,.055),   /* hairline of glass */
    inset 0 1px 0 rgba(255,255,255,.10),      /* light from above */
    0 1px 2px rgba(0,0,0,.35),                /* contact */
    0 30px 64px -18px rgba(0,0,0,.78);        /* ambient */
  overflow-y: auto; overscroll-behavior: contain;
  animation: slide 0.28s cubic-bezier(0.2, 0.8, 0.2, 1);
}
#panel::-webkit-scrollbar { width: 10px; }
#panel::-webkit-scrollbar-track { background: transparent; }
#panel::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,.11); border-radius: 99px;
  border: 3px solid transparent; background-clip: content-box;
}
#panel::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,.2); }
#panel-content { padding: 0; }   /* the two zones carry their own padding now */

/* content dissolves at the bottom edge instead of being guillotined.
   It is a 42px block of its own, not a negative-margin overlay: when the panel
   is scrolled to the very end the gradient lands on its own empty space, so the
   last line of the footnote stays fully legible. Mid-scroll, sticky pins it to
   the scrollport and it dissolves whatever is passing under the edge. */
.panel-fade {
  position: sticky; bottom: 0; z-index: 2; pointer-events: none;
  height: 42px;
  background: linear-gradient(to top, rgba(13,17,14,.95), rgba(13,17,14,0));
}
```

Because the fade block supplies the panel's bottom spacing, `.p-body` needs no bottom padding:
`.p-body { padding: 0 var(--pad); }` in §3.

The old single `1px solid var(--line)` border is replaced by the two rings inside `box-shadow`. That
is what fixes the real bug in the current panel: a `.09` white hairline is invisible where the panel
overlaps roads, water or city, so the panel had no edge there. Outer dark ring plus inner light ring
reads on any imagery.

---

## 3. Header as a zone

```css
.p-head {
  position: sticky; top: 0; z-index: 3;
  padding: 19px var(--pad) 15px;
  background: linear-gradient(180deg, rgba(17,22,18,.97) 0, rgba(17,22,18,.93) 62%,
                              rgba(17,22,18,.72) 88%, rgba(17,22,18,0) 100%);
  backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
}
.p-head::after {                 /* hairline that fades out before the rounded corners */
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 1px;
  background: linear-gradient(90deg, transparent 0, rgba(255,255,255,.115) 10%,
                              rgba(255,255,255,.115) 90%, transparent 100%);
}
.p-body { padding: 0 var(--pad); }   /* the .panel-fade block supplies the bottom spacing */

.loc-title {
  font-size: 21px; font-weight: 500; letter-spacing: -.014em; line-height: 1.18;
  margin: 0 40px 0 0;
}
.loc-title .adm { color: var(--faint); font-weight: 400; }
.loc-geo {
  margin-top: 7px; font-family: var(--mono); font-size: 10.5px; font-weight: 400;
  color: var(--muted); font-variant-numeric: tabular-nums; letter-spacing: .005em;
}
.loc-geo .sep { color: rgba(255,255,255,.16); margin: 0 .55em; }
.loc-note { margin-top: 7px; font-size: 11px; line-height: 1.5; color: var(--faint); }
.loc-note b {
  font-family: var(--mono); font-size: 10.5px; font-weight: 400;
  color: var(--muted); font-variant-numeric: tabular-nums;
}

.panel-close {
  position: absolute; top: 17px; right: 16px; width: 26px; height: 26px;
  border: 0; border-radius: 7px; background: none; color: var(--faint);
  font-size: 17px; line-height: 1; cursor: pointer; padding: 0;
  transition: color .15s, background .15s;
}
.panel-close:hover { color: var(--text); background: rgba(255,255,255,.07); }
```

Three moves here. The place name splits at its first comma so `Cubatão` is the datum and
`, São Paulo, Brasil` is administrative annotation, which gives the header real hierarchy on one
line. The old `.loc-sub` run-on that welded mono coordinates to a prose clause with a `·` splits into
two lines with distinct typographic jobs: `.loc-geo` (data, mono) and `.loc-note` (annotation, prose).
And the close button loses its grey chip, drops to 26px, and its reserved gutter falls from 90px to
40px, which hands the place name 50px of width back.

**Delete** `.loc-sub`. After §10 all three panel states use `.loc-geo` for their second line and the
empty-list message uses `.sp-empty`, so nothing renders `.loc-sub` any more.

Because `.p-head` is sticky and `position: sticky` establishes a containing block, the close button
must live **inside** `.p-head` (see §10.1) so it pins with the header instead of scrolling away.

---

## 4. Section labels

```css
.section-h {
  font-size: 9.5px; font-weight: 500; text-transform: uppercase; letter-spacing: .145em;
  color: var(--faint); margin: var(--s6) 0 var(--s3);
}
```

Was 11px/600/1px in `--muted`. Uppercase micro-labels want generous tracking and low weight; at 600
they were competing with the content they label.

---

## 5. Climate figure and the site readout

```css
.site-fig { margin: 0 -16px; }        /* the hero gets 32px more drawing width than the text column */
.site-fig svg { display: block; width: 100%; height: auto; }

/* Site facts as a two-column table: fills top-to-bottom, so the DOM order stays
   the logical reading order and no label/value pair can ever be split by a wrap. */
.readout {
  margin: var(--s5) 0 0;
  display: grid; grid-template-rows: repeat(4, auto);
  grid-auto-flow: column; grid-auto-columns: 1fr; column-gap: 26px;
}
.readout .rd {
  display: flex; justify-content: space-between; align-items: baseline; gap: 10px;
  font-size: 11px; color: var(--faint); padding: 4.5px 0; border-top: 1px solid var(--line);
}
.readout .rd:nth-child(1), .readout .rd:nth-child(5) { border-top: 0; }
.readout b {
  font-family: var(--mono); font-size: 10.5px; font-weight: 400; color: var(--text);
  font-variant-numeric: tabular-nums; white-space: nowrap;
}
```

The old readout was a wrapping run-on that orphaned separators and split pairs across lines
(`· mínima` / `recorde 8 °C` is visible in the live app right now). A ruled two-up table cannot wrap,
aligns all eight values, and reads as instrument panel rather than paragraph. The `nth-child(1)`/`(5)`
rule assumes exactly 8 rows, which `renderResults` always emits (every value has an `n/d` fallback).

---

## 6. Criteria row: finish only, structure unchanged

Replace these rules; every selector, state and behaviour from `SPEC.md` stays.

```css
.sec-row { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin: var(--s7) 0 var(--s3); }
.sec-row .section-h { margin: 0; }

.crit-toggle {
  flex: 0 0 auto; font: inherit; font-size: 10.5px; color: var(--faint);
  background: none; border: 0; padding: 0; cursor: pointer; white-space: nowrap;
}
.crit-toggle b {
  font-family: var(--mono); font-size: 10.5px; font-weight: 400;
  color: var(--muted); font-variant-numeric: tabular-nums;
}
.crit-toggle.active b { color: var(--accent); }
.crit-toggle:hover { color: var(--muted); }
/* a chevron reads finer than a filled triangle at this size */
.crit-toggle .car {
  display: inline-block; width: 4.5px; height: 4.5px; margin-left: 7px; vertical-align: 2px;
  border-right: 1px solid currentColor; border-bottom: 1px solid currentColor;
  transform: rotate(45deg); opacity: .6; transition: transform .18s ease;
}
.crit-toggle[aria-expanded="true"] .car { transform: rotate(-135deg); }

.crit-summary {
  display: block; width: 100%; text-align: left; font: inherit; font-size: 11px; line-height: 1.7;
  color: var(--faint); background: none; border: 0; padding: 0; margin: -6px 0 var(--s3); cursor: pointer;
}
.crit-summary b { font-weight: 400; color: var(--muted); }
.crit-summary .d { color: rgba(255,255,255,.15); margin: 0 .4em; }
.crit-summary:hover b { color: var(--accent); }
.crit-summary[hidden] { display: none; }

/* No closing rule: the list's first hairline closes the block. Two rules 12px apart
   read as an accident. Criteria and species become one continuous ledger. */
.crit-panel { margin: 0 calc(var(--pad) * -1); padding: 0 var(--pad); }
.crit-panel[hidden] { display: none; }
.crit-row { display: flex; align-items: baseline; gap: 12px; padding: 9px 0; border-top: 1px solid var(--line); }
.crit-row .k {
  flex: 0 0 78px; font-size: 9.5px; text-transform: uppercase; letter-spacing: .11em;
  color: var(--faint); padding-top: 2px;
}
.crit-row .opts { display: flex; flex-wrap: wrap; align-items: baseline; column-gap: 15px; row-gap: 4px; margin: -3px 0; }
.opt { font: inherit; font-size: 11.5px; background: none; border: 0; padding: 3px 0; margin: 0; color: var(--muted); cursor: pointer; }
.opt:hover { color: var(--text); }
.opt.on { color: var(--text); }
.opt.on.constrained { color: var(--accent); }
.opt .c { font-family: var(--mono); font-size: 9px; color: var(--faint); margin-left: 5px; font-variant-numeric: tabular-nums; }
.opt.on .c { display: none; }
.opt[disabled] { opacity: .35; cursor: default; }
.crit-clear { display: block; margin: 10px 0 0 auto; font: inherit; font-size: 10px; color: var(--faint); background: none; border: 0; padding: 0; cursor: pointer; }
.crit-clear:hover { color: var(--text); }
```

**Delete** `.crit-row:last-of-type { border-bottom: ... }`.

---

## 7. Species list: a ledger, not a stack of boxes

**Delete** the box entirely:

```css
/* DELETE */
.sp { border: 1px solid var(--line); border-radius: 12px; margin-bottom: 8px; background: var(--glass-soft); overflow: hidden; }
/* DELETE (dead: nothing renders class="track" any more) */
.track { ... }  .track .fill { ... }  .factor .track { ... }
```

**Replace with:**

```css
#sp-list { margin: 0 calc(var(--pad) * -1); }   /* hairlines bleed to the panel edge */
.sp { border-top: 1px solid var(--line); }
.sp:last-child { border-bottom: 1px solid var(--line); }
.sp-head {
  display: flex; align-items: center; gap: 13px;
  padding: 10px var(--pad); min-height: 62px; cursor: pointer; user-select: none;
  transition: background .13s;
}
.sp-head:hover { background: rgba(255,255,255,.028); }
.sp.open { background: rgba(255,255,255,.022); }
.sp-rank {
  font-family: var(--mono); font-size: 10px; color: var(--faint);
  width: 15px; text-align: right; flex-shrink: 0; font-variant-numeric: tabular-nums;
}
.sp-thumb {
  width: 42px; height: 42px; border-radius: 11px; flex-shrink: 0;
  background-color: rgba(255,255,255,.045); background-size: cover; background-position: center;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.09);
}
.sp-names { flex: 1; min-width: 0; }
.sp-common { font-size: 13.5px; font-weight: 500; letter-spacing: -.004em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sp-sci { font-size: 11px; font-style: italic; color: var(--faint); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 1px; }
.nearby { font-size: 9.5px; font-weight: 500; letter-spacing: .02em; margin-left: 5px; color: var(--accent); }
.nearby.gbif { color: var(--faint); font-weight: 400; }
.sp-score { display: flex; flex-direction: column; align-items: flex-end; gap: 3px; flex-shrink: 0; }
.sp-score .pct {
  font-family: var(--mono); font-size: 13px; font-weight: 400;
  font-variant-numeric: tabular-nums; letter-spacing: -.01em;
}
.sp-score .pct .u { font-size: .68em; opacity: .5; margin-left: .5px; }
.sp-score .fit { font-family: var(--mono); font-size: 9.5px; color: var(--faint); font-variant-numeric: tabular-nums; }
.sp-empty { padding: 18px var(--pad); font-size: 11.5px; color: var(--muted); }
```

Five moves. The rounded bordered card per row was boxes-inside-a-box; hairlines separate just as well
with a fraction of the ink, and let the rows sit flush so the list gains density without gaining
noise. The score stops being 13px/600 sans (two competing 600s at the same size as the name) and
becomes 13px/400 mono with tabular figures, so the whole column aligns down the list; the `%` glyph
drops to `.68em` at half opacity. This matters more than it sounds: at a tropical site the top dozen
species all score 100, and the old treatment produced a wall of bold saturated green carrying no
information. The two badges get two colours: `nativa` is a flora claim and stays accent, `na região`
is weaker GBIF evidence and goes `--faint`. And the thumb grows 38→42px with an inset hairline ring so
the photograph has an edge instead of bleeding into the dark.

---

## 8. Expanded card as one composition

**Delete** the pill tags:

```css
/* DELETE */
.sp-tags { display: flex; flex-wrap: wrap; gap: 5px; margin: 10px 0 4px; }
.tag { font-size: 11px; padding: 3px 8px; border-radius: 999px; background: rgba(255,255,255,.06); color: var(--muted); }
.tag.good { background: var(--accent-dim); color: var(--accent); }
```

**Replace with:**

```css
.sp-body { padding: 0 var(--pad) var(--s5); }   /* note: no border-top any more */
.sp-body[hidden] { display: none; }

/* the photo bleeds to the panel edge: specimen plate, single focus of the card */
.sp-photo {
  width: calc(100% + var(--pad) * 2); margin: 0 calc(var(--pad) * -1); height: 176px;
  background-color: rgba(255,255,255,.04); background-size: cover; background-position: center;
  box-shadow: inset 0 1px 0 rgba(0,0,0,.45), inset 0 -1px 0 rgba(0,0,0,.45);
}
/* two deliberate lines: verdict, then uses. Never an accidental wrap. */
.sp-meta { margin: var(--s4) 0 0; font-size: 11.5px; color: var(--muted); }
.sp-meta .grade { color: var(--accent); }
.sp-meta .sep { color: rgba(255,255,255,.16); margin: 0 .45em; }
.sp-uses { margin: 4px 0 0; font-size: 11px; line-height: 1.65; color: var(--faint); }
.sp-uses .it { display: inline-block; white-space: nowrap; margin-right: 13px; }

/* envelope strips: label | strip | value on ONE line */
.factors { margin: var(--s5) 0 0; }
.factor { display: grid; grid-template-columns: 74px 1fr 60px; align-items: center; gap: 11px; padding: 5px 0; }
.factor .fk { font-size: 11px; color: var(--muted); }
.factor .fx { font-family: var(--mono); font-size: 10.5px; color: var(--text); text-align: right; font-variant-numeric: tabular-nums; }
.rtrack { position: relative; height: 4px; border-radius: 2px; background: rgba(255,255,255,.035); }
.rabs { position: absolute; top: 0; height: 100%; border-radius: 2px; background: rgba(99,201,135,.17); }
.ropt { position: absolute; top: 0; height: 100%; border-radius: 2px; background: rgba(99,201,135,.40); }
/* a caliper mark, not a slider handle: dark halo so it reads over the band */
.rtick {
  position: absolute; top: -4px; width: 1.5px; height: 12px; border-radius: 1px;
  background: var(--text); box-shadow: 0 0 0 2.5px rgba(13,17,14,.7);
}
.rtick.out { background: var(--warn); }
.evidence { font-size: 10.5px; color: var(--faint); margin-top: var(--s3); line-height: 1.6; }
.evidence a { color: var(--accent); text-decoration: none; }

.growth-fig { margin: var(--s5) 0 0; }
.growth-fig svg { display: block; width: 100%; height: auto; }
.fig-cap { font-size: 10.5px; color: var(--faint); margin-top: var(--s2); line-height: 1.55; }

.stats { margin: var(--s5) 0 0; }
.stat { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; font-size: 11.5px; padding: 5.5px 0; }
.stat .sk { color: var(--muted); white-space: nowrap; }
.stat .sv { font-family: var(--mono); font-size: 11px; color: var(--text); font-variant-numeric: tabular-nums; }
.stat.wide { margin-top: var(--s2); padding-top: var(--s3); border-top: 1px solid var(--line); font-size: 12.5px; }
.stat.wide .sv { font-size: 12px; }
```

The pills went because a wrapping soup of six rounded chips is the single most dashboard-looking
element in the panel; the same content set as two quiet lines of text costs a third of the height and
reads as a caption. The strips were the other big offender: `label` above, then a 6px track with a
bright green fill spanning most of its width, which reads as a progress bar at 84%. Folding them to
`label | strip | value` on one line halves their height, aligns three rows into a small matrix, and
the caliper tick plus a 4px track kills the progress-bar reading. Note that `.rabs` legitimately
spans the full track whenever the site value falls inside the tolerated range; it only shortens when
the site is outside the envelope, which is exactly when that shortening carries information.

---

## 9. Buttons and footnote

```css
/* "mostrar mais" continues the ledger instead of being a pill */
.chip.more {
  display: block; width: calc(100% + var(--pad) * 2); margin: 0 calc(var(--pad) * -1);
  padding: 14px 0; text-align: center; font: inherit; font-size: 11px; color: var(--muted);
  background: none; border: 0; border-bottom: 1px solid var(--line); cursor: pointer;
  transition: color .13s, background .13s;
}
.chip.more:hover { color: var(--text); background: rgba(255,255,255,.028); }
/* the bare .chip stays a pill: it is only used for "Mostrar mesmo assim" and "Tentar de novo" */
.chip {
  font: inherit; font-size: 11px; padding: 6px 11px; border-radius: 999px;
  background: rgba(255,255,255,.05); border: 1px solid var(--line); color: var(--muted); cursor: pointer;
}
.chip:hover { color: var(--text); border-color: rgba(255,255,255,.2); }

.footnote {
  margin-top: var(--s6); padding-top: var(--s4); border-top: 1px solid var(--line);
  font-size: 10.5px; line-height: 1.8; color: var(--faint);
}
.footnote a { color: var(--faint); text-decoration: underline; text-decoration-color: rgba(255,255,255,.18); text-underline-offset: 2px; }
.footnote a:hover { color: var(--muted); }
```

**Delete** `.chip.on` (no longer rendered) and the old `.chip.more { display:block; margin: 10px auto 0; }`.

---

## 10. `app.js` diffs

### 10.1 `openPanel` (app.js:412): stop appending the close button

```js
function openPanel(html) {
  content.innerHTML = html;
  panel.hidden = false;
}
```

Each caller now owns its `.p-head` (with the close button inside it) and `.p-body`.

### 10.2 loading state (app.js:355): wrap in the two zones

```js
  openPanel(`
    <div class="p-head">
      <div class="loc-title">${tr("Analyzing area")}</div>
      <div class="loc-geo">${c.lat.toFixed(4)}, ${c.lng.toFixed(4)}<span class="sep">&middot;</span>${fmtHa(ha)}</div>
      <button class="panel-close" data-close title="${tr("Close")}">&times;</button>
    </div>
    <div class="p-body">
      <div class="loading">
        <div class="load-step active" id="ls-climate"><span class="dot"></span>${tr("Climate normals &middot; Open-Meteo ERA5, 10 years daily")}</div>
        <div class="load-step" id="ls-soil"><span class="dot"></span>${tr("Soil profile &middot; SoilGrids 2.0")}</div>
        <div class="load-step" id="ls-score"><span class="dot"></span>${tfmt("Scoring {n} species", { n: fmt(SPECIES.length || 1021) })}</div>
      </div>
      <div class="skel">
        <div class="skel-fig"></div>
        <div class="skel-row"></div><div class="skel-row"></div><div class="skel-row"></div>
      </div>
    </div>`);
```

`.loading` needs `padding-top: var(--s5)` added to its existing rule, since `.p-body` no longer has
top padding:

```css
.loading { display: flex; flex-direction: column; gap: 10px; padding: var(--s5) 0 8px; }
```

### 10.3 error state (app.js:381)

```js
    content.innerHTML = `
      <div class="p-head">
        <div class="loc-title">${tr("Analysis failed")}</div>
        <div class="loc-geo">${c.lat.toFixed(4)}, ${c.lng.toFixed(4)}</div>
        <button class="panel-close" data-close title="${tr("Close")}">&times;</button>
      </div>
      <div class="p-body">
        <div class="error-box" style="margin-top:var(--s5)">${tr("Could not load the climate record for this point. The Open-Meteo archive may be busy or rate limited; wait a moment and retry.")}<span class="mono">${e.message}</span></div>
        <div class="retry-row"><button id="retry" class="chip">${tr("Retry")}</button></div>
      </div>`;
```

### 10.4 `renderResults` (app.js:509)

Add above `openPanel(`:

```js
  // the place name is the datum; the administrative tail is annotation
  const place = site.place ?? tr("Selected area");
  const [head, tail] = place.split(/,(.+)/s);
  const titleHtml = tail ? `${head}<span class="adm">,${tail}</span>` : head;
  const rd = (k, v, title) =>
    `<div class="rd"${title ? ` title="${title}"` : ""}><span>${k}</span><b>${v}</b></div>`;
```

Replace the header + readout block (app.js:520-531) with:

```js
    <div class="p-head">
      <div class="loc-title">${titleHtml}</div>
      <div class="loc-geo">${current.center.lat.toFixed(4)}, ${current.center.lng.toFixed(4)}<span class="sep">&middot;</span>${fmtHa(ha)}</div>
      ${noLand ? "" : `<div class="loc-note">${tfmt("{s} of {n} species rate suitable or better",
        { s: `<b>${fmt(suitable)}</b>`, n: `<b>${fmt(SPECIES.length)}</b>` })}</div>`}
      <button class="panel-close" data-close title="${tr("Close")}">&times;</button>
    </div>
    <div class="p-body">
    <div class="section-h">${tr("Site climate &middot; ERA5 2015&ndash;2024")}</div>
    <div class="site-fig">${climateSvg(site)}</div>
    <div class="readout">
      ${rd(tr("soil pH"), site.ph != null ? fmt(site.ph, 1) : tr("no data"))}
      ${rd(tr("elevation"), `${fmt(site.elevation)} m`)}
      ${rd(tr("daylength"), `${fmt(Math.min(...dls), 1)}&ndash;${fmt(Math.max(...dls), 1)} h`)}
      ${rd(tr("record low"), site.absMin != null ? `${fmt(site.absMin)} °C` : tr("n/a"))}
      ${rd(tr("sun"), site.rad != null ? `${fmt(site.rad, 1)} ${tr("kWh/m²·day")}` : tr("n/a"), tr("mean daily shortwave radiation, all weather included"))}
      ${rd(tr("humidity"), site.rh != null ? `${fmt(site.rh)}%` : tr("n/a"))}
      ${rd(tr("cloud"), site.cloud != null ? `${fmt(site.cloud)}%` : tr("n/a"), tr("high humidity plus high cloud cover marks fog-prone sites"))}
      ${rd(tr("slope"), site.terrain ? `${fmt(site.terrain.slope)}°${site.terrain.facing ? ` ${tr("facing")} ` + tr(site.terrain.facing) : ""}` : tr("n/a"))}
    </div>
```

Three notes. The suitability sentence moves out of `.loc-sub` into `.loc-note` with its two numerals
wrapped in `<b>` so they set in mono. `toFixed` gives way to `fmt` throughout, because the readout was
printing `4.9` with a period while the strip two sections down printed `4,9` with a comma in the same
pt-BR panel. And the `title` tooltips move from the `<b>` to the whole `.rd` row, so the hover target
is the label as well as the value.

Then the empty-list fallback (app.js:534) needs its own padded class, since `#sp-list` is now
negative-margined and a `.loc-sub` there would sit flush against the panel edge:

```js
    <div id="sp-list">${rows.map((s, i) => speciesRow(s, i)).join("") || `<div class="sp-empty">${tr("Nothing clears the bar for this filter here.")}</div>`}</div>
```

Finally, close `.p-body` and add the fade as the last node of the template, after `</div>` of the
footnote:

```js
    </div>
    </div>
    <div class="panel-fade"></div>`);
```

(That is: `</div>` closing `.footnote`, `</div>` closing `.p-body`, then `.panel-fade` as a sibling
of `.p-body` inside `#panel-content`. It must be outside `.p-body` so its sticky containing block runs
the full content height.)

### 10.5 `speciesRow` (app.js:548)

Two markup changes: the `%` gets its own span, and the GBIF badge gets `.gbif`.

```js
      <div class="sp-score">
        <span class="pct" style="color:${col}">${pct}<span class="u">%</span></span>
        <span class="fit">${tr("fit")} ${Math.round(s.fit * 100)}</span>
      </div>
```

```js
          <span class="nearby gbif" data-nearby="${s.sp.id}" ${s.gbif?.count > 0 ? "" : "hidden"} title="${tr("GBIF occurrence records near this area")}">&#10003; ${tr("nearby")}</span>
```

### 10.6 open/closed class (app.js:597, inside the `[data-toggle]` branch)

Add one line after `body.hidden = !body.hidden;` so `.sp.open` works without relying on `:has()`:

```js
    head.parentElement.classList.toggle("open", !body.hidden);
```

### 10.7 `speciesDetail` (app.js:696): tags become two lines

```js
    <div class="sp-photo" data-hero="${sp.id}" hidden></div>
    <div class="sp-meta"><span class="grade">${tr(grade(s.score))}</span><span class="sep">&middot;</span>${tfmt("{rate} growth &middot; {zone}", { rate: tr(rate), zone: tr(zone) })}</div>
    <div class="sp-uses">${sp.uses.map(u => `<span class="it">${tr(USE_LABELS[u] ?? u)}</span>`).join("")}</div>
```

Line one cannot wrap at 420px so it keeps its middots. Line two can (up to eight uses), so it is
separated by space alone: the same lesson `SPEC.md` recorded for the criteria options, where a wrap
orphaned a `·`.

### 10.8 `rangeStrip` (app.js:610): label, strip and value on one line

```js
  return `<div class="factor">
    <div class="fk">${label}</div>
    <div class="rtrack" title="${tfmt("tolerated {a} to {d} · optimal {b} to {c}", { a: f(a), b: f(b), c: f(c), d: f(d) })}${unit}">
      <div class="rabs" style="left:${P(a)}%;width:${(((d - a) / span) * 100).toFixed(2)}%"></div>
      <div class="ropt" style="left:${P(b)}%;width:${(((c - b) / span) * 100).toFixed(2)}%"></div>
      <div class="rtick${out ? " out" : ""}" style="left:${P(val)}%"></div>
    </div>
    <div class="fx">${f(val)}${unit}</div></div>`;
```

Only the element order and wrappers change; every computed value is untouched.

### 10.9 `climateSvg` (app.js:637): replace the whole function

One figure, one month axis. Temperature above the spine, month letters on the spine, rain hanging
below it. The sub-zero reference line is preserved for temperate sites.

```js
// One figure, one month axis: temperature above the spine, rain hanging below.
// The spine spans the data, not the container; 4px teeth mark each month for both series.
function climateSvg(site) {
  const W = 414, L = 2, R = 64, top = 16, tH = 50, gapA = 9, letters = 13, gapB = 7, pH = 56, bot = 15;
  const spineY = top + tH + gapA;
  const barTop = spineY + letters + gapB;
  const H = barTop + pH + bot;
  const iw = W - L - R;
  const cx = m => L + (m + 0.5) * iw / 12;
  // narrow bar: at 21px the driest month rendered as a horizontal dash, not a bar
  const bw = Math.max(8, Math.round(iw / 12) - 15);
  const tmid = (Math.max(...site.tavg) + Math.min(...site.tavg)) / 2;
  // floor of 11 °C, not 14: at an equatorial site the curve used half the band and looked inert.
  // The extremes stay labelled, so the scale is readable even though it varies by place.
  const tspan = Math.max(11, Math.max(...site.tavg) - Math.min(...site.tavg) + 4);
  const thi = tmid + tspan / 2, tlo = tmid - tspan / 2;
  const ty = v => top + (thi - v) / (thi - tlo) * tH;
  const pmax = Math.max(...site.prec, 10) * 1.1;
  const py = v => (v / pmax) * pH;
  const warm = site.tavg.indexOf(Math.max(...site.tavg));
  const cold = site.tavg.indexOf(Math.min(...site.tavg));
  const wet = site.prec.indexOf(Math.max(...site.prec));
  const MONO = "IBM Plex Mono, monospace";
  // dark knockout behind in-plot numerals: a label can land exactly on a rule
  const KO = `paint-order="stroke" stroke="rgba(13,17,14,.9)" stroke-width="2.6" stroke-linejoin="round"`;
  const line = site.tavg.map((v, m) => `${m ? "L" : "M"}${cx(m).toFixed(1)},${ty(v).toFixed(1)}`).join("");
  const bars = site.prec.map((v, m) =>
    `<rect x="${(cx(m) - bw / 2).toFixed(1)}" y="${barTop}" width="${bw}" height="${py(v).toFixed(1)}" rx="1.5" fill="#79a6c6" opacity="${m === wet ? .95 : .52}"/>`).join("");
  const teeth = site.tavg.map((_, m) =>
    `<line x1="${cx(m).toFixed(1)}" x2="${cx(m).toFixed(1)}" y1="${spineY - 4}" y2="${spineY}" stroke="rgba(255,255,255,.13)"/>`).join("");
  const months = "JFMAMJJASOND".split("").map((ch, m) =>
    `<text x="${cx(m).toFixed(1)}" y="${spineY + 10}" font-size="8" fill="#6b786f" text-anchor="middle" letter-spacing=".4">${ch}</text>`).join("");
  const hover = site.tavg.map((v, m) =>
    `<rect x="${(cx(m) - iw / 24).toFixed(1)}" y="0" width="${(iw / 12).toFixed(1)}" height="${H}" fill="transparent"><title>${MONTHS[m]} &middot; ${fmt(v, 1)} °C &middot; ${fmt(site.prec[m])} mm</title></rect>`).join("");
  const zeroLabel = Math.abs(ty(0) - ty(site.meanTemp)) < 12 ? "" :
    `<text x="${L + iw + 11}" y="${(ty(0) + 3).toFixed(1)}" font-size="8.5" fill="#6b786f">0 °C</text>`;
  const zero = tlo < 0 && thi > 0
    ? `<line x1="${L}" x2="${L + iw}" y1="${ty(0).toFixed(1)}" y2="${ty(0).toFixed(1)}" stroke="rgba(255,255,255,.12)" stroke-dasharray="3 3"/>${zeroLabel}` : "";
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="monthly temperature and precipitation">
    ${zero}
    <line x1="${L}" x2="${L + iw}" y1="${ty(site.meanTemp).toFixed(1)}" y2="${ty(site.meanTemp).toFixed(1)}" stroke="#d7a463" stroke-opacity=".26" stroke-dasharray="2 3"/>
    <path d="${line}" fill="none" stroke="#d7a463" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${cx(warm)}" cy="${ty(site.tavg[warm]).toFixed(1)}" r="2" fill="#d7a463"/>
    <text x="${cx(warm).toFixed(1)}" y="${(ty(site.tavg[warm]) - 7).toFixed(1)}" font-size="9" font-family="${MONO}" fill="#99a69c" text-anchor="middle" ${KO}>${fmt(site.tavg[warm])}°</text>
    <circle cx="${cx(cold)}" cy="${ty(site.tavg[cold]).toFixed(1)}" r="2" fill="#d7a463"/>
    <text x="${cx(cold).toFixed(1)}" y="${(ty(site.tavg[cold]) + 12).toFixed(1)}" font-size="9" font-family="${MONO}" fill="#99a69c" text-anchor="middle" ${KO}>${fmt(site.tavg[cold])}°</text>
    <text x="${L + iw + 11}" y="${(ty(site.meanTemp) + 1).toFixed(1)}" font-size="10.5" font-family="${MONO}" fill="#d7a463">${fmt(site.meanTemp, 1)} °C</text>
    <text x="${L + iw + 11}" y="${(ty(site.meanTemp) + 12).toFixed(1)}" font-size="8.5" fill="#6b786f">${tr("mean")}</text>
    ${teeth}
    <line x1="${(cx(0) - 12).toFixed(1)}" x2="${(cx(11) + 12).toFixed(1)}" y1="${spineY}" y2="${spineY}" stroke="rgba(255,255,255,.2)"/>
    ${months}
    ${bars}
    <text x="${cx(wet).toFixed(1)}" y="${(barTop + py(site.prec[wet]) + 10).toFixed(1)}" font-size="9" font-family="${MONO}" fill="#99a69c" text-anchor="middle" ${KO}>${fmt(site.prec[wet])}</text>
    <text x="${L + iw + 11}" y="${barTop + 12}" font-size="10.5" font-family="${MONO}" fill="#79a6c6">${fmt(site.annualRain)} mm</text>
    <text x="${L + iw + 11}" y="${barTop + 23}" font-size="8.5" fill="#6b786f">${tr("per year")}</text>
    ${hover}
  </svg>`;
}
```

Colours are literal here rather than `var(--amber)` etc. because these strings are also what the
existing code does, and it keeps the SVG independent of custom-property inheritance quirks.

If the owner dislikes rain hanging from the axis, it becomes a bars-grow-up figure by changing two
lines: `const py = v => (v / pmax) * pH;` stays, and in `bars` swap
`y="${barTop}" height="${py(v)}"` for `y="${(barTop + pH - py(v)).toFixed(1)}" height="${py(v).toFixed(1)}"`,
then move the wet-month label above the bar. Everything else holds.

### 10.10 `growthSvg` (app.js:730): replace the whole function

```js
// Height growth. The 40 m ceiling is shared across species so they compare
// honestly, which is why a short species leaves the upper half empty on purpose.
function growthSvg(sp) {
  const pts = projection(sp, 40);
  const W = 376, H = 116, L = 26, R = 4, T = 9, B = 16, ymax = 40;
  const x = t => L + (t / 40) * (W - L - R);
  const y = h => T + (1 - h / ymax) * (H - T - B);
  const MONO = "IBM Plex Mono, monospace";
  const KO = `paint-order="stroke" stroke="rgba(13,17,14,.9)" stroke-width="2.6" stroke-linejoin="round"`;
  const path = pts.map((p, i) => `${i ? "L" : "M"}${x(p.t).toFixed(1)},${y(p.h).toFixed(1)}`).join("");
  const yrules = [20, 40].map(v =>
    `<line x1="${L}" y1="${y(v).toFixed(1)}" x2="${W - R}" y2="${y(v).toFixed(1)}" stroke="rgba(255,255,255,.055)"/>
     <text x="${L - 5}" y="${(y(v) + 3).toFixed(1)}" fill="#6b786f" font-size="8.5" font-family="${MONO}" text-anchor="end">${v}m</text>`).join("");
  const xlab = [10, 20, 30, 40].map(t =>
    `<text x="${x(t).toFixed(1)}" y="${H - 4}" fill="#6b786f" font-size="8.5" font-family="${MONO}" text-anchor="${t === 40 ? "end" : "middle"}">${t}${tr("y")}</text>`).join("");
  const marks = [10, 20].map(t =>
    `<circle cx="${x(t).toFixed(1)}" cy="${y(pts[t].h).toFixed(1)}" r="2.2" fill="#63c987"/>
     <text x="${x(t).toFixed(1)}" y="${(y(pts[t].h) - 7).toFixed(1)}" fill="#e8ede8" font-size="9" font-family="${MONO}" text-anchor="middle" ${KO}>${pts[t].h.toFixed(0)}m</text>`).join("");
  const hover = [5, 10, 15, 20, 25, 30, 35, 40].map(t =>
    `<circle cx="${x(t).toFixed(1)}" cy="${y(pts[t].h).toFixed(1)}" r="10" fill="transparent"><title>${t} ${tr("yr")} &middot; ${fmt(pts[t].h, 1)} m &middot; ${tr("trunk")} ${fmt(pts[t].d)} cm &middot; ${fmt(pts[t].co2)} kg CO&#8322;e</title></circle>`).join("");
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="height growth curve">
    ${yrules}
    <line x1="${L}" y1="${y(0)}" x2="${W - R}" y2="${y(0)}" stroke="rgba(255,255,255,.09)"/>
    <path d="${path}" fill="none" stroke="#63c987" stroke-width="1.7" stroke-linecap="round"/>
    ${marks}${xlab}${hover}</svg>`;
}
```

The four vertical grid lines are gone: they were the densest ink in the figure and the x labels
already locate the decades. The unused `const cls = CLASSES[sp.gclass]` goes with them. A baseline at
0 m is added, because the curve previously floated with nothing to stand on. The 20 m rule and the
`14m` mark label collide at exactly 20 years for medium-growth tropical species, which is what `KO`
fixes.

---

## 11. New PT keys

```js
  "Close": "Fechar",
  "Selected area": "Área selecionada",
  "fit": "ajuste",
```

All three fix genuine gaps rather than new copy: `"Selected area"` and the `fit` label are hardcoded
English in the live pt-BR panel today, and the close button had no accessible label at all.

Every other label in the redesigned panel reuses an existing key.

---

## 12. Optional, flagged separately

**`scoring.js` `gradeColor` (scoring.js:157).** The five stops are the last saturated holdout; the
score column inherits them, so they fight the new low-chroma palette. Same hues, lower chroma:

```js
  if (s > 0.8) return "#63c987";
  if (s > 0.6) return "#a9cd72";
  if (s > 0.4) return "#d9c46a";
  if (s > 0.2) return "#d79a63";
  return "#d4756f";
```

**`slope` in the readout.** `12° face L` currently sets entirely in mono because the whole value is
inside `<b>`. Splitting it (`<b>12°</b> face L`) would be more correct typographically. Left out of
the main spec because it needs a second markup shape in `rd()`.

---

## 13. Why IBM Plex stays

Plex was cut by Bold Monday for IBM as a technical corporate face, and three of its properties are
load-bearing here. Its low stroke contrast and large x-height survive 9.5 to 11px on a dark ground,
which is most of this panel. Plex Mono shares the design DNA and vertical proportions of Plex Sans, so
a mono numeral can sit on the same baseline as sans text in the same line (`pH do solo 4.9`,
`31 de 374`) without a visible jump; pairing an unrelated mono is exactly where data readouts start
looking assembled rather than designed. And Plex Sans ships a true italic, not an oblique, which the
panel needs constantly for binomial names.

What changed is not the family but how it is used: weight 600 drops to 500 at every size above 12px,
tracking goes negative on the 21px title and up to `.145em` on the uppercase micro-labels, and every
numeral that sits in a column gets `font-variant-numeric: tabular-nums`. The old panel set almost
everything at 600 and let proportional figures ragged-align down the score column, which is the
mechanical reason it read as heavy and slightly cheap.

---

## 14. One separator rule, panel-wide

Middots appear only in lines that cannot wrap: the coordinate line, the section subtitle, the card's
verdict line, the footnote. Every sequence that can wrap (site readout, criteria options, uses) is
separated by space alone. `SPEC.md` learned this the hard way when a wrap orphaned a `·` in the
criteria options; the same failure was live in the readout, and this makes it a rule rather than a
patch.
