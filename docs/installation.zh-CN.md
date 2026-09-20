# 安装

[English](installation.md) | [简体中文](installation.zh-CN.md)

安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)，然后在仓库根目录执行：

```bash
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# 或：
bash demos/apple-stem-grasp/run.sh --backend superdex
```

安装脚本使用 **PyPI 上的官方 SuperDex 1.0.0 wheel**，并自动获取 Python 3.12，无需 Clang、CMake、SuperDex 源码仓库或 API key。目前安装脚本支持 Linux x86_64。上游虽然提供其他平台的 wheel，但本演示尚未验证原生 macOS 和 Windows 运行。

两个命令都会在 SDF 创建、苹果静置和抓取规划完成后打开交互式 MuJoCo 窗口。所选后端负责动力学，MuJoCo 负责两者的渲染。即使安装较快，启动和仿真也需要一定时间。

两者均运行 [14 秒 SDF–SDF 抓取](sdf-backends.zh-CN.md)。MuJoCo 后端使用固定版本的官方 `mujoco==3.11.0` wheel，并在本地生成动力学模型，无需引擎补丁或编译器。默认输出分别位于演示目录下的 `runs/latest-superdex-sdf/` 和 `runs/latest-mujoco-sdf/`。

无桌面的服务器可执行：

```bash
bash demos/apple-stem-grasp/run.sh --backend mujoco --headless
```

## 验证与视频

每个演示记录 14 秒仿真运动。动力学在 CPU 上运行，实际计算时间长于仿真时长。安装脚本根据带版本的[资产清单](../demos/apple-stem-grasp/assets.json)获取机器人资产包和苹果基础色纹理。小型任务专用苹果网格和参数保留在 Git 中。

```bash
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py demos/apple-stem-grasp/runs/latest-mujoco-sdf
MUJOCO_GL=egl .venv/bin/python demos/apple-stem-grasp/src/render_stem_focus.py demos/apple-stem-grasp/runs/latest-mujoco-sdf
```

另一个后端使用 `latest-superdex-sdf` 替换 `latest-mujoco-sdf`。视频导出需要 FFmpeg 和可用的 OpenGL / EGL 驱动。若要单独保留一份记录，在 `run.sh` 命令后添加 `--output demos/apple-stem-grasp/runs/my-run`。

两个已记录运行均通过完整三秒保持检查，详见 [MuJoCo 报告](../demos/apple-stem-grasp/evidence/sdf-mujoco/summary.json)、[SuperDex 报告](../demos/apple-stem-grasp/evidence/sdf-superdex/summary.json)及[验收标准](sdf-backends.zh-CN.md#验证与视频导出)。

## 运行库来源

默认安装在 `scripts/runtime-requirements.txt` 中固定以下官方发行包：

- [superdex-physics[double]==1.0.0](https://pypi.org/project/superdex-physics/1.0.0/)
- [superdex-robotics[double]==1.0.0](https://pypi.org/project/superdex-robotics/1.0.0/)

`double` 可选依赖会安装两个 FP64 实现包。在导入公开的 `superdex.physics` 和 `superdex.robotics` API 前设置 `SUPERDEX_PRECISION=fp64`。DexLab 不重新编译或分发这些 wheel；源码仓库、发布者证明和各平台文件哈希可在 PyPI 查询。本演示不需要安装总入口 `superdex` 包。

## UniLab 运行环境

传递依赖固定在 `scripts/python-constraints.txt`，对应当前验收环境。

安装器同时以 editable 方式安装 DexLab 的任务扩展，固定 `unilab==1.3.3`、`unisim-core==1.7.10`，并选择 `torch==2.9.1` 的 **CPU wheel**，不下载 CUDA 运行库。UniLab 本身仍有训练、日志和数值计算依赖，因此首次下载量明显大于原来的独立脚本；CPU Torch wheel 本身约 176 MiB。安装后无需联网即可运行抓取。不要安装 `unilab[superdex]` 来替代本演示依赖：该 extra 使用 `superdex-physics-uni`，不是当前验收的官方 1.0.0 FP64 组合。

当前采用 UniLab 任务注册与环境生命周期，物理场景由任务管理；不宣称已使用 UniSim 内置后端。详见[任务接口](../demos/apple-stem-grasp/README.zh-CN.md#unilab-任务接口)。

## 可选：从 UniLab 源码构建

需要原始 UniLab 源码基线的开发者可执行：

```bash
bash scripts/setup.sh --source
SUPERDEX_ROOT="$PWD/vendor/project_superdex" bash demos/apple-stem-grasp/run.sh --backend superdex
```

该命令构建 [UniLab Project SuperDex](https://github.com/unilabsim/project_superdex) 的提交 `f216dace36464d70f224caa4253074ec365ed14f`，不修改引擎源码。此提交标识源码构建路径，并不代表官方 PyPI wheel 的构建来源。

需要 Git、Clang 18 和 C++ 开发头文件；uv 安装 CMake 4.4.0 和 Ninja 1.13.2。完整 CMake 参数见 [build_superdex.sh](../scripts/build_superdex.sh)：Release、双精度、共享库、Python 绑定和 robotics 开启；调试器、mesh CLI 和渲染器关闭。构建目标包含 `mochi_physics_pybind` 和 `superdex_robotics_pybind`，`BUILD_JOBS` 默认值为 8。

干净源码基线已在 Ubuntu 22.04、Clang 18.1.8、Python 3.12.12、glibc 2.35 下完成构建。已有修改或版本不同的源码检出不会被覆盖。复用其他构建时，可设置 `SUPERDEX_ROOT`、`SUPERDEX_PYTHON`，以及可选的 `SUPERDEX_NATIVE_BIN`。

机器人和苹果的适用条款见[资产来源](ASSETS.zh-CN.md)。

## 资产下载

`setup.sh` 自动安装所需资产。单独获取或检查资产：

```bash
.venv/bin/python scripts/download_assets.py
```

机器人资产包约 16 MB，来自带版本的 GitHub Release；苹果基础色纹理直接从清单记录的 NVIDIA 来源获取。不下载未使用的法线、粗糙度和金属度纹理。适用条款见[资产来源](ASSETS.zh-CN.md)。

压缩包和各文件均进行 SHA-256 校验。下载缓存在 `${XDG_CACHE_HOME:-~/.cache}/dexlab/assets`，已安装且哈希匹配的文件可离线复用，缺失文件可从缓存恢复。已修改文件会保留并报告；重新安装前请将其移至其他位置。失败的下载不会作为完整资产安装。

约 2 MB 的任务专用苹果几何与控制器共同纳入版本管理，避免要求额外安装 USD 转换工具或改变碰撞几何。仓库也包含演示视频和验收摘要。
