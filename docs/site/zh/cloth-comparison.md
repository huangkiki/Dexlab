# 布料：同一场景，不同引擎

先看布怎么动，再看数值检查。下方回放历史记录的真实顶点，使用相同的固定相机、光照和时间轴；没有重跑物理、移动顶点来消除穿透，或给网格增加虚构褶皱。

## 下垂：固定一边，释放布条

```{image} ../../../docs/evidence/cloth-studio/sag.gif
:alt: 同一布条在四个引擎的代表配置下的完整三秒下垂记录
:width: 1280px
```

```{raw} html
<p><a href="_static/cloth-studio/sag.mp4">完整视频</a> · <a href="_static/cloth-studio/sag.json">逐帧时间与来源</a></p>
```

比较悬垂形状、振荡和表面穿越。每格显示该条完整记录的协议检查结果；绿色只表示通过规定检查，不代表布料参数已符合真实织物。浅色地面是展示背景，短杆标记原有固定边；它们不参与物理计算，这个实验没有地面接触。

## 覆盖球体：看接触处，而不只看外轮廓

```{image} ../../../docs/evidence/cloth-studio/drape.gif
:alt: 同一自由布片覆盖球体；失败与最大穿透值保留在各配置画面内
:width: 1280px
```

```{raw} html
<p><a href="_static/cloth-studio/drape.mp4">完整视频</a> · <a href="_static/cloth-studio/drape.json">逐帧时间与来源</a></p>
```

布片从静止释放，落向半径 60 mm 的球体与地面。每格同时给出整段记录的最大穿透量；布落到地面以下时不会被移回表面。动图不能检验两个采样帧之间的碰撞，结论仍以独立评分为准。

## Newton 的其他求解器也保留

上面先并排展示 MuJoCo、SuperDex、Newton VBD、PhysX，便于看清布面。下方展开全部八种配置，其中 Newton 有五种；每张动图内的相机与时间轴仍统一。

![八配置下垂](../../../docs/evidence/cloth-studio/sag-profiles.gif)

![八配置球面覆盖](../../../docs/evidence/cloth-studio/drape-profiles.gif)

```{raw} html
<p><a href="_static/cloth-studio/sag-profiles.mp4">下垂完整视频</a> · <a href="_static/cloth-studio/sag-profiles.json">来源</a> · <a href="_static/cloth-studio/drape-profiles.mp4">覆盖完整视频</a> · <a href="_static/cloth-studio/drape-profiles.json">来源</a></p>
```

## 六个引擎，目前分别比较到了哪里

| 引擎／历史配置 | 现有布料证据 | 同场景动图 |
| --- | --- | --- |
| MuJoCo 3.11.0 flex | 15 条中 4 条通过；下垂有表面穿越，球面覆盖有穿透 | 下垂、覆盖球体 |
| SuperDex 1.0.0 FP64 shell | 15 条中 7 条通过；覆盖球体仍失败 | 下垂、覆盖球体 |
| Newton Physics 1.7.0.dev0，`2dee3234` | XPBD／VBD／SemiImplicit／Featherstone 各 8/15，Style3D 9/15；五种配置属于同一个引擎 | 五种配置全部展示 |
| PhysX 表面可变形体，Isaac Sim 5.1.0.0 | 另一批 15 条：10 通过、1 表面穿越失败、4 逐节点外力实验不支持 | 使用最终批次的对应记录 |
| Genesis 1.4.3 PBD | 已做接触、动量交换与夹布诊断；尚无这套同输入基准记录 | 暂无匹配记录 |
| Drake | 现有仓库没有通过资格验证的同协议薄布料记录 | 暂无匹配记录 |

这是**四引擎的历史响应对照，加六引擎覆盖说明**，尚不是完整六引擎布料基准。PhysX 的宿主版本不等于原生核心版本；旧记录中的“107.3”不能补齐核心身份，见[版本审计](https://github.com/huangkiki/Dexlab/blob/main/docs/physx-solver-audit.md)。Genesis 的诊断结果见[布料接触报告](https://github.com/huangkiki/Dexlab/blob/main/docs/genesis-cloth.md)。

两幅动图均按清单顺序固定选择 `test-sag-00`、`test-drape-00`，展示完整 0–3 s，正常速度；没有按结果挑选最好的一条。完整历史批次仍为 [105 条／七配置](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/evidence/heldout-v1.json)和[另行记录的 PhysX 批次](https://github.com/huangkiki/Dexlab/blob/main/demos/physx-contact/evidence/cloth-v1.json)，没有重新标为新留出集。材料未做跨引擎标定，迭代预算和精度也不同，因此不能用外观或通过数排名物理精度、速度。

## 从 RSS 借鉴了什么

[RSS 的布料示例](https://github.com/robosimstudio/robosimstudio/blob/23417de77edf59d614531a833334ed4e2206fc2c/examples/01_cloth/02_engines.py)让同一布片切换 Newton、SuperDex、Genesis；[渲染配置](https://github.com/robosimstudio/robosimstudio/blob/23417de77edf59d614531a833334ed4e2206fc2c/robosimstudio/core/render/look.py)提供有环境背景、主光与补光的呈现。这里借鉴这些展示方法，统一了场景与视角，并保留记录中的低分辨率几何。布面纹理与平滑法线只影响光照。

RSS 的[夹布示例](https://github.com/robosimstudio/robosimstudio/blob/23417de77edf59d614531a833334ed4e2206fc2c/examples/01_cloth/00_towel.py)采用单向耦合，机械臂不会感到布的反力；这不作为 DexLab 摩擦夹持成功的依据。[机器人夹布](experiments.md)仍有独立的模型、记录和评分。

## 重新生成

从[布料基准](https://github.com/huangkiki/Dexlab/blob/main/demos/cloth-benchmark/README.zh-CN.md)及[PhysX 原始档案](https://github.com/huangkiki/Dexlab/releases/download/v0.11.0/v0.11.0-physx-cloth-evidence.tar.gz)准备同一 case 的记录，然后在仓库环境中运行：

```bash
.venv/bin/python demos/cloth-benchmark/src/render.py \
  /path/to/test-sag-00-mujoco \
  /path/to/test-sag-00-superdex-shell \
  --output /path/to/new-comparison
```

一次可传 1–8 条记录。输入、初态、静止网格或时间轴不匹配会拒绝拼接；输出目录必须新建且位于原记录之外。PNG 检查帧、MP4、GIF 和来源文件一起生成。渲染器只读输入，记录前后哈希，执行零个物理步。
