#!/usr/bin/env node

import { execSync, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const CONFIG = path.join(ROOT, "scripts", "docs", "markdown-link-check.local.json");

const bin = process.platform === "win32"
  ? path.join(ROOT, "node_modules", ".bin", "markdown-link-check.cmd")
  : path.join(ROOT, "node_modules", ".bin", "markdown-link-check");

if (!fs.existsSync(bin)) {
  console.error("markdown-link-check not found. Run: npm install");
  process.exit(1);
}

let files = [];
try {
  const out = execSync("rg --files -g '*.md'", { encoding: "utf8" }).trim();
  files = out ? out.split("\n") : [];
} catch (error) {
  console.error("Unable to list markdown files with ripgrep.");
  console.error(String(error));
  process.exit(1);
}

const failures = [];

for (const file of files) {
  const result = spawnSync(bin, [file, "-q", "-c", CONFIG], {
    encoding: "utf8",
    stdio: "pipe",
  });

  if (result.status !== 0) {
    failures.push({
      file,
      output: `${result.stdout ?? ""}${result.stderr ?? ""}`.trim(),
    });
  }
}

if (failures.length > 0) {
  console.error(`docs-links: failed (${failures.length} file(s))`);
  for (const fail of failures) {
    console.error(`\n--- ${fail.file} ---`);
    console.error(fail.output || "Unknown markdown-link-check error");
  }
  process.exit(1);
}

console.log(`docs-links: ok (${files.length} markdown files checked)`);
