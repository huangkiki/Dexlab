import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import loadMujoco from "@mujoco/mujoco";

// Match the immutable cabinet selection performed at browser module load.
globalThis.location = { search: `?cabinet=${process.argv[2]}` };
const { ClawComparison } = await import("../../src/claw-comparison.ts");
const { TOYS } = await import("../../src/claw-toys.ts");
const module = await loadMujoco({ wasmBinary: await readFile(fileURLToPath(import.meta.resolve("@mujoco/mujoco/mujoco.wasm"))) });
const comparison = new ClawComparison(module);
try {
  const task = comparison.reference;
  for (let step = 0; step < 1500; step++) task.step();
  assert.equal(task.won.size, 0);
  for (let i = 0; i < TOYS.length; i++) {
    const position = task.position(i);
    assert.ok(Math.abs(position.x) < .29 && Math.abs(position.y) < .22);
    assert.ok(position.z > -.04 && position.z < .14);
  }
  const target = task.position(0);
  task.move("x", target.x - task.target.x);
  task.move("y", target.y - task.target.y);
  comparison.start(60);
  assert.deepEqual(comparison.tasks[0].checkpoint(), comparison.tasks[1].checkpoint());
  assert.deepEqual(comparison.tasks[0].checkpoint(), comparison.tasks[2].checkpoint());
  for (let step = 0; !comparison.complete && step < 15000; step++) {
    comparison.step();
    for (const world of comparison.tasks) {
      assert.ok(Array.from(world.data.qpos).every(Number.isFinite));
      assert.ok(Array.from(world.data.qvel).every(Number.isFinite));
      if (["descend", "close", "lift", "carry"].includes(world.phase)) assert.equal(world.won.size, 0);
    }
  }
  assert.equal(comparison.complete, true);
  assert.equal(comparison.tasks[0].data.time, comparison.tasks[1].data.time);
  assert.equal(comparison.tasks[0].data.time, comparison.tasks[2].data.time);
  console.log(JSON.stringify({ cabinet: process.argv[2], toys: TOYS.map(t => t.kind), scores: comparison.tasks.map(t => t.won.size), frames: comparison.frames.length }));
} finally { comparison.dispose(); }
