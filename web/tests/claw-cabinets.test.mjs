import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { CATALOG, CABINETS, cabinetFromSearch } from "../src/claw-toys.ts";

test("every character is selectable and its shipped mesh matches recorded provenance", () => {
  assert.equal(CATALOG.length, 16);
  assert.equal(new Set(Object.values(CABINETS).flatMap(c => c.toys)).size, 16);
  assert.equal(cabinetFromSearch("?cabinet=invalid"), "classic");
  const root = new URL("../src/assets/nai/", import.meta.url);
  const manifest = JSON.parse(readFileSync(new URL("manifest.json", root)));
  const collisions = JSON.parse(readFileSync(new URL("collisions.json", root)));
  for (const [i, toy] of CATALOG.entries()) {
    const entry = manifest.assets.find(a => a.kind === toy.kind);
    const blob = readFileSync(new URL(`${toy.kind}.glb`, root));
    assert.equal(createHash("sha256").update(blob).digest("hex"), entry.glb_sha256);
    assert.ok(collisions[i].length > 0 && collisions[i].length <= 16);
    assert.ok(Math.abs(collisions[i].reduce((m, p) => m + p.mass, 0) - .08) < 1e-6);
  }
});

for (const cabinet of ["friends", "curios"]) {
  test(`${cabinet}: settled native toys and synchronized three-solver grab remain finite`, () => {
    const output = execFileSync(process.execPath, ["--experimental-strip-types", fileURLToPath(new URL("fixtures/cabinet-round.mjs", import.meta.url)), cabinet], { timeout: 90000, encoding: "utf8" });
    assert.match(output, new RegExp(`"cabinet":"${cabinet}"`));
    console.log(output.trim());
  });
}
