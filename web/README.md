# DexLab browser claw machine

Move with arrow keys / WASD or the on-screen D-pad, then press Space or **Drop claw**. The three-finger claw descends, closes, lifts, carries to the gold chute and releases. A toy counts after it actually lands in the bin. Use top view to aim, try again after a miss, or reset the cabinet to reshuffle its six characters. Everything runs locally; there are no payments or accounts.

## Physics and scoring

MuJoCo 3.17 WASM owns the state. Three carriage slide joints and three radial finger slides are driven by position actuators; each finger has a connected radial guide, joint, curved capsule segments and an inward-facing tip. A visible trolley and cable suspend the hub. The six Nai-family characters (frog, mouse, bean, chicken, cat and rabbit) are textured meshes generated locally with Microsoft's TRELLIS image-to-3D model from the generated character art. Their visible meshes follow MuJoCo body positions and orientations. CoACD convex parts derived from those same meshes provide approximate rigid collision geometry, including the ears and tails. Each toy has a synthetic total mass of 80 g; part masses follow hull volume, with 60% foot ballast on frog and chicken to stabilize their generated soles. These are not measured material or inertia values. The floor has a physical opening with a 300 mm deep collection bin, sized to hold all six toys without changing scoring thresholds.

Contact uses synthetic friction 0.9, `condim=4`, Newton / elliptic, implicitfast and a 2 ms timestep. There is no attachment, weld, in-round object-state injection, probability roll or guaranteed catch. The automatic sequence changes actuator targets only. Toy centers must settle inside the bin's inner scoring area (within 40 mm of its center), below −70 mm, with speed under 40 mm/s for 0.3 simulated seconds. Each toy scores once. This game is not a calibrated robot, deformable-plush simulation or frozen native benchmark result.

## Develop and verify

```bash
npm ci
npm test
npm run build
npm run dev
```

Open `http://localhost:5173/lab/`; add `?lang=en` for English. Tests execute the real WASM engine: a centered catch, release-before-score, an empty drop, idle open-claw behavior, duplicate-input rejection, reset and collecting all six toys by aiming at measured positions. The longer multi-round case also exercises contact-wrapper lifetime: both the returned vector and individual embind contact handles must be deleted.

The generated character atlas and individual image-to-3D inputs follow the user-provided Nai-family reference. The atlas is used for collection thumbnails; gameplay renders the actual textured GLBs. Inputs, prompts, model revision, export parameters and collider provenance are recorded in `src/assets/README.md` and `src/assets/nai/`. Meshes are generated offline; the browser only loads finished assets and never downloads or runs the generation model. Plush appearance does not imply soft-body simulation.

The state/controller/scorer is in `src/claw-task.ts`, rendering in `src/claw-lab.ts`, and bilingual controls in `src/claw-page.ts`. The scene pauses when hidden and preserves resources across BFCache navigation. A static loading/reload state appears before heavy imports; the docs parent accepts frame height messages only from its own same-origin lab frame.

`?mode=solver&embed=1` preserves the existing solver-configuration comparison. The claw machine uses WebGL; the older comparison retains WebGPU with a WebGL fallback. Browser scores are not written into the native experiment catalog.

## Interaction reference

The aim/drop/return/prize-loop interaction was informed by [neciszhang/claw3d](https://github.com/neciszhang/claw3d/tree/02d5c53d0175e0018d791a7e89e5c45cf12b51f4). Source inspection of its [GrabController](https://github.com/neciszhang/claw3d/blob/02d5c53d0175e0018d791a7e89e5c45cf12b51f4/src/game/GrabController.tsx) on 2026-11-02 found that caught toys switch to kinematic following, with randomized slipping and a pity mechanic. DexLab implements its own MuJoCo contact path and does not adopt those mechanisms or copy code/models. The reference's live demo was not successfully runtime-verified in this session.
