# 苹果梗抓取

[English](README.md) | [简体中文](README.zh-CN.md)

**OpenArm 双臂 + Wuji 灵巧手 · MuJoCo / SuperDex · SDF–SDF 接触**

右手接近苹果、夹住梗、抬升并保持三秒，左臂保持静止。两个后端均仿真一个质量为 0.2 kg 的自由苹果刚体，苹果、拇指指腹和食指指腹均使用 SDF 碰撞体。

| MuJoCo 3.11.0 | SuperDex 1.0.0 FP64 |
|:---:|:---:|
| [![MuJoCo 抓梗](media/mujoco-sdf.gif)](media/mujoco-sdf.mp4) | [![SuperDex 抓梗](media/superdex-sdf.gif)](media/superdex-sdf.mp4) |
| [▶ 观看演示](media/mujoco-sdf.mp4) · [验收报告](evidence/sdf-mujoco/summary.json) | [▶ 观看演示](media/superdex-sdf.mp4) · [验收报告](evidence/sdf-superdex/summary.json) |

两段动图仅展示抓取近景，连续回放完整的 14 秒物理记录，无剪辑，均由 MuJoCo 渲染。展示相机跟随苹果，不参与控制。控制使用已知物体位姿、逆运动学和脚本化关节目标，图像不是控制器输入。抓取通过接触力保持，苹果没有附着约束或直接驱动。

## 运行

完成[安装](../../docs/installation.zh-CN.md)后，在仓库根目录执行以下任一命令：

```bash
bash demos/apple-stem-grasp/run.sh --backend mujoco
bash demos/apple-stem-grasp/run.sh --backend superdex
```

SDF 准备与规划完成后会打开窗口。添加 `--headless` 可关闭窗口；添加 `--output demos/apple-stem-grasp/runs/my-run` 可单独保存记录。两个后端的默认输出分别位于本演示目录下的 `runs/latest-mujoco-sdf/` 和 `runs/latest-superdex-sdf/`。

## 验证与视频导出

每次运行都会自动执行物理检查。重新执行独立检查并导出视频：

```bash
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/latest-mujoco-sdf
MUJOCO_GL=egl .venv/bin/python demos/apple-stem-grasp/src/render_stem_focus.py \
  demos/apple-stem-grasp/runs/latest-mujoco-sdf
```

验证另一个后端时，将目录替换为 `latest-superdex-sdf`。视频导出需要 FFmpeg 和 OpenGL / EGL。物理检查失败或记录不完整时返回非零退出码。

检查覆盖完整的 11–14 s 保持阶段，包括离桌高度、两指指腹持续支撑苹果梗、穿透、相对腕部运动和动量平衡。接近阶段允许果身接触；保持阶段不允许通过果身接触提供支撑。

位置/速度/力的 RMS、峰值和逐指腹低载荷区间可用[离线抖动诊断](../../docs/jitter.zh-CN.md)分析。缺失记录保持未知，不会被当成零接触。


## UniLab 任务接口

场景准备还会写入只读的 `model-audit.superdex.json`，MuJoCo 运行额外生成 `model-audit.mujoco.json`。参数来源、初始重叠和独立复查方法见[模型审查](../../docs/model-audit.zh-CN.md)。

安装后的 `unilab.tasks` 扩展入口将 `DexLab-AppleStem-v0` 注册到 UniLab 1.3.3。任务实现实际的 `ABEnv`／`NpEnvState` 生命周期；每次 `step` 推进一个原生物理步。当前 SDF 场景和接触记录由任务自身管理，尚未改用 UniSim 内置适配器，该工作见 [issue #4](https://github.com/huangkiki/Dexlab/issues/4)。

```python
from unilab.base import registry

registry.ensure_registries(packages=["dexlab.tasks"])
env = registry.make("DexLab-AppleStem-v0", sim_backend="mujoco")
try:
    state = env.init_state()  # 创建、静置并规划新场景
    while not state.terminated[0]:
        state = env.step(state.info["scripted_target"])
finally:
    env.close()
```

`obs["obs"]` 的形状为 `(1, 关节数 + 8)`，依次包含**实际关节角**、苹果位置／四元数真值（`xyz`、`xyzw`）及实验时间。关节顺序见 `info["joint_names"]`。动作形状为 `(1, 关节数)`，含义是弧度制的绝对关节目标；脚本目标是显式控制先验，不是观测或学习输出。奖励为零，终止后的物理验收位于 `info["summary"]`。非法形状和非有限动作在步进前报错。重置会重新构建场景，不自动重置；每进程仅支持一个场景。此接口不表示已具备 RL 训练或视觉策略。

`unilab.json` 保存任务、运行库和生效参数。证据记录器独立记录每个物理步；正常结束或提前退出均释放原生资源。实时窗口在创建时配置，视频导出则单独回放记录的位姿。

## 实现

- [MuJoCo 模型转换与 SDF 设置](src/mujoco_model.py)、[动力学与控制器](src/mujoco_grasp.py)。
- [SuperDex 设置与控制器](src/wuji_stem_grasp.py)、[逐步证据记录](src/superdex_evidence.py)。
- [独立验收器](src/verify_sdf_grasp.py)。
- [引擎底层、具体参数、结果与限制](../../docs/sdf-backends.zh-CN.md)。

两者均使用官方 PyPI 运行库，没有引擎源码补丁。MuJoCo 路径使用 SuperDex 加载资产和完成初始规划，此后的实验动力学由 MuJoCo 计算。苹果与梗组成单个刚体；本演示未验证梗变形、断裂或硬件精度。

[返回 DexLab](../../README.md) · [资产来源](../../docs/ASSETS.zh-CN.md)
