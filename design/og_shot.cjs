// Screenshot base for the OG image: brownfield analysis, native filter, simulated stand.
const puppeteer = require("/Users/guilhermedavid/.nvm/versions/node/v24.18.0/lib/node_modules/puppeteer-core");

const URL = "https://replantio.com/#p=-23.87257,-46.39239;-23.87386,-46.38932;-23.87639,-46.3918;-23.87523,-46.39355";

(async () => {
  const browser = await puppeteer.launch({
    executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true,
    args: ["--window-size=1800,1100", "--lang=pt-BR"],
    defaultViewport: { width: 1800, height: 1000 },
  });
  const page = await browser.newPage();
  await page.evaluateOnNewDocument(() => localStorage.setItem("lang", "pt"));
  await page.goto(URL, { waitUntil: "networkidle2", timeout: 60000 });
  await page.waitForSelector(".sp[data-id]", { timeout: 90000 });
  await new Promise(r => setTimeout(r, 1500));
  await page.evaluate(() => document.querySelector(".sp .sp-head").click()); // top native, sim starts
  await page.waitForSelector("#sim input", { timeout: 20000 });
  await new Promise(r => setTimeout(r, 2500));
  await page.evaluate(() => {
    const i = document.querySelector("#sim input");
    i.value = Math.min(25, +i.max);
    i.dispatchEvent(new Event("input"));
  });
  await new Promise(r => setTimeout(r, 3000)); // photos settle
  await page.screenshot({ path: "/tmp/replantio-demo/og_base.png" });
  await browser.close();
  console.log("og_base saved");
})().catch(e => { console.error(e); process.exit(1); });
