# BladeMaster-style banana material and force qualification / 香蕉材料与测力资格

`material-protocol.json` separates values stated in BladeMaster IV-C from the plastic update that the paper leaves unspecified. DexLab implements an independent perfect-J2 projection in principal logarithmic strain and keeps `yield_stress=0` as the unchanged elastic default.

`material-protocol.json` 将 BladeMaster IV-C 明确给出的参数与论文未说明的塑性更新分开。DexLab 采用主对数应变空间中的独立理想 J2 投影；`yield_stress=0` 仍是未改动的纯弹性默认路径。

`force-protocol.json` then freezes an independent single-cut force experiment: twenty deterministic stratified particle samplings, one-factor timestep/contact sensitivity, a quarter-grid exact-64× refinement, separate material/support/actuator force channels, and finite cgroup resource budgets. `evidence.json` requires complete final bounded receipts. Baseline and sensitivity suites pass; the completed 64× suite is retained as a declared negative result because support contact is absent.

`force-protocol.json` 进一步冻结独立单刀测力：20 组确定性分层粒子采样、一因子步长／接触敏感性、四分之一网格的精确 64× 粒子细化、材料／支撑／驱动力分离，以及有限 cgroup 资源预算。`evidence.json` 必须由带最终遥测的完整受限运行收据生成；基准与敏感性套件通过，完整的 64× 套件因未接触支撑而作为事前规则下的负结果保留。

Existing public three-cut banana records remain synthetic and immutable. The force experiment uses the paper values but independent geometry, sampling, trajectory, contact scales and J2 projection. It cannot claim author-code equivalence or real-banana force accuracy because the raw robot trace and several numerical settings are unavailable.

The exact source identity also freezes unpublished controls that the protocol JSON did not enumerate individually: particle contact radius `s_R=1`, cut-band rear extent `2Δx`, lead extent `2R_p`, minimum cut-advance speed `0`, and intact-reference-neighbor exclusion at `2Δx`. Only the published `6Δx` band half-width is directly aligned. These extra controls are reported as a limitation and are not retroactively added to the predeclared protocol.

现有公开香蕉三刀记录仍是原合成材料且保持不变。单刀测力采用论文参数，但几何、采样、轨迹、接触尺度和 J2 投影属于独立选择；作者未公开机器人原始力曲线及若干数值设置，因此不能声称作者代码等价或真实香蕉力精度。

精确源码身份还固定了冻结 JSON 未逐项列出的未知控制量：粒子接触半径 `s_R=1`、切割带后缘 `2Δx`、前缘 `2R_p`、最小切入速度 `0` 与完整材料近邻排除阈值 `2Δx`；只有带宽 `6Δx` 直接来自原文。这些量没有被追溯补进事前协议，而是在结果中作为限制披露。

Build the compact public evidence after all bounded suites complete:

```bash
python scripts/build_banana_force_report.py \
  --baseline <baseline-dir> --sensitivity <sensitivity-dir> --refined <refined-dir> \
  --receipt <receipt-1> --receipt <receipt-2> \
  --evidence demos/banana-force/evidence.json \
  --figure docs/evidence/cutting/banana-force/force-protocol.svg
```
