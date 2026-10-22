import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { CONTENT_FILES } from "../scripts/content-files.mjs";
import { buildMessage, formatPerCheck, formatUsd, readContent, splitNotes, type DemoInput } from "./content";

const site = process.cwd(); // vitest runs from site/
const repo = path.resolve(site, "..");

describe("content copies", () => {
  it("match their sources in the repo (run `npm run sync` if this fails)", () => {
    for (const [from, to] of CONTENT_FILES) {
      const src = path.join(repo, from);
      if (!fs.existsSync(src)) continue;
      expect(fs.readFileSync(path.join(site, to), "utf8"), to).toBe(fs.readFileSync(src, "utf8"));
    }
  });
});

describe("notes and messages", () => {
  const notes = "# Week\n\n## Acme Robotics\n- a\n\n## Bluefin Foods\n- b\n";
  const base: DemoInput = { id: "x", client: "acme-robotics", notes: "none", task: "Do it.", expected: "GREEN", stage: true };

  it("splits notes by client heading", () => {
    expect(splitNotes(notes)).toEqual({ acme: "## Acme Robotics\n- a", bluefin: "## Bluefin Foods\n- b" });
  });

  it("builds the same messages as the Python script", () => {
    expect(buildMessage(base, notes)).toBe("Do it.");
    expect(buildMessage({ ...base, notes: "acme" }, notes)).toBe("Do it.\n\n## Acme Robotics\n- a");
    expect(buildMessage({ ...base, notes: "all" }, notes)).toBe(`Do it.\n\n${notes.trim()}`);
    expect(() => buildMessage({ ...base, notes: "zeta" }, notes)).toThrow();
  });
});

describe("readContent", () => {
  it("returns three stage steps in green, amber, red order, and only step 3 mentions Bluefin", () => {
    const c = readContent();
    expect(c.stageSteps.map((s) => s.input.expected)).toEqual(["GREEN", "AMBER", "RED"]);
    expect(c.stageSteps[0].message).not.toContain("Bluefin");
    expect(c.stageSteps[2].message).toContain("Bluefin");
    expect(c.instructions).toContain("Firewall: RED");
  });
});

describe("formatUsd", () => {
  it("shows small amounts with four decimals and larger with two", () => {
    expect(formatUsd(0.00412)).toBe("$0.0041");
    expect(formatUsd(4.123)).toBe("$4.12");
  });
});

describe("formatPerCheck", () => {
  it("always shows four decimals so the column lines up", () => {
    expect(formatPerCheck(0.01428)).toBe("$0.0143");
    expect(formatPerCheck(0.000378)).toBe("$0.0004");
  });
});
