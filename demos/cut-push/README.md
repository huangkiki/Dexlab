# Continuous cutting and knife-face pushing / 连续切割与刀面推动

[中文实验说明](../../docs/site/zh/cut-push.md) · [English experiment](../../docs/site/en/cut-push.md)

`protocol.json` freezes the two synthetic tasks, paired controls, thresholds, source identities and resource budget. `evidence.json` records every completed run, step-size sensitivity and pre-push equality; `media-validation.json` verifies the plotted quantities directly from the saved arrays.

`protocol.json` 冻结任务、对照、阈值、源码与预算；`evidence.json` 保留各次结果、步长敏感性及推动前数组一致性；`media-validation.json` 从原始数组独立核对每帧显示的数值。历史数据不改写，原始大体积 NPZ 单独保存；本 PR 不发布新的数据 Release。

After reproducing the two displayed runs (tofu: η=5 Pa·s, 0.125 ms; banana: η=0, 0.25 ms) under the repository resource limits:

```bash
python demos/cut-push/verify_media.py --tofu-run TOFU --banana-run BANANA --output media-check.json
```

The video displays centroid displacement from the initial state. Task acceptance uses the last-cut end as its baseline, excluding cutting compression from push displacement. Surface rendering is an approximation; this is neither calibrated food nor a matched cross-engine benchmark.

`showcase-selection.json` records why the original elastic half-step tofu was selected after the jitter report. `motion-sensitivity.json` compares its raw quiet-window motion with the retained 0.25 ms baseline. This changes numerical timestep, not food calibration. An additional half-step no-push control preserves the causal check.

`showcase-selection.json` 记录加入黏性前的纯弹性回放选择；`motion-sensitivity.json` 比较保留的 0.25 ms 基线与已通过机械检查的 0.125 ms 豆腐记录，另补半步长无侧推对照。没有平滑画面或添加阻尼参数，数值敏感性不等于食材标定。

```bash
python demos/cut-push/verify_motion.py --baseline TOFU_025 --candidate TOFU_0125 --output motion-check.json
```

The subsequent viscosity extension is frozen in `viscosity-protocol.json`: tofu uses η=5 Pa·s at 0.125 ms, banana stays at η=0. `viscosity-evidence.json` separates the short resource probe from three complete cases (nominal, half-step and matched half-step no-push). `viscosity-sensitivity.json` compares η=0 and η=5 at the same timestep; the original timestep-only comparison above remains historical.

后续黏性扩展见 `viscosity-protocol.json`：豆腐 η=5 Pa·s、0.125 ms，香蕉保持 η=0。`viscosity-evidence.json` 区分短探针与三个完整案例；`viscosity-sensitivity.json` 固定步长比较黏性前后。上面的纯弹性步长对照作为历史保留。黏度是合成参数，未做食材标定。

```bash
python -m dexlab.tofu_cut --task tofu-sequential --grid-spacing .005 --dt .000125 --viscosity 5 --output TOFU
python demos/cut-push/verify_viscosity.py TOFU --output dissipation-check.json
python demos/cut-push/verify_motion.py --baseline TOFU_ELASTIC_0125 --candidate TOFU --vary viscosity --output viscosity-check.json
```

`verify_viscosity.py` independently reconstructs compatible P2G velocities and Newtonian constitutive dissipation at saved states. This is not the system's total energy balance. The matched no-push control also retains η=5 and 0.125 ms.

`zero-viscosity-regression.json` covers 18 bitwise material-step comparisons with the frozen old kernel. To repeat it with the original elastic record and source, extract `src/dexlab/cutting.py` from base commit `052d1934ba1a2c976ddcd79210afb7c528a36827` and pass it as `--baseline-source` to `verify_zero_viscosity.py`. This reuses event states, not a new complete trajectory. All raw-source hashes are checked before replay.
