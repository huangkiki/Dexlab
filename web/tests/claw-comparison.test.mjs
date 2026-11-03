import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import loadMujoco from "@mujoco/mujoco";
import { ClawComparison } from "../src/claw-comparison.ts";
import { TOYS, BIN } from "../src/claw-task.ts";

const mj = await loadMujoco({
  wasmBinary: await readFile(
    fileURLToPath(import.meta.resolve("@mujoco/mujoco/mujoco.wasm")),
  ),
});
function prepare(c, empty = false) {
  c.reference.move("x", (empty ? BIN.x : TOYS[0].x) - c.reference.target.x);
  c.reference.move("y", (empty ? BIN.y : TOYS[0].y) - c.reference.target.y);
  for (let i = 0; i < 250; i++) c.reference.step();
}
function finish(c) {
  for (let step = 0; !c.complete && step < 15000; step++) {
    c.step();
    for (const task of c.tasks.slice(1)) {
      assert.equal(task.data.time, c.reference.data.time);
      assert.deepEqual(
        Array.from(task.data.ctrl),
        Array.from(c.reference.data.ctrl),
      );
    }
  }
  assert.equal(c.complete, true);
}
test("all solvers copy full integration and scoring state, with only solver and requested budget changing", () => {
  const c = new ClawComparison(mj);
  try {
    prepare(c);
    const original = c.reference.checkpoint();
    assert.notEqual(original.physics[0], 0);
    c.start(20);
    for (const task of c.tasks) {
      assert.deepEqual(task.checkpoint().physics, original.physics);
      assert.equal(task.attempts, 1);
      const opt = task.model.opt;
      assert.equal(opt.iterations, 20);
      assert.equal(opt.cone, mj.mjtCone.mjCONE_ELLIPTIC.value);
      assert.equal(opt.integrator, mj.mjtIntegrator.mjINT_IMPLICITFAST.value);
      assert.equal(opt.timestep, 0.002);
      assert.equal(opt.tolerance, 1e-8);
      opt.delete();
    }
    const selectors = c.tasks.map((task) => {
      const o = task.model.opt;
      const v = o.solver;
      o.delete();
      return v;
    });
    assert.equal(new Set(selectors).size, 3);
    c.togglePlayback();
    const frozen = c.tasks.map((task) => task.checkpoint());
    c.step();
    assert.deepEqual(
      c.tasks.map((task) => task.checkpoint()),
      frozen,
    );
    c.start(5); // Repeated drop cannot restart a running attempt.
    assert.equal(c.iterations, 20);
  } finally {
    c.dispose();
  }
});
test("native grabs stay synchronized; replay is read-only and original-state repetition reproduces outcomes", () => {
  const c = new ClawComparison(mj);
  try {
    prepare(c);
    c.start(60);
    finish(c);
    const end = c.tasks.map((task) => task.checkpoint());
    const frames = c.frames.map((frame) =>
      frame.worlds.map((world) => Array.from(world.bodyPosition)),
    );
    assert.ok(c.reference.roundWon > 0);
    assert.ok(
      c.current.worlds.every(
        (world) => world.meanStepMs > 0 && world.meanIterations > 0,
      ),
    );
    c.seek(0);
    assert.equal(c.current.time, 0);
    c.togglePlayback();
    for (let i = 0; i < 30; i++) c.step();
    assert.ok(c.cursor > 0);
    assert.deepEqual(
      c.tasks.map((task) => task.checkpoint()),
      end,
    );
    c.start(60, true);
    finish(c);
    assert.deepEqual(
      c.tasks.map((task) => task.checkpoint()),
      end,
    );
    assert.deepEqual(
      c.frames.map((frame) =>
        frame.worlds.map((world) => Array.from(world.bodyPosition)),
      ),
      frames,
    );
    c.aim();
    assert.equal(c.started, false);
    assert.equal(c.reference.phase, "aim");
    assert.deepEqual([...c.reference.won], end[0].won);
    assert.equal(c.frames.length, 0);
  } finally {
    c.dispose();
  }
});
test("empty-space comparisons do not award prizes; reset clears replay and retained start", () => {
  const c = new ClawComparison(mj);
  try {
    prepare(c, true);
    c.start(5);
    finish(c);
    assert.ok(
      c.tasks.every((task) => task.roundWon === 0 && task.won.size === 0),
    );
    c.reset(1);
    assert.equal(c.firstDifference, null);
    assert.equal(c.started, false);
    assert.equal(c.frames.length, 0);
    c.start(60, true);
    assert.equal(c.started, false);
    assert.ok(
      c.tasks.every((task) => task.data.time === 0 && task.attempts === 0),
    );
    assert.throws(() => c.start(NaN), /Invalid iteration/);
  } finally {
    c.dispose();
  }
});
