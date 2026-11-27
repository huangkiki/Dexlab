# RaiSim 斜面九例

**RaiSim 2.16.0 通过 6/9，记录全部有效。** 15° 静止和 15° 名义零摩擦各通过三例。35° 有摩擦滑动时，三个步长下的方块都在约 55 ms 达到旋转上限，最终最大转角约 48°。{ref}`查看十引擎斜面矩阵与曲线 <incline>`

| 同一协议的工况 | 2 ms | 1 ms | 0.5 ms |
| --- | --- | --- | --- |
| 15° 静止，μ=0.5 | 通过 | 通过 | 通过 |
| 35° 滑动，μ=0.5 | 未通过 | 未通过 | 未通过 |
| 15° 名义零摩擦，μ=0 | 通过 | 通过 | 通过 |

## 怎样跑的

40 mm、64 g 的方块从底面贴合斜面、速度为零开始，只受重力与接触作用，跑 2 s。沿用原协议的九例、参考解和评分阈值。原生路径用 Linux x86-64 上的 RaiSim C++ `World::integrate()`，CPU 双精度，刚体盒与斜放厚板。动态、静态摩擦填同一 μ，恢复系数、滚动与旋转摩擦系数均为零。默认接触求解器的迭代上限为 150，行误差容差为 10⁻⁸。禁用休眠。 [原斜面协议](https://github.com/huangkiki/Dexlab/blob/main/docs/incline-comparison-protocol.zh-CN.md) · [RaiSim World API](https://raisim.com/api/raisim/World.html)

记录每一步的位姿、线速度、角速度、接触位置、接触坐标系中的冲量及其作用对象。用坐标系转置和对象符号把冲量变换到世界坐标系，再对齐到该步的动量变化。九例的最大单步残差为 2.1×10⁻¹⁶ N·s，通过原协议的 10⁻⁷ N·s 门槛。另跑的 1 ms 无地板对照全程无接触，方块自由下落并穿过原斜面位置，正确被拒绝。负对照单列。 [RaiSim Contact API](https://raisim.com/api/raisim/Contact.html)

## 滑动三例怎样失效

三例均从静止开始。第一步没有接触冲量。第二步各有四个接触点，切向冲量分布已有偏置，合起来对方块施加了绕斜面法向的角冲量。就像一块书板下滑时，底下几处摩擦拉得不均，书板会在原来的平面里转向。这个类比只描述转动方向，表中的角冲量和角度来自原生记录。

| 步长 | 第一次接触后的时间、法向角速度 | 首次超过 0.01 rad | 最大转角及时间 | 位移 / 速度 RMSE |
| --- | --- | --- | --- | --- |
| 2 ms | 4 ms，−0.01283 rad/s | 第 28 步，56 ms，0.01071 rad | 0.83464 rad，0.814 s | 16.85 mm / 26.50 mm/s |
| 1 ms | 2 ms，−0.00761 rad/s | 第 55 步，55 ms，0.01025 rad | 0.83398 rad，0.815 s | 16.05 mm / 26.32 mm/s |
| 0.5 ms | 1 ms，−0.00381 rad/s | 第 110 步，55 ms，0.01016 rad | 0.83374 rad，0.815 s | 15.69 mm / 26.29 mm/s |

第一次接触步，三档的法向轴角冲量依次为 −0.2190、−0.1299、−0.0650 μN·m·s。逐步用接触点相对步初质心的位置与世界坐标冲量做叉乘。总角冲量与方块的角动量变化在三个工况中均吻合到 3.5×10⁻²⁰ N·m·s 内。第一处有证据的偏差是切向冲量产生平面内旋转。三个工况仍持续获得支撑，力平衡误差也通过了评分，旋转及位移、速度误差分别超过 0.01 rad、10 mm、10 mm/s 门槛。步长缩小四倍后旋转仍然存在。

这批数据定位到了接触冲量的分布，尚无法唯一确定分布偏置由哪个求解细节产生。进一步判因需要固定 35°、初态与步长，镜像接触几何或单独改变求解器的接触顺序，检查首次接触的有符号角冲量是否跟着改变。结论适用于本次固定配置及协议。 [判因边界和对照条件见 #431](https://github.com/huangkiki/Dexlab/issues/431)

## 下载与复算

```{raw} html
<p><a href="_static/incline-extension/raisim-native-v1.zip">原生记录 ZIP</a> · <a href="_static/incline-extension/raisim-results.json">九例评分与负对照 JSON</a> · <a href="_static/incline-extension/manifest.json">冻结协议 JSON</a></p>
```

压缩包包含逐步状态、接触点与冲量、求解器迭代、原生设置读回、评分及文件校验清单。 [从记录复算或重新运行](https://github.com/huangkiki/Dexlab/blob/main/demos/contact-benchmark/INCLINE_EXTENSION.md#raisim-2160) · [RaiSim 安装说明](https://raisim.com/sections/Installation.html)
