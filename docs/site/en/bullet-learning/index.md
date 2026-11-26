# Bullet Physics learning module

Drop a box from Python and read its pose, velocity and contact force after every step. **Bullet Physics** is the engine. **PyBullet** is the Python interface used here. The exercises use the headless CPU `DIRECT` path.

## Start here

1. [Step through a box drop and read the support force](box-contact.md). Run the same script with collision enabled and disabled, and compare the contact force and fall speed.
2. [Diagnose sliding and load at a joint](friction-and-joints.md). Slide a box down an incline, then compare a joint command, its measured angle and motor torque.

The introductory example uses Python 3.11 and PyBullet 3.2.7. See [PyPI](https://pypi.org/project/pybullet/3.2.7/) for supported platforms and distribution files.

{ref}`All courses <all-courses>` · [The same exercise in Chaos](../chaos-learning/index.md) · [Bullet upstream source](https://github.com/bulletphysics/bullet3)

```{toctree}
:hidden:

box-contact
friction-and-joints
```
