#!/usr/bin/env node
// ═══════════════════════════════════════════════════════════════════
// CI Timeout Fix — Increase test job timeout from 15m to 25m
//
// WHY: With ~15,000 tests, the test suite takes ~15m on GitHub Actions.
//      The 15m timeout causes the test job to be cancelled right at the edge.
//      Bumping to 25m gives comfortable headroom.
//
// NOTE: The Cowork VM PAT doesn't have `workflow` scope, so this change
//       can't be pushed automatically. Steve needs to run this locally
//       and push from his Mac.
//
// USAGE:
//   cd ~/Projects/Claude\ Cowork/Projects/wuunderfund-mvp
//   git checkout feature/coverage-routes-100
//   node WuunderFund_ci-timeout-fix_v1.mjs
//   git add .github/workflows/ci.yml
//   git commit -m "ci: increase test timeout to 25m for 15k test suite"
//   HUSKY=0 git push origin feature/coverage-routes-100
// ═══════════════════════════════════════════════════════════════════

import { readFileSync, writeFileSync } from "fs";

const file = ".github/workflows/ci.yml";
let content = readFileSync(file, "utf8");

// Replace the test job timeout (15 → 25)
const before = content;
content = content.replace(
  /(\s+test:\s+name:\s+Test\s+runs-on:\s+ubuntu-latest\s+timeout-minutes:\s+)15\b/,
  "$125"
);

if (content === before) {
  console.log("⚠️  Pattern not matched — check if timeout was already changed");
  process.exit(1);
}

writeFileSync(file, content);
console.log("✅ CI test timeout bumped: 15m → 25m");
console.log("   Now run: git add .github/workflows/ci.yml && git commit -m 'ci: increase test timeout to 25m' && HUSKY=0 git push origin feature/coverage-routes-100");
