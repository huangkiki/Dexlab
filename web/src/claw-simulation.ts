import type { ClawFrame, ComparisonFrame } from "./claw-comparison";
import type { MoveAxis } from "./claw-task";

export interface ClawModelView {
  ngeom: number;
  geom_bodyid: Int32Array;
  geom_size: Float64Array;
  geom_type: Int32Array;
  toyBodies: number[];
  clawParts: number[];
  hub: number;
}
export interface ClawSimulationState {
  started: boolean;
  complete: boolean;
  paused: boolean;
  cursor: number;
  frameCount: number;
  firstDifference: number | null;
  current: ComparisonFrame | undefined;
  reference: ClawFrame;
  surfaceHeight: number;
}
export type ClawCommand =
  | { type: "tick"; elapsed: number; speed: number; x: number; y: number }
  | { type: "move"; axis: MoveAxis; distance: number }
  | { type: "start"; iterations: number; repeat: boolean }
  | { type: "reset"; layout: number }
  | { type: "seek"; frame: number }
  | { type: "aim" | "play" };

/** Native worlds and replay remain in one worker; only display poses cross this seam. */
export class ClawSimulation {
  state!: ClawSimulationState;
  model!: ClawModelView;
  private pending = false;
  private disposed = false;
  private worker = new Worker(new URL("./claw-worker.ts", import.meta.url), { type: "module" });
  private constructor() {}

  static create(onState: () => void, onError: (error: unknown) => void) {
    const simulation = new ClawSimulation();
    return new Promise<ClawSimulation>((resolve, reject) => {
      let ready = false;
      const fail = (error: unknown) => {
        simulation.dispose();
        if (ready) onError(error); else reject(error);
      };
      simulation.worker.onerror = (event) => fail(new Error(event.message));
      simulation.worker.onmessage = ({ data }) => {
        try {
          if (data.error) throw new Error(data.error);
          simulation.state = data.state;
          if (data.model) simulation.model = data.model;
          if (data.tick) simulation.pending = false;
          if (!ready) { ready = true; resolve(simulation); }
          else onState();
        } catch (error) { fail(error); }
      };
    });
  }
  advance(elapsed: number, speed: number, x: number, y: number) {
    if (this.pending || this.disposed) return false;
    this.pending = true;
    this.send({ type: "tick", elapsed, speed, x, y });
    return true;
  }
  send(command: ClawCommand) { if (!this.disposed) this.worker.postMessage(command); }
  dispose() {
    this.disposed = true;
    this.worker.onmessage = this.worker.onerror = null;
    this.worker.terminate();
  }
}
