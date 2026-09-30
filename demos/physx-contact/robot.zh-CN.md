# OpenArm＋Wuji 整机关节验收

[English](robot.md) | [简体中文](robot.zh-CN.md)

PhysX 经 UniSim 驱动 OpenArm 双臂与 Wuji 双手的 **54 个实际关节**。本协议关闭重力和接触，用于检查模型转移、关节顺序、实际运动、运动学一致性与回零。它不验证负载下的机器人控制、SDF 接触或苹果抓取，也不是硬件精度测量。

## 模型与控制来源

输入是已有 MuJoCo 抓梗运行目录中的编译模型、`model.xml` 和 `command-plan.npz`。质量、质心、惯量及驱动增益取自编译后的模型，避免直接使用 XML 中的零质量编译占位值。指令初始姿态来自该运行的预抓取姿态。

15 个零质量、零惯量的固定坐标链接折叠到父链接，位置与旋转同时合成；原坐标系保留为离线模型中的命名 site。92 个机器人链接变成 77 个原生刚体，54 个关节不变。固定根的单位质量／惯量仅为导入锚点，不能解释为硬件参数。转换器在 17 个姿态上核对完整的 54×54 关节质量矩阵及保留连杆的位姿，误差阈值为 `1e-10`。自包含评分模型保留关节与惯量，不需要外部网格。

驱动保留原运行生效的增益，包括其 `dt × kp` 阻尼项；没有将新实验步长重新代入该项。原任务没有电机力矩限幅，UniSim 对应为 `1e9 N·m`，**不是实际电机上限**。本协议不检验驱动与 MuJoCo 的瞬态响应是否相同。固定坐标链接的折叠、凸网格转换与关闭接触均明确记录。

## 协议与结果

步长 1 ms，4,000 个物理步。前 2 s 以平方正弦指令往返两次，后 2 s 返回初态并静置；每个关节的幅度不超过 0.03 rad，向离限位更远的一侧运动。所有步均记录实际关节位置／速度和原生连杆位姿；评分器从实际关节角独立计算正运动学，不使用指令角替代读数。没有在循环内重置状态或驱动物体位置。

| 指标 | 当前资格测试 | 冻结阈值 |
|---|---:|---:|
| 最大连杆位置一致性残差 | 0.712 μm | < 100 μm |
| 最大连杆旋转一致性残差 | 2.790 μrad | < 1,000 μrad |
| 最小单关节实际运动幅度 | 0.02819 rad | > 0.01 rad |
| 最后 0.5 s 最大回零误差 | 0.00001776 rad | < 0.001 rad |
| 最后 0.5 s 最大关节速度 | 0.0004318 rad/s | < 0.001 rad/s |

另检查采样完整性、有限数值、限位、四元数归一化、54 关节拓扑、原生刚体顺序、质量回读与源码／记录哈希。模型折叠的最大位置误差为 `1.11e-16 m`，关节质量矩阵最大元素误差为 `3.05e-16`。这些数值描述数字模型的一致性，不代表真实机器人的测量精度或引擎排名。

## 复现

先按[安装说明](README.zh-CN.md#安装与运行)准备可选 Isaac Sim 环境。每次使用新输出目录。

```bash
bash demos/apple-stem-grasp/run.sh --backend mujoco --headless \
  --output demos/apple-stem-grasp/runs/robot-source
.venv/bin/python -m dexlab.physx_robot run \
  --source-run demos/apple-stem-grasp/runs/robot-source \
  --output demos/physx-contact/runs/robot
.venv/bin/python -m dexlab.physx_robot verify demos/physx-contact/runs/robot
```

[v0.7.0 证据附件](https://github.com/huangkiki/Dexlab/releases/download/v0.7.0/v0.7.0-robot-articulation-evidence.tar.gz)包含全部 9 次导入、开发与资格运行，以及原始失败。附件约 25.4 MiB，含 576 个带哈希的文件，日常安装不下载它。参见[归档标识](evidence/robot-v1/archive.json)和[最终结果](evidence/robot-v1/summary.json)。解压后可独立复核：

```bash
.venv/bin/python -m dexlab.physx_robot verify robot-v1/robot-articulation-final-v1
```

独立 `verify` 不启动 Isaac Sim；它校验原始文件哈希，并重新计算每一帧的关节运动与位姿一致性。运行结束与验收通过分别记录。启动失败、部分轨迹和清理错误不会被判定为通过。

## 保留的失败与剩余工作

- 直接导入原 MJCF 时，UniSim 拒绝非默认 `inertiafromgeom` 编译配置。全部惯量均显式给出后，移除该冗余设置仍需与原编译模型核对。
- Isaac Sim 的 MJCF 导入器没有生成原 `type="sdf"` 的两个指腹碰撞体，UniSim 按几何数量不匹配拒绝启动。当前无接触实验将它们明确转为网格，**尚未实现原生 PhysX SDF 映射**。
- 首次运动开发记录中，靠近限位的拇指末关节运动不足；正式协议改为向限位内侧运动，并要求每个关节都有实际运动。
- 首轮资格记录的物理检查通过，但评分器错误地要求质量元数据字符串为 `exact`；适配器对实际浮点差异报告 `unknown`。修复后按原生回读数值与模型逐体比较，原失败记录保留，物理阈值未变。

接下来验证重力与受载运动、原生 SDF 几何及接触过滤，然后再运行苹果抓取。[Issue #5](https://github.com/huangkiki/Dexlab/issues/5) 仍未完成。
