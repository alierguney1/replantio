// Records the launch demo of replantio.com as webm segments (concat later).
// v3: starts on the site (no search, no long flights), 720p for capture fps.
// Run: node design/demo_video.cjs
const puppeteer = require("/Users/guilhermedavid/.nvm/versions/node/v24.18.0/lib/node_modules/puppeteer-core");

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const FFMPEG = "/opt/homebrew/bin/ffmpeg";
const OUT = "/tmp/replantio-demo";
const URL = "https://replantio.com";

// riverside brownfield in Cubatão (OSM landuse=brownfield), bare dirt lot
const POLY = [
  [-23.87257, -46.39239],
  [-23.87386, -46.38932],
  [-23.87639, -46.3918],
  [-23.87523, -46.39355],
];
const CENTER = [-23.8745, -46.3918];

const sleep = ms => new Promise(r => setTimeout(r, ms));

const fs = require("fs");
let CDP = null, REC = null;
async function startRec(page, name) {
  if (!CDP) {
    CDP = await page.createCDPSession();
    CDP.on("Page.screencastFrame", ev => {
      if (REC) {
        const f = `${REC.dir}/f${String(REC.i++).padStart(5, "0")}.jpg`;
        fs.writeFileSync(f, Buffer.from(ev.data, "base64"));
        REC.frames.push({ f, ts: ev.metadata.timestamp });
      }
      CDP.send("Page.screencastFrameAck", { sessionId: ev.sessionId }).catch(() => {});
    });
  }
  const dir = `${OUT}/${name}`;
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  REC = { dir, name, i: 0, frames: [] };
  await CDP.send("Page.startScreencast", { format: "jpeg", quality: 90, everyNthFrame: 1 });
}
async function stopRec() {
  await CDP.send("Page.stopScreencast");
  const r = REC; REC = null;
  const lines = r.frames.map((fr, i) => {
    const d = i + 1 < r.frames.length ? Math.max(0.008, r.frames[i + 1].ts - fr.ts) : 0.12;
    return `file '${fr.f}'\nduration ${d.toFixed(4)}`;
  });
  lines.push(`file '${r.frames[r.frames.length - 1].f}'`);
  fs.writeFileSync(`${OUT}/${r.name}.txt`, lines.join("\n") + "\n");
  console.log(r.name, r.frames.length, "frames");
}


async function glide(page, x, y, ms = 500) {
  const steps = Math.max(10, Math.round(ms / 16));
  await page.mouse.move(x, y, { steps });
}
async function clickAt(page, x, y, ms = 500) {
  await glide(page, x, y, ms);
  await sleep(150);
  await page.mouse.down(); await sleep(90); await page.mouse.up();
}

async function main() {
  require("fs").mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ["--window-size=1280,820", "--lang=en-US", "--force-device-scale-factor=1"],
    defaultViewport: { width: 1280, height: 720 },
  });
  const page = await browser.newPage();
  await page.evaluateOnNewDocument(() => localStorage.setItem("lang", "en"));
  await page.goto(URL, { waitUntil: "networkidle2", timeout: 60000 });
  await page.waitForFunction("!!window.canopy", { timeout: 30000 });

  // visible cursor overlay
  await page.evaluate(() => {
    const c = document.createElement("div");
    c.id = "democursor";
    c.style.cssText = `position:fixed;z-index:2147483647;width:20px;height:20px;margin:-10px 0 0 -10px;
      border-radius:50%;background:rgba(255,255,255,.28);border:1.5px solid rgba(255,255,255,.95);
      box-shadow:0 1px 6px rgba(0,0,0,.5);pointer-events:none;left:640px;top:360px;
      transition:transform .1s ease;`;
    document.body.appendChild(c);
    addEventListener("mousemove", e => { c.style.left = e.clientX + "px"; c.style.top = e.clientY + "px"; }, true);
    addEventListener("mousedown", () => { c.style.transform = "scale(.65)"; c.style.background = "rgba(99,201,135,.55)"; }, true);
    addEventListener("mouseup", () => { c.style.transform = ""; c.style.background = "rgba(255,255,255,.28)"; }, true);
  });

  // open already on the site: no search theater, no laggy tile flights
  await page.evaluate(([lat, lng]) => window.canopy.map.setView([lat, lng], 17), CENTER);
  await sleep(4000); // tiles fully in

  // ---- segment 1: settle, draw, glimpse of loading
  await startRec(page, "seg1");
  await sleep(1400);

  const db = await (await page.$("#draw-btn")).boundingBox();
  await clickAt(page, db.x + db.width / 2, db.y + db.height / 2, 700);
  await sleep(600);
  const pts = await page.evaluate(poly =>
    poly.map(([la, ln]) => {
      const p = window.canopy.map.latLngToContainerPoint([la, ln]);
      return [p.x, p.y];
    }), POLY);
  for (const [x, y] of pts) { await clickAt(page, x, y, 620); await sleep(230); }
  await clickAt(page, pts[0][0], pts[0][1], 700); // close on first vertex
  await sleep(2200); // loading steps glimpse
  await stopRec();

  // ---- wait for results off camera
  await page.waitForSelector(".sp[data-id]", { timeout: 90000 });
  await sleep(2500); // photos/GBIF trickle in

  // ---- segment 2: results, native filter, card, simulator, saplings, end card
  await startRec(page, "seg2");
  await sleep(1800);

  // scroll the panel through the ledger
  await page.evaluate(() => document.querySelector("#panel")
    .scrollTo({ top: 420, behavior: "smooth" }));
  await sleep(1900);
  await page.evaluate(() => document.querySelector("#panel")
    .scrollTo({ top: 0, behavior: "smooth" }));
  await sleep(1300);

  // chips: flip to shrubs and herbs (seed prices appear), then back to trees
  const nb = await (await page.$('.chips-row .opt[data-v="nontree"]')).boundingBox();
  await clickAt(page, nb.x + nb.width / 2, nb.y + nb.height / 2, 600);
  await sleep(1700);
  const tb = await (await page.$('.chips-row .opt[data-v="tree"]')).boundingBox();
  await clickAt(page, tb.x + tb.width / 2, tb.y + tb.height / 2, 500);
  await sleep(900);

  // open the top species: simulation starts immediately
  const hb = await (await page.$(".sp .sp-head")).boundingBox();
  await clickAt(page, hb.x + hb.width / 2, hb.y + hb.height / 2, 650);
  await sleep(3000); // fitBounds + sprites
  // the guerrilla answer: where to actually get it
  await page.evaluate(() => document.querySelector(".sp.open .getrows")?.scrollIntoView({ block: "center", behavior: "smooth" }));
  await sleep(2300);
  await page.evaluate(() => document.querySelector("#panel").scrollTo({ top: 0, behavior: "smooth" }));
  await sleep(1100);

  // slider: pull back to year ~3, plant saplings at ~12, sweep to +30y
  const sl = await page.$("#sim input[type=range]");
  const sb = await sl.boundingBox();
  const [min, max, val] = await page.evaluate(() => {
    const i = document.querySelector("#sim input");
    return [+i.min, +i.max, +i.value];
  });
  const frac = y => Math.min(1, (y - min) / (max - min));
  const xAt = f => sb.x + 8 + (sb.width - 16) * f;
  const cy = sb.y + sb.height / 2;
  await glide(page, xAt(frac(val)), cy, 800);
  await page.mouse.down();
  await glide(page, xAt(frac(3)), cy, 1200);
  await sleep(400);
  await glide(page, xAt(frac(12)), cy, 1400);
  await page.mouse.up();
  await sleep(700);

  // plant three saplings inside the plot
  const spots = await page.evaluate(([la, ln]) => {
    const m = window.canopy.map;
    return [[la + 0.0004, ln - 0.0006], [la - 0.0003, ln + 0.0005], [la + 0.0007, ln + 0.0008]]
      .map(q => { const p = m.latLngToContainerPoint(q); return [p.x, p.y]; });
  }, CENTER);
  for (const [x, y] of spots) { await clickAt(page, x, y, 550); await sleep(280); }
  await sleep(600);

  // sweep the years to +30
  await glide(page, xAt(frac(12)), cy, 550);
  await page.mouse.down();
  await glide(page, xAt(frac(30)), cy, 3600);
  await page.mouse.up();
  await sleep(1600);

  // one animated zoom-out (zoomanim path keeps the sim canvas in step)
  await page.evaluate(() => window.canopy.map.zoomOut());
  await sleep(2600);

  // end card
  await page.evaluate(() => {
    const v = document.createElement("div");
    v.style.cssText = `position:fixed;inset:0;z-index:2147483646;background:rgba(7,10,8,.88);
      display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;
      opacity:0;transition:opacity 1.1s ease;font-family:'IBM Plex Sans',sans-serif;`;
    v.innerHTML = `
      <div style="display:flex;align-items:center;gap:14px">
        <img src="assets/logo.png" width="46" height="46" style="border-radius:11px">
        <span style="font-size:40px;font-weight:600;color:#e8ede8;letter-spacing:-.5px">Replantio</span>
      </div>
      <div style="font-size:17px;color:#99a69c">Draw an area anywhere on Earth and see what would grow there.</div>
      <div style="font-size:15px;color:#63c987;font-family:'IBM Plex Mono',monospace">replantio.com</div>`;
    document.body.appendChild(v);
    requestAnimationFrame(() => { v.style.opacity = "1"; });
    document.getElementById("democursor").style.display = "none";
  });
  await sleep(3200);
  await stopRec();

  await browser.close();
  console.log("segments recorded in", OUT);
}

main().catch(e => { console.error(e); process.exit(1); });
