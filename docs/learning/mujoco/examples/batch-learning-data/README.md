# E5 原创批量阅读片段

配套[CPU批量课](../../docs/cpu-batching.md)、[学习与随机化](../../docs/learning-and-randomization.md)及[记录课](../../docs/recording-and-replay.md)。

`slider.xml`是一个无重力、关闭几何碰撞的单滑动关节与普通motor；输入范围为[-1,1]，gear=1，position/velocity传感器没有history。`cpu_rollout.py`构造4条轨迹和2个独立worker工作区，使用原生state API保存初态，显式提供控制与零warmstart，通过持久`Rollout`对象取得state/sensordata。

本轮只检查Python AST和XML结构，没有import MuJoCo、编译模型、运行rollout或计时。执行脚本会编译并推进物理；不将运行作为本阶段验收命令。没有预存输出或宣称运行成功。

阅读顺序：

1. 看每次构造`MjData`，确认没有用列表乘法制造共享写对象；model在调用中保持只读。
2. 看`mj_stateSize`与`mj_getState`，确认没有把3.15的FULLPHYSICS误写成旧版维数公式。
3. 看显式control数组，避免默认mask下`control=None`留下旧ctrl。
4. 对照C++循环看积分后的state与留下的sensordata；示例未补post-step forward，不能把二者当作完全同步读数。
5. 看有限值/时间检查的局限：warning分支可能填充后续帧，最后一步warning却未必出现时间停滞；此检查不是逐轨迹warning审计或物理验收。

该模型不涉及sleep、IPC、插件、SO3输入、多模型结构或GPU，不能以这个片段推断相关能力。学习奖励、自动reset和外部RL适配器由课程解释其契约，未包装成新框架。后续实验复用DexLab。
