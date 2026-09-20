# 自动研究

[English](autoresearch.md) | [简体中文](autoresearch.zh-CN.md)

由 Codex 定时读取 GitHub issues，每次实现一个范围明确的改动，验证后提交到独立分支并创建 PR。`scripts/autoresearch.py` 管理队列、工作树、检查和提交；研究与修改由 Codex 执行。这个脚本本身不是模型或自主优化器，也不会在抓取控制器内调用 Astra／Jev。

## 队列与执行

1. 选择带 `autoresearch` 标签的开放 issue，排除 `needs-input` 以及已有 `autoresearch/issue-N` 开放 PR 的项。优先处理最小编号，空队列输出 `null`。
2. 基于 `origin/main` 创建或继续使用 `.autoresearch/worktrees/issue-N`，保留未完成工作。同一队列仅运行一个定时 worker。
3. 阅读验收标准与源码证据，实现限定范围的改动；记录参数来源、假设和失败实验，同步中英文文档。
4. 运行单元测试，通过 UniLab 分别执行两个后端的完整 14 秒 SDF 抓取，再独立验收。失败就停止提交。
5. 提交并推送 `autoresearch/issue-N`，创建或更新包含改动及证据的 PR。不重写、不自动合并 main；`Fixes #N` 仅在合并后关闭 issue。

以下队列命令均在主 checkout 执行；代码修改和安装在返回的隔离工作树执行。

```bash
python3 scripts/autoresearch.py next
python3 scripts/autoresearch.py start 1
# 在返回的工作树中执行 bash scripts/setup.sh，然后实现 issue。
python3 scripts/autoresearch.py check .autoresearch/worktrees/issue-1
python3 scripts/autoresearch.py submit 1 --summary-file /path/to/review.md
```

`submit` 会在提交前重新验证，不能用旧的通过日志替代。认证使用现有 `gh` 和 Git 配置；使用 SSH 的环境需配置相应 origin。每个工作树需要自己的 editable 安装，不能共用指向另一个 checkout 的虚拟环境；资产和 uv 下载缓存可以复用。

## 定时运行

Codex 应用通过本线程的 heartbeat 每小时检查一次，每次最多处理一个 issue。定时配置属于当前应用和账户，克隆仓库不会自动创建定时任务或获得模型访问权限。运行主机须可用，并具备已认证的 GitHub 工具及 Python 环境。worker 在提交 PR 或出现具体阻塞时报告，空队列状态不变时保持安静；不得无限重试同一个失败实验。

这是按 issue 推进的辅助研究流程，不能保证无人干预完成科学研究。模型审查和可复现实验可以自动执行，缺失的真机测量不能自动编造；进入 main 仍经过 PR 审查。

## 已建立的 issues

- [#1 模型审查](https://github.com/huangkiki/Dexlab/issues/1)：可自动处理。
- [#2 抖动与接触间断](https://github.com/huangkiki/Dexlab/issues/2)：可自动处理。
- [#3 冻结场景回归与步长研究](https://github.com/huangkiki/Dexlab/issues/3)：研究队列。
- [#4 UniSim 内置适配器等价性](https://github.com/huangkiki/Dexlab/issues/4)：研究队列。
- [#5 PhysX／IsaacSim](https://github.com/huangkiki/Dexlab/issues/5)：需要可用 worker 环境。
- [#6 真机校准](https://github.com/huangkiki/Dexlab/issues/6)：需要实测数据。

[参数来源与假设](research-focus.zh-CN.md) · [返回 DexLab](../README.md)
