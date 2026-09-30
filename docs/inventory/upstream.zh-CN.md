# 上游任务卡与选题依据

[English](upstream.md) | [简体中文](upstream.zh-CN.md)

**10 张任务卡、8 个固定版本仓库；全部为源码阅读，没有声称本轮安装、运行或复现。** 2026-09-30 读取的 41 个文件、完整 commit、URL 与 SHA-256 见[来源清单](upstream-sources.json)。不重新分发上游源码或资产。运行入口是上游调用方式/注册类；依赖、权重和资产未资格验证，因此不能视作已经验证的一键安装。

按已有研究笔记“任务/接触模式、形态与驱动、物理、传感、策略与数据、真机校准”六层整理。这里评估对 DexLab 实验设计的用途；上游能力与 DexLab 已交付能力严格分开。每卡的成本均为**未测量**；代码许可标签不覆盖第三方资产。

## U1 — DexGraspBench：抓取、保持与扰动

[JYChen18/DexGraspBench@d9ea6cf282de](https://github.com/JYChen18/DexGraspBench/tree/d9ea6cf282de1f463c20fa54b4f68d7025bad40e) · [eval.yaml](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/config/task/eval.yaml); [tabletop_mocap.py](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/src/task/eval_func/tabletop_mocap.py); [fc_mocap.py](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/src/task/eval_func/fc_mocap.py); [example.sh](https://github.com/JYChen18/DexGraspBench/blob/d9ea6cf282de1f463c20fa54b4f68d7025bad40e/script/example.sh)

**入口与前提：** `bash script/example.sh`；需要上游手与物体资产。

**模型 / 控制 / 观测：** MuJoCo；预抓取→抓取→压紧→抬高 0.1 m；候选姿态输入与 mocap 手运动是显式先验。当前配置质量 0.1 kg、摩擦 0.6/0.02，与论文 baseline 分支不同。

**成功定义、缺口与用途：** 初始穿透及扰动后平移/旋转判定；力闭合指标与动力学结果分开。mocap 路径不验证完整机械臂驱动。可借鉴失败对照与负载测试，不能把上游阈值当本项目材料精度标准。

**许可快照：** 本次根目录树未识别独立 LICENSE.

## U2 — IsaacLab：Allegro 掌内重定向

[isaac-sim/IsaacLab@9c572e483959](https://github.com/isaac-sim/IsaacLab/tree/9c572e48395943279f78dfbc81eb19b92d37487c) · [__init__.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/core/reorient/config/allegro_hand/__init__.py); [allegro_hand_direct_env_cfg.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/core/reorient/config/allegro_hand/allegro_hand_direct_env_cfg.py); [allegro_hand_common.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/core/reorient/config/allegro_hand/allegro_hand_common.py); [reorient_direct_env.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/core/reorient/reorient_direct_env.py)

**入口与前提：** 注册入口 `Isaac-Reorient-Cube-Allegro-Direct`；上游训练启动器和机器人资产需单独安装。

**模型 / 控制 / 观测：** 手中立方体与姿态目标；16 维动作、124 维 full 状态、10 s episode、dt=1/120 s；关节目标与物体/目标状态，非纯图像输入。此 pin 声明 PhysX 与 Newton/MJWarp preset，不能沿用旧版“只有 PhysX”的描述。

**成功定义、缺口与用途：** 角度目标容差 0.2 rad 等任务奖励/重置条件，不是独立接触有效性证书。适合扩展接触切换/滚动；需另加穿透、载荷与材料滑移评分。当前 DexLab 未实现。

**许可快照：** BSD-3-Clause（源码）.

## U3 — IsaacLab Factory：精密装配

[isaac-sim/IsaacLab@9c572e483959](https://github.com/isaac-sim/IsaacLab/tree/9c572e48395943279f78dfbc81eb19b92d37487c) · [__init__.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/contrib/factory/__init__.py); [factory_env.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/contrib/factory/factory_env.py); [factory_tasks_cfg.py](https://github.com/isaac-sim/IsaacLab/blob/9c572e48395943279f78dfbc81eb19b92d37487c/source/isaaclab_tasks/isaaclab_tasks/contrib/factory/factory_tasks_cfg.py)

**入口与前提：** 注册入口 `IsaacContrib-Factory-PegInsert-Direct`、`...-GearMesh-Direct`、`...-NutThread-Direct`。

**模型 / 控制 / 观测：** Franka + 固定/被持物体；PhysX 专用配置；位姿增量动作经任务空间控制，actor/critic 状态不同。质量、摩擦、接触偏置在 task 配置中指定。

**成功定义、缺口与用途：** 成功代码检查 xy 距离 <2.5 mm 与相对高度；螺纹可另查旋转。不会自动证明孔壁无穿透或力合理。先借鉴几何公差/卡滞对照；FORGE 随机化方案本轮未单独追踪，不宣称已复核。

**许可快照：** BSD-3-Clause（源码）.

## U4 — ManiSkill：推方块

[haosulab/ManiSkill@62ff3a5896b4](https://github.com/haosulab/ManiSkill/tree/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3) · [push_cube.py](https://github.com/haosulab/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/envs/tasks/tabletop/push_cube.py)

**入口与前提：** 注册入口 `PushCube-v1`；SAPIEN/PhysX 与上游机器人控制模式。

**模型 / 控制 / 观测：** 桌面方块与目标区域；机器人状态与可选视觉，state 模式额外返回物体位姿与目标；动作由所选控制模式决定。

**成功定义、缺口与用途：** 成功是 xy 入目标范围且 z<方块半高+5 mm；没有独立摩擦辨识。适合与 R1 平面滑动串联验证推力/位移，但需要额外物理评分。

**许可快照：** Apache-2.0（源码）.

## U5 — ManiSkill：开抽屉

[haosulab/ManiSkill@62ff3a5896b4](https://github.com/haosulab/ManiSkill/tree/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3) · [open_cabinet_drawer.py](https://github.com/haosulab/ManiSkill/blob/62ff3a5896b4d5b4cf0ac4c8d79afe600c9404a3/mani_skill/envs/tasks/mobile_manipulation/open_cabinet_drawer.py)

**入口与前提：** 注册入口 `OpenCabinetDrawer-v1`；需要 PartNet-Mobility 资产。

**模型 / 控制 / 观测：** 随机柜体与可动链接；机器人动作依控制模式；读取柜体关节和把手状态。引擎关节约束与资产摩擦不是实测导轨。

**成功定义、缺口与用途：** 开启量达到目标且把手角速度≤1 rad/s、线速度≤0.1 m/s。任务完成不限制全过程驱动力/穿透；后续可作关节与接触耦合迁移，当前无 DexLab 入口。

**许可快照：** Apache-2.0（源码）.

## U6 — DexMimicGen：双臂托盘

[NVlabs/dexmimicgen@940e8a1b3ad7](https://github.com/NVlabs/dexmimicgen/tree/940e8a1b3ad70eb1925ada6b364b197de6bb2af9) · [README.md](https://github.com/NVlabs/dexmimicgen/blob/940e8a1b3ad70eb1925ada6b364b197de6bb2af9/README.md); [environments.md](https://github.com/NVlabs/dexmimicgen/blob/940e8a1b3ad70eb1925ada6b364b197de6bb2af9/environments.md); [two_arm_lift_tray.py](https://github.com/NVlabs/dexmimicgen/blob/940e8a1b3ad70eb1925ada6b364b197de6bb2af9/dexmimicgen/environments/two_arm_lift_tray.py)

**入口与前提：** `TwoArmLiftTray` 环境类；README 提供 `scripts/demo_random_action.py --env ...` 启动方式。

**模型 / 控制 / 观测：** robosuite / MuJoCo；双臂与托盘、两个载物；相机观测可开启，控制器配置决定动作。示教与数据生成能力不能等同于本项目已训练策略。

**成功定义、缺口与用途：** 实际 `_check_success` 检查托盘与两个物体高于桌面 0.1 m，且两物体接触托盘底；奖励中的倾斜系数不是同一成功条件。可借鉴双臂载荷分配，需另测支撑力与稳定性。

**许可快照：** NVIDIA Source Code License；LICENSE §3.3 限 research/evaluation；数据条款另查.

## U7 — DexGarmentLab：折衣与衣物接触

[wayrise/DexGarmentLab@e4e298e696ba](https://github.com/wayrise/DexGarmentLab/tree/e4e298e696bae5d866ded3b31e0ae27becea5376) · [README.md](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/README.md); [Fold_Tops_Env.py](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/Env_StandAlone/Fold_Tops_Env.py); [Particle_Garment.py](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/Env_Config/Garment/Particle_Garment.py); [Deformable_Garment.py](https://github.com/wayrise/DexGarmentLab/blob/e4e298e696bae5d866ded3b31e0ae27becea5376/Env_Config/Garment/Deformable_Garment.py)

**入口与前提：** `isaac Env_StandAlone/Fold_Tops_Env.py`（上游 Isaac Sim 4.5 的 Python 别名）；衣物资产及模型另下载。

**模型 / 控制 / 观测：** 双 UR10e 灵巧操作；所读 FoldTops 明确实例化 Particle_Garment，而非同仓库 Deformable_Garment；点云匹配操作点后发末端目标与手势命令。

**成功定义、缺口与用途：** 代码以 `judge_pcd(..., threshold=0.12)` 判终态，部分静置阶段把 gravity_scale 设为 10 后恢复 1。夹持调用链及附着约束未完整资格验证；不得宣称全程自然摩擦抓持。可借鉴任务分解；物理比较先完成 C1/C2。

**许可快照：** 本次根目录树未识别独立 LICENSE.

## U8 — DexScrew：工具旋转先验

[x-robotics-lab/dexscrew@3bde4e3a4d97](https://github.com/x-robotics-lab/dexscrew/tree/3bde4e3a4d973743921c75719ca88167de144e83) · [README.md](https://github.com/x-robotics-lab/dexscrew/blob/3bde4e3a4d973743921c75719ca88167de144e83/README.md); [XHandHoraScrewDriver.yaml](https://github.com/x-robotics-lab/dexscrew/blob/3bde4e3a4d973743921c75719ca88167de144e83/configs/task/XHandHoraScrewDriver.yaml); [xhand_hora.py](https://github.com/x-robotics-lab/dexscrew/blob/3bde4e3a4d973743921c75719ca88167de144e83/dexscrew/tasks/xhand_hora.py)

**入口与前提：** `scripts/screwdriver_teacher.sh 0 42 output_name`（上游训练）；当前 DexLab 无入口。

**模型 / 控制 / 观测：** IsaacGym/PhysX；XHand 12 维动作，dt=5 ms；特权 teacher→本体感知 student→真机含触觉的示教微调是分阶段流程。配置带质量/摩擦/尺度随机化。

**成功定义、缺口与用途：** 旋转策略/回报不能直接证明螺纹咬合、轴向推进和可标定扭矩。作为后续滚动/工具使用候选；真实力矩和耦合几何需另定义，本轮未复现训练或真机结果。

**许可快照：** MIT（源码）.

## U9 — Taccel：触觉软体接触

[Taccel-Simulator/Taccel@cb23bc251b53](https://github.com/Taccel-Simulator/Taccel/tree/cb23bc251b531ba6908a3788c2f91423cd543149) · [README.md](https://github.com/Taccel-Simulator/Taccel/blob/cb23bc251b531ba6908a3788c2f91423cd543149/README.md); [peg.py](https://github.com/Taccel-Simulator/Taccel/blob/cb23bc251b531ba6908a3788c2f91423cd543149/examples/peg.py)

**入口与前提：** `python examples/peg.py`（需上游 Taccel/Warp IPC 环境与网格）；无 DexLab 适配。

**模型 / 控制 / 观测：** `ASRModel` + `IPCIntegrator` GPU 路径；软传感器跟随插值运动学目标，孔为仿射运动学对象。示例输出网格与步耗时。

**成功定义、缺口与用途：** 所读 peg 脚本未定义独立抓取成功评分；运动学边界不是完整机器人执行器。候选用于软指腹接触模型研究，不能据此宣称现有 SDF 刚体任务等价或可直接替换。

**许可快照：** MIT（源码）.

## U10 — HydroShear：触觉观测模型

[MMintLab/hydroshear@f815b82fdf34](https://github.com/MMintLab/hydroshear/tree/f815b82fdf3451852acd918933020a82cede1f3b) · [README.md](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/README.md); [training.md](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/training.md); [vec_task.py](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/rl/tasks/base/vec_task.py); [hydrosoft.py](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/rl/demo_utils/hydrosoft.py); [hydroshear.yaml](https://github.com/MMintLab/hydroshear/blob/f815b82fdf3451852acd918933020a82cede1f3b/configs/sensor/hydroshear.yaml)

**入口与前提：** 上游 `scripts/experiments/hydroshear/play_hydroshear.py --ckpt_path CHECKPOINT`；权重、IsaacGym 环境另准备。

**模型 / 控制 / 观测：** IsaacGym RL loop 与 SDF/历史位移驱动的 HydroSoft 传感模型是不同层；代码计算法向/切向场及触觉 marker 位移。

**成功定义、缺口与用途：** 读取了传感器和基础步进接口，未完整证明所有任务的力反馈耦合；不能把传感图像改善视为刚体接触求解器改善。后续传感器精度需要触觉实测参考，当前未接入 DexLab。

**许可快照：** MIT（源码）.

## 对 benchmark 的具体影响

1. 刚体先保留滑动、受控压入、夹持/超载/释放；它们能分离摩擦、法向响应和驱动误差。抓梗只是迁移任务之一。
2. 布料先做可观测的拉伸、下垂与碰撞，再修复机器人夹布；最终折叠形状正确不能抵消过程穿透。
3. 掌内重定向、装配、双臂协作补充接触切换与约束耦合，待统一评分定义后选择最小代表任务。
4. 工具与触觉另立观测/耦合假设，实测数据缺失时保持未知。上游任务奖励与本项目独立物理验收必须分开。

这些是选题建议，不新增已授权实现范围。后续指标工作见 [#31](https://github.com/huangkiki/Dexlab/issues/31)，硬件采集协议见 [#33](https://github.com/huangkiki/Dexlab/issues/33)。[返回盘点](README.zh-CN.md)
