## 球落到桌面时，这两个参数分别管什么？

只看一个已经启用的法向接触。设 $r$ 是约束位置误差，$v$ 是接触点的法向相对速度。以零接触裕量为例，球压入桌面时 $r<0$，向下运动时 $v<0$。MuJoCo 用弹簧和阻尼的形式计算参考加速度，因此压入和继续靠近都能产生朝分离方向的纠正。

$$
a_\mathrm{ref}=-bv-kr
$$

这里 $b$ 是约束空间里的阻尼，$k$ 是刚度。对单个标量约束，可以用下面的关系理解阻抗的作用。$a_\mathrm{free}$ 是自由运动的加速度，$d$ 是无量纲阻抗，$a_\mathrm{c}$ 是施加约束后的加速度。

$$
a_\mathrm{c}=(1-d)a_\mathrm{free}+d\,a_\mathrm{ref}
$$

$d$ 越接近 1，响应越接近恢复目标。多个接触会通过同一物体的质量和惯量耦合，不能用这条单约束关系直接算整只手的接触力。[MuJoCo 约束动力学](https://mujoco.readthedocs.io/en/4.0.0/computation/index.html#solver-parameters)

(soft-constraint-solref)=
## solref 的两种写法

- **正格式 `timeconst dampratio`**，例如 `solref="0.02 1"`。20 ms 是恢复时间常数，阻尼比 1 对应临界阻尼。固定阻尼比，缩短时间常数通常使恢复更快、接触更硬。调整阻尼比也会改变内部刚度。
- **直接格式 `-stiffness -damping`**，例如 `solref="-4000 -80"`。两个输入都是非正值，幅值分别控制约束空间的刚度与阻尼。MuJoCo 还会按阻抗缩放这些值，材料的 N/m 则由力与位移的关系标定。

正格式默认受 `refsafe` 保护，有效 `timeconst` 至少为两倍仿真步长。假设步长为 2 ms，填 3 ms 和填 4 ms 都会按 4 ms 来算。接触上的 `solref` 读回可以仍显示填写的 3 ms，因此还要一起核对步长和保护开关。[MuJoCo 的 `refsafe` 规则](https://mujoco.readthedocs.io/en/4.0.0/XMLreference.html#option-flag-refsafe)

(soft-constraint-solimp)=
## solimp 的五个数

默认是 `solimp="0.9 0.95 0.001 0.5 2"`。它描述阻抗如何随位置误差的大小 $|r|$ 变化。

| 顺序 | 参数 | 作用 |
| --- | --- | --- |
| 1 | `d0` | 误差为零时的阻抗。 |
| 2 | `dwidth` | 误差达到过渡宽度及更大时的阻抗。 |
| 3 | `width` | 过渡跨越的误差量。用米描述法向距离时，0.001 表示 1 mm。 |
| 4 | `midpoint` | 过渡曲线拐点在宽度内的相对位置，0.5 表示居中。 |
| 5 | `power` | 曲线的形状，1 对应线性过渡。 |

例如把前两项都设成 `0.9`，阻抗保持恒定。设为 `0.2 0.95` 时，刚开始接触较柔，误差增到 `width` 后介入更强。**width 定义阻抗过渡的距离。** 施力时机和检测范围分别见 [`margin`](margin.md) 与 [`gap`](gap.md)。

椭圆摩擦锥的摩擦分量以及关节、肌腱的干摩擦约束，其位置误差恒为零，所以阻抗曲线在 $d(0)$ 处取值。对这些摩擦约束，正格式用时间常数来衰减相对速度，忽略阻尼比。直接格式使用阻尼，忽略刚度。显式接触对可用 `solreffriction` 为椭圆锥的摩擦分量单独指定参考响应。[MuJoCo 摩擦约束](https://mujoco.readthedocs.io/en/4.0.0/modeling.html#friction) · [`solreffriction` XML 字段](https://mujoco.readthedocs.io/en/4.0.0/XMLreference.html#contact-pair-solreffriction)

(soft-constraint-readback)=
## 参数改了，为什么接触看起来没变？

1. **先确认接触参与求解。** 读取目标接触的 `dist` 和 `efc_address`。`efc_address=-1` 表示它没有进入活动约束。若根本没检测到这对几何，先查形状、碰撞过滤和检测时刻。
2. **再看这对接触实际拿到什么值。** 对自动生成的 geom 接触，优先级高的一侧决定 `solref` 和 `solimp`。同优先级按 `solmix` 加权，任一侧用直接格式时，`solref` 改为逐项取最小值。还要检查显式 `contact/pair` 和全局 `override`。读 `data.contact[i].solref`、`solimp` 时同时核对步长与 `refsafe`。
3. **最后做单变量对照。** 例如球落桌面时，固定初始高度、质量、几何和积分设置，只改 `timeconst` 或阻抗曲线。对齐接触建立时刻及采样时点，比较法向力、峰值压入、反弹高度和稳定时间。若问题是沿桌面打滑，先核对法向载荷、摩擦系数和 `condim`，再决定是否调整摩擦响应。

[MuJoCo 接触读回字段](https://mujoco.readthedocs.io/en/4.0.0/APIreference/APItypes.html#mjcontact) · [DexLab 接触、摩擦与求解课程](../mujoco-learning/contact.md) · [DexLab 法向接触响应对照](../contact-response.md)
