# DexLab browser claw machine

[English](README.md) | [简体中文：本次对比](#同一次下爪对比求解器)

Move with arrow keys / WASD or the on-screen D-pad, then press Space or **Drop claw**. The three-finger claw descends, closes, lifts, carries to the gold chute and releases. A toy counts after it actually lands in the bin. Use top view to aim, try again after a miss, or reset the cabinet to reshuffle its six characters. Everything runs locally; there are no payments or accounts.

## Compare the same grab

At drop, three independent native worlds receive the complete MuJoCo integration state plus controller/scoring state. They use identical actuator targets, a common simulation clock, elliptic friction, implicitfast, 2 ms steps and a 1e-8 stopping tolerance. Only the solver differs; the common iteration cap is selectable (5, 20, 60, 100). The camera is shared. Scenes appear side by side on wider canvases and stack below 700 px.

Pause or slow the run. After completion, scrub the shared 50 Hz pose recording or jump to the first sampled toy-position spread above 1 mm. This threshold locates a visible difference; it is not an error criterion. Replay only changes displayed poses, never the scored physics state. **Repeat this grab** restores the original drop state with the selected budget; **Re-aim** continues the Newton cabinet. Reset discards the recording. A 30 s simulation cap bounds each round.

Each view reports its own settled-bin outcome, peak toy-height gain from the initial drop state, mean native `mj_step` time and mean of each step’s maximum solver iterations across constraint islands. Timing excludes rendering and controller/scoring work, but includes the whole physics step; it is local observational timing, not isolated solver cost or a speed ranking. Agreement is valid, and catching a toy does not establish physical accuracy. The bilingual guide distinguishes contact solvers from explicit, semi-implicit and implicit integration, including MuJoCo-specific `Euler` and `implicitfast` behavior.

## 同一次下爪对比求解器

瞄准后按下爪，Newton、非线性 CG、PGS 三个原生世界复制同一份完整积分状态、控制与计分状态，使用同一指令和仿真时间。三路统一为 elliptic 摩擦锥、implicitfast、2 ms 步长、1e-8 停止容差，可共同选择 5、20、60、100 次迭代上限。宽画面并排展示，画布不足 700 px 时上下排列；视角保持一致。

可以暂停、慢放，结束后拖动 50 Hz 回放或跳到首次玩偶位置差超过 1 mm 的记录；1 mm 只是定位标记，不是误差判据。回放不修改计分状态。「原局重试」恢复下爪起点并采用所选上限；「重新瞄准」继续 Newton 那一柜；重置会清除记录，每轮最多计算 30 秒仿真时间。

各路独立显示入盒结果、相对起点的最大玩偶抬升、原生 `mj_step` 平均耗时，以及每步各约束岛最大迭代次数的平均值。耗时不含渲染和控制/计分代码，但包含整个物理步，不是单独求解器耗时或性能排名。结果一致也是有效观察，抓到不等于更准确。中英文解释区分清接触求解器与显式、半隐式、隐式积分，并说明 MuJoCo 的 Euler 和 implicitfast 不可只按名字理解。

## Physics and scoring

MuJoCo 3.17 WASM owns the state. Three carriage slide joints and three radial finger slides are driven by position actuators; each finger has a connected radial guide, joint, curved capsule segments and an inward-facing tip. A visible trolley and cable suspend the hub. The six Nai-family characters (frog, mouse, bean, chicken, cat and rabbit) are textured meshes generated locally with Microsoft's TRELLIS image-to-3D model from the generated character art. Their visible meshes follow MuJoCo body positions and orientations. CoACD convex parts derived from those same meshes provide approximate rigid collision geometry, including the ears and tails. Each toy has a synthetic total mass of 80 g; part masses follow hull volume, with 60% foot ballast on frog and chicken to stabilize their generated soles. These are not measured material or inertia values. The floor has a physical opening with a 300 mm deep collection bin, sized to hold all six toys without changing scoring thresholds.

Contact uses synthetic friction 0.9, `condim=4`, Newton, nonlinear CG and PGS with a common elliptic cone, implicitfast and a 2 ms timestep. There is no attachment, weld, in-round object-state injection, probability roll or guaranteed catch. The automatic sequence changes actuator targets only. Toy centers must settle inside the bin's inner scoring area (within 40 mm of its center), below −70 mm, with speed under 40 mm/s for 0.3 simulated seconds. Each toy scores once. This game is not a calibrated robot, deformable-plush simulation or frozen native benchmark result.

## Develop and verify

```bash
npm ci
npm test
npm run build
npm run dev
```

Open `http://localhost:5173/lab/`; add `?lang=en` for English. Tests also check complete start-state equality, matched commands and time across solvers, repeatable trajectories, replay isolation, original-state retries and clearing on reset. Tests execute the real WASM engine: a centered catch, release-before-score, an empty drop, idle open-claw behavior, duplicate-input rejection, reset and collecting all six toys by aiming at measured positions. The longer multi-round case also exercises contact-wrapper lifetime: both the returned vector and individual embind contact handles must be deleted.

The generated character atlas and individual image-to-3D inputs follow the user-provided Nai-family reference. The atlas is used for collection thumbnails; gameplay renders the actual textured GLBs. Inputs, prompts, model revision, export parameters and collider provenance are recorded in `src/assets/README.md` and `src/assets/nai/`. Meshes are generated offline; the browser only loads finished assets and never downloads or runs the generation model. Plush appearance does not imply soft-body simulation.

The state/controller/scorer is in `src/claw-task.ts`, comparison/recording in `src/claw-comparison.ts`, bilingual teaching copy in `src/claw-explainer.ts`, rendering in `src/claw-lab.ts`, and bilingual controls in `src/claw-page.ts`. The scene pauses when hidden and preserves resources across BFCache navigation. A static loading/reload state appears before heavy imports; the docs parent accepts frame height messages only from its own same-origin lab frame.

`?mode=solver&embed=1` preserves the existing solver-configuration comparison. The claw machine uses WebGL; the older comparison retains WebGPU with a WebGL fallback. Browser scores are not written into the native experiment catalog.

## Interaction reference

The aim/drop/return/prize-loop interaction was informed by [neciszhang/claw3d](https://github.com/neciszhang/claw3d/tree/02d5c53d0175e0018d791a7e89e5c45cf12b51f4). Source inspection of its [GrabController](https://github.com/neciszhang/claw3d/blob/02d5c53d0175e0018d791a7e89e5c45cf12b51f4/src/game/GrabController.tsx) on 2026-11-02 found that caught toys switch to kinematic following, with randomized slipping and a pity mechanic. DexLab implements its own MuJoCo contact path and does not adopt those mechanisms or copy code/models. The reference's live demo was not successfully runtime-verified in this session.
