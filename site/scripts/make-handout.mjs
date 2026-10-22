// Usage: npm run handout -- --url=https://your-site.vercel.app
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import QRCode from "qrcode";
import { chromium } from "playwright";

const site = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outDir = path.resolve(site, "..", "handout");

const usage = "Usage: npm run handout -- --url=https://your-site.vercel.app";
const urlArg = process.argv.find((a) => a.startsWith("--url="));
if (!urlArg) {
  console.error(usage);
  process.exit(1);
}
let parsed;
try {
  parsed = new URL(urlArg.slice("--url=".length));
} catch {
  console.error(usage);
  process.exit(1);
}
if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
  console.error(usage);
  process.exit(1);
}
const url = parsed.href.replace(/\/$/, "");
const shownUrl = url.replace(/^https?:\/\//, "");

const copy = JSON.parse(fs.readFileSync(path.join(site, "content", "copy.json"), "utf8"));
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const dot = { GREEN: "#1f7a3f", AMBER: "#9a6200", RED: "#b42318" };

const qrSvg = await QRCode.toString(url, { type: "svg", margin: 4, errorCorrectionLevel: "M" });

const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>${esc(copy.title)}</title>
<style>
  @page { size: Letter; margin: 0.6in; }
  body { font: 13.5pt/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; color: #1d1d1b; margin: 0; }
  h1 { font-size: 30pt; margin: 0; line-height: 1.1; }
  .tagline { font-size: 15pt; color: #5d5b55; margin: 6pt 0 18pt; }
  .grid { display: grid; grid-template-columns: 1fr 2.3in; gap: 0.35in; align-items: start; }
  h2 { font-size: 14pt; margin: 16pt 0 6pt; }
  ol { margin: 0; padding-left: 18pt; }
  .pointer { color: #5d5b55; margin: 6pt 0 0; }
  .color { display: grid; grid-template-columns: 72pt 1fr; column-gap: 6pt; margin: 4pt 0; }
  .qr { text-align: center; }
  .qr svg { width: 2.1in; height: 2.1in; }
  .url { font-weight: 700; font-size: 11pt; word-break: break-all; margin-top: 4pt; }
  .scan { color: #5d5b55; font-size: 10.5pt; }
  .limit { margin-top: 22pt; padding: 10pt 12pt; border: 1px solid #e3e0d8; border-radius: 8pt; }
  footer { margin-top: 22pt; color: #5d5b55; font-size: 10.5pt; }
</style></head><body>
  <h1>${esc(copy.title)}</h1>
  <p class="tagline">${esc(copy.tagline)}</p>
  <div class="grid">
    <div>
      <p>${esc(copy.problem)}</p>
      <h2>Set up in 3 steps</h2>
      <ol>${copy.steps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>
      <p class="pointer">The instructions and a blank rules file are on the site. Scan the QR code.</p>
      <h2>Before Claude writes a word</h2>
      ${copy.colors
        .map((c) => `<p class="color"><b style="color:${dot[c.verdict]}">● ${c.verdict}</b><span>${esc(c.rule)}</span></p>`)
        .join("")}
    </div>
    <div class="qr">
      ${qrSvg}
      <div class="url">${esc(shownUrl)}</div>
      <div class="scan">Scan for the free template, setup steps and a 3-message demo to try.</div>
    </div>
  </div>
  <div class="limit"><b>It's a second check, not a guarantee.</b> ${esc([copy.limits[0], copy.limits[2]].join(" "))}</div>
  <footer>${esc(copy.author.name)} · ${esc(copy.author.linkedin)} · ${esc(copy.author.site)}</footer>
</body></html>`;

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, "qr.svg"), qrSvg);
fs.writeFileSync(path.join(outDir, "handout.html"), html);

const browser = await chromium.launch();
const page = await browser.newPage();
await page.setContent(html, { waitUntil: "load" });
const pdf = await page.pdf({ format: "Letter", printBackground: true, preferCSSPageSize: true });
await browser.close();

const pages = (pdf.toString("latin1").match(/\/Type\s*\/Page(?!s)/g) || []).length;
if (pages > 1) {
  console.error(`Handout is ${pages} pages; it must fit on 1. Shorten copy or tighten spacing.`);
  process.exit(1);
}
if (pages === 0) {
  console.error("Could not count PDF pages; refusing to write a handout that may not be one page.");
  process.exit(1);
}
fs.writeFileSync(path.join(outDir, "client-firewall-handout.pdf"), pdf);
console.log(`Wrote handout/client-firewall-handout.pdf, handout/qr.svg for ${url}`);
