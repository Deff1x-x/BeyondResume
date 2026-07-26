import { chromium } from "playwright";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE = process.env.BASE_URL || "http://localhost:3002";
const OUT = path.resolve(__dirname);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });
await page.goto(`${BASE}/dev/eif-preview`, { waitUntil: "networkidle" });
await page.waitForTimeout(1100);

for (const name of ["idle", "loading", "success", "error"]) {
  const section = page.locator(`[data-shot="${name}"]`);
  await section.screenshot({
    path: path.join(OUT, `eif-${name}.png`)
  });
  console.log("saved", name);
}

await page.setViewportSize({ width: 390, height: 844 });
await page.waitForTimeout(300);
await page.locator('[data-shot="idle"]').screenshot({
  path: path.join(OUT, "eif-mobile.png")
});
console.log("saved mobile");

await browser.close();
