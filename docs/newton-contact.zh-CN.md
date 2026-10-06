# Newton XPBD 接触准入

[English](newton-contact.md) | [简体中文](newton-contact.zh-CN.md)

## 研究问题与冻结的开发协议

官方 Newton 1.6.1 核心与 Warp 1.18.0 能否在不使用 MuJoCo 的情况下完成有限、可复现的球–平面接触？本次预登记基本几何准入已通过；安装与源码检查本身不等于物理证据。

使用原生 `SolverXPBD`、CPU、float32 状态；解析球半径 0.05 m、质量 0.1 kg，无限平面 z=0，重力 (0,0,-9.81) m/s²，初始球心 z=0.10 m。没有机器人、驱动、学习策略或渲染；使用基本几何碰撞，不是 SDF–SDF。密度由质量与球体积计算。这些是合成工程参数，并非标定过的苹果或指腹材料。

在任何原生实验前冻结：步长 0.001 s、1,000 步、XPBD 四次迭代、接触松弛系数 0.8、启用接触计数加权、关闭恢复系数、摩擦/黏附/几何 margin 为零。记录初始状态及每一步。完整重建并重复一次正常接触场景；另运行仅禁用球碰撞的负对照。没有参数搜索或调参预算。原生接口和安装失败也保留，但不算物理成功或失败。单次有界执行墙钟上限 600 秒。

独立评分器检查有限且完整的观测、每步球面穿透 ≤1 mm、最后 0.25 s 球心高度误差 ≤1 mm、速度 ≤0.01 m/s，以及原生竖直支撑力误差 ≤5% mg。这些是预先声明的工程准入界限，不代表真实物理精度。报告全程接触冲量与实测动量变化之差、重复运行差异。禁碰撞负对照必须未通过支撑验收，同时符合半隐式自由落体参考（位置误差 ≤0.1 mm，速度误差 ≤0.001 m/s）；不得从结果中删掉。

## 力的语义与限制

创建 contacts 前申请 `force` 属性，每步求解后调用 `SolverXPBD.update_contacts`。上游将前三维定义为 shape1 对 shape0 所属刚体施加的世界坐标力；根据实际 shape-to-body 索引映射符号，不能取绝对值掩盖方向。保留原始接触配对与力。XPBD 从累计约束冲量重建力；上游明确说明接触计数加权带来的近似，以及一般多体接触不保证动量守恒。本静态平面测试不能验证多接触抓取力、关节控制、布料、可微性或 GPU 速度。

## 适配器盘点

仓库固定 UniSim Core 1.7.10，其 Newton extra 固定 Newton 1.5.1、MuJoCo/MJWarp 3.11.0、Warp 1.16.0。这些历史依赖不能称为最新稳定版准入。隔离的核心实验不覆盖它们，也不证明 UniSim 适配器等价性。Newton 可选 `sim` extra 与核心 Warp 依赖不同。`SolverMuJoCo` 封装 MuJoCo；XPBD 是另一种求解器，也不是 MuJoCo 中 Newton 优化方法的别名。其他 Newton 求解器配置需要分别取得运行证据。

来源：[官方 Newton 1.6.1 发布](https://github.com/newton-physics/newton/releases/tag/v1.6.1)、[XPBD 源码](https://github.com/newton-physics/newton/blob/v1.6.1/newton/_src/solvers/xpbd/solver_xpbd.py)、[接触力约定](https://github.com/newton-physics/newton/blob/v1.6.1/newton/_src/sim/contacts.py)。结果及全部负对照见下文。

### 源码盘点，不作为能力通过证明

UniSim 1.7.10 的 `unisim/adapters.py` 将 `mujoco`、`motrix`、`drake`、`mjwarp`、`newton`、`superdex`、`genesis`、`isaacgym`、`isaacsim` 声明为 available，但文件明确提醒这不证明运行时支持。Newton 后端在 `unisim/backend/newton/backend.py` 构造 `SolverMuJoCo`；本实验使用独立的上游核心 API。

| Newton 1.6.1 公开求解器导出 | 本工作的证据 |
|---|---|
| SolverXPBD | 选定刚体接触配置，正常/重复/负对照记录通过准入 |
| SolverMuJoCo | 已检查封装身份，尚未验证最新版本适配器 |
| SolverFeatherstone、SolverSemiImplicit、SolverVBD、SolverKamino | 上游源码有导出，本工作未执行或验证任务 |
| SolverImplicitMPM、SolverStyle3D | 上游源码有导出，不属于本刚体基本几何协议 |

`SolverBase` 是接口，不是另一套引擎。出现在 `newton/_src/solvers/__init__.py` 不证明可选依赖、关节/接触功能或任务有效性。不得隐式切换这些求解器作为降级替代。

## 结果：基本几何准入通过

三段 CPU 轨迹及评分共 **12.826 s**，含首次 JIT、观测复制；cgroup 内存峰值 **299,753,472 字节**，无 high/max/OOM 事件。这不是稳态吞吐率。重复场景为完全相同的重建，不是独立随机种子。没有参数搜索或修改原生引擎。

| 检查项 | 正常接触及完全一致的重复 | 禁碰撞负对照 |
|---|---:|---:|
| 最大表面穿透 | 0.000849 mm | 4,859.901 mm；按预期未通过支撑 |
| 保持期最大高度误差 | 0.0000142 mm | 4,859.901 mm |
| 保持期最大速度 | 0 m/s | 9.810061 m/s |
| 保持期最大力误差 / mg | 0.051353% | 100% |
| 全程竖直动量残差 | 0.000441780 N·s | -0.000006050 N·s |
| 自由落体位置参考误差 | 接触后不再是自由落体 | 0.008643 mm |
| 自由落体速度参考误差 | 接触后不再是自由落体 | 0.0000605 m/s |
| 冻结的支撑判据 | 通过 | 失败，符合负对照要求 |

禁碰撞记录的接触力为零。正常碰撞峰值达 53.0434 N；图中保留峰值，并单独放大保持阶段。低穿透不证明柔顺性已经标定，也不证明冲击力准确。动量残差如实列出，没有假设为零。压缩原始记录包含全部状态、有符号接触力、材料/几何读回及负对照。

![逐步高度与有符号力曲线](evidence/newton-xpbd/traces.png)

[原始记录 gzip](evidence/newton-xpbd/record.json.gz) · [独立评分](evidence/newton-xpbd/score.json) · [哈希、成本与安装失败](evidence/newton-xpbd/manifest.json) · [官方包及已安装代码一致性](evidence/newton-xpbd/official-wheels.json)

代理和直连 PyPI 下载均因传输缓慢中断，部分文件保留。Python 3.10 校验辅助程序在任何原生实验前因没有 `hashlib.file_digest` 失败，改用流式 SHA256 后修复。随后镜像下载的文件与 PyPI 权威 SHA256、全部已安装 Python/原生代码逐文件一致。这些属于安装失败，并非隐去的物理试验。原生运行后，评分器补充了几何/材料读回及非有限质量值检查；同一原始数据通过，未改变任何阈值。

## 复现

可选核心环境与 DexLab 原生 MuJoCo/SuperDex 环境隔离。执行前核对官方包证据；新实验需重新确认最新稳定版。将 `DEXLAB_DATA_DIR`、`DEXLAB_DATA_DEVICE` 设为已有输出盘及其实际块设备；资源守卫要求实测桌面余量及强制 cgroup 限额。输出目录必须是新目录。

```bash
uv venv --python 3.12 .venv-newton
uv pip install --python .venv-newton/bin/python newton==1.6.1 warp-lang==1.18.0 numpy==2.5.3
python3 scripts/bounded_run.py --profile experiment --timeout 600 \
  --data-dir "$DEXLAB_DATA_DIR" --io-device "$DEXLAB_DATA_DEVICE" \
  --receipt "$DEXLAB_DATA_DIR/newton-repro-resources.json" -- \
  env PYTHONPATH="$PWD/src" WARP_CACHE_PATH="$DEXLAB_DATA_DIR/newton-cache" \
  "$PWD/.venv-newton/bin/python" -m dexlab.newton_contact_probe "$DEXLAB_DATA_DIR/newton-repro"
PYTHONPATH=src python3 -m dexlab.newton_contact_score "$DEXLAB_DATA_DIR/newton-repro/record.json"
```

无需 Newton 或重跑引擎，可复核随仓库提供的历史数据：

```bash
gzip -dc docs/evidence/newton-xpbd/record.json.gz > /tmp/dexlab-newton-record.json
PYTHONPATH=src python3 -m dexlab.newton_contact_score /tmp/dexlab-newton-record.json
```

本次仅准入一个合成 CPU XPBD 接触配置；机器人控制、SDF–SDF、布料、其他可选求解器、GPU、收敛及真机有效性均未验证，不能得到普适引擎排名。
