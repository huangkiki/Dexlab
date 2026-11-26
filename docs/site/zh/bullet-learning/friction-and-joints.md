# Bullet Physics：排查滑动与关节带载

方块在斜面上滑动，可能是摩擦不足。机械臂在带载时偏离目标，也可能是电机到达力矩上限。两种解释都要从每步读回中检验。

## 在斜面上测摩擦

1. 从[落地脚本](box-contact.md)开始。改用静止斜板，将方块面与斜板对齐，从面间留很小间隙的静止状态释放。保持 `DIRECT`、重力、步长和迭代设置一致。记录斜板角度、两侧 `lateralFriction` 设置和方块姿态。
2. 用 `changeDynamics` 分别设置两个物体的横向摩擦，先把两侧都设为零并记录对照。剔除初次撞击窗口后，只有在持续接触且旋转很小时，才用无摩擦下滑加速度 $g\sin\theta$ 对照切向速度斜率。正例恢复摩擦时，继续读回实际位移、支撑力和滑动速度。
3. 从 `getContactPoints` 读取两个横向摩擦分量与各自方向，要合成摩擦力时先按方向还原为向量。观察到方块没滑时，只能给出该工况下未超过静摩擦门槛的证据。要测门槛，需要在接触稳定且没有先翻倒的条件下逐步增加斜角或切向载荷。

## 分开读关节命令和实测

1. 用 `loadURDF(..., useFixedBase=True)` 加载一条含旋转关节的机械臂。用 `getJointInfo` 按名称确认关节、类型及角度限制。将其他关节保持在记录好的姿态，并留出足够空间，避免碰到地面。
2. 对同一旋转关节用 `setJointMotorControl2` 设置位置目标和显式力矩上限。先跑无额外载荷，再从相同初态加固定载荷。若用 `applyExternalForce` 提供持续载荷，在每次显式步进前重发同一世界坐标系的力与作用点。
3. 每步用 `getJointState` 分别记录实际角度、角速度和电机力矩。若误差在加载后上升且电机力矩接近限额，下一次只提高限额，检查同一负载下的角度误差是否减小。默认电机会影响被动关节对照。做自由转动对照时，先设 `VELOCITY_CONTROL`，并把 `force` 设为 0 以关闭该关节电机。关节反力需要单独启用力矩传感器并检查其坐标系。

这些是延伸练习，本课公开运行记录来自方块落地对照。 [PyBullet 官方入门指南](https://github.com/bulletphysics/bullet3/blob/master/docs/pybullet_quickstartguide.pdf) · [上游关节控制示例](https://github.com/bulletphysics/bullet3/blob/master/examples/pybullet/examples/jointFrictionAndMotor.py)

[课程目录](index.md) · [DexLab 接触与摩擦基础](../mujoco-learning/contact.md)
