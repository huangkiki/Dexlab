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
function runRound(task, index = 28) {
  let highest = 0,
    contacts = 0,
    scoredBeforeRelease = false;
  for (let i = 0; i < 15000 && task.phase !== "result"; i++) {
    task.step();
    highest = Math.max(highest, task.position(index).z);
    contacts = Math.max(contacts, task.fingerContacts());
    if (
      ["descend", "close", "lift", "carry"].includes(task.phase) &&
      task.won.size > 0
    )
      scoredBeforeRelease = true;
  }
  return { highest, contacts, scoredBeforeRelease };
}
test("a native grab lifts the exposed cat from the pile and carries it into the actual bin", () => {
  const task = new ClawTask(mj);
  try {
    task.reset(29); // Fixed exposed-cat positive control; buried targets may miss.
    for (let i = 0; i < 1500; i++) task.step();
    const target = task.position(28);
    task.move("x", target.x - task.target.x);
    task.move("y", target.y - task.target.y);
    for (let i = 0; i < 250; i++) task.step();
    task.drop();
    const trace = runRound(task);
    assert.ok(
      trace.highest > 0.3,
      JSON.stringify({ trace, s: task.snapshot(), p: task.position(28) }),
    );
    assert.equal(trace.scoredBeforeRelease, false);
    assert.equal(task.phase, "result");
    assert.equal(
      task.won.has(28),
      true,
      JSON.stringify({ trace, s: task.snapshot(), p: task.position(28) }),
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
    task.move("x", BIN.x - task.target.x);
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
    assert.ok(task.position(28).z < 0.25);
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
