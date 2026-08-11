// Crown renderer — candidate implementation for app.js drawTree().
//
// Calibrated against the same Esri World Imagery the app uses as its basemap,
// sampled over Atlantic forest at Cubatao (z18/z19):
//   HSL lightness p10 4.6, p25 13.8, p50 23.2, p75 30.3, p90 34.6, p98 39
//   hue p50 123 deg, saturation p50 22%, 8x8 luminance sigma 11-14
//   sun from the NE: ground shadows fall SW (measured off tank/pole shadows)
//
// Technique: pre-rendered sprite atlas, one drawImage per tree.
//  - detail is sized in ground units, not screen pixels, so texture contrast
//    falls off with zoom the way a fixed-GSD sensor's does;
//  - above maxNativeZoom the basemap is an upscale, so sprites upscale too;
//  - each sprite is histogram-matched to the reference imagery, so the palette
//    is measured rather than hand-picked;
//  - crown edges are feathered, so neighbours interleave into one canopy
//    instead of stacking as legible discs.

const SPR_R = [3, 7, 16, 40];               // reference crown radius per tier, CSS px
const SPR_SIL = 6, SPR_TINT = 7, SPR_N = SPR_SIL * SPR_TINT;
const TUFT = 0.19;                          // foliage tuft radius / crown radius
const LX = 0.455, LY = -0.455, LZ = 0.766;  // sun from NE, ~50 deg elevation

// Reference quantiles, and how much of that range one crown spans on its own:
// the rest of the spread has to come from crown-to-crown tone, or the canopy
// ends up with the right histogram but far too much local contrast.
const TONE_Q = [0, 0.02, 0.10, 0.25, 0.50, 0.75, 0.90, 0.98, 1];
const TONE_L = [0, 1.6, 4.6, 13.8, 23.2, 30.3, 34.6, 39.0, 47];
const TONE_MID = 23.2, TONE_NARROW = 0.55, TONE_LIFT = 1.10;

let SPR = null, SPR_DPR = 0, SOFT = 1;

// Above the imagery's native zoom Leaflet upscales its tiles; match that blur by
// picking a smaller sprite and scaling it up rather than inventing detail.
function setCrownSoft(zoom, maxNative) {
  SOFT = Math.min(4, Math.pow(2, Math.max(0, zoom - maxNative + 0.5)));
}

function crownSet(tier, conifer) {
  const dpr = window.devicePixelRatio || 1;
  if (!SPR || SPR_DPR !== dpr) { SPR = [[], []]; SPR_DPR = dpr; }
  const bank = SPR[conifer ? 1 : 0];
  let set = bank[tier];
  if (!set) {
    set = bank[tier] = [];
    for (let i = 0; i < SPR_N; i++) set.push(buildCrown(tier, conifer, i, dpr));
  }
  return set;
}

function buildCrown(tier, conifer, variant, dpr) {
  const R0 = SPR_R[tier];
  const sil = variant % SPR_SIL, tint = (variant / SPR_SIL) | 0;
  const rf = 0.92 + sil * (0.16 / (SPR_SIL - 1));   // crowns vary in width, not only shape
  const R = R0 * rf, gr = Math.max(0.45, R * TUFT);
  const M = Math.max(2, R0 * 0.86);                 // room for lobes + the SW ground shadow
  const W = Math.ceil((R0 + M) * 2), cx = W / 2, cy = W / 2;
  const rng = mulberry32(1013904 + sil * 6151 + tier * 3331 + (conifer ? 7717 : 0));

  const hue0 = (conifer ? 126 : 122) + (rng() - 0.5) * 5;
  const sat0 = (conifer ? 19 : 16) + (rng() - 0.5) * 4;
  const deepL = conifer ? 3 : 4;                    // between-tuft gaps: near black
  const litL = conifer ? 40 : 44;

  // irregular silhouette: four octaves of angular noise, tighter for conifers
  const p1 = rng() * 6.283, p2 = rng() * 6.283, p3 = rng() * 6.283, p4 = rng() * 6.283;
  const lob = conifer ? 0.5 : 1;
  const rad = a => R * (1 + lob * (0.125 * Math.sin(3 * a + p1) + 0.088 * Math.sin(5 * a + p2)
    + 0.058 * Math.sin(8 * a + p3) + 0.038 * Math.sin(13 * a + p4)));

  // ---- crown body, drawn on its own so it can be feathered and calibrated ----
  const body = document.createElement("canvas");
  body.width = body.height = Math.round(W * dpr);
  const b = body.getContext("2d");
  b.scale(dpr, dpr);

  const path = new Path2D();
  const NSEG = tier < 2 ? 24 : 72;
  for (let i = 0; i <= NSEG; i++) {
    const a = i / NSEG * 6.28319, rr = rad(a);
    const px = cx + Math.cos(a) * rr, py = cy + Math.sin(a) * rr;
    i ? path.lineTo(px, py) : path.moveTo(px, py);
  }
  path.closePath();

  // sub-crown lobes: real crowns are several bright masses, not one smooth ball
  const NL = 4 + Math.floor(rng() * 5), lobes = [];
  for (let i = 0; i < NL; i++) {
    const a = rng() * 6.283, d = Math.sqrt(rng()) * R * 0.62;
    lobes.push([Math.cos(a) * d, Math.sin(a) * d, (rng() - 0.5) * 0.42, R * (0.30 + rng() * 0.30)]);
  }
  const shadeOf = (dx, dy, jit) => {
    const u = dx / R, v = dy / R;
    const w = Math.sqrt(Math.max(0.04, 1 - u * u - v * v));
    let s = 0;
    for (let j = 0; j < NL; j++) {
      const ex = dx - lobes[j][0], ey = dy - lobes[j][1], rr = lobes[j][3];
      const t = 1 - (ex * ex + ey * ey) / (rr * rr);
      if (t > 0) s += lobes[j][2] * t;
    }
    const nd = 0.18 + 0.50 * (u * LX + v * LY + w * LZ) + s + jit;
    return nd < 0 ? 0 : nd > 1 ? 1 : nd;
  };
  const tuftCol = nd => `hsl(${hue0 + (rng() - 0.5) * 10}, ${sat0 + (1 - nd) * 9}%, ` +
    `${deepL + (litL - deepL) * Math.pow(nd, 0.85)}%)`;

  b.save();
  b.clip(path);
  b.fillStyle = `hsl(${hue0 + 8}, ${sat0 + 7}%, ${deepL}%)`;
  b.fillRect(0, 0, W, W);

  // Foliage mounds over a dark base. No ring is drawn around each mound: the
  // crevices are simply where the base shows through, which comes out sinuous
  // and irregular like the real canopy instead of a field of round dimples.
  // Every mound is nudged up-sun, so the base peeks out on its shaded side.
  for (let oct = 0; oct < 2; oct++) {
    const fg = oct ? gr * 0.46 : gr, step = fg * (oct ? 1.5 : 1.04), pts = [];
    for (let py = -R * 1.1; py <= R * 1.1; py += step)
      for (let px = -R * 1.1; px <= R * 1.1; px += step) {
        const jx = px + (rng() - 0.5) * step * 1.05, jy = py + (rng() - 0.5) * step * 1.05;
        const d2 = jx * jx + jy * jy;
        if (oct && rng() < 0.5) continue;
        if (Math.sqrt(d2) > rad(Math.atan2(jy, jx)) * (1 + 0.26 * rng())) continue;
        pts.push([jx, jy, rng(), rng()]);
      }
    pts.sort((A, B) => (A[0] - A[1]) - (B[0] - B[1]));
    const amp = oct ? 0.10 : 0.20;   // mounds belong to a crown; keep them coherent
    for (let i = 0; i < pts.length; i++) {
      const dx = pts[i][0], dy = pts[i][1], q = pts[i][3];
      const nd = shadeOf(dx, dy, (pts[i][2] - 0.5) * amp);
      if (oct && nd < 0.42) continue;                  // fine highlights only on lit mounds
      const fr = fg * (q > 0.9 ? 1.5 + q : 0.62 + q * 0.85);
      b.fillStyle = tuftCol(oct ? Math.min(1, nd + 0.14) : nd);
      b.beginPath();
      b.arc(cx + dx + fr * 0.16, cy + dy - fr * 0.16, fr * (oct ? 0.7 : 1.0), 0, 6.28319);
      b.fill();
    }
  }

  if (conifer) { // whorled branch structure reads through from above
    b.strokeStyle = `hsla(${hue0}, ${sat0 + 6}%, 5%, 0.30)`;
    b.lineWidth = Math.max(0.6, R * 0.05);
    const spokes = 7 + Math.floor(rng() * 4);
    for (let i = 0; i < spokes; i++) {
      const a = rng() * 6.283 + i / spokes * 6.283;
      b.beginPath();
      b.moveTo(cx + Math.cos(a) * R * 0.10, cy + Math.sin(a) * R * 0.10);
      b.lineTo(cx + Math.cos(a) * R * 0.86, cy + Math.sin(a) * R * 0.86);
      b.stroke();
    }
  }
  b.restore();

  // spur tufts across the silhouette so the edge never reads as a clean disc
  for (let i = 0, n = tier < 2 ? 12 : 30; i < n; i++) {
    const a = rng() * 6.283, rr = rad(a) * (0.90 + rng() * 0.24);
    const dx = Math.cos(a) * rr, dy = Math.sin(a) * rr;
    const fr = gr * (0.55 + rng() * 0.5);
    b.fillStyle = tuftCol(shadeOf(dx, dy, (rng() - 0.5) * 0.4));
    b.beginPath(); b.arc(cx + dx, cy + dy, fr * 0.9, 0, 6.28319); b.fill();
  }

  calibrate(b, W, dpr, (conifer ? 0.86 : 1) * (0.45 + tint * (0.85 / (SPR_TINT - 1))));

  // Feather the outer edge. Crowns overlap heavily at real stand densities, and
  // a hard edge is what makes a stand read as a tray of separate balls.
  b.globalCompositeOperation = "destination-out";
  const fade = b.createRadialGradient(cx, cy, R * 0.88, cx, cy, R * 1.34);
  fade.addColorStop(0, "rgba(0,0,0,0)");
  fade.addColorStop(0.45, "rgba(0,0,0,0.20)");
  fade.addColorStop(0.75, "rgba(0,0,0,0.55)");
  fade.addColorStop(1, "rgba(0,0,0,0.95)");
  b.fillStyle = fade; b.fillRect(0, 0, W, W);
  b.globalCompositeOperation = "source-over";

  // ---- final sprite: ground shadow first, crown over it ----
  const c = document.createElement("canvas");
  c.width = c.height = Math.round(W * dpr);
  const g = c.getContext("2d");
  g.scale(dpr, dpr);
  const sh = g.createRadialGradient(cx - R * 0.30, cy + R * 0.34, R * 0.10,
                                    cx - R * 0.30, cy + R * 0.34, R * 1.05);
  sh.addColorStop(0, "rgba(6,15,9,0.50)");
  sh.addColorStop(0.55, "rgba(6,15,9,0.32)");
  sh.addColorStop(1, "rgba(6,15,9,0)");
  g.fillStyle = sh; g.fillRect(0, 0, W, W);
  g.drawImage(body, 0, 0, W, W);
  return { c, w: W, cx, cy };
}

// Histogram-match the crown body to the reference imagery instead of hand-tuning
// constants. `scale` is the tint bank's exposure, so tone patches survive it.
function calibrate(g, W, dpr, scale) {
  const px = Math.round(W * dpr);
  const img = g.getImageData(0, 0, px, px), d = img.data, n = px * px;
  const lum = new Float32Array(n), ls = [];
  for (let i = 0; i < n; i++) {
    const r = d[i * 4], gg = d[i * 4 + 1], bb = d[i * 4 + 2];
    const l = (Math.max(r, gg, bb) + Math.min(r, gg, bb)) / 5.1;   // HSL L, 0..100
    lum[i] = l;
    if (d[i * 4 + 3] > 200) ls.push(l);
  }
  if (ls.length < 24) return;
  ls.sort((a, b) => a - b);
  const src = TONE_Q.map(q => ls[Math.round(q * (ls.length - 1))]);
  const dst = TONE_L.map(l => Math.min(58, (TONE_MID + (l - TONE_MID) * TONE_NARROW) * scale * TONE_LIFT));
  for (let i = 0; i < n; i++) {
    if (d[i * 4 + 3] === 0) continue;
    const l = lum[i];
    let k = 1;
    while (k < src.length - 1 && l > src[k]) k++;
    const s0 = src[k - 1], s1 = src[k];
    const nl = dst[k - 1] + (dst[k] - dst[k - 1]) * (s1 > s0 ? (l - s0) / (s1 - s0) : 0);
    if (l <= 0.4) continue;
    const f = Math.min(5, Math.max(0.12, nl / l));
    d[i * 4] = Math.min(255, d[i * 4] * f);
    d[i * 4 + 1] = Math.min(255, d[i * 4 + 1] * f);
    d[i * 4 + 2] = Math.min(255, d[i * 4 + 2] * f);
  }
  g.putImageData(img, 0, 0);
}

// Canopy tone patches: neighbouring trees share a tint, so a stand breaks into
// lighter and darker masses instead of reading as one uniform lattice.
function hash2(x, y) {
  let n = Math.imul(x | 0, 374761393) ^ Math.imul(y | 0, 668265263);
  n = Math.imul(n ^ n >>> 13, 1274126177);
  return ((n ^ n >>> 16) >>> 0) / 4294967296;
}
function vnoise(X, Y) {
  const x0 = Math.floor(X), y0 = Math.floor(Y), fx = X - x0, fy = Y - y0;
  const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
  const a = hash2(x0, y0), b = hash2(x0 + 1, y0), c = hash2(x0, y0 + 1), d = hash2(x0 + 1, y0 + 1);
  const t = a + (b - a) * sx;
  return t + ((c + (d - c) * sx) - t) * sy;
}
function toneOf(tree) {
  if (tree.tn === undefined) {
    const X = tree.ln * 3400, Y = tree.la * 3400;       // ~30 m cells, plus a ~95 m octave
    let n = 0.52 * vnoise(X, Y) + 0.48 * vnoise(X / 3.1, Y / 3.1);
    n = (n - 0.5) * 2.2 + 0.5;
    tree.tn = n < 0 ? 0 : n > 0.999 ? 0.999 : n;
  }
  return tree.tn;
}

// sub-pixel trees: one rect, lightness drawn from the real canopy histogram
const SUBPX = [];
for (let i = 0; i < 16; i++)
  SUBPX.push(`hsl(${119 + (i * 7) % 11}, ${16 + (i * 5) % 9}%, ${5.5 + i * 2.3}%)`);

function drawTree(g, x, y, r, tree, conifer) {
  if (r < 1.4) { // sub-pixel: a single rect, but never a uniform one
    g.fillStyle = SUBPX[tree.seed & 15];
    const w = r * 2 + 0.4;
    g.fillRect(x - w / 2, y - w / 2, w, w);
    return;
  }
  const e = r / SOFT;
  const tier = e < 6.5 ? 0 : e < 15 ? 1 : e < 35 ? 2 : 3;
  const set = crownSet(tier, conifer);
  let ti = toneOf(tree) * SPR_TINT + ((tree.seed >>> 11 & 3) - 1.5) * 0.6;
  ti = ti < 0 ? 0 : ti > SPR_TINT - 1 ? SPR_TINT - 1 : ti;
  const sp = set[((tree.seed >>> 3) % SPR_SIL) * SPR_TINT + (ti | 0)];
  const k = r / SPR_R[tier];
  g.drawImage(sp.c, x - sp.cx * k, y - sp.cy * k, sp.w * k, sp.w * k);
}

function mulberry32(a) {
  return function () {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | a) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
