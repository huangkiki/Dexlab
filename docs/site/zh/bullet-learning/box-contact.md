# Bullet Physics：逐步读取方块落地与法向支撑

一个 1 kg 的方块停在水平地面时，平均向上支撑力应接近自身重量 9.81 N。先让脚本读回接触，再只关掉这对物体的碰撞，检查支撑是否随之消失。

## 跑一次正反对照

先{download}`下载 bullet_box_contact.py <../../../learning/examples/bullet_box_contact.py>`，在脚本目录执行。以下命令适用于有对应 wheel 的 Linux x86-64 环境。

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: pybullet==3.2.7 numpy==2.2.6
.venv/bin/python bullet_box_contact.py
```

这个 PyBullet wheel 在导入时依赖 NumPy，因此命令显式安装两者。

脚本用 `GEOM_BOX` 建立边长 0.20 m 的方块，中心从 1.00 m 开始落向位于 Z=0 的静止平面。每次 `stepSimulation()` 推进 1/240 s，随后读取同一步的接触。两次都运行 480 步。第二次只关闭方块与地面的碰撞。

```{literalinclude} ../../../learning/examples/bullet_box_contact.py
:language: python
```

## 读输出

下面是 DexLab 用 Linux x86-64、Python 3.11.14 和 PyBullet 3.2.7 运行上面脚本的结果。

| 看什么 | 正常碰撞 | 关闭碰撞 |
| --- | --- | --- |
| 第一次有向上支撑 | 第 104 步，0.433 s | `null` |
| 2 s 时的中心高度、竖向速度 | 0.09999 m，约 0 m/s | −18.661 m，−19.62 m/s |
| 最后 0.5 s 平均支撑 | 9.81 N | 0 N |

`getContactPoints(box, floor)` 读回上一次仿真步的接触。每条记录的 `contactNormalOnB` 指向 Box，用它的 Z 分量乘 `normalForce`，再把所有接触点加起来，得到竖直方向的法向支撑。这个平地练习里法向接近竖直，斜面上应按所关心的方向投影。可把 `getClosestPoints` 用于几何距离查询，它返回的距离本身不能说明地面在承重。 [PyBullet 官方入门指南](https://github.com/bulletphysics/bullet3/blob/master/docs/pybullet_quickstartguide.pdf) · [上游接触力示例](https://github.com/bulletphysics/bullet3/blob/master/examples/pybullet/examples/contactFriction.py)

如果方块没有支撑，先查它是否进入了地板的接触范围，再查这对物体有没有参与碰撞。确认有接触点后，再判断法向力是否改变了竖向速度。负例的作用是验证接触读数对碰撞过滤敏感。抓取与实物材料需要另外的证据。

[课程目录](index.md) · [下一课：滑动与关节带载](friction-and-joints.md)
