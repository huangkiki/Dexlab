# Browser experiment ports

The web catalogue includes every experiment currently presented by DexLab. This
document separates a browser entry from a live local port so the site never
implies that recorded evidence was rerun in the browser.

## Status

| Experiment | Browser entry | Live portability | Next step |
| --- | --- | --- | --- |
| Analytical incline / solver comparison | Live | MuJoCo WASM and Three.js WebGPU | Add contact-model and timestep presets |
| Contact plane / indent | Recorded | MuJoCo WASM | Reuse the solver bridge and add force probes |
| Fixture pinch / force limit | Recorded | MuJoCo WASM | Add actuator controls and contact-force overlays |
| Wuji sphere hold / unload / release | Recorded | MuJoCo WASM, subject to asset compatibility | Package the Wuji asset and verify SDF support |
| Apple-stem SDF grasp | Recorded | MuJoCo WASM after a browser-safe asset package | Check mesh/SDF plugins and asset license |
| RSS wiping | Recorded | MuJoCo scene requires Isaac assets and latch controls | Extract a minimal browser fixture |
| Cloth benchmark | Recorded | MuJoCo flex/WASM uncertain | Add one extension scene and reject unsupported cases |
| Robot cloth grasp | Recorded | Needs robot and flex assets | Build a reduced browser scene before claiming parity |
| Cutting / pushing | Recorded | CPU TLMPM, not ported to WASM | Keep recorded entry until a browser backend exists |
| LIBERO replay | Recorded | LIBERO runtime is too large for the first web slice | Preserve recorded states; add a compact replay viewer |
| G1 landing | Recorded | MuJoCo Warp/Isaac Lab native path | Keep native evidence; web entry remains recorded |

## Porting order

1. Generalize the current MuJoCo session into reusable scene and metric adapters.
2. Add contact-plane and pinch scenes with identical solver variants.
3. Package Wuji assets and verify the exact web/native differences.
4. Add recorded-state viewers for experiments that cannot run in WASM.
5. Only then consider a companion worker for PhysX, Drake or Warp.

## Equivalence rule

A live browser run is a new execution. It must report its own runtime and cannot
inherit a frozen native result unless source, assets, solver settings and
independent scoring are shown to match under the repository's existing evidence
rules.
