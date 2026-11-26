(contact-distance-thresholds)=
## 先查 MuJoCo 版本，再看两道阈值

以下针对普通 geom 接触。表中的 `margin` 和 `gap` 指这对几何实际使用的值。

| MuJoCo 版本 | 检测距离阈值 | 施力距离阈值 `includemargin` |
| --- | --- | --- |
| 3.9 起 | `margin + gap` | `margin` |
| 3.9 以前 | `margin` | `margin - gap` |

设定生效后，碰撞距离 `dist` 小于检测阈值才可能有接触记录，小于施力阈值才进入普通接触的施力区。3.9 起，自动配对的两个 geom 各自的 `margin` 相加，`gap` 也相加。显式 `contact/pair` 使用 pair 的值。启用了全局接触覆盖时，再查 `o_margin`。

从旧版迁移且使用了非零 `gap`，按发布说明用 `margin_new = margin_old - gap_old`、`gap_new = gap_old`，再读回两个阈值。对于允许负 `margin` 的新版，仍需保持 `margin + gap >= 0`。[MuJoCo 3.9 迁移说明](https://mujoco.readthedocs.io/en/4.0.0/changelog.html#version-3-9-0-may-27-2026)

## 看起来还没碰上，物体已经被推走

- 从两表面分离开始逐步靠近。按同一物理步记录目标 geom 的 `dist`、`includemargin`、`efc_address`，以及 `mj_contactForce` 的法向力。找到首次有法向力的那一步。
- 若此时 `0 < dist < includemargin`，施力阈值使物体提前受力。在新版减小这对几何的有效 `margin`，保持其余设置固定，复查首次施力距离和静止时的表面间距。若 `dist` 已经非正而画面仍有缝，检查碰撞几何与视觉网格的偏置。
- 如果只想让控制器提前感知靠近，见 [`gap`](gap.md)。若接触开始时机符合预期，但随后压得过深或弹跳，查 [`solref` 和 `solimp`](soft-constraint.md)。

{ref}`按现象查接触参数 <contact-tuning>`
