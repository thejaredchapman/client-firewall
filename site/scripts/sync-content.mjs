import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { CONTENT_FILES } from "./content-files.mjs";

const site = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repo = path.resolve(site, "..");

for (const [from, to, required] of CONTENT_FILES) {
  const src = path.join(repo, from);
  if (!fs.existsSync(src)) {
    if (required) throw new Error(`Missing required source: ${from}`);
    console.log(`skip (not generated yet): ${from}`);
    continue;
  }
  fs.mkdirSync(path.dirname(path.join(site, to)), { recursive: true });
  fs.copyFileSync(src, path.join(site, to));
  console.log(`copied ${from} -> site/${to}`);
}
