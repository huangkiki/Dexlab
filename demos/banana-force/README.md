# BladeMaster banana material qualification / 香蕉材料资格

`material-protocol.json` separates values stated in BladeMaster IV-C from the plastic update that the paper leaves unspecified. DexLab implements an independent perfect-J2 projection in principal logarithmic strain and keeps `yield_stress=0` as the unchanged elastic default.

`material-protocol.json` 将 BladeMaster IV-C 明确给出的参数与论文未说明的塑性更新分开。DexLab 采用主对数应变空间中的独立理想 J2 投影；`yield_stress=0` 仍是未改动的纯弹性默认路径。

This slice qualifies elastic/plastic loading, unloading, superposed rigid rotation, determinant preservation, elastic-energy removal and saved plastic-dissipation telemetry. It does not run or claim the paper's force experiment. Existing public banana records remain synthetic and immutable.

本阶段只验收弹性／塑性加载、卸载、叠加刚体转动、正 Jacobian、弹性能移除和塑性耗散记录，不执行也不声称复现论文测力实验；现有公开香蕉记录仍是合成材料且保持不变。
