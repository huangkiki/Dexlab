# E1 验证与范围记录

任务：[SuperDex E1 #2](https://github.com/huangkiki/superdex-atlas/issues/2)。基线为 E0 已合入的仓库提交 `7c2e0588f35a2e40f7aa65c7cbdd534a1f954604`；本记录与章节同一次提交保存，实际交付提交由该文件 Git 历史及关联 PR 标识。检查日期：2026-10-09。

阅读上游固定在 `facebookresearch/project_superdex@1d7150946fa3f3d3fb09c2bff07eaa138cbfdee6`；[sources.json](sources.json)逐文件记录 Git blob，[源码地图](source-map.md)提供入口。源码课程基线不等于安装的 wheel 或 DexLab 历史运行版本。

## 验收覆盖

| Issue 要求 | 本次交付及核对 | 仍不宣称 |
|---|---|---|
| 坐标/单位/姿态 | [专题](modeling-state-time.md)第 1–2 节：Physics/Robotics 坐标、TransformRT、xyzw、质心与采样点 | 所有宿主/资产均自动转换 |
| 惯量/建模/导入 | 第 3 节：惯量排序/符号/单位/平行轴、质量密度、mesh/URDF 限制 | runtime URDF 或 Studio 完整支持任意资产 |
| 状态维度/所有权 | 第 4 节：rigid/articulated/变形体表示、pose/DoF 分离、PySpan 与输出缓冲 | 跨版本稳定内存布局；借用视图是历史日志 |
| reset/snapshot | 第 5 节：历史失效、快照范围、同场景/拓扑要求、失败非事务 | 自定义 Python 状态和 scene 参数自动回滚；跨构建确定性 |
| 时间/数值基础 | 第 6–8 节：pre/post phase、step(0)、substep/stage、积分枚举、精度/可微限制 | 实际收敛性、推荐通用步长、完整 E3 求解数学 |
| 原生 API 例子 | [inspect_rigid_state.py](../examples/inspect_rigid_state.py)，使用调用方拥有的 Scene/Actor | 已 import 或执行、线程间原子快照 |
| 练习与答案 | 第 9 节 10 题，包含惯量缩放、采样点、URDF、积分历史和视图问题 | 实验结果或独立复现证据 |
| 双语入口与进度 | 中文/英文 README、curriculum/roadmap 更新；B0/B4 仅标明 E1 基础覆盖 | 后续 E2–E7 已完成 |

## 实际静态检查

以下检查通过后才记录本状态，未启动 Physics、Robotics、Studio、debugger，也未调用正时间步。

- `git diff --check`：无空白错误。
- `python scripts/check_docs.py`：仓库相对 Markdown 文件链接存在。该脚本不验证远端 URL 或锚点，下面的源码检查补充版本/路径身份。
- 对本仓库所有 `.py` 使用 `ast.parse`：2 个 Python 文件（文档检查脚本与新原生片段）语法通过；同时扫描 Markdown 的 1 个 `python` 代码块。示例无 native import/执行验证。
- 从固定上游 Git tree 核对 manifest 的 35 个路径及 Git blob；下载的每个文件以 `SHA1("blob " + byte_length + NUL + content)` 验证。该步骤证明引用内容身份，不单独证明教程结论。
- 从全部 Markdown 提取 `facebookresearch/project_superdex/blob/<sha>/<path>`，检查 SHA、路径及 manifest 覆盖。本章还使用 reference-style 链接，已一并纳入扫描。
- 自审主要语义：惯量六元顺序、质心速度 frame、URDF inertial rotation 丢弃路径、Span 零拷贝与输出缓冲、捕获标记、step(0) 回调及积分历史失效。均与正文所列字段/函数核对；不冒充独立 reviewer。

语法检查可在仓库根目录复查（不执行被检查代码）：

```python
import ast
from pathlib import Path

for path in Path(".").rglob("*.py"):
    if not any(part in {".git", ".venv"} for part in path.parts):
        ast.parse(path.read_text(), filename=str(path))
```

发现并保留的限制：runtime URDF importer 对 inertial rpy 的处理不足是固定源码静态结论，未量化运行误差；Span 快速路径的步幅缺少检查不代表任意 NumPy slice 安全；原生 snapshot 的恢复失败可能部分生效。相关规避与恢复方式已写入正文，未修改上游源码。

## 完成一项后的下一步判断

E0 所需对象导读与 source map 已在目标 main 中。E1 为 E2/E3/E4 提供共同基础；下一项优先 E2，沿 prefab 的 joint/link/DoF 映射接到驱动、控制器和任务接口。E3 后续补完整接触/残差/容差/力观测，E4 补传感更新/渲染。E5 等 E2/E4，E6 等 E3，E7 等 E2–E6。E1 的文档完成不把延后的实验算成已完成；实验仍后续复用 DexLab。
