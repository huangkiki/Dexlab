import type { MainModule } from "@mujoco/mujoco";

export const STEP = 0.002;
export const HOME = { x: 0, y: -0.02, z: 0.23 };
export const BIN = { x: -0.215, y: -0.135, half: 0.06, floor: -0.3 };
import { TOYS, TOY_ASSETS, toyXml } from "./claw-toys.ts";
export { TOYS } from "./claw-toys.ts";
export type ClawPhase =
  | "aim"
  | "descend"
  | "close"
  | "lift"
  | "carry"
  | "release"
  | "return"
  | "result";
export type MoveAxis = "x" | "y";
export const CLAW_SOLVERS = ["Newton", "CG", "PGS"] as const;
export type ClawSolver = (typeof CLAW_SOLVERS)[number];
const padNames = ["pad0", "pad1", "pad2"];
const clamp = (v: number, lo: number, hi: number) =>
  Math.max(lo, Math.min(hi, v));

export function clawXml(solver: ClawSolver = "Newton") {
  const fingers = [0, 120, 240]
    .map(
      (angle, i) => `<body euler="0 0 ${angle}">
    <geom name="guide${i}" type="capsule" fromto="0.012 0 0.070 0.066 0 0.070" size="0.006" mass="0.005"/>
    <body pos="0.058 0 0"><joint name="finger${i}" type="slide" axis="-1 0 0" range="0 0.04" damping="1" armature="0.004"/>
      <geom name="joint${i}" type="sphere" pos="0 0 0.070" size="0.009" mass="0.005"/>
      <geom name="upper${i}" type="capsule" fromto="0 0 0.070 0.010 0 0.035" size="0.006" mass="0.015"/>
      <geom name="${padNames[i]}" type="capsule" fromto="0.010 0 0.035 0 0 -0.025" size="0.006" mass="0.025"/>
      <geom name="tip${i}" type="capsule" fromto="0 0 -0.025 -0.013 0 -0.031" size="0.006" mass="0.01"/>
    </body></body>`,
    )
    .join("");
  return `<mujoco model="DexLab claw machine">
    <option timestep="${STEP}" gravity="0 0 -9.81" integrator="implicitfast" solver="${solver}" cone="elliptic" iterations="60" tolerance="1e-8"/>
    <default><geom friction="0.9 0.005 0.0001" condim="4" solref="0.008 1" solimp="0.95 0.99 0.001"/></default>
    <asset>${TOY_ASSETS}</asset>
    <worldbody>
      <geom name="floor_main" type="box" pos="0.065 0 -0.012" size="0.215 0.205 0.012"/>
      <geom name="floor_back" type="box" pos="-0.215 0.0675 -0.012" size="0.065 0.1375 0.012"/>
      <geom name="floor_front" type="box" pos="-0.215 -0.2025 -0.012" size="0.065 0.0075 0.012"/>
      <geom name="bin_floor" type="box" pos="${BIN.x} ${BIN.y} ${BIN.floor - 0.01}" size="0.065 0.065 0.01"/>
      <geom name="bin_left" type="box" pos="-0.28 ${BIN.y} ${BIN.floor / 2}" size="0.006 0.07 ${-BIN.floor / 2 + 0.01}"/>
      <geom name="bin_right" type="box" pos="-0.15 ${BIN.y} ${BIN.floor / 2}" size="0.006 0.07 ${-BIN.floor / 2 + 0.01}"/>
      <geom name="bin_front" type="box" pos="${BIN.x} -0.20 ${BIN.floor / 2}" size="0.065 0.006 ${-BIN.floor / 2 + 0.01}"/>
      <geom name="bin_back" type="box" pos="${BIN.x} -0.07 ${BIN.floor / 2}" size="0.065 0.006 ${-BIN.floor / 2 + 0.01}"/>
      <geom name="wall_left" type="box" pos="-0.29 0 0.12" size="0.01 0.22 0.14"/>
      <geom name="wall_right" type="box" pos="0.29 0 0.12" size="0.01 0.22 0.14"/>
      <geom name="wall_back" type="box" pos="0 0.215 0.12" size="0.29 0.01 0.14"/>
      <geom name="wall_front" type="box" pos="0 -0.215 0.12" size="0.29 0.01 0.14"/>
      ${TOYS.map((_, i) => toyXml(i)).join("")}
      <body name="carriage">
        <joint name="x" type="slide" axis="1 0 0" range="-0.24 0.24" damping="4" armature="0.02"/>
        <joint name="y" type="slide" axis="0 1 0" range="-0.16 0.16" damping="4" armature="0.02"/>
        <joint name="z" type="slide" axis="0 0 1" range="0.035 0.25" damping="4" armature="0.02"/>
        <geom name="hub" type="cylinder" pos="0 0 0.080" size="0.026 0.016" mass="0.3"/>
        ${fingers}
      </body>
    </worldbody>
    <actuator>
      <position joint="x" kp="600" kv="35" forcerange="-25 25"/>
      <position joint="y" kp="600" kv="35" forcerange="-25 25"/>
      <position joint="z" kp="900" kv="40" forcerange="-30 30"/>
      ${[0, 1, 2].map((i) => `<position joint="finger${i}" kp="160" kv="2" forcerange="-2.5 2.5"/>`).join("")}
    </actuator>
  </mujoco>`;
}

export interface ClawSnapshot {
  phase: ClawPhase;
  closed: boolean;
  score: number;
  attempts: number;
  contacts: number;
  highestMm: number;
  won: number[];
  roundWon: number;
  target: typeof HOME;
}

export interface ClawCheckpoint {
  physics: number[];
  target: typeof HOME;
  phase: ClawPhase;
  closed: boolean;
  attempts: number;
  won: number[];
  roundWon: number;
  phaseTime: number;
  scoreAtDrop: number;
  settled: number[];
}

/** Synthetic rigid toys; all in-round motion comes from actuator forces and contact. */
export class ClawTask {
  readonly solver: ClawSolver;
  readonly model: InstanceType<MainModule["MjModel"]>;
  readonly data: InstanceType<MainModule["MjData"]>;
  readonly toyBodies: number[];
  readonly toyGeoms: number[];
  readonly clawGeoms: number[];
  readonly clawParts: number[];
  readonly hub: number;
  target = { ...HOME };
  phase: ClawPhase = "aim";
  closed = false;
  attempts = 0;
  won = new Set<number>();
  roundWon = 0;
  stepMs = 0;
  private phaseTime = 0;
  private scoreAtDrop = 0;
  private settled = TOYS.map(() => 0);
  private toyDofs: number[];
  private toyQpos: number[];
  private axisQpos: number[];
  private module: MainModule;

  constructor(module: MainModule, solver: ClawSolver = "Newton") {
    this.module = module;
    this.solver = solver;
    this.model = module.MjModel.from_xml_string(clawXml(solver));
    this.data = new module.MjData(this.model);
    const id = (kind: number, name: string) => {
      const value = module.mj_name2id(this.model, kind, name);
      if (value < 0) throw new Error(`Missing ${name}`);
      return value;
    };
    const geom = (name: string) => id(module.mjtObj.mjOBJ_GEOM.value, name);
    const joint = (name: string) => id(module.mjtObj.mjOBJ_JOINT.value, name);
    this.toyBodies = TOYS.map((_, i) =>
      id(module.mjtObj.mjOBJ_BODY.value, `toy${i}`),
    );
    this.toyGeoms = TOYS.map((_, i) => geom(`toy_geom${i}`));
    this.toyDofs = TOYS.map(
      (_, i) => this.model.jnt_dofadr[joint(`toy_joint${i}`)],
    );
    this.toyQpos = TOYS.map(
      (_, i) => this.model.jnt_qposadr[joint(`toy_joint${i}`)],
    );
    this.axisQpos = ["x", "y", "z"].map(
      (name) => this.model.jnt_qposadr[joint(name)],
    );
    this.clawGeoms = [0, 1, 2].flatMap((i) => [
      geom(`upper${i}`),
      geom(`pad${i}`),
      geom(`tip${i}`),
    ]);
    this.hub = geom("hub");
    this.clawParts = [
      this.hub,
      ...this.clawGeoms,
      ...[0, 1, 2].flatMap((i) => [geom(`guide${i}`), geom(`joint${i}`)]),
    ];
    this.reset();
  }

  checkpoint(): ClawCheckpoint {
    const spec = this.module.mjtState.mjSTATE_INTEGRATION.value;
    const buffer = new this.module.DoubleBuffer(
      this.module.mj_stateSize(this.model, spec),
    );
    try {
      this.module.mj_getState(this.model, this.data, buffer, spec);
      return {
        physics: Array.from(buffer.GetView()),
        target: { ...this.target },
        phase: this.phase,
        closed: this.closed,
        attempts: this.attempts,
        won: [...this.won],
        roundWon: this.roundWon,
        phaseTime: this.phaseTime,
        scoreAtDrop: this.scoreAtDrop,
        settled: [...this.settled],
      };
    } finally {
      buffer.delete();
    }
  }

  restore(state: ClawCheckpoint) {
    this.module.mj_setState(
      this.model,
      this.data,
      state.physics,
      this.module.mjtState.mjSTATE_INTEGRATION.value,
    );
    this.target = { ...state.target };
    this.phase = state.phase;
    this.closed = state.closed;
    this.attempts = state.attempts;
    this.won = new Set(state.won);
    this.roundWon = state.roundWon;
    this.phaseTime = state.phaseTime;
    this.scoreAtDrop = state.scoreAtDrop;
    this.settled = [...state.settled];
    this.module.mj_forward(this.model, this.data);
  }

  setIterations(iterations: number) {
    if (!Number.isInteger(iterations) || iterations < 1 || iterations > 100)
      throw new Error("Iteration limit must be an integer between 1 and 100");
    const option = this.model.opt;
    option.iterations = iterations;
    option.delete();
  }

  reset(layout = 0) {
    this.module.mj_resetData(this.model, this.data);
    this.target = { ...HOME };
    this.phase = "aim";
    this.closed = false;
    this.attempts = 0;
    this.won.clear();
    this.roundWon = 0;
    this.phaseTime = 0;
    this.scoreAtDrop = 0;
    this.settled.fill(0);
    this.axisQpos.forEach(
      (q, i) => (this.data.qpos[q] = [HOME.x, HOME.y, HOME.z][i]),
    );
    // Scene placement changes only on an explicit new-cabinet reset.
    this.toyQpos.forEach((q, i) => {
      const slot = TOYS[(i + layout) % TOYS.length]!;
      this.data.qpos[q] = slot.x;
      this.data.qpos[q + 1] = slot.y;
    });
    this.writeControls();
    this.module.mj_forward(this.model, this.data);
  }
  move(axis: MoveAxis, distance: number) {
    if (this.phase !== "aim" || !Number.isFinite(distance)) return;
    this.target[axis] = clamp(
      this.target[axis] + distance,
      axis === "x" ? -0.235 : -0.155,
      axis === "x" ? 0.235 : 0.155,
    );
  }
  drop() {
    if (this.phase !== "aim" || this.won.size === TOYS.length) return;
    this.attempts++;
    this.scoreAtDrop = this.won.size;
    this.roundWon = 0;
    this.enter("descend");
  }
  retry() {
    if (this.phase === "result") {
      this.closed = false;
      this.enter("aim");
    }
  }
  private enter(phase: ClawPhase) {
    this.phase = phase;
    this.phaseTime = 0;
  }
  private approach(axis: "x" | "y" | "z", value: number, speed: number) {
    this.target[axis] += clamp(
      value - this.target[axis],
      -speed * STEP,
      speed * STEP,
    );
    return Math.abs(this.target[axis] - value) < 0.0001;
  }
  private writeControls() {
    [
      this.target.x,
      this.target.y,
      this.target.z,
      ...[0, 1, 2].map(() => (this.closed ? 0.04 : 0)),
    ].forEach((value, i) => (this.data.ctrl[i] = value));
  }
  position(index: number) {
    const k = this.toyBodies[index]! * 3;
    return {
      x: Number(this.data.xpos[k]),
      y: Number(this.data.xpos[k + 1]),
      z: Number(this.data.xpos[k + 2]),
    };
  }
  fingerContacts() {
    const touching = new Set<number>();
    const contacts = this.data.contact;
    for (let i = 0; i < this.data.ncon; i++) {
      const c = contacts.get(i)!;
      const a = Number(c.geom1),
        b = Number(c.geom2);
      const finger =
        this.clawGeoms.indexOf(a) >= 0
          ? a
          : this.clawGeoms.indexOf(b) >= 0
            ? b
            : -1;
      const other = finger === a ? b : a;
      if (finger >= 0 && this.toyBodies.includes(this.model.geom_bodyid[other]))
        touching.add(Math.floor(this.clawGeoms.indexOf(finger) / 3));
      c.delete();
    }
    contacts.delete();
    return touching.size;
  }
  step() {
    this.phaseTime += STEP;
    switch (this.phase) {
      case "descend":
        if (this.approach("z", 0.043, 0.09)) {
          this.closed = true;
          this.enter("close");
        }
        break;
      case "close":
        if (this.phaseTime > 0.8) this.enter("lift");
        break;
      case "lift":
        if (this.approach("z", HOME.z, 0.09)) this.enter("carry");
        break;
      case "carry": {
        const x = this.approach("x", BIN.x, 0.1),
          y = this.approach("y", BIN.y, 0.1);
        if (x && y) {
          this.closed = false;
          this.enter("release");
        }
        break;
      }
      case "release":
        if (this.phaseTime > 1.8) this.enter("return");
        break;
      case "return": {
        const x = this.approach("x", HOME.x, 0.14),
          y = this.approach("y", HOME.y, 0.14);
        if (x && y) {
          this.roundWon = this.won.size - this.scoreAtDrop;
          this.enter("result");
        }
        break;
      }
    }
    this.writeControls();
    const started = performance.now();
    this.module.mj_step(this.model, this.data);
    this.stepMs = performance.now() - started;
    for (let i = 0; i < TOYS.length; i++) {
      const p = this.position(i);
      if (!Object.values(p).every(Number.isFinite))
        throw new Error("Non-finite toy state");
      const speed = Math.hypot(
        ...(Array.from(
          this.data.qvel.slice(this.toyDofs[i], this.toyDofs[i]! + 3),
        ) as number[]),
      );
      const inBin =
        Math.abs(p.x - BIN.x) < BIN.half - 0.02 &&
        Math.abs(p.y - BIN.y) < BIN.half - 0.02 &&
        p.z < -0.07 &&
        speed < 0.04;
      this.settled[i] = inBin ? this.settled[i]! + STEP : 0;
      if (this.settled[i]! >= 0.3) this.won.add(i);
    }
  }
  snapshot(): ClawSnapshot {
    return {
      phase: this.phase,
      closed: this.closed,
      score: this.won.size,
      attempts: this.attempts,
      contacts: this.fingerContacts(),
      highestMm: Math.max(
        0,
        ...TOYS.map((_, i) =>
          this.won.has(i) ? 0 : (this.position(i).z - 0.035) * 1000,
        ),
      ),
      won: [...this.won],
      roundWon: this.roundWon,
      target: { ...this.target },
    };
  }
  dispose() {
    this.data.delete();
    this.model.delete();
  }
}
