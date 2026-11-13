# 一步仿真，几种时间

**物理步长决定状态多久推进一次；控制周期决定动作多久换一次；画面帧率决定你多久看到一次。** 三者可以不同。墙钟时间则是机器实际花掉的时间。

## 先看夹爪的 20 ms

设物理步长为 2 ms，每 10 步更新一次夹爪目标。于是控制周期为 20 ms，频率为 50 Hz。两次目标之间仍在计算动力学；保持控制输入不等于冻结机器人，也不保证执行器力保持常数。

把物理步长减半，同时保持每 10 步更新控制，控制频率就会翻倍。如果想只比较物理步长，应相应调整重复步数，保留原控制周期。

## 调一调时间轴

先预测：把下面的 2 ms 改成 1 ms，控制频率会怎样？再把重复步数改为 20，看看能否回到原来的控制周期。

```{raw} html
<div class="time-lab" id="time-lab" data-enhanced hidden>
  <label for="physics-step">物理步长 h：<output id="step-value" for="physics-step">2 ms</output></label>
  <input id="physics-step" type="range" min="1" max="10" step="1" value="2">
  <label for="control-repeat">每 N 个物理步更新控制：<output id="repeat-value" for="control-repeat">10</output></label>
  <input id="control-repeat" type="range" min="1" max="20" step="1" value="10">
  <div class="time-results" aria-live="polite"><div><span>控制周期 N × h</span><output id="control-period">20 ms</output></div><div><span>控制频率 1000 / (N × h)</span><output id="control-frequency">50.0 Hz</output></div></div>
  <svg class="timeline" viewBox="0 0 540 150" role="img" aria-label="100 ms 仿真时间内的物理步进与控制更新；精确数值见上方输出">
    <text x="30" y="20">物理步进</text><text x="30" y="69">控制更新</text>
    <path class="axis" d="M30 41H510 M30 86H510"/><g id="time-ticks"></g>
    <text x="30" y="130">0 ms</text><text x="510" y="130" text-anchor="end">100 ms</text>
  </svg>
  <p class="note" id="time-explanation"></p>
  <p class="note">教学时间示意，不调用 MuJoCo，也不测量实时性能。</p>
</div>
<noscript><p>时间示例：2 ms × 10 步 = 20 ms（50 Hz）；1 ms × 10 步 = 10 ms（100 Hz）；1 ms × 20 步 = 20 ms（50 Hz）。启用 JavaScript 可调节时间轴。</p></noscript>
```

<details class="explanation"><summary>为什么输入保持不变，力还会变化？</summary>
<p><code>ctrl</code> 的语义由执行器定义。位置执行器的输入可以是目标位置，产生的力会随实际位置、速度等量变化；电机、激活动态与限幅又有各自的路径。不能把所有 <code>ctrl</code> 都当成直接力矩。</p>
<p>这类似于驾驶时保持油门踏板位置：保持的是输入，车辆的速度并没有被锁住。类比只帮助区分输入与状态，不替代具体执行器方程。</p>
</details>

## 观测也有自己的时刻

调用 `mj_step` 后，积分状态已经推进；派生量和传感器值由各自计算阶段产生。记录时同时保留仿真时间、采样阶段和单位，避免把不同阶段的力与位姿拼成同一瞬间。需要新状态上的派生量时，按依赖调用相应的前向计算；额外调用也可能涉及控制回调。

Python 中 `data.qpos` 通常是原生内存视图。保存历史日志时要复制数据，否则所谓“旧快照”可能随之后的步进变化。详见[状态与时间课程](../learn/mujoco/docs/state-and-time.md)；其中状态掩码与具体字段以其 3.15.0 基线为准。

## 自测：改变了哪个变量？

```{raw} html
<form class="quiz" data-answer="b" data-correct="对。N × h 决定控制周期：20 × 1 ms = 20 ms。" data-incorrect="再看 N × h：物理步长减半，重复步数要翻倍，才能保持控制周期。">
  <fieldset><legend>将物理步长从 2 ms 改为 1 ms，如何保持原来的 50 Hz 控制？</legend>
  <label><input type="radio" name="timing" value="a">仍每 10 步更新控制</label>
  <label><input type="radio" name="timing" value="b">改为每 20 步更新控制</label>
  <label><input type="radio" name="timing" value="c">把渲染改为 50 FPS</label></fieldset>
  <button type="submit" data-enhanced hidden>检查答案</button><p class="quiz-feedback" role="status" hidden></p>
</form>
<details><summary>查看解释</summary><p>每 20 步更新控制。渲染帧率不决定控制周期；同样的仿真时间也不代表相同墙钟耗时。</p></details>
```

## 带回实际系统

先读回实际步长、控制更新时间戳和重复步数，再定位采样位置。对 MATRiX 的具体集成，应检查真实调度入口与日志；不要把这里的 2 ms / 50 Hz 教学值当成系统配置。

继续读：[执行器与控制](../learn/mujoco/docs/actuation-and-control.md) · [动力学与计算流水线](../learn/mujoco/docs/dynamics-and-pipeline.md) · [官方仿真循环说明](https://mujoco.readthedocs.io/en/4.0.0/programming/simulation.html)
