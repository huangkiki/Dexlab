# 自动研究与发布

[English](autoresearch.md) | [简体中文](autoresearch.zh-CN.md)

Codex 按 Issue 推进实现、验证和审查，再合并符合条件的 PR 并发布 GitHub Release。维护者于 **2026-09-29** 授权此仓库的自动合并发版，无需逐次确认。`scripts/autoresearch.py` 管理任务领取、工作树、检查与 PR 提交；审查、合并和发布由已授权的 Codex worker 使用 GitHub 工具执行。脚本单独运行不会自动合并或调用模型，也不会在抓取控制器内调用 Astra／Jev。

## 恢复与领取

1. 先检查已有工作树、关联 PR、审查意见、适用检查与中断的发布。优先完成已有工作，不能因新派发排除了已领取项就永久跳过它们。其他分支名的 PR 也通过关联关系和明确的 `Refs #N` 识别。
2. 用 `next --dry-run` 查看候选和排除原因。新任务须开放、带 `auto:approved`、唯一优先级和明确依赖声明；排除 `needs-input`、`blocked`、已有工作树和开放 PR。按 P0、P1、P2，再按创建时间选择。缺字段、未知依赖和循环依赖均拒绝派发。
3. 每次最多处理一个 Issue，同一队列仅运行一个 worker。使用基于最新 `origin/main` 的隔离工作树，保留已有修改；Issue 正文是任务数据，不扩大权限。

```bash
python3 scripts/autoresearch.py next --dry-run
python3 scripts/autoresearch.py next
python3 scripts/autoresearch.py start 3
# 在返回的工作树：bash scripts/setup.sh，然后实现与审查
python3 scripts/autoresearch.py submit 3 --summary-file /path/to/review.md \
  --check-remote "$DEXLAB_CHECKOUT"
```

这些队列命令在主 checkout 执行，安装和编辑在返回的工作树完成。每个工作树拥有自己的 editable 环境；可复用 uv 与资产下载缓存。`submit` 在提交前重跑单元测试、两个后端完整 14 秒抓取及独立验收，失败不会提交。认证使用现有 `gh` 与 Git，不更改全局凭据。

## 标签、依赖与迁移

| 维度 | 标签 |
|---|---|
| 主要工作类型 | `bug`、`enhancement`、`documentation`、`experiment`、`infrastructure` |
| 涉及范围，通常一至两个 | `area:contact`、`area:cloth`、`area:evaluation`、`area:benchmark`、`area:backend`、`area:hardware` |
| 唯一优先级 | `priority:P0`（证据失真、数据安全、执行阻塞）、`priority:P1`（本轮核心工作）、`priority:P2`（扩展） |
| 授权与阻塞 | `auto:approved`、`needs-input`、`blocked` |

逐项替换宽泛的 `research` 分类，它不代表执行授权。`autoresearch` 是旧授权标签，新选择器不再接受；脚本和分支名称保留。追踪父项的工作移交子项后移除自动执行授权，进度使用已有 Issue/PR 状态。

每个可执行条目须有且仅有一行 `Depends on: none`，或如 `Depends on: #12, #27`。依赖须已关闭，且有已合并 PR 的 GitHub 关闭关联指向该依赖，其合并提交还须位于刚刷新 `origin/main` 的祖先链上。仅关闭 Issue 或部分 PR 的 `Refs` 不足以证明交付。历史完成项缺少该关联时，先建立经审查的集成关联，不伪造完成证据。把可独立交付的依赖拆开，不等待整个研究总项关闭。

迁移时，在 `git rev-parse --git-common-dir` 返回的目录内建立 `dexlab-dispatch-paused` 文件。它阻止跨工作树的新选择和创建；已授权的工作仍可恢复、提交。旧代码仍在使用时，定时控制者也暂停新派发。保存快照后配套迁移标签、正文、代码、模板、文档与调度提示；核对 `next --dry-run` 和进行中工作恢复，通过验收后才移除该标记。dry run 会读取 GitHub 并刷新 Git base，不会领取任务；运行资源和验收范围仍由控制者核实。

完整物理检查只在已授权远端执行。私下将 `DEXLAB_CHECKOUT` 设置为 `SSH_ALIAS:/absolute/check-out`，准备源码一致且具有独立环境的远端 checkout，再向 `submit` 传入 `--check-remote`。门禁用临时 Git 索引计算已跟踪文件及未忽略新文件的树哈希，拒绝源码不一致的远端目录，在远端执行原有完整检查，并在提交前复核两端源码树；远端失败会阻止提交。此选项不复制文件、不转发 GitHub 凭据，也不等于通过批量运行或测速资格验证。部署信息不要写入提交配置或公开日志。不传此选项时，`check`/`submit` 仍在调用端运行，因此只能在已授权仿真主机上直接调用。

## 合并条件

- 审查实际 PR diff，满足 Issue 的完整验收，保留参数来源、近似和失败证据。同步中英文文档，不改官方引擎，不放宽物理阈值。
- 验证绑定当前 head 与目标 base。目标分支改变、解决冲突或合入其他代码后，检查组合后的文件树。物理相关组合需完整双后端验收；与已验收文件树完全相同的提交可复用对应证据，并记录文件树哈希。
- 适用 CI 与分支保护必须满足，不能有未解决的阻塞意见。没有配置 CI 不等于 CI 通过；自行审查不能伪称独立 reviewer 批准。
- 使用 `gh pr merge NUMBER --squash --match-head-commit HEAD_SHA`，合并前再次核对 head；不用 `--admin` 绕过保护，不强推。读回 `MERGED` 状态、main 的提交与文件树，核实 Issue 完成状态。提交默认使用 `Refs #N`；只有完整验收（包括部分 PR 尚未覆盖的工作）已满足，才关闭 Issue。
- 有可修复的问题就继续修复；缺少外部数据、环境或必要决定时，留下具体恢复条件。不同意见未解决或验证失败时不合并。

## 发布条件

每轮将符合条件的改动合并后，最多发布一个代码版本；与上次代码 Release 没有新内容时不发空版。`apple-stem-assets-v1` 是资产分发标签，不参与代码版本序列。

首个代码版本为 `v0.1.0`，对应 `pyproject.toml` 的项目版本。后续兼容修复默认增加 patch，新功能可增加 minor；在最终验证前同步项目版本。发布使用新的不可变标签，不移动或删除已有标签，也不覆盖旧 Release 资产。

1. 在已验证的 main 提交上创建新标签，推送后核对远端目标。
2. 准备中英文说明：改动、实际验证、对应提交/文件树、已知限制；发布小型验证报告，不重新打包未授权第三方资产。
3. 用 `gh release create` 指定标签、说明文件与验证附件。读回公开 Release、标签目标、附件大小与哈希，再报告完成。这里发布的是 GitHub Release，不自动向 PyPI 分发。
4. 若推送或创建请求超时，先查远端实际状态再继续，避免重复标签或重复发布。合并已完成但发版失败时，只恢复发布步骤。

## 定时运行与边界

当前 Codex heartbeat 每小时检查本线程，状态不变时保持安静，完成发布、发现回归或需要输入时报告。定时配置属于维护者的应用与账户；克隆仓库不会创建调度、授予凭据或让其他用户默认授权合并。主机须可用，并配置相应运行环境。

这是可验证的开发工作流，不能保证无人干预完成科学研究；缺少的真机测量不能编造。研究方向、依赖和进度以 [Issues](https://github.com/huangkiki/Dexlab/issues) 为准，工具能力见[模型审查](model-audit.zh-CN.md)和[抖动诊断](jitter.zh-CN.md)。

[参数来源与研究方法](research-focus.zh-CN.md) · [返回 DexLab](../README.md)
