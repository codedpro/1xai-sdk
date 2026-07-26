/**
 * Post-build fixups for the dual ESM/CJS output.
 *
 * The package is `"type": "module"`, so Node treats every .js under it as ESM.
 * Dropping a tiny package.json into each dist folder pins the module system per
 * directory, which is the standard way to ship both from one build.
 *
 * Also makes the CLI executable, so `npx onexai doctor` works.
 */

import { chmodSync, existsSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname;

for (const [dir, type] of [
  ["dist/esm", "module"],
  ["dist/cjs", "commonjs"],
]) {
  const target = join(root, dir, "package.json");
  if (!existsSync(join(root, dir))) {
    console.warn(`[fixup] skipped ${dir} (not built)`);
    continue;
  }
  writeFileSync(target, JSON.stringify({ type }, null, 2) + "\n");
  console.log(`[fixup] wrote ${dir}/package.json {"type":"${type}"}`);
}

const cli = join(root, "dist/esm/cli.js");
if (existsSync(cli)) {
  chmodSync(cli, 0o755);
  console.log("[fixup] chmod +x dist/esm/cli.js");
}
