# 接触参数读回

[English](CONTACT_READBACK.md) | [简体中文](CONTACT_READBACK.zh-CN.md)

开发验证：八次冻结的原生运行均通过原物理验收。记录器在求解力的同一时刻读取 MuJoCo 接触摩擦、维度、solref、solimp 和 include margin。独立诊断仅检查相同材料的解析方块／平面夹具，包含编译后的几何类型、尺寸与组合参数输入，不证明一般网格烹制或材料精度。MuJoCo3.14 头文件规定 mjMINMU=1e-5，未激活的扭转／滚动参数槽也受此限制；参数值不是摩擦力。

SuperDex1.0.0 FP64 从两个 actor 分别读取参数。公开 ContactPoint 有力、位置和速度，没有组合接触律参数。组合结果与烹制几何等价性保持未知，不能因 actor 参数相同就判等价。

```bash
python -m dexlab.contact_readback RECORD_DIRECTORY
```

命令先检查完整归档哈希、源码快照、固定阈值与力账本，再进行诊断。物理验收独立保留，缺少读数表示不完整。只有物理验收通过且直接观测的参数完整一致才返回零；SuperDex 的不可观测项返回非零，但不改变原物理评分。不覆盖历史记录，不从旧数据补造字段。

[MuJoCo 官方组合语义](https://mujoco.readthedocs.io/en/stable/modeling.html#contact-parameters)。冻结开发矩阵为 `benchmarks/contact-readback-v1.json`，最多八次原生运行、600秒，不属于留出基准。

## 实测开发对照

四个 MuJoCo 记录均有完整一致的读回（接触数依次为 3,660／4,000／4,000／7,340）；四个 SuperDex 记录的 actor 参数一致，但组合接触参数仍不可观测。与此前对应摩擦工况比较，八组状态数组和原有接触字段完全一致。这仅验证所测工况下记录功能未改变结果，不是一般性的无干扰保证。

另六个 MuJoCo 静态对照均符合预先声明的预期：同优先级加权、平面较高优先级、直接格式 solref 逐项最小值、显式各向异性接触对、全局覆盖及分离负例。五个正例各有四个接触，负例无接触。仅调用 `mj_forward`，不推进仿真时间，不证明动态稳定性。复现命令为 `probe_contact_mixing.py OUTPUT --wheel-dir OFFICIAL_WHEEL_DIRECTORY`。

原始证据已打包并通过离线复核；v0.22.0 的完整原生抓取回归及发布已完成。一般网格烹制等价性和真实材料标定仍未证明。

[Readback JSON](evidence/contact-readback-v1.json) · [Mixing JSON](evidence/contact-mixing-v1.json)

```bash
python demos/contact-benchmark/report_contact_readback.py READBACK_RECORDS --previous FRICTION_RECORDS --output REPORT.json
```

已发布原始附件: `dexlab-contact-readback-evidence-v1.tar.gz`, 2,403,074 bytes, SHA-256 `ba59bd8beca7fab3091df52759070febcdb9bce35344bc31fb0e1e26c63e3b02`. 解压后以归档源码核对 186 个文件哈希并重现八组诊断。原生状态／接触字节不变，仅脱敏私有源码路径键并记录前后哈希；原件保留。

[Published raw evidence / 已发布原始证据 (v0.22.0)](https://github.com/huangkiki/Dexlab/releases/download/v0.22.0/dexlab-contact-readback-evidence-v1.tar.gz). Publication and downloaded-asset verification are complete; this does not resolve the unobservable fields described above.
