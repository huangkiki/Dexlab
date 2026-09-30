# PhysX SDF 苹果梗抓取

[English](apple.md) | [简体中文](apple.zh-CN.md)

OpenArm + Wuji 通过 **UniSim 的 Isaac Sim 5.1 后端**完成 14 秒抓取，最后连续保持 3 秒。苹果与两个指腹使用原生 PhysX SDF。官方 PhysX、Isaac Sim 和 IsaacLab 未修改；UniSim 适配扩展与控制参数明确公开。

![PhysX 抓梗近景](media/physx-sdf.gif)

[连续视频](media/physx-sdf.mp4) · [单场景验收](evidence/apple-grasp-v1/qualification.json) · [独立几何复核](evidence/apple-grasp-v1/geometry.json) · [开发记录与失败](evidence/apple-grasp-v1/development.json)

## 运行

先完成仓库安装与[可选 PhysX 环境](README.zh-CN.md#安装与运行)。准备链继承已有 SuperDex/MuJoCo 模型和运动学先验；这不是独立的纯 PhysX 资产准备流程。已有完整 MuJoCo 运行目录可以直接复用。

```bash
bash demos/apple-stem-grasp/run.sh --backend mujoco --headless \
  --output demos/apple-stem-grasp/runs/physx-source
.venv/bin/python -m dexlab.physx_apple \
  --source-run demos/apple-stem-grasp/runs/physx-source \
  --output demos/physx-contact/runs/my-apple
# 用独立三角表面查询复核每个已记录物理步的几何覆盖。
"$UNISIM_ISAACSIM_HOME/venv/bin/python" src/dexlab/physx_geometry.py \
  demos/physx-contact/runs/my-apple --output demos/physx-contact/runs/my-apple-geometry.json
.venv/bin/python -m dexlab.physx_apple_score \
  demos/physx-contact/runs/my-apple \
  --geometry demos/physx-contact/runs/my-apple-geometry.json \
  --output demos/physx-contact/runs/my-apple-qualification.json
```

运行器返回 0 只表示完整记录；独立评分器才判定是否通过。省略 `--geometry` 可以得到原生记录诊断，但不计完整验收通过。输出目录和评分文件必须不存在，失败不会被覆盖。现有 SDK 验证使用 Python 3.11.14、Isaac Sim 5.1.0.0、IsaacLab core 0.47.2、Torch 2.7.0+cu128；几何复核使用 Warp 1.17.0。全新机器安装尚未重新验证。

## 参数与模型边界

| 项目 | 设置及来源 |
|---|---|
| 物体 | 苹果与梗为同一个 0.2 kg 自由刚体；不模拟梗弯曲或断裂 |
| 接触 | 原生 SDF 分辨率 256、子网格 6；源表面重新采样，不等于其他引擎的离散 SDF |
| 积分与求解 | 1 ms，TGS 8 次位置 / 2 次速度迭代，启用逐位置迭代外力 |
| 材料与偏移 | 静/动摩擦 1.0；contact offset 0.1 mm，rest offset 0；工程配置，未做材料标定 |
| 扭转 | 显式最小扭转接触半径 1 mm，应用于场景碰撞体；通过官方 PhysX 属性配置 |
| 驱动 | 编译后的源惯量与增益，保留目标速度补偿；不代表实机电机或力矩限幅已标定 |
| 控制 | 已知状态的关节轨迹先验，静置 1 秒后对齐一次，额外高度 10.75 mm；闭合只执行原手指协同路径的 95% |

源 MuJoCo 配置有 `condim=4` 和扭转摩擦系数 `0.001`。1 mm 的 PhysX 接触半径具有相关的力矩尺度，但不是接触模型等价或材料标定结论。默认最小半径为零的对照在同一闭合配置下未抬起苹果；该参数作用于整个场景，不能将差异全归于苹果接触。

95% 闭合用于减少过度夹紧与果身/指甲辅助接触。100% 闭合虽然留住苹果，保持阶段仍有指甲载荷，因此严格夹梗失败。原始失败、相邻高度失败及无扭转对照均保留。这里没有视觉策略、学习控制、附着约束或初始化后的物体位姿写入。机器人自碰撞保持开启，267 对源碰撞排除保留；远处地面省略，台面保留。

## 单场景结果

| 指标 | 结果 |
|---|---:|
| 物理步 / 保持窗口 | 14,000 / [11, 14) s |
| 最低离桌高度 | 125.087 mm |
| 相对腕部位移 / 旋转 | 0.540 mm / 0.745° |
| 手部平均竖直支撑 / 重力 | 0.999972 |
| 保持期果身及其他手部接触载荷 | 0 N |
| 原生手部接触最大穿透 | 0.0487 mm |
| 独立表面采样最大穿透 | 0.1397 mm |
| 加入空间及时间覆盖量后的穿透上界 | 0.7396 mm |

原生接触分离距离与参考表面穿透是两种测量。独立复核覆盖 79 个机器人碰撞表面：远离苹果的表面由包围球排除，其余使用双向三角表面距离；空间边长不超过 0.4 mm，未单独查询的已记录步通过刚体相对运动界覆盖，最大增加 0.2 mm。Warp FP32 距离查询另通过解析盒体与坐标变换检查。覆盖上界不包含源网格误差或通用浮点误差证明，不是硬件精度保证。

每步记录实际刚体/关节状态，以及相互独立的法向接触和摩擦锚点。动量残差峰值为重力的 0.00269%；尚未记录完整接触力矩，因此不声称角动量或全系统能量收支通过。完整 worker stderr 保留；固定 SDK 的 `IPhysxBenchmarks` 插件依赖声明警告单列，不当作接触求解失败，其他物理警告/错误会阻止验收。初始苹果/台面原生重叠约 1.470 mm，单独披露；1 mm 上限针对手部/苹果。

这是一个开发场景，独立重新启动得到相同状态记录；不构成留出成功率或引擎精度排名。公开报告是摘要，不能替代完整本地数组和原始几何；上述命令可重新生成并评分。

## 回放

```bash
.venv/bin/python -m dexlab.physx_apple_replay \
  demos/physx-contact/runs/my-apple \
  --display-run demos/apple-stem-grasp/runs/physx-source \
  --output demos/physx-contact/runs/my-apple-replay
MUJOCO_GL=egl .venv/bin/python demos/apple-stem-grasp/src/render_stem_focus.py \
  demos/physx-contact/runs/my-apple-replay --output demos/physx-contact/runs/my-apple-media
```

MuJoCo 只渲染 PhysX 的实际位姿；仅被折叠的无质量固定坐标系由运动学恢复。视频连续 14 秒、280 帧，无指尖标记；镜头跟随记录中的苹果，只用于展示。
