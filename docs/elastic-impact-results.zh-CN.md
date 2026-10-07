# 一维弹性碰撞：末速度准确与接触穿透必须分开评价

[English](elastic-impact-results.md) | [简体中文](elastic-impact-results.zh-CN.md)

18/18个预登记工况通过数值阈值。最大末速度绝对误差0.00160672 m/s，相对动能误差0.16077%，全轨迹动量误差不超过1.12×10⁻¹⁵ kg·m/s。但最大几何重叠为5.0003–20.0161 mm；它不在本批末态阈值内，不能把通过称为低穿透抓取资格。

[冻结协议](elastic-impact-protocol.zh-CN.md) · [#99](https://github.com/huangkiki/Dexlab/issues/99) · [Preregistration](https://github.com/huangkiki/Dexlab/issues/99#issuecomment-6047131003)

三档步长下六组工况的末速度误差均下降；这是该固定配置的有限步长敏感性证据，不是普适收敛阶证明。零阻尼仍产生小幅数值增能，最细步长的最坏动能误差约0.00935%。横向速度和自转读数均为0。

柔顺接触允许压缩：在本设置的标量近似r̈+10000r=0中，自然频率100s⁻¹，重叠量尺度约为入射相对速度/100，因而对应5/10/20mm。该解释与观察相符，但没有独立验收整段接触ODE，不将其当作新的已验证模型。固定刚度下缩小时间步并不会消除物理模型本身的柔顺重叠。抓取后续需独立比较刚度、穿透、峰值力、冲量和计算成本；本批不能给真实材料恢复系数，也不能解释多点接触或复杂物体碰撞。

| Case | m2 (kg) | u1 (m/s) | dt (ms) | max velocity error (m/s) | energy error (%) | overlap (mm) | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| impact-01 | 1 | 0.5 | 1 | 0.0003013 | 0.12058 | 5.0040 | PASS |
| impact-02 | 1 | 0.5 | 0.5 | 0.0000451 | 0.01803 | 5.0005 | PASS |
| impact-03 | 1 | 0.5 | 0.25 | 0.0000175 | 0.00701 | 5.0003 | PASS |
| impact-04 | 1 | 1 | 1 | 0.0006025 | 0.12058 | 10.0081 | PASS |
| impact-05 | 1 | 1 | 0.5 | 0.0000901 | 0.01803 | 10.0010 | PASS |
| impact-06 | 1 | 1 | 0.25 | 0.0000350 | 0.00701 | 10.0007 | PASS |
| impact-07 | 1 | 2 | 1 | 0.0012050 | 0.12058 | 20.0161 | PASS |
| impact-08 | 1 | 2 | 0.5 | 0.0001803 | 0.01803 | 20.0020 | PASS |
| impact-09 | 1 | 2 | 0.25 | 0.0000701 | 0.00701 | 20.0014 | PASS |
| impact-10 | 2 | 0.5 | 1 | 0.0004017 | 0.16077 | 5.0040 | PASS |
| impact-11 | 2 | 0.5 | 0.5 | 0.0000601 | 0.02404 | 5.0005 | PASS |
| impact-12 | 2 | 0.5 | 0.25 | 0.0000234 | 0.00935 | 5.0003 | PASS |
| impact-13 | 2 | 1 | 1 | 0.0008034 | 0.16077 | 10.0081 | PASS |
| impact-14 | 2 | 1 | 0.5 | 0.0001202 | 0.02404 | 10.0010 | PASS |
| impact-15 | 2 | 1 | 0.25 | 0.0000467 | 0.00935 | 10.0007 | PASS |
| impact-16 | 2 | 2 | 1 | 0.0016067 | 0.16077 | 20.0161 | PASS |
| impact-17 | 2 | 2 | 0.5 | 0.0002404 | 0.02404 | 20.0020 | PASS |
| impact-18 | 2 | 2 | 0.25 | 0.0000935 | 0.00935 | 20.0014 | PASS |

本机Intel Core i9-14900K，CPU FP64；无远端混合计时，零渲染。资源限制16GiB/两核配额/128任务/swap0/1800s，独占研究窗口；环境安装16.252s，正式启动服务0.896s。18例循环总墙钟0.05879s，其中场景准备累计0.01029s、原生步进0.01167s、观测0.01804s；余量含压缩/写出等。独立评分0.02105s，服务0.385s。毫秒级观测开销显著，不据此作引擎速度排名。运行文件验证与导入在循环计时外，服务墙钟包含这些成本；完整发布门禁另计。

Source protocol/runner/scorer commit: `3edc3eff7e0b125233fabe132fc13abddc7b5f48`. Native MuJoCo3.15.0, package record hash `a48c3263e40378576b39f2739cc8d5b151a56ffd69ca0fcc11d66b32b60668e1`. This analytical primitive is separate from whole-grasp/backend qualification.

[Machine-readable results](evidence/elastic-impact/results.json) · [Archive digest](evidence/elastic-impact/archive.json) · [Raw release asset](https://github.com/huangkiki/Dexlab/releases/download/v0.44.0/elastic-impact-raw-v1.zip). Archive 282871bytes; SHA256 `56fb67cf6ffa5cf930ae2dbe777504d2fe28c3f41d2e68e00f9490dd239a5b3c`; every entry read back. No physics rerun is needed to score:

```bash
python -m dexlab.impact_score --input extracted-archive --output rescored.json
# New, explicitly requested reproduction only:
python -m dexlab.impact_run --manifest docs/evidence/elastic-impact/manifest.json --output new-run
```

评分先核对原生参数/哈希、完整轨迹、力的时刻、逐体冲量与初态。4项单测覆盖解析代数、合成弹性记录、9类损坏证据和动量守恒但非弹性的负例。证据链不等于真实材料验证。正式结果18例，无重复试验或按结果调阈值。
