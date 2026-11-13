# 2. 接触几何怎样变成物理响应

[教程目录](README.md) · [上一章：仿真一步](01-simulation-step.md) · [下一章：摩擦](03-friction.md)

同一只夹爪、相同质量和摩擦系数，换引擎后物体下陷得更深。先别提高迭代数：先确认两个系统表示的是同一种接触问题。本章帮助你从碰撞几何一路追到法向响应。先修为教材伴读的离散化与边界条件部分。

## 从三个层次看一次接触

```text
形状、位姿与碰撞表示
    ↓ 候选对、距离、法向、接触点或面
接触模型与材料参数
    ↓ 本步的约束、势能或力关系
时间离散与数值求解
    ↓ 速度、位姿、力或冲量
```

渲染网格与碰撞表示可能不同。碰撞距离、接触生成阈值和材料柔顺也承担不同职责：在物体旁边提前生成候选接触，不等于材料已经被压缩相同距离。先查几何和字段消费者，再解释参数。

## 理想刚性约束与柔顺模型

以无黏附法向接触为例，令间隙 $`g`$ 在分离时为正，法向支撑力 $`f_n`$ 向外为正。理想 Signorini 条件为

```math
g\ge0,\qquad f_n\ge0,\qquad g f_n=0.
```

意思是：不能穿透、接触不能拉住物体、有间隙时没有法向支撑。$`g`$ 单位 m，$`f_n`$ 单位 N。离散求解器可能在速度、预测间隙或冲量上构造问题；不能把这三个连续条件当成所有引擎实际代码的逐行公式。

柔顺模型允许用形变或接触误差建立响应。只保留弹性的教学模型是

```math
\delta=\max(0,-g),\qquad f_n=k\delta.
```

$`k`$ 为 N/m。若负载为 10 N、$`k=10^4`$ N/m，静态平衡压缩量是 1 mm；这个结果源于所选模型，即使数值问题解得很准也不会自动变成零压缩。实际模型还可能含阻尼、非线性和限幅，上式不是任何引擎的完整接触法则。

<details><summary>进阶：为什么更硬会使数值问题更难？</summary>

在线性质量弹簧特例中，自然角频率为 $`\omega=\sqrt{k/m}`$。提高 $`k`$ 会缩短系统的特征时间。固定步长可能因此不能解析运动，局部矩阵的尺度差异也可能增大。隐式离散能改变稳定性条件，但不会自动消除时间误差或材料误差。因此应分别记录刚度、质量、步长和数值残差，不能只用“更稳定”评价结果。

</details>

## Point、hydroelastic、convex 与 IPC 怎么定位

| 名称 | 先问的问题 | 原生深入入口 |
|---|---|---|
| point contact | 用哪些点和局部几何量定义接触响应？ | [Drake 接触模型](https://github.com/huangkiki/drake-learning/blob/main/docs/contact-models.md) |
| hydroelastic | 如何由压力场与接触面汇总力、力矩？几何对是否受支持？ | [Drake 固定实现导读][drake] |
| Signorini / convex | 当前字段选择什么法则或问题？与 solver、摩擦锥、兼容模式有哪些限制？ | [Genesis 固定实现导读][genesis] |
| IPC 距离屏障 | 哪个距离定义进入屏障势能，怎样用连续碰撞检测限制一步？ | [教材伴读](../physics-based-simulation.md)，原书第 7–8 章 |

Drake hydroelastic 的压力模量以 Pa 计，point 的接触刚度以 N/m 计。数值同为 $`10^5`$ 不能叫“等刚度”。固定 Genesis 版本中，Signorini 只允许 Newton、elliptic 与非兼容模式的相应组合；`convex` 是这个引擎的原生枚举语义，不能泛化成所有凸接触方法都等价。[版本来源](source-versions.md)保留不同运行身份。

IPC 也不等于“开启 CCD”：屏障势能、可行初始状态、搜索轨迹与步长控制共同构成具体方法。教材的优化式问题不能直接替换 MuJoCo、Drake 或 PhysX 的接触模型。

## 配置与诊断练习

阅读一份接触配置时，记录：碰撞形状与尺度、间隙/穿透符号、材料参数及单位、接触模型、时间步、solver，以及观测的是瞬时力还是一段时间的冲量。原字段未读回就标未知。

| 现象 | 第一份要查的证据 | 对应判断 |
|---|---|---|
| 画面接触了却没有支撑 | 碰撞表示、过滤、实际接触集合 | 是否在数值求解前就没有形成问题 |
| 提高迭代仍有压缩 | 材料响应与平衡残差 | 是所选柔顺模型的响应，还是未解准 |
| 更小步长改变碰撞峰值 | 采样区间、冲量与峰值的定义 | 比较的是同一观测量吗 |
| 切换 hydroelastic 后报错 | 严格/fallback 模式及两侧几何属性 | 是否属于模型支持范围，而非迭代预算不足 |

1. **10 N 负载下，希望上述线性模型压缩不超过 0.2 mm，纸面刚度下界是多少？** $`k\ge 5\times10^4`$ N/m；这只用于该标量静态模型，不是完整引擎调参建议。
2. **有间隙却测到拉力一定错吗？** 先确认是不是无黏附法向接触量；驱动、黏附、关节和坐标符号会改变解释。
3. **Signorini 标签能证明离散状态绝无穿透吗？** 不能。还需读实际离散形式、容差、碰撞路径和输出证据。

## English summary

Separate collision geometry, contact/material models, and the discrete problem being solved. Signorini, compliant point contact, hydroelastic pressure integration and IPC barriers describe different assumptions. Equal parameter numbers do not establish equal materials. The equations and exercises are constructed teaching examples, not engine measurements. No native execution is included.

[drake]: https://github.com/huangkiki/drake-learning/blob/fbbe13644896862b4d6516b0ee8085292ec6159f/docs/solver-reading-guide.md
[genesis]: https://github.com/huangkiki/genesis-learning/blob/93fef2af89ad43788a534f38b603b552e9dd9aa2/docs/solver-reading-guide.md
