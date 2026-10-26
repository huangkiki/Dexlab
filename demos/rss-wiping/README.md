# RSS sponge wiping reproduction / RSS 海绵擦拭复现

This experiment runs RoboSimStudio's public wiping scene independently and compares its original compliant grasp assistance with an explicit no-pinning variant. It is the first slice of [#223](https://github.com/huangkiki/Dexlab/issues/223), following [Discussion #220](https://github.com/huangkiki/Dexlab/discussions/220).

本实验独立运行 RSS 官方擦拭场景，对比原版辅助保持与关闭节点约束的版本。它是手内操作研究的准备案例；擦拭成功不代表已经实现手内旋转。

**Observed result / 实测结果:** unchanged native test 9/9; controlled original 3/3 task passes, no-latch 0/3. See the [English report](../../docs/site/en/rss-wiping.md), [中文报告](../../docs/site/zh/rss-wiping.md), and [per-run summaries, trajectories and raw hashes / 逐次摘要、轨迹与原始哈希](../../docs/evidence/rss-wiping/results.json).

## What latch means / latch 是什么

The original's latch is **compliant grasp assistance**. Contact first squeezes the sponge; after grasp readiness, `pin_nodes` adds position constraints to nodes near the pads and `ride` moves their targets with the hand at each soft-body substep. An open command releases them. The authored stiffness is 4000 N/m and damping is 20 N·s/m, so nodes may deviate from their targets and the sponge still deforms. This is extra retention beyond friction, not a rigid weld or a physical glue model. [Pinned upstream implementation](https://github.com/robosimstudio/robosimstudio/blob/23417de77edf59d614531a833334ed4e2206fc2c/examples/08_demos/wipe_the_bar/bar.py#L425-L559).

原版的 latch 是**柔顺辅助固定**：先靠接触夹住海绵，达到抓取就绪条件后，用 `pin_nodes` 约束夹持区域附近的节点，再由 `ride` 在每个软体子步更新随手运动的目标；收到张开命令时解除。设定刚度为 4000 N/m、阻尼为 20 N·s/m，节点可以小幅偏离目标，海绵仍能变形。这是摩擦之外的保持作用，不是刚性焊接或真实胶水模型。

`--mode original` reproduces assisted wiping. `--mode no-latch` removes that assistance while retaining the same readiness and contact settings. Its failure does not by itself identify a friction, controller or coupling defect; see the paired report before interpreting success as physical accuracy.

`--mode original` 复现带辅助保持的擦拭；`--mode no-latch` 保留相同就绪条件与接触设置，撤去辅助固定。带 latch 成功不能证明纯摩擦保持可靠；无 latch 失败也不能单独归因为摩擦、控制器或耦合缺陷。

## Download and rescore first / 先下载并复算

The [immutable evidence release](https://github.com/huangkiki/Dexlab/releases/tag/rss-wiping-evidence-v1) publishes the complete first controlled original/no-latch pair: 159 files, about 126 MiB compressed and 349 MiB extracted. Follow the [homepage CPU quickstart](../../README.en.md#quickstart) or run these commands from the checkout root. The isolated Python 3.12 environment needs NumPy and Matplotlib, with no simulator or GPU; the first command downloads dependencies/data, and the second uses offline mode.

[不可变证据包](https://github.com/huangkiki/Dexlab/releases/tag/rss-wiping-evidence-v1)公开首个受控配对的完整 raw。按[首页 CPU 快速开始](../../README.md#quickstart)，或在仓库根目录运行：首次下载依赖与数据，随后离线复算；不安装仿真引擎，不使用 GPU，不修改项目已有环境。

```bash
uv run --no-project --isolated --python 3.12 \
  --with-requirements demos/rss-wiping/offline-requirements.txt \
  python scripts/download_assets.py \
  --manifest demos/rss-wiping/evidence-bundle.json \
  --destination downloads/rss-wiping-v1
uv run --offline --no-project --isolated --python 3.12 \
  --with-requirements demos/rss-wiping/offline-requirements.txt \
  python demos/rss-wiping/rescore_bundle.py downloads/rss-wiping-v1 \
  --output results/rss-wiping-v1
```

`comparison.png`, two CSV files and `report.json` reconstruct this pair's cleaning and material-patch displacement from saved states. Both records pass integrity checks; the no-latch task still fails. Output must be a new directory outside the bundle. Missing/corrupt files, mixed attempts, mismatched compiled arrays and summary-only substitutes are rejected before successful reporting. Original input hashes are checked before and after scoring.

结果是曲线图、两份 CSV 与 JSON 报告；无 latch 的 `task_pass: false` 是预期保留的物理任务失败。输入保持不变，输出目录必须新建且位于包外。包中 `attempt-index.json` 保留全部 12 条执行记录及单列的准备／后处理失败；仅首对具有完整公开 raw，其他范围仍由 [#247](https://github.com/huangkiki/Dexlab/issues/247)承接。三份派生 `.pyc` 缓存因可携带本机路径而省略，源码与排除哈希保留。

Native reproduction below has additional requirements: the historical cohort used NVIDIA CUDA, pinned RSS/lockfile, SuperDex Physics 1.0.0 single precision, Newton 1.6.0, MuJoCo/Warp 3.12.0 and Warp 1.18.0. Use its own environment, not the apple demo environment. RTX appearance replay separately needs RT cores and [OVRTX's NVIDIA proprietary license](https://pypi.org/project/ovrtx/0.4.0.346409/); [SuperDex Physics 1.0.0](https://pypi.org/project/superdex-physics/1.0.0/) declares Apache-2.0 for first-party code. No engine binaries are included. This publication reruns offline scoring only; it adds no RSS physics collection.

下述原生重跑需要匹配的 NVIDIA CUDA 环境、固定上游依赖与独立环境；RTX 外观回放还受 OVRTX 专有许可与 RT 核心要求约束。SuperDex 的许可与 OVRTX 不同，不要混称为商业依赖。数据包不含引擎二进制，本轮没有新增 RSS 物理采集。

## Frozen upstream / 固定上游

- Repository: [RoboSimStudio](https://github.com/robosimstudio/robosimstudio).
- Commit: `23417de77edf59d614531a833334ed4e2206fc2c`.
- Example: `examples/08_demos/wipe_the_bar`.
- Unchanged native test: `python -m unittest tests.test_demo_wipe_the_bar -v`.
- Install the upstream Python 3.12 environment with its checked-in lockfile and the `superdex` extra. Its default RTX group supplies the renderer; this comparison explicitly uses the upstream `tiled` collision renderer.
- RSS is Apache-2.0; bundled robot assets retain their licenses and upstream `NOTICE`.

Use the existing DexLab resource admission and serialization when executing research. Source, environment, generated assets and raw records belong on the configured data volume. The commands below describe the workload to place inside that bounded execution window.

使用已有资源准入与串行运行工具。源码、独立环境、缓存与原始记录存于配置的数据盘。下列命令是受限运行窗口内的工作负载。

```bash
export ROBOSIMSTUDIO_RENDERER=tiled

python demos/rss-wiping/run.py --source /path/to/robosimstudio \
  --output /path/to/fresh-original-run --mode original \
  --geometry-cache demos/rss-wiping/geometry-cache

python demos/rss-wiping/run.py --source /path/to/robosimstudio \
  --output /path/to/fresh-no-latch-run --mode no-latch \
  --geometry-cache demos/rss-wiping/geometry-cache

python demos/rss-wiping/score.py /path/to/fresh-original-run
python demos/rss-wiping/score.py /path/to/fresh-no-latch-run

python demos/rss-wiping/plot.py /path/to/fresh-original-run \
  /path/to/fresh-no-latch-run --output /path/to/comparison.png

python demos/rss-wiping/annotate.py /path/to/fresh-original-run \
  --output /path/to/original-with-measurements.mp4
```

`run.py` needs the upstream environment, NumPy and imageio; `score.py` needs NumPy; plotting additionally needs Matplotlib. Every output directory must be new. Use fresh processes for repetitions. `--max-seconds 3` is a deliberately truncated diagnostic, not a successful task.

`annotate.py` uses FFmpeg with subtitles support to label the existing frames from saved measurements. It preserves their order and playback rate; the raw recording remains available. The annotation is postprocessing, not a controller input.

## Render a saved trajectory / 重渲染已有轨迹

![Same recorded state: tiled left, RTX right; simulation 10–20 s, 1× playback / 同一状态左 tiled、右 RTX，原速回放](../../docs/evidence/rss-wiping/rtx/comparison.gif)

`render.py` loads a complete raw recording and renders matching tiled and RTX views. It reuses the pinned RSS materials, room and area lighting. Both views share the recorded camera and exact simulation timestamps. The command does not advance physics, interpolate particles, or change the existing scores.

`render.py` 从完整原始记录恢复刚体位姿、海绵材料点与墨迹，输出同机位、同时刻的 tiled／RTX 对照。它复用固定版本的材质、房间与面光源，不推进物理、不插值顶点，也不改变原评分。

Use the pinned upstream environment with its RTX dependency group and an NVIDIA GPU with RT cores. The input must contain `manifest.json`, `compiled-model.npz`, `observations.jsonl` and `states/*.npz`. Summary/CSV files alone cannot reconstruct the deforming sponge. The downloadable evidence bundle now supplies the complete first controlled pair; use its raw run directories, another retained recording, or a new recording made with the pinned environment.

需要固定上游环境的 RTX 依赖组、具备 RT 核心的 NVIDIA 显卡，以及完整原始状态。摘要／CSV 本身不包含重建海绵所需的全部顶点；现在可使用可下载证据包中的首对完整原始记录，或在固定环境中另行录制。

Inside the bounded execution window / 在受限运行窗口内：

```bash
python demos/rss-wiping/render.py /path/to/fresh-original-run \
  --source /path/to/robosimstudio \
  --output /path/to/new-render \
  --start 10 --end 20 --fps 10 --passes 12
```

The default 10-second segment produces 100 frames at the recorded 960×544 camera resolution. `comparison.mp4` places the tiled collision view on the left and RTX on the right; `tiled.mp4` and `rtx.mp4` retain each full-size view. First/middle PNGs allow frame inspection. `render.json` records the input/output hashes, frame-to-simulation mapping, camera, material/lighting preset, package versions, state readbacks and measured rendering costs. A directory without the final report is an incomplete attempt.

默认输出 10 秒、100 帧的片段，沿用记录中的 960×544 相机。`comparison.mp4` 左侧为碰撞视图、右侧为 RTX；两路独立视频和首帧／中间帧 PNG 同时保留。`render.json` 包含哈希、逐帧仿真时间、相机、外观配置、版本、状态读回与耗时；缺少最终报告的目录表示尝试未完成。

The input geometry and compiled-model fingerprints must match. Missing, duplicated, nonfinite or incompatible states fail the replay. After every pair of renders, loaded state and live colors must remain unchanged. The playback rate is not a real-time simulator speed claim.

输入几何与编译模型指纹必须一致。缺帧、重复帧、非有限值或维度不匹配会使回放失败；每对画面输出后检查状态与动态颜色未改变。视频播放帧率不表示实时仿真速度。

## Freeze preprocessing / 固定碰撞预处理

Repeated unchanged upstream CoACD preprocessing produced different collision decompositions. The retained unpaired reference therefore cannot isolate the effect of the latch. `geometry-cache` contains one set of arrays produced by the original upstream `_convex_pieces` method: 49 and 48 convex pieces for its two input meshes. Both controlled modes replay these exact arrays at the asset-preprocessing boundary. Input hashes, call order, file hashes and complete compiled-model hashes are checked; material, inertia and contact settings are preserved.

重复执行官方 CoACD 预处理时，碰撞分解会变化。正式对照复用同一次官方方法生成的数组，并核验输入、调用顺序、缓存文件及完整编译模型的哈希。引擎与上游源码保持原样；固定的是预处理结果。未固定几何的原版记录单独保留，不混入两组对照。

For a separate geometry cohort, capture a fresh cache with `--geometry-cache /path/to/new-cache --capture-geometry` during a short probe. Do not regenerate it between modes or reinterpret a new cache as the same cohort. The included derivative geometry retains the upstream and I2RT notices and licenses.

如需研究另一组碰撞几何，应另建缓存与实验批次。不要在两组之间重新生成，也不要把不同缓存混为同一批。

## What changes / 唯一实验干预

The original mode calls the upstream example's `main()`, opens its normal studio session without a browser, and advances the same arm panels and routine generator used by the native full-task test. It does not inject object states or bypass the joint controller.

The no-latch mode copies the three example files into the run directory and saves `no-latch.patch`. It preserves the upstream settling, bilateral force and squeeze conditions and the material-node patch selected at readiness. It removes `pin_nodes` and `ride`, and changes the routine's wait condition from actual latch engagement to that same grasp readiness. The actual bridge pin count is independently checked after every control step.

The repository's [review patch](no-latch.patch) uses zero context; `git apply --unidiff-zero` against the pinned example reproduces the exact recorded ablation files. Each raw run retains its original full-context patch.

原版保留场景、材料、接触、控制与求解设置。无 latch 版本保留原版“开度稳定、两侧受力、海绵被压缩”的就绪条件，只取消节点保持约束，并让流程在达到相同就绪条件后继续。每次修改生成可审查补丁；上游源码和物理引擎不修改。

This comparison isolates the contribution of grasp assistance in this configuration. It does not isolate coupling delay, friction regularization, collision geometry or material-model error.

## Records and interpretation / 记录与解释

- `observations.jsonl`: each control step, phase, measured hand pose, jaw width and command, sponge centroid, native pad forces, bar force/pressure, cleaned fraction, actual pin count and material-patch motion.
- `contacts.jsonl`: native contact sample positions, forces, normals, area and separation.
- `states/*.npz`: particles, rigid-body poses, joints and stripe ink at each recorded step.
- `settled-particles.npy`: the return reference after the same 20 settling steps as the upstream test.
- `tracked-patch.npy`: fixed material-node indices selected by the upstream grasp-readiness calculation.
- `video.mp4` and `video-times.npy`: continuous video and corresponding simulation timestamps.
- `manifest.json`: source, harness, package, authored material, native precision, physics, geometry and camera identities.
- `compiled-model.npz`: generated mesh arrays, shape transforms, contact fields and rigid mass/inertia.
- `summary.json`: observed outcome, costs and retained errors.
- `score.json`: independent saved-state checks and task outcomes.

The reported patch centroid displacement is measured in the moving hand frame. Soft-body deformation may contribute to it; it is not a direct friction-law measurement. Maximum material-node displacement is reported separately so opposing deformations cannot cancel in the centroid. Motion after deliberately opening the hand is excluded from the holding maximum.

接触区域位移在实测手坐标系下计算，并分别报告区域质心位移与最大材料点位移。软体变形也可能产生位移，不能把这些数值直接当作摩擦定律误差。主动张开后的释放运动不计入保持阶段最大值。

The native test's nine assertions remain unchanged. The independent task report preserves its shared thresholds: cleaned fraction at least 90%, peak bar force over 1 N, peak pressure over 5 kPa, sponge return within 20 mm horizontally and 3 mm vertically, both arms within 6 mm of home, finite state and completed routine. Pin semantics are evaluated separately; the absence of a latch is not itself a failed no-latch task.

These are repeated upstream example runs, not unseen validation cases, a calibrated material model, a visual policy or real-robot evidence. Results must be reported for every attempted run, including failures and resource interruptions.

Native-test success, saved-record integrity, task success and holding behavior are separate results. Independent scoring normalizes the measured quaternion before constructing a rotation, recomputes patch and node motion from saved material points, derives cleaned fraction from saved ink, and checks return/home errors against saved positions. Neither rendering nor a successful routine message establishes these outcomes.

官方测试、记录一致性、任务成功和保持能力分别报告。独立评分归一化实测四元数，从保存的材料点重算位移、从墨水状态重算清洁率，并核对归位误差。画面播放和流程结束提示不能替代这些检查。
