# RSS sponge wiping reproduction / RSS 海绵擦拭复现

This experiment runs RoboSimStudio's public wiping scene independently and compares its original compliant grasp assistance with an explicit no-pinning variant. It is the first slice of [#223](https://github.com/huangkiki/Dexlab/issues/223), following [Discussion #220](https://github.com/huangkiki/Dexlab/discussions/220).

本实验独立运行 RSS 官方擦拭场景，对比原版辅助保持与关闭节点约束的版本。它是手内操作研究的准备案例；擦拭成功不代表已经实现手内旋转。

**Observed result / 实测结果:** unchanged native test 9/9; controlled original 3/3 task passes, no-latch 0/3. See the [English report](../../docs/site/en/rss-wiping.md), [中文报告](../../docs/site/zh/rss-wiping.md), and [per-run summaries, trajectories and raw hashes / 逐次摘要、轨迹与原始哈希](../../docs/evidence/rss-wiping/results.json).

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
