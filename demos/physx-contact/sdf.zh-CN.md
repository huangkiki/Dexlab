# PhysX 原生 SDF 接触对照

[English](sdf.md) | [简体中文](sdf.zh-CN.md)

通过 UniSim 的 Isaac Sim 后端，验证网格来源的原生 SDF 能保留凹形孔洞并产生支撑力。官方 PhysX 与 IsaacLab 未修改；DexLab 明确提供 UniSim 1.7.10 适配补丁。**这不是 PhysX 苹果抓取成功报告。**

## 转换与近似

Isaac Sim 的 MJCF 导入器遗漏 `type="sdf"` 几何。适配器保留逐几何 SDF 标志，在临时同目录 XML 中用 mesh 传输表面，再通过官方 `PhysxSDFMeshCollisionAPI` 设置 SDF 碰撞并读回。普通 mesh 保持原有凸近似。转换版本、逐几何标志和 SDF 参数进入缓存身份；缺失原生 API、改变近似类型或错误分辨率会中止初始化。

SDF 分辨率为最长包围盒边长的 256 等分，稀疏子网格分辨率 6；它从三角表面重新采样，不复制 MuJoCo 八叉树或 SuperDex 距离场。源网格、网格分辨率、SDF 分辨率与接触求解分别记录。没有网格的插件 SDF 不支持。

## 冻结实验

| 项目 | 配置与来源 |
|---|---|
| 圆环 | 主半径 30 mm、管半径 8 mm；96×32 表面采样；固定刚体 |
| 小球 | 半径 8 mm，20 g；icosphere 细分 4；惯量采用解析实心球近似 |
| 接触 | 摩擦 0.5；接触偏移 0.1 mm、静止偏移 0；工程设定，未经材料标定 |
| 计算 | 1 ms，350 步；TGS 位置/速度迭代 8/2；每次位置迭代应用外力 |
| 测量 | 实际刚体位置、速度及两体间法向接触力；不宣称测得切向摩擦力 |

三种配置使用同一源圆环和小球。`sdf-hole` 让小球穿孔；`sdf-surface` 将其放在环管上方；`convex-hole` 仅把圆环替换为普通 mesh 的凸包，用来暴露孔洞被填平的行为。物体均自由受力，不按预录轨迹定位。0.35 秒只用于短时碰撞资格检查，不代表长期夹持鲁棒性。

```bash
# 先完成可选 PhysX 环境安装；其下载量与基础安装分开
bash scripts/setup_physx.sh
.venv/bin/python -m dexlab.physx_sdf run --case sdf-hole --output demos/physx-contact/runs/my-sdf-hole
.venv/bin/python -m dexlab.physx_sdf run --case sdf-surface --output demos/physx-contact/runs/my-sdf-surface
.venv/bin/python -m dexlab.physx_sdf run --case convex-hole --output demos/physx-contact/runs/my-convex-hole
# 离线独立重评分，不调用原生引擎
.venv/bin/python -m dexlab.physx_sdf verify demos/physx-contact/runs/my-sdf-hole
```

所有场景、原始数组、原生读回、源码快照和失败日志留在新输出目录。验证失败返回非零退出码。既有环境使用 `UNISIM_ISAACSIM_HOME` 指定专用 worker；补丁只安装进当前 DexLab 主机环境。

## 结果与失败

SDF 孔洞通行和环面支撑通过；凸包对照会挡住孔洞，但存在横向运动，未通过 5 mm/s 的速度上限。缩小接触偏移及细化小球表面均未消除该失败；未放宽阈值。完整逐次指标见 [证据索引](evidence/sdf-v1/index.json)。旧配置的失败和无效导入尝试均保留，不能只统计通过项。

完整 OpenArm＋Wuji 模型的 54 个关节及右手两个 SDF 指腹已导入并读回；该检查仅运行 20 步、关闭重力，没有苹果或接触载荷。它修复了之前导入器漏掉指腹的路径，不证明已经完成 PhysX 抓梗。后续仍需审查碰撞过滤、受载机器人控制、苹果接触和完整离线验收；[Issue #5](https://github.com/huangkiki/Dexlab/issues/5) 保持开放。

参考：[官方 SDF 碰撞 API](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/rigid_bodies_articulations/collision.html#create-an-sdf-collider)。

后续[受载诊断](contact-details.zh-CN.md)已保留源模型共 267 对碰撞排除，并记录法向及摩擦力；苹果短暂抬起后仍未通过连续保持验收。
