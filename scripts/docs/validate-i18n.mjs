#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const DOCS_DIR = path.join(ROOT, "docs", "project");
const EN_DIR = path.join(DOCS_DIR, "en");

const CORE_FILES = [
  "INDEX.md",
  "QUICK-START.md",
  "ARCHITECTURE.md",
  "TECHNICAL-REFERENCE.md",
  "OBSERVABILITY.md",
  "GOOGLE-DRIVE-SETUP.md",
  "GOOGLE-DRIVE-FEATURES.md",
  "GLOBAL-PLAYER.md",
  "BUGS.md",
];

const issues = [];

const headingSeq = (content) => {
  const lines = content.split(/\r?\n/);
  const seq = [];
  let inFence = false;

  for (const line of lines) {
    if (/^\s*```/.test(line)) {
      inFence = !inFence;
      continue;
    }
    if (inFence) {
      continue;
    }
    const match = line.match(/^(##|###)\s+(.+)$/);
    if (!match) {
      continue;
    }
    seq.push(match[1] === "##" ? 2 : 3);
  }
  return seq;
};

for (const file of CORE_FILES) {
  const ptPath = path.join(DOCS_DIR, file);
  const enPath = path.join(EN_DIR, file);

  if (!fs.existsSync(ptPath)) {
    issues.push(`PT missing: docs/project/${file}`);
    continue;
  }
  if (!fs.existsSync(enPath)) {
    issues.push(`EN missing: docs/project/en/${file}`);
    continue;
  }

  const pt = fs.readFileSync(ptPath, "utf8");
  const en = fs.readFileSync(enPath, "utf8");

  const ptHeader = `[**PT-BR**](./${file}) | [EN](./en/${file})`;
  const enHeader = `[PT-BR](../${file}) | **EN**`;

  if (!pt.includes(ptHeader)) {
    issues.push(`PT header mismatch: docs/project/${file}`);
  }
  if (!en.includes(enHeader)) {
    issues.push(`EN header mismatch: docs/project/en/${file}`);
  }

  const ptSeq = headingSeq(pt);
  const enSeq = headingSeq(en);

  if (ptSeq.length !== enSeq.length) {
    issues.push(
      `H2/H3 count mismatch in ${file}: PT=${ptSeq.length} EN=${enSeq.length}`
    );
    continue;
  }

  for (let i = 0; i < ptSeq.length; i += 1) {
    if (ptSeq[i] !== enSeq[i]) {
      issues.push(
        `H2/H3 structure mismatch in ${file} at position ${i + 1}: PT=${ptSeq[i]} EN=${enSeq[i]}`
      );
      break;
    }
  }
}

const enFiles = fs.existsSync(EN_DIR)
  ? fs.readdirSync(EN_DIR).filter((f) => f.endsWith(".md"))
  : [];
for (const file of enFiles) {
  if (!CORE_FILES.includes(file)) {
    issues.push(`Unexpected EN file outside core list: docs/project/en/${file}`);
  }
}

if (issues.length > 0) {
  console.error("docs-i18n: failed");
  for (const issue of issues) {
    console.error(`- ${issue}`);
  }
  process.exit(1);
}

console.log("docs-i18n: ok");
console.log(`- Core files checked: ${CORE_FILES.length}`);
console.log("- Headers validated: PT + EN");
console.log("- H2/H3 structural parity validated");
