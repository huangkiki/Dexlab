# Wuji 抓持、卸载与释放

[English](README.md) | [简体中文](README.zh-CN.md)

运行固定手腕的 Wuji 双指夹球，再检查实测接触是否真的保持和释放了这个 20 g 球。准备结束后，物体没有 latch、焊接或外部支撑。这是合成数值实验，不是经过真机标定的手模型。

保留的 v2 记录持续双指接触，但最大位移为 **2.459 mm**，超过事前冻结的 **2 mm** 门槛。[另行冻结的 v3](PROTOCOL-v3.zh-CN.md)只把控制周期从 2 ms 改为 0.5 ms：平均指垫法向力从约 0.27 N 增至 0.76 N，位移却增至 **2.734 mm**，仍未通过原门槛。更早的 v1 已有初始几何和控制缺陷。三次尝试全部保留，各批其余五项均按停止条件未执行。很小的力与动量残差不能把任务失败改成成功，目前没有建立合格的 solver failure 结论。

下一批[独立冻结的 v4 协议](PROTOCOL-v4.zh-CN.md)增加合成抗扭接触模型，保留双指、球、2 mm 门槛及剩余预算，结果尚待验证。下方命令显式选择 v4。

## 运行原生夹持实验

在仓库根目录执行，需要 Linux x86_64、[uv](https://docs.astral.sh/uv/getting-started/installation/)、Python 3.12 和隔离环境。物理使用 CPU MuJoCo 3.17.0，不需要 GPU、SuperDex、Torch 或模型 API key。固定机器人压缩包约 16 MB；原生 SDF 场景实测内存超过 2 GiB，建议预留 8 GiB，4.4 秒仿真通常需要计算数分钟。以下命令只在 uv 隔离环境安装本实验依赖。

```bash
uv run --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/native-requirements.txt \
  python scripts/download_assets.py --manifest demos/wuji-contact/assets.json \
  --destination downloads/wuji-contact-assets
PYTHONPATH=demos/apple-stem-grasp/src \
uv run --offline --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/native-requirements.txt \
  python demos/wuji-contact/run.py --robot-assets downloads/wuji-contact-assets/robot \
  --protocol demos/wuji-contact/protocol-v4.json --case hold-release \
  --output results/wuji-contact-first
```

输出包含原生场景、关节目标、运行库与源码哈希、初始几何检查、有效参数和每一步的前后观测。已有输出目录会被拒绝。`recorded` 只表示记录完成，不代表抓持成功。

## 从记录复算并画图

这一步不导入仿真引擎，也不推进物理时间。先检查原始哈希、时钟、状态连续性、原生接触力重建和线性动量平衡，再按原门槛评分。

```bash
uv run --no-project --isolated --python 3.12.12 \
  --with-requirements demos/wuji-contact/offline-requirements.txt \
  python demos/wuji-contact/plot.py results/wuji-contact-first \
  --output results/wuji-contact-first-report
```

打开 `measurements.png` 看曲线；`measurements.csv` 保留完整时间序列，`report.json` 分别报告记录一致性、数值平衡、保持、释放和卸载。CSV 明确区分步进前后时刻：位姿与速度取步后状态，接触力与驱动力取积分前求解。每次报告写到输入目录之外的新目录。图中明确标注对称对数坐标，以同时显示毫米级保持位移和随后自由落体。从未合格抓稳、后来掉出手外，不能算主动释放成功。

冻结案例还包含 `unload-index_finger`、`unload-thumb`、`open`、`no-contact`、`zero-friction`。资格批次须先通过正例，再执行这些对照。卸载按指定指垫的实测力判断；失去两个支撑接触中的一个后掉球，单独报告。零摩擦仍保持时应检查几何托住的可能，不能直接归因为 solver 缺陷。

[原始协议和判据](PROTOCOL.md) · [v2 几何与控制修正](PROTOCOL-v2.md) · [v3 控制频率假设](PROTOCOL-v3.zh-CN.md) · [适用性范围](applicability.json) · [Issue #251](https://github.com/huangkiki/Dexlab/issues/251)

首个原生夹持配置不等于跨引擎比较、真实材料准确性、手内旋转或数值求解器失败。接触切换与开发后验证仍由 [#48](https://github.com/huangkiki/Dexlab/issues/48)承接。
