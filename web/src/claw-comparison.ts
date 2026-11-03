import type { MainModule } from "@mujoco/mujoco";
import {
  CLAW_SOLVERS,
  ClawTask,
  STEP,
  TOYS,
  type ClawCheckpoint,
  type ClawSnapshot,
} from "./claw-task.ts";

export const RECORD_STEPS = 10; // 50 Hz display replay; physics remains 500 Hz.
export interface ClawFrame {
  geomPosition: Float32Array;
  geomMatrix: Float32Array;
  bodyPosition: Float32Array;
  bodyQuaternion: Float32Array;
  snapshot: ClawSnapshot;
  liftMm: number;
  meanStepMs: number;
  meanIterations: number;
}
export interface ComparisonFrame {
  time: number;
  worlds: ClawFrame[];
  spreadMm: number;
}

/** One complete start state, three native worlds, one simulation clock. */
export class ClawComparison {
  readonly tasks: ClawTask[] = [];
  frames: ComparisonFrame[] = [];
  started = false;
  complete = false;
  paused = false;
  cursor = 0;
  firstDifference: number | null = null;
  iterations = 60;
  private initial: ClawCheckpoint | null = null;
  private steps = 0;
  private playbackSteps = 0;
  private totals = CLAW_SOLVERS.map(() => ({ ms: 0, iterations: 0, lift: 0 }));
  private initialHeights: number[] = [];

  constructor(module: MainModule) {
    try {
      for (const solver of CLAW_SOLVERS)
        this.tasks.push(new ClawTask(module, solver));
    } catch (error) {
      this.dispose();
      throw error;
    }
  }
  get reference() {
    return this.tasks[0]!;
  }
  get current() {
    return this.frames[this.cursor];
  }

  start(iterations: number, repeat = false) {
    if (this.started && !this.complete) return;
    if (!repeat) {
      if (
        this.reference.phase !== "aim" ||
        this.reference.won.size === TOYS.length
      )
        return;
      this.initial = this.reference.checkpoint();
    }
    if (!this.initial) return;
    // Validate before touching any world.
    if (!Number.isInteger(iterations) || iterations < 1 || iterations > 100)
      throw new Error("Invalid iteration limit");
    for (const task of this.tasks) {
      task.setIterations(iterations);
      task.restore(this.initial);
      task.drop();
    }
    this.iterations = iterations;
    this.initialHeights = TOYS.map((_, i) => this.reference.position(i).z);
    this.totals = CLAW_SOLVERS.map(() => ({ ms: 0, iterations: 0, lift: 0 }));
    this.frames = [];
    this.steps = this.cursor = this.playbackSteps = 0;
    this.firstDifference = null;
    this.started = true;
    this.complete = this.paused = false;
    this.record();
  }

  step() {
    if (!this.started || this.paused) return;
    if (this.complete) {
      if (++this.playbackSteps >= RECORD_STEPS) {
        this.playbackSteps = 0;
        this.cursor = Math.min(this.cursor + 1, this.frames.length - 1);
        if (this.cursor === this.frames.length - 1) this.paused = true;
      }
      return;
    }
    // Rotate execution order to avoid always timing the same solver first.
    for (let offset = 0; offset < this.tasks.length; offset++) {
      const i = (this.steps + offset) % this.tasks.length;
      const task = this.tasks[i]!;
      task.step();
      const total = this.totals[i]!;
      total.ms += task.stepMs;
      total.iterations += Math.max(
        0,
        ...(Array.from(task.data.solver_niter) as number[]),
      );
      for (let toy = 0; toy < TOYS.length; toy++) {
        if (!this.initial!.won.includes(toy))
          total.lift = Math.max(
            total.lift,
            (task.position(toy).z - this.initialHeights[toy]!) * 1000,
          );
      }
    }
    this.steps++;
    this.complete = this.tasks.every((task) => task.phase === "result");
    if (this.steps % RECORD_STEPS === 0 || this.complete) this.record();
    if (this.complete) this.paused = true;
    if (this.steps > 15000)
      throw new Error("Claw comparison exceeded its 30 s simulation limit");
  }

  private record() {
    let spreadMm = 0;
    for (let toy = 0; toy < TOYS.length; toy++) {
      if (this.initial!.won.includes(toy)) continue;
      for (let a = 0; a < this.tasks.length; a++) {
        const p = this.tasks[a]!.position(toy);
        for (let b = a + 1; b < this.tasks.length; b++) {
          const q = this.tasks[b]!.position(toy);
          spreadMm = Math.max(
            spreadMm,
            Math.hypot(p.x - q.x, p.y - q.y, p.z - q.z) * 1000,
          );
        }
      }
    }
    this.frames.push({
      time: this.steps * STEP,
      spreadMm,
      worlds: this.tasks.map((task, i) => ({
        geomPosition: new Float32Array(task.data.geom_xpos),
        geomMatrix: new Float32Array(task.data.geom_xmat),
        bodyPosition: new Float32Array(task.data.xpos),
        bodyQuaternion: new Float32Array(task.data.xquat),
        snapshot: task.snapshot(),
        liftMm: this.totals[i]!.lift,
        meanStepMs: this.steps ? this.totals[i]!.ms / this.steps : 0,
        meanIterations: this.steps
          ? this.totals[i]!.iterations / this.steps
          : 0,
      })),
    });
    this.cursor = this.frames.length - 1;
    if (spreadMm > 1 && this.firstDifference === null)
      this.firstDifference = this.cursor;
  }

  seek(index: number) {
    if (!this.complete || !Number.isFinite(index)) return;
    this.cursor = Math.max(
      0,
      Math.min(Math.round(index), this.frames.length - 1),
    );
    this.playbackSteps = 0;
    this.paused = true;
  }
  togglePlayback() {
    if (!this.started) return;
    if (this.complete && this.cursor === this.frames.length - 1)
      this.cursor = 0;
    this.paused = !this.paused;
  }
  aim() {
    if (!this.complete) return;
    // Continue the Newton cabinet, never a replay pose or a hidden winning world.
    this.reference.retry();
    this.reference.setIterations(60);
    this.clear();
  }
  reset(layout: number) {
    for (const task of this.tasks) {
      task.setIterations(60);
      task.reset(layout);
    }
    this.clear();
  }
  private clear() {
    this.initial = null;
    this.frames = [];
    this.started = this.complete = this.paused = false;
    this.firstDifference = null;
    this.cursor = 0;
  }
  dispose() {
    for (const task of this.tasks) task.dispose();
  }
}
