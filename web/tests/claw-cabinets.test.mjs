import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { CATALOG, CABINETS, cabinetFromSearch, toysForCabinet } from "../src/claw-toys.ts";

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

test("all cabinets have sixteen separate spawn slots, outside the prize chute", () => {
  const collisions = JSON.parse(readFileSync(new URL("../src/assets/nai/collisions.json", import.meta.url)));
  for (const key of Object.keys(CABINETS)) {
    const toys = toysForCabinet(key);
    assert.equal(toys.length, 16);
    assert.equal(new Set(toys.map(t => `${t.x},${t.y}`)).size, 16);
    for (let layout = 0; layout < 16; layout++) {
      const bounds = toys.map((toy, i) => {
        const slot = toys[(i + layout) % toys.length];
        const parts = collisions[CATALOG.findIndex(t => t.kind === toy.kind)];
        const xs = parts.flatMap(p => p.vertices.filter((_, j) => j % 3 === 0));
        const ys = parts.flatMap(p => p.vertices.filter((_, j) => j % 3 === 1));
        return [slot.x + Math.min(...xs), slot.x + Math.max(...xs), slot.y + Math.min(...ys), slot.y + Math.max(...ys)];
      });
      for (const [i, a] of bounds.entries()) {
        assert.ok(a[0] >= -.28 && a[1] <= .28 && a[2] >= -.205 && a[3] <= .205);
        assert.ok(a[0] >= -.15 || a[2] >= -.07, `${key}/${layout}/${i} intersects chute`);
        for (const b of bounds.slice(i + 1)) assert.ok(a[1] < b[0] || b[1] < a[0] || a[3] < b[2] || b[3] < a[2], `${key}/${layout}: overlapping toys`);
      }
    }
  }
});

for (const cabinet of ["friends", "curios"]) {
  test(`${cabinet}: settled native toys and synchronized three-solver grab remain finite`, () => {
    const output = execFileSync(process.execPath, ["--experimental-strip-types", fileURLToPath(new URL("fixtures/cabinet-round.mjs", import.meta.url)), cabinet], { timeout: 90000, encoding: "utf8" });
    assert.match(output, new RegExp(`"cabinet":"${cabinet}"`));
    console.log(output.trim());
  });
}
