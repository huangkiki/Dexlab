# DexLab

**用可复现的接触、摩擦与操作实验，研究机器人为什么抓得住、会滑脱，以及怎样选择和调整物理仿真。**

[English](https://huangkiki.github.io/Dexlab/en/latest/index.html) · [快速开始](#quickstart) · [完整实验目录](experiments.md) · [全部报告](results.md)

(research-findings)=
## 做了哪些实验

```{raw} html
<span id="visual-experiment-catalogue"></span>
```

点击实验名或动图查看完整报告与复现方法。

````{list-table}
:header-rows: 1
:widths: 20 45 35

* - 实验
  - 动图预览
  - 一句结果
* - ```{raw} html
    <span id="rss"></span>
    ```

    [RSS 擦拭](rss-wiping.md)
  - ```{image} ../../../docs/evidence/rss-wiping/preview.gif
    :alt: RSS 原版／关闭约束，2 倍速
    :width: 300px
    :target: rss-wiping.html
    ```

  - 辅助约束开启时保持，关闭后滑脱；当前复现的是擦拭。
* - ```{raw} html
    <span id="cut-push"></span><span id="banana-force"></span>
    ```

    [连续切割与推动](cut-push.md)
  - ```{image} ../../../docs/evidence/cutting/tofu-cut-push/surface.gif
    :alt: 豆腐状／香蕉状软材料
    :width: 145px
    :target: cut-push.html
    ```

    ```{image} ../../../docs/evidence/cutting/banana-cut-push/surface.gif
    :alt: 豆腐状／香蕉状软材料
    :width: 145px
    :target: cut-push.html
    ```

  - 合成材料可接触侧推；[独立单刀测力未证明收敛](banana-force.md)。
* - ```{raw} html
    <span id="scoring"></span>
    ```

    [交叉浅划](tofu-scoring.md)
  - ```{image} ../../../docs/evidence/cutting/tofu-scoring/particles.gif
    :alt: 原生粒子切割历史
    :width: 300px
    :target: tofu-scoring.html
    ```

  - 两次浅切后底部仍相连；颜色标记切割历史。
* - ```{raw} html
    <span id="apple"></span>
    ```

    [苹果抓梗](apple-replays)
  - ```{image} ../../../demos/apple-stem-grasp/media/mujoco-sdf.gif
    :alt: MuJoCo／SuperDex 历史脚本轨迹
    :width: 145px
    :target: experiments.html#apple-replays
    ```

    ```{image} ../../../demos/apple-stem-grasp/media/superdex-sdf.gif
    :alt: MuJoCo／SuperDex 历史脚本轨迹
    :width: 145px
    :target: experiments.html#apple-replays
    ```

  - MuJoCo／SuperDex 历史脚本轨迹均完成 3 s 保持。
* - ```{raw} html
    <span id="cloth-comparison"></span>
    ```

    [布料引擎对比](cloth-comparison.md)
  - ```{image} ../../../docs/evidence/cloth-studio/sag.gif
    :alt: 布料引擎对比
    :width: 300px
    :target: cloth-comparison.html
    ```

  - 四引擎的历史布料响应并排展示，失败与缺项保留。
* - ```{raw} html
    <span id="cloth"></span>
    ```

    [机器人夹布](experiments.md)
  - ```{image} ../../../docs/evidence/cloth-studio/grasp.gif
    :alt: 夹布、抬升与释放
    :width: 300px
    :target: experiments.html
    ```

  - 一个开发场景完成抬升、保持与释放；尚非主动折布。
* - ```{raw} html
    <span id="visual-highlight-pinch"></span>
    ```

    [夹持力对照](pinch)
  - ```{image} ../../../docs/evidence/force-limit/comparison.gif
    :alt: 驱动力限额 0.4 N／0.8 N
    :width: 300px
    :target: visual-comparisons.html#pinch
    ```

  - 同一 Genesis 协议下，驱动力限额 0.4 N 滑脱、0.8 N 保持。
* - ```{raw} html
    <span id="visual-highlight-libero"></span>
    ```

    [LIBERO 回放](libero-workflow.md)
  - ```{image} ../../../docs/evidence/visual/libero-demo0-baseline.gif
    :alt: demo 0 原生基线状态回放
    :width: 300px
    :target: libero-workflow.html
    ```

  - 500 条官方示范：任务成功 495 条，全部数值诊断通过 0 条。
* - ```{raw} html
    <span id="visual-highlight-incline"></span>
    ```

    [六引擎斜面滑动](incline)
  - ```{image} ../../../docs/evidence/visual/incline-sliding-0.001.gif
    :alt: 1 ms 步长滑动记录
    :width: 300px
    :target: visual-comparisons.html#incline
    ```

  - 比较六引擎滑动响应；相同参数数值不代表模型等效。
* - ```{raw} html
    <span id="visual-highlight-normal"></span>
    ```

    [法向接触标定](normal)
  - ```{image} ../../../docs/evidence/visual/normal-calibration.gif
    :alt: 合成目标的加载、保持与卸载
    :width: 300px
    :target: visual-comparisons.html#normal
    ```

  - 合成目标的加载拟合改善，卸载和迁移仍需分别验证。
````

[完整实验目录](experiments.md) · 动图来自实际仿真或记录回放；结果仅适用于各报告的配置与条件。

(quickstart)=
## 先运行苹果抓梗

推荐从已有安装脚本覆盖的 MuJoCo 苹果抓梗开始。需要 Linux x86_64 和 [uv](https://docs.astral.sh/uv/getting-started/installation/)；不需要模型 API key。该入口复现固定版本的历史演示，不是六引擎最新版本比较环境。

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
```

等待 SDF 准备、静置与规划后，窗口会显示抓梗、抬升和保持。输出保存在 `demos/apple-stem-grasp/runs/latest-mujoco-sdf/`；无桌面时在运行命令后加 `--headless`，切换后端用 `--backend superdex`。14 s 是仿真时长，实际计算会更久。

```bash
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/latest-mujoco-sdf
```

验收器会写出 `summary.json`；全部检查通过时 `passed` 为 `true`，失败时保留具体检查项并返回非零退出码。

[安装、依赖与资产来源](https://github.com/huangkiki/Dexlab/blob/main/docs/installation.zh-CN.md) · [任务接口与命令](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.zh-CN.md)

(research-diagnosis)=
## 场景不对时，先查什么

先核对几何、质量／惯量、控制时刻和实际接触读回，再围绕一个明确问题调整参数，用原始记录和独立评分检查结果。已有失败、修正和下一步判断见[诊断方法](diagnosis.md)。

(research-selection)=
## 新任务怎样选引擎和配置

按载荷、接触尺度、粘着／滑动、接触切换和柔顺性找相近实验，再验证候选配置。研究涉及 MuJoCo、SuperDex、Genesis、Newton Physics、PhysX 和 Drake，但各任务覆盖与验收不同；完整配置、版本和失败见[覆盖矩阵](coverage.md)，具体起点见[场景选型](selection.md)。

(solver-coupling)=
## 多个求解器怎样协同

仿真时间、电脑耗时和数据交换周期是三个不同的量。求解器之间等待会影响运行速度，反馈延迟还会影响相互作用。[用手指与海绵理解同步、迭代与 preCICE](solver-coupling.md)；preCICE 在这里是方法参考，尚未接入 DexLab。

(research-scope)=
## 当前边界与深入阅读

以经典物理规律和已有经验关系为参照。实验成功只适用于各自版本、场景和验收条件；任务成功、数值诊断与真实物理准确性分别报告。手内旋转、主动折布、真实材料标定和视觉策略能力仍需各自验证，不能从上面的动图推出。

[研究经验](experience.md) · [求解配置如何分类](solver-taxonomy.md) · [研究路线](dexterity.md) · [外部参考](references.md) · [数据与版本](https://github.com/huangkiki/Dexlab/releases)

[开发与验收约定](https://github.com/huangkiki/Dexlab/blob/main/docs/autoresearch.zh-CN.md) · [当前工作与暂停状态](https://github.com/huangkiki/Dexlab/blob/main/docs/current-work.zh-CN.md)

```{toctree}
:hidden:
:maxdepth: 1

布料引擎对比 <cloth-comparison>

实验目录 <experiments>
安装复现 <quickstart>
研究结果 <results>
完整覆盖 <coverage>
研究经验 <experience>
诊断方法 <diagnosis>

RSS 擦拭与 latch 对照 <rss-wiping>
连续切割与刀面推动 <cut-push>
香蕉单刀测力 <banana-force>
豆腐状软块对半切 <cutting>
香蕉连续切片 <banana-cutting>
豆腐交叉浅切 <tofu-scoring>
切割方法对比 <cutting-comparison>
豆腐连续两刀与独立运动 <tofu-comparison>
切割保真度与动态测量 <cutting-fidelity>

多求解器同步与 preCICE <solver-coupling>

求解配置分层 <solver-taxonomy>

可视对照 <visual-comparisons>
LIBERO 原生流程 <libero-workflow>
场景选型 <selection>
引擎与模型 <engines>
研究路线 <dexterity>
研究账本 <research-ledger>
基准 <benchmark>
外部参考 <references>
参与贡献 <contributing>
```
