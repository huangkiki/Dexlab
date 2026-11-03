# DexLab browser claw machine

[English](README.md) | [简体中文：本次对比](#同一次下爪对比求解器)

Move with arrow keys / WASD or the on-screen D-pad, then press Space or **Drop claw**. The three-finger claw descends, closes, lifts, carries to the gold chute and releases. A toy counts after it actually lands in the bin. Use top view to aim, try again after a miss, or reset the cabinet to reshuffle the same 30 toys, mixing all 16 characters in one cabinet. Click a portrait to inspect the real mesh up close. Everything runs locally; there are no payments or accounts.

## Compare the same grab

At drop, three independent native worlds receive the complete MuJoCo integration state plus controller/scoring state. They use identical actuator targets, a common simulation clock, elliptic friction, implicitfast, 2 ms steps and a 1e-8 stopping tolerance. Only the solver differs; the common iteration cap is selectable (5, 20, 60, 100). The camera is shared. Scenes appear side by side on wider canvases and stack below 700 px.

Pause or slow the run. After completion, scrub the shared 50 Hz pose recording or jump to the first sampled toy-position spread above 1 mm. This threshold locates a visible difference; it is not an error criterion. Replay only changes displayed poses, never the scored physics state. **Repeat this grab** restores the original drop state with the selected budget; **Re-aim** continues the Newton cabinet. Reset discards the recording. A 30 s simulation cap bounds each round.

Each view reports its own settled-bin outcome, peak toy-height gain from the initial drop state, mean native `mj_step` time and mean of each step’s maximum solver iterations across constraint islands. Timing excludes rendering and controller/scoring work, but includes the whole physics step; it is local observational timing, not isolated solver cost or a speed ranking. Agreement is valid, and catching a toy does not establish physical accuracy. The bilingual guide distinguishes contact solvers from explicit, semi-implicit and implicit integration, including MuJoCo-specific `Euler` and `implicitfast` behavior.

## 同一次下爪对比求解器

瞄准后按下爪，Newton、非线性 CG、PGS 三个原生世界复制同一份完整积分状态、控制与计分状态，使用同一指令和仿真时间。三路统一为 elliptic 摩擦锥、implicitfast、2 ms 步长、1e-8 停止容差，可共同选择 5、20、60、100 次迭代上限。宽画面并排展示，画布不足 700 px 时上下排列；视角保持一致。

可以暂停、慢放，结束后拖动 50 Hz 回放或跳到首次玩偶位置差超过 1 mm 的记录；1 mm 只是定位标记，不是误差判据。回放不修改计分状态。「原局重试」恢复下爪起点并采用所选上限；「重新瞄准」继续 Newton 那一柜；重置会清除记录，每轮最多计算 30 秒仿真时间。

各路独立显示入盒结果、相对起点的最大玩偶抬升、原生 `mj_step` 平均耗时，以及每步各约束岛最大迭代次数的平均值。耗时不含渲染和控制/计分代码，但包含整个物理步，不是单独求解器耗时或性能排名。结果一致也是有效观察，抓到不等于更准确。中英文解释区分清接触求解器与显式、半隐式、隐式积分，并说明 MuJoCo 的 Euler 和 implicitfast 不可只按名字理解。

## Physics and scoring

MuJoCo 3.17 WASM owns the state. Three carriage slide joints and three radial finger slides are driven by position actuators; each finger has a connected radial guide, joint, curved capsule segments and an inward-facing tip. A visible trolley and cable suspend the hub. The 16 Nai-family characters are textured meshes generated locally with Microsoft's TRELLIS image-to-3D model from the generated character art. Their visible meshes follow MuJoCo body positions and orientations. CoACD convex parts derived from those same meshes provide approximate rigid collision geometry, including the ears and tails. Each toy has a synthetic total mass of 80 g; part masses follow hull volume, with 60% foot ballast on frog and chicken to stabilize their generated soles. These are not measured material or inertia values. The floor has a physical opening with a 600 mm deep collection bin, with a raised lip to keep the pile clear of the delivery opening.

Contact uses synthetic friction 0.9, `condim=4`, Newton, nonlinear CG and PGS with a common elliptic cone, implicitfast and a 2 ms timestep. There is no attachment, weld, in-round object-state injection, probability roll or guaranteed catch. The automatic sequence changes actuator targets only. Toy centers must settle inside the bin's inner scoring area (within 65 mm of its center on each horizontal axis, a 20 mm inset from its walls), below −70 mm, with speed under 40 mm/s for 0.3 simulated seconds. Each toy scores once. This game is not a calibrated robot, deformable-plush simulation or frozen native benchmark result.

## Develop and verify

```bash
npm ci
npm test
npm run build
npm run dev
```

Open `http://localhost:5173/lab/`; add `?lang=en` for English. Tests also check complete start-state equality, matched commands and time across solvers, repeatable trajectories, replay isolation, original-state retries and clearing on reset. Tests execute the real WASM engine: an exposed-toy catch from the pile, release-before-score, an empty drop, idle open-claw behavior, duplicate-input rejection and reset. Three fixed arrangements check 30 settled toys, elevated bodies in mutual contact and synchronized grabs; all 30 spawn permutations are checked for initial interpenetration. This does not establish that every buried prize can be collected in one try. Native state resets are reported as failures rather than accepted as valid replay; the low-budget regression checks this boundary.

The generated character atlas and individual image-to-3D inputs follow the user-provided Nai-family reference. Individual input portraits identify each prize; gameplay renders the actual textured GLBs. Inputs, prompts, model revision, export parameters and collider provenance are recorded in `src/assets/README.md` and `src/assets/nai/`. Meshes are generated offline; the browser only loads finished assets and never downloads or runs the generation model. Plush appearance does not imply soft-body simulation.

The state/controller/scorer is in `src/claw-task.ts`, comparison/recording in `src/claw-comparison.ts`, bilingual teaching copy in `src/claw-explainer.ts`, rendering in `src/claw-lab.ts`, and bilingual controls in `src/claw-page.ts`. The scene pauses when hidden and preserves resources across BFCache navigation. A static loading/reload state appears before heavy imports; the docs parent accepts frame height messages only from its own same-origin lab frame.

`?mode=solver&embed=1` preserves the existing solver-configuration comparison. Both pages prefer local WebGPU with a WebGL 2 fallback. The claw page reports the actual initialized backend. Browser scores are not written into the native experiment catalog.

## Interaction reference

The aim/drop/return/prize-loop interaction was informed by [neciszhang/claw3d](https://github.com/neciszhang/claw3d/tree/02d5c53d0175e0018d791a7e89e5c45cf12b51f4). Source inspection of its [GrabController](https://github.com/neciszhang/claw3d/blob/02d5c53d0175e0018d791a7e89e5c45cf12b51f4/src/game/GrabController.tsx) on 2026-11-02 found that caught toys switch to kinematic following, with randomized slipping and a pity mechanic. DexLab implements its own MuJoCo contact path and does not adopt those mechanisms or copy code/models. The reference's live demo was not successfully runtime-verified in this session.

## Sixteen characters and PBR / 16 款角色与 PBR

The original six are joined by Nai Egg, Baby Nai Frog, Nai Dog, Pink Nai Frog, Nai Swirl, Soy Milk, Nai Fish, Nai Tea, Nai Bottle and Sigma Nai Frog. Each cabinet contains 30 toys mixing all 16 characters, including repeats; repeated toys share decoded mesh and texture resources. The retained source meshes use the original 1024/2048-pixel textures. Browser display derivatives use 6,000 triangles and 512-pixel textures per identity, generated with UV/normal-aware mesh simplification and a recorded error bound. Visual meshes and convex collision meshes use the same 1.6× scale. Thirty toys spawn in three layers and settle under gravity into a pile; the claw is 1.35× its original size. At drop, a native ray measures the surface under the aim marker and freezes the descent depth for all three worlds. The viewer uses nonmetallic rough fabric. The cabinet has deep-purple lacquer, rose light strips and sculpted moon/star trim; the metallic claw has matching cat-ear and moon decorations. The decorations do not alter its collision geometry. No fabricated normal maps or material measurements are implied.

新增奶蛋、小奶蛙、奶狗、奶粉、奶屎、豆奶、奶鱼、奶茶、奶瓶、西格玛奶蛙，共 16 款。每柜固定混放 30 只，覆盖全部 16 款角色；不需要选择组合，“换一柜”只重新摆放同一组娃娃。同款复用解码后的网格和纹理。模型与碰撞形状同步放大为原来的 1.6 倍，分三层装柜后自然下落、堆叠；夹爪放大为 1.35 倍。瞄准环跟随堆顶，下爪时用原生射线测出表面高度，三路共用由该起点确定的下降深度。点头像可近看真实网格，拖动旋转，俯视按钮返回全景。保留原始 1024/2048 像素贴图的源模型；浏览器展示模型每款 6,000 三角面、512 像素贴图，简化过程考虑法线与 UV 并记录误差界限；娃娃为粗糙非金属 PBR；柜体采用深紫漆面、粉色灯条和立体星月装饰，金属夹爪配猫耳与月牙。这些装饰不改变夹爪碰撞形状。这不代表实测织物或生成了真实法线贴图。

## Browser performance / 浏览器性能

The three native worlds and replay stay in `claw-worker.ts`. The main thread receives display snapshots with at most one physics-tick request in flight. Worker batches yield after an 8 ms budget, checked between complete three-world steps; no simulation steps or solvers are omitted. A slow device advances simulation time more slowly. Hidden tabs stop requesting work.

Coarse-pointer devices or pages initially narrower than 600 px use a pixel ratio capped at 1, a 30 fps render cap and no real-time shadow map. Other pages cap the pixel ratio at 1.5. Offscreen stacked views are skipped. These are resource limits, not a measured frame-rate guarantee for every phone. The public game no longer uses an OVRTX stream.

三个原生世界及回放保存在 `claw-worker.ts`；主线程只接收画面状态，最多保留一个未完成的物理帧请求。Worker 每批在完整的三路步进后检查 8 ms 工作预算，不跳过物理步或某个求解器；性能不足时仿真时间自然变慢。页面隐藏时停止请求计算。触屏或首次打开宽度小于 600 px 的页面采用 1 倍像素比、30 fps 渲染上限并关闭实时阴影；桌面像素比上限为 1.5。上下排列时跳过屏幕外的视窗。这些是资源限制，不等于所有手机都已实测达到相应帧率；游戏不再使用 OVRTX 视频流。

Generate display assets after installing Pillow for the selected Python interpreter:

```bash
PYTHON=python3 node scripts/optimize-toys.mjs
```

The source GLBs, source portraits and native collision hulls stay unchanged. `src/assets/nai/display/manifest.json` records source/derivative hashes, byte counts, triangle counts and simplification error. The browser loads the derivatives, including 128-pixel portraits, without loading the original generation inputs.

原生 WASM 检查覆盖三种固定摆放的 30 只玩偶堆叠、真实相互接触、同步抓取和空抓负例，以及全部 30 种初始排列不穿插。低迭代预算触发引擎自动重置时会明确暂停并报错；不能把重置后的状态当作有效结果。不承诺底层角色一次就能抓到，也不声称完成了整柜 30 只的收集验证。
