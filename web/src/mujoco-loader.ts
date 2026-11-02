import loadMujoco from "@mujoco/mujoco";
import mujocoWasmUrl from "@mujoco/mujoco/mujoco.wasm?url";

/** Explicit bytes avoid the streaming-instantiation path in embedded pages. */
export async function loadPhysics() {
  const response = await fetch(mujocoWasmUrl, {
    signal: AbortSignal.timeout(30000),
  });
  if (!response.ok) throw new Error(`MuJoCo download: HTTP ${response.status}`);
  const wasmBinary = await response.arrayBuffer();
  return loadMujoco({ wasmBinary });
}
