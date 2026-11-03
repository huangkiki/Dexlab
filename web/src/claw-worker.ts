import { ClawComparison } from "./claw-comparison";
import { loadPhysics } from "./mujoco-loader";
import { STEP } from "./claw-task";
import type { ClawFrame } from "./claw-comparison";
import type { ClawCommand, ClawModelView, ClawSimulationState } from "./claw-simulation";

let comparison: ClawComparison;
let accumulator = 0;

function publish(tick = false, model?: ClawModelView) {
  const task = comparison.reference;
  const reference: ClawFrame = {
    geomPosition: new Float32Array(task.data.geom_xpos),
    geomMatrix: new Float32Array(task.data.geom_xmat),
    bodyPosition: new Float32Array(task.data.xpos),
    bodyQuaternion: new Float32Array(task.data.xquat),
    snapshot: task.snapshot(), liftMm: 0, meanStepMs: task.stepMs, meanIterations: 0,
  };
  const state: ClawSimulationState = {
    started: comparison.started, complete: comparison.complete, paused: comparison.paused,
    cursor: comparison.cursor, frameCount: comparison.frames.length,
    firstDifference: comparison.firstDifference, current: comparison.current, reference,
    surfaceHeight: comparison.started ? 0 : task.surfaceHeight(
      reference.geomPosition[task.hub * 3]!, reference.geomPosition[task.hub * 3 + 1]!),
  };
  // Keep replay buffers owned by the worker; structured clone never detaches the history.
  self.postMessage({ state, model, tick });
}

function handle(command: ClawCommand) {
  const task = comparison.reference;
  switch (command.type) {
    case "tick": {
      accumulator = Math.min(.05, accumulator + Math.min(.05, command.elapsed) *
        (comparison.started ? command.speed : 1));
      const deadline = performance.now() + 8;
      while (accumulator >= STEP) {
        if (comparison.started) comparison.step();
        else {
          task.move("x", command.x * .11 * STEP);
          task.move("y", command.y * .11 * STEP);
          task.step();
        }
        accumulator -= STEP;
        // Always finish a complete three-world step; yield without skipping simulation steps.
        if (performance.now() >= deadline) break;
      }
      break;
    }
    case "move": task.move(command.axis, command.distance); break;
    case "start": comparison.start(command.iterations, command.repeat); accumulator = 0; break;
    case "reset": comparison.reset(command.layout); accumulator = 0; break;
    case "aim": comparison.aim(); accumulator = 0; break;
    case "seek": comparison.seek(command.frame); accumulator = 0; break;
    case "play": comparison.togglePlayback(); accumulator = 0; break;
  }
  publish(command.type === "tick");
}

try {
  comparison = new ClawComparison(await loadPhysics());
  const task = comparison.reference, model = task.model;
  self.onmessage = (event: MessageEvent<ClawCommand>) => {
    try { handle(event.data); }
    catch (error) { self.postMessage({ error: String(error) }); }
  };
  publish(false, {
    ngeom: model.ngeom, geom_bodyid: new Int32Array(model.geom_bodyid),
    geom_size: new Float64Array(model.geom_size), geom_type: new Int32Array(model.geom_type),
    toyBodies: task.toyBodies, clawParts: task.clawParts, hub: task.hub,
  });
} catch (error) { self.postMessage({ error: String(error) }); }
