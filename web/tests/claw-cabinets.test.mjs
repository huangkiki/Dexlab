import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { CATALOG, TOYS, TOY_SCALE } from "../src/claw-toys.ts";

test("every character is present and its shipped mesh matches recorded provenance", () => {
  assert.equal(CATALOG.length, 16);
  assert.equal(new Set(TOYS.map(t => t.kind)).size, 16);
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

test("thirty nonpenetrating spawn poses form three layers in every reshuffle", () => {
  const collisions = JSON.parse(readFileSync(new URL("../src/assets/nai/collisions.json", import.meta.url)));
  assert.equal(TOYS.length, 30);
  assert.equal(new Set(TOYS.map(t => `${t.x},${t.y},${t.z}`)).size, 30);
  assert.equal(new Set(TOYS.map(t => t.z)).size, 3);
  for (let layout = 0; layout < TOYS.length; layout++) {
    const bounds = TOYS.map((toy, i) => {
      const slot = TOYS[(i + layout) % TOYS.length];
      const parts = collisions[CATALOG.findIndex(t => t.kind === toy.kind)];
      return [slot.x, slot.y, slot.z].flatMap((center, axis) => {
        const values = parts.flatMap(p => p.vertices.filter((_, j) => j % 3 === axis));
        return [center + Math.min(...values) * TOY_SCALE, center + Math.max(...values) * TOY_SCALE];
      });
    });
    for (const [i, a] of bounds.entries()) {
      assert.ok(a[0] >= -.31 && a[1] <= .31 && a[2] >= -.26 && a[3] <= .26 && a[4] > 0);
      assert.ok(a[0] >= -.13 || a[2] >= -.075, `${layout}/${i} intersects chute`);
      for (const b of bounds.slice(i + 1))
        assert.ok([0, 2, 4].some(axis => a[axis + 1] < b[axis] || b[axis + 1] < a[axis]), `${layout}: penetrating spawn`);
    }
  }
});

for (const layout of [0, 1, 29]) {
  test(`layout ${layout}: thirty prizes settle into a native pile and three-solver grabs remain finite`, () => {
    const output = execFileSync(process.execPath, ["--experimental-strip-types", fileURLToPath(new URL("fixtures/cabinet-round.mjs", import.meta.url)), String(layout)], { timeout: 120000, encoding: "utf8" });
    assert.match(output, new RegExp(`"layout":${layout}`));
    console.log(output.trim());
  });
}

test("display derivatives retain source provenance and bound GPU geometry and texture sizes", () => {
  const root = new URL('../src/assets/nai/', import.meta.url);
  const manifest = JSON.parse(readFileSync(new URL('display/manifest.json', root)));
  assert.equal(manifest.assets.length, CATALOG.length);
  for (const entry of manifest.assets) {
    const source = readFileSync(new URL(entry.name,root));
    const bytes = readFileSync(new URL('display/'+entry.name,root));
    assert.equal(createHash('sha256').update(source).digest('hex'),entry.sourceSha256);
    assert.equal(createHash('sha256').update(bytes).digest('hex'),entry.sha256);
    assert.ok(entry.relativeError <= manifest.maxRelativeError);
    const length = bytes.readUInt32LE(12);
    const gltf = JSON.parse(bytes.subarray(20,20+length).toString());
    const binary = bytes.subarray(28+length);
    let triangles = 0;
    for (const mesh of gltf.meshes) for (const primitive of mesh.primitives) {
      triangles += gltf.accessors[primitive.indices].count / 3;
      const accessor = gltf.accessors[primitive.indices], view = gltf.bufferViews[accessor.bufferView];
      const indices = binary.subarray(view.byteOffset,view.byteOffset+view.byteLength);
      const vertexCount = gltf.accessors[primitive.attributes.POSITION].count;
      for (let i=0;i<indices.length;i+=2) assert.ok(indices.readUInt16LE(i)<vertexCount);
      assert.ok(primitive.attributes.NORMAL !== undefined && primitive.attributes.TEXCOORD_0 !== undefined);
    }
    assert.equal(triangles,entry.triangles);
    assert.ok(triangles <= manifest.targetTriangles);
    for (const image of gltf.images) {
      const view = gltf.bufferViews[image.bufferView], png = binary.subarray(view.byteOffset,view.byteOffset+view.byteLength);
      assert.equal(png.subarray(1,4).toString(),'PNG');
      assert.ok(png.readUInt32BE(16)<=512 && png.readUInt32BE(20)<=512);
    }
  }
});
