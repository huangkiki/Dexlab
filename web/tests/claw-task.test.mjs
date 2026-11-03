import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import loadMujoco from "@mujoco/mujoco";
import { ClawTask, TOYS, STEP, BIN } from "../src/claw-task.ts";
const mj = await loadMujoco({
  wasmBinary: await readFile(
    fileURLToPath(import.meta.resolve("@mujoco/mujoco/mujoco.wasm")),
  ),
});
function runRound(task) {
  let highest = 0,
    contacts = 0,
    scoredBeforeRelease = false;
  for (let i = 0; i < 15000 && task.phase !== "result"; i++) {
    task.step();
    highest = Math.max(highest, task.position(0).z);
    contacts = Math.max(contacts, task.fingerContacts());
    if (
      ["descend", "close", "lift", "carry"].includes(task.phase) &&
      task.won.size > 0
    )
      scoredBeforeRelease = true;
  }
  return { highest, contacts, scoredBeforeRelease };
}
test("centered native three-finger grab carries a toy into the actual bin", () => {
  const task = new ClawTask(mj);
  try {
    task.move("x", TOYS[0].x - task.target.x);
    task.move("y", TOYS[0].y - task.target.y);
    for (let i = 0; i < 250; i++) task.step();
    task.drop();
    const trace = runRound(task);
    assert.ok(
      trace.highest > 0.1,
      JSON.stringify({ trace, s: task.snapshot(), p: task.position(0) }),
    );
    assert.equal(trace.scoredBeforeRelease, false);
    assert.equal(task.phase, "result");
    assert.equal(
      task.won.has(0),
      true,
      JSON.stringify({ trace, s: task.snapshot(), p: task.position(0) }),
    );
    assert.equal(task.roundWon, 1);
    task.retry();
    assert.equal(task.phase, "aim");
    task.reset();
    assert.equal(task.won.size, 0);
    assert.equal(task.attempts, 0);
    assert.equal(task.data.time, 0);
  } finally {
    task.dispose();
  }
});
test("dropping in empty space finishes without awarding a prize", () => {
  const task = new ClawTask(mj);
  try {
    task.move("x", BIN.x);
    task.move("y", BIN.y - task.target.y);
    for (let i = 0; i < 250; i++) task.step();
    task.drop();
    runRound(task);
    assert.equal(task.phase, "result");
    assert.equal(task.won.size, 0);
    assert.equal(task.roundWon, 0);
  } finally {
    task.dispose();
  }
});
test("idle open claw never lifts or awards toys and repeated drop cannot restart a round", () => {
  const task = new ClawTask(mj);
  try {
    for (let i = 0; i < 2000; i++) task.step();
    assert.equal(task.won.size, 0);
    assert.ok(task.position(0).z < 0.04);
    task.drop();
    task.drop();
    assert.equal(task.attempts, 1);
    const x = task.target.x;
    task.move("x", 0.1);
    assert.equal(task.target.x, x);
  } finally {
    task.dispose();
  }
});

test("all sixteen toys can be collected by re-aiming at their measured positions", () => {
  const task = new ClawTask(mj);
  try {
    for (let i = 0; i < 500; i++) task.step();
    for (let i = 0; i < TOYS.length; i++) {
      const p = task.position(i);
      task.move("x", p.x - task.target.x);
      task.move("y", p.y - task.target.y);
      for (let j = 0; j < 250; j++) task.step();
      task.drop();
      runRound(task);
      assert.equal(
        task.won.has(i),
        true,
        JSON.stringify({ i, s: task.snapshot(), p: task.position(i) }),
      );
      task.retry();
    }
    assert.equal(task.won.size, TOYS.length);
  } finally {
    task.dispose();
  }
});
