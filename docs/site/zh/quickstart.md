# 安装与第一次复现

## 历史演示环境

当前已发布安装脚本复现的是原固定版本，**不是最新稳定版比较环境**。新实验采用最新稳定版的升级与资格由 [#41](https://github.com/huangkiki/Dexlab/issues/41) 跟踪，不能在旧环境里直接升级后沿用旧验收结论。

Linux x86_64，安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 后：

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# 或选择官方 SuperDex FP64 路径
bash demos/apple-stem-grasp/run.sh --backend superdex
```

无显示环境添加 `--headless`。首次准备 SDF 与规划会耗时，窗口显示不等于动力学已验收。只运行此演示不需要模型 API key。完整实验及批量渲染在实验服务器运行，桌面只做受资源限制的轻量工作。

## 验收与记录

运行后保留配置、实际关节/物体轨迹、原生接触、独立评分、日志及连续近景。通过依赖于完整的离桌、支撑、保持、穿透与动量平衡检查，不能只看末帧或 GIF。

[详细安装与依赖](https://github.com/huangkiki/Dexlab/blob/main/docs/installation.zh-CN.md) · [命令与输出目录](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.zh-CN.md) · [资产许可与来源](https://github.com/huangkiki/Dexlab/blob/main/docs/ASSETS.zh-CN.md)

## 仅构建文档

文档环境不安装 DexLab、PyTorch、MuJoCo 或机器人资产：

```bash
uv venv --python 3.12 .venv-docs
uv pip install --python .venv-docs/bin/python -r docs/site/requirements.txt
.venv-docs/bin/python scripts/build_docs.py
.venv-docs/bin/python -m http.server 8000 --directory docs/_build/html
```

打开 `http://localhost:8000`，默认进入中文，可切换英文。构建把警告作为错误；它不运行任何物理仿真。
