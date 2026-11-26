# Bullet Physics 学习模块

先用 Python 让一个方块下落，再逐步读取位姿、速度和接触力。**Bullet Physics** 是引擎，**PyBullet** 是这门课使用的 Python 接口。练习走无需图形窗口的 CPU `DIRECT` 路径。

## 从这里开始

1. [逐步读取方块落地与法向支撑](box-contact.md)。运行同一脚本对照正常碰撞和禁碰撞，看接触力与下落速度如何一起变化。
2. [排查滑动与关节带载](friction-and-joints.md)。让方块在斜面上滑动，再比较关节的命令、实际角度与电机力矩。

入门示例使用 Python 3.11 和 PyBullet 3.2.7。支持的平台与分发文件见 [PyPI](https://pypi.org/project/pybullet/3.2.7/)。

{ref}`全部课程 <all-courses>` · [同主题的 Chaos 练习](../chaos-learning/index.md) · [Bullet 上游源码](https://github.com/bulletphysics/bullet3)

```{toctree}
:hidden:

box-contact
friction-and-joints
```
