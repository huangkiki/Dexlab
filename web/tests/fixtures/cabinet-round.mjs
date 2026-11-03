import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import loadMujoco from "@mujoco/mujoco";

const { ClawComparison } = await import("../../src/claw-comparison.ts");
const { TOYS } = await import("../../src/claw-toys.ts");
const module = await loadMujoco({ wasmBinary: await readFile(fileURLToPath(import.meta.resolve("@mujoco/mujoco/mujoco.wasm"))) });
const comparison = new ClawComparison(module);
try {
  const task = comparison.reference;
  task.reset(Number(process.argv[2]));
  for (let step = 0; step < 1500; step++) task.step();
  assert.equal(task.won.size, 0);
  for (let i = 0; i < TOYS.length; i++) {
    const position = task.position(i);
    assert.ok(Math.abs(position.x) < .31 && Math.abs(position.y) < .26);
    assert.ok(position.z > 0 && position.z < .4);
  }
  assert.ok(TOYS.filter((_, i) => task.position(i).z > .1).length >= 5, "pile flattened into a display row");
  let toyContacts = 0;
  const contacts = task.data.contact;
  for (let i = 0; i < task.data.ncon; i++) {
    const contact = contacts.get(i);
    if (task.toyBodies.includes(task.model.geom_bodyid[contact.geom1]) && task.toyBodies.includes(task.model.geom_bodyid[contact.geom2])) toyContacts++;
    contact.delete();
  }
  contacts.delete();
  assert.ok(toyContacts >= 10, "elevated toys must be in real mutual contact");
  const target = task.position(28);
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
  console.log(JSON.stringify({ layout: Number(process.argv[2]), count: TOYS.length, toyContacts, scores: comparison.tasks.map(t => t.won.size), frames: comparison.frames.length }));
} finally { comparison.dispose(); }
