# Native PhysX SDF contact controls

[English](sdf.md) | [简体中文](sdf.zh-CN.md)

These UniSim Isaac Sim experiments test whether native mesh-backed SDF collision preserves a concave hole and generates support. Official PhysX and IsaacLab are unchanged; DexLab supplies a disclosed UniSim 1.7.10 adapter patch. **This is not a successful PhysX apple-grasp report.**

## Translation and approximations

Isaac Sim's MJCF importer omits `type="sdf"` geometry. The adapter preserves per-geom SDF intent, transports its surface as mesh in a temporary sibling XML, then authors and reads back the official `PhysxSDFMeshCollisionAPI`. Ordinary meshes retain their existing convex approximation. Artifact identities include the transport version, per-geom intent and SDF parameters; missing native APIs, changed approximations or wrong resolutions abort initialization.

SDF resolution is 256 across the longest bounding-box extent, with sparse subgrid resolution 6. Distances are resampled from the triangle surface, not copied from MuJoCo octrees or SuperDex fields. Source geometry, mesh resolution, SDF resolution and contact solving are separate approximation choices. Plugin SDFs without a mesh are unsupported.

## Frozen experiments

| Item | Configuration and source |
|---|---|
| Torus | Major radius 30 mm, tube radius 8 mm; 96×32 surface samples; fixed rigid body |
| Sphere | Radius 8 mm, mass 20 g; subdivision-4 icosphere; analytic solid-sphere inertia approximation |
| Contact | Friction 0.5; contact offset 0.1 mm, rest offset 0; engineering settings without material calibration |
| Computation | 350 steps at 1 ms; TGS position/velocity iterations 8/2; external forces every position iteration |
| Measurements | Actual body positions, velocities and pair normal contact force; no tangential-friction measurement claim |

All three cases use the same source torus and sphere. `sdf-hole` drops the sphere through the hole; `sdf-surface` starts it above the tube; `convex-hole` changes only the torus to an ordinary convex mesh to expose the filled hole. Bodies evolve under forces, without recorded-pose playback. The 0.35 s protocol qualifies short contact behavior, not long-duration grasp robustness.

```bash
# Optional PhysX installation is separate from the base environment/download
bash scripts/setup_physx.sh
.venv/bin/python -m dexlab.physx_sdf run --case sdf-hole --output demos/physx-contact/runs/my-sdf-hole
.venv/bin/python -m dexlab.physx_sdf run --case sdf-surface --output demos/physx-contact/runs/my-sdf-surface
.venv/bin/python -m dexlab.physx_sdf run --case convex-hole --output demos/physx-contact/runs/my-convex-hole
# Independent offline scoring; no native engine required
.venv/bin/python -m dexlab.physx_sdf verify demos/physx-contact/runs/my-sdf-hole
```

New output directories retain scenes, raw arrays, native readback, source snapshots and failed logs. Failed verification returns nonzero. Set `UNISIM_ISAACSIM_HOME` to reuse a dedicated worker; the adapter installs only into the current DexLab host environment.

## Results and failures

The SDF hole and surface-support controls pass. The convex control blocks the hole but moves laterally, failing the unchanged 5 mm/s speed limit. Smaller contact offsets and a refined sphere surface did not eliminate that failure. The [evidence index](evidence/sdf-v1/index.json) lists every record, including earlier failed configurations and invalid import attempts; do not count only passing cases.

The complete 54-joint OpenArm/Wuji model now imports both right-hand SDF pads with native readback. This check runs only 20 steps with gravity disabled and no apple/contact load. It repairs the missing-pad import route, not the full PhysX grasp. Collision filtering, loaded robot control, apple contact and complete independent acceptance remain under [Issue #5](https://github.com/huangkiki/Dexlab/issues/5).

Reference: [official SDF collision API](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/rigid_bodies_articulations/collision.html#create-an-sdf-collider).
