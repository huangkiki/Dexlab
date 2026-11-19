# NeuralActuator：执行器误差要单独建模，接触仍要交给物理

## TL;DR

**NeuralActuator 最值得借鉴的是一个独立执行器层：用伺服命令、关节状态、电流／负载、电压、温度和跟踪误差的历史，学习送入仿真的有效 effort。它不该被当成接触模型。**

作者用可微仿真监督 torque surrogate，避免依赖 `τ = K_tI` 和真实 torque 标签。在低成本机械臂上，这显著改善了轨迹与外力预测；但论文训练时主动关闭接触，默认的 implicit coupling 也让预测外力不进入状态更新。对 DexLab，正确顺序是“先证明执行器 telemetry 可辨识，再只替换执行器层”，接触、物体动力学和任务评分继续独立。

## 一个 500 g 负载暴露了什么

机械臂夹住 500 g 物体。理想的低成本控制链把电流乘常数变成关节力矩：

$$
\tau=K_tI
$$

真实舵机还经过减速器、摩擦、背隙、饱和和温升。同一条位置命令下，关节可能继续下沉，但控制端仍认为目标已经发送。这个误差若留进仿真，容易让后续诊断把执行器问题误写成 contact solver、物体质量或策略问题。

NeuralActuator 读取过去 8 帧和当前帧的命令、位置、速度、电流或 load register、电压、温度与跟踪误差。Transformer 直接预测仿真需要的 generalized effort：

$$
\mathbf s_{t+1}=F_t(\mathbf s_t,\boldsymbol\tau_t^{pred}),
\qquad
\boldsymbol\tau_t^{pred}=g_\theta(\mathbf X_t).
$$

训练不需要 torque 标签；真实未来位姿经可微仿真回传 loss。网络因此学到的是“能让轨迹变对的 effort”，而不是可辨识的真实 actuator torque。

## 哪个结果最有价值

OpenManipulator-X payload benchmark 上，NeuralActuator 的 force MAE 为 `0.12 N`；论文报告的 GMO、ID-Friction、ID-Linear 为 `0.66/1.23/1.41 N`。

这组数字最有价值的地方不是“神经模型赢了”，而是：三个 model-based baseline 每步读取 GT 机器人状态，NeuralActuator 反而使用自己的 rollout 状态。结果支持“在这个低成本舵机和这套 telemetry 上，固定线性电流—力矩关系不足”，但不能推出所有模型方法都无效。

另一个独立信号是电机受限检测：在 Joint 3 加橡皮筋机械阻力后，模型达到 `91.0%` accuracy、`96.2%` recall 和 `0.95` AUC。它说明 telemetry 历史里确实存在执行器状态信息；但这不是寿命预测或通用故障诊断。

## 不能忽略的反例：contact 被关掉了

官方训练入口明确设置：

```text
mjDSBL_CONTACT
```

benchmark 中 payload 不作为场景几何，gripper 跟随记录孔径，训练轨迹按设计不产生场景碰撞。

默认的 implicit coupling 只有 torque surrogate 驱动状态；外力 head 虽然受监督，但不施加到仿真。explicit coupling 把外力真正注入动力学，却在两个低成本平台上都更差。

因此，较准的 pose rollout 可能来自：

- actuator 非线性；
- 未建模载荷；
- 被 torque surrogate 吸收的接触效应；
- 记录 telemetry 与 rollout 状态之间的反馈。

这几种解释没有被统一成可辨识的 actuator torque。把 NeuralActuator 放进切割、布料、抓取或 pinch 仿真后看到更低 pose error，也不能据此声称接触物理更准。

## DexLab 应该怎样借鉴

### 直接借鉴

1. **执行器误差单独成层。** command、q、qdot、current/load、voltage、temperature、torque surrogate 和 contact force 分别记录，不合成一个黑盒误差。
2. **先做 telemetry 资格。** 每步需要单调时间、命令与反馈来源、单位、方向、缺失值、轨迹 ID 和硬件实例。
3. **轨迹级 split。** 不随机切相邻 frame；热漂移、摩擦历史和同一安装批次会泄漏。
4. **保留负例。** free motion、no-load、normal motor、mechanically restricted motor、contact 与 matched no-contact 都要保留。

### 需要验证

未来若拿到低成本舵机日志，可先做一个 actuator-only pilot：

- 单平台、单安装实例；
- 比较 direct torque surrogate、residual `K_tI + Δτ` 和 GMO；
- contact solver 保持开启；
- 用独立力参考检查模型有没有把载荷吸收进 actuator effort；
- 同时报告 pose、force、saturation、temperature 和 no-contact false positive。

模型训练不是第一步。第一步是证明现有数据能否区分“命令没送达／执行器跟踪误差”和“真实接触载荷”。

### 暂不采用

- 不用 implicit torque surrogate 替代接触求解；
- 不把 3D 末端 resultant 力当作多指接触；
- 不把记录 telemetry 的 rollout 当反事实动作预测器；
- 不把 condition score 外推为通用电机健康诊断；
- 不在没有独立力参考的日志上宣称外力感知已验证。

## 第一个可验证问题

**DexLab 当前的一条执行器日志，能否在时间、单位、正负方向和力参考上，把执行器跟踪误差与真实接触载荷分开？**

如果答案是否定，先补数据合同；如果答案是肯定，再做单平台执行器 pilot。只有这一步通过，NeuralActuator 才会改变 DexLab 的实验判断，而不是只增加一个更难解释的模型。

## 继续阅读

- [论文 arXiv v2](https://arxiv.org/abs/2607.11734v2)
- [项目主页](https://people.csail.mit.edu/frankzydou/projects/NeuralActuator/index.html)
- [官方代码固定版本](https://github.com/Frank-ZY-Dou/Dynamics-Modeling/tree/541a93aac4368e73883e86a51f31a7add6bde059/NeuralActuator)
- [DexLab Discussion #414](https://github.com/huangkiki/Dexlab/discussions/414)
- [Research intake #415](https://github.com/huangkiki/Dexlab/issues/415)

## 证据范围

本文基于 arXiv `2607.11734v2` 与官方提交 `541a93aac4368e73883e86a51f31a7add6bde059` 的静态代码核查。所有数值均为作者报告；本轮没有运行 MJX、Newton、MuJoCo Warp、SuperDex、OMX、SO-101、Franka，也没有采集新的真机数据。
