# DexLab 外部工作蒸馏与 Research Intake 契约

[English](distill-contract.md) | [简体中文](distill-contract.zh-CN.md)

本文件定义 DexLab 仓库专属的外部工作蒸馏落点、分类规则与 Research Intake 接口，供通用技能 [distill](https://github.com/huangkiki/codex-skills) 在进入本仓库时读取，不在通用技能中硬编码 DexLab 路径与 schema。

## 1. 四步交付顺序

用户请求对外部论文、开源仓库或产品工作做 DexLab 蒸馏、且未指定其他落点时，按以下顺序交付：

1. **论文笔记入库（强制前置）**：先按 `paper-reader` 完整流程在配置的 Obsidian 笔记库生成或补全正式论文笔记（含全部原图、公式、表格、概念库与按配置刷新 MOC）。聊天摘要或草稿不能替代入库；Vault 的 git commit/push 遵循共享配置与既有授权。入库后向蒸馏阶段结构化交接：固定版本与开源现状、完整方法拆解、1–2 张最具代表性的原图 URL、核心公式、主实验/消融表与关键反例。
2. **Blog 深度蒸馏页（单一事实源，中英文同步）**：在 `docs/site/zh/<slug>.md` 与 `docs/site/en/<slug>.md` 发布完整深度技术解析（约 1500–2500 字），**先完整讲清外部工作本身（一页速览、输入/输出与模块流水线、1–2 张核心原图、关键公式、主实验/消融对比表），再展开反例边界、对 DexLab 的借鉴顺序与最小可证伪验证切片**。
   - 必须读取 `docs/topic-taxonomy.json`，根据文章真正回答的研究问题，为 `docs/concept-atlas.json` 中对应 `synthesis` 条目标记 `"distillation": true` 并指定最匹配的 `topic`（优先复用现有专题；仅现有分类确实无法覆盖时新增双语专题并同步测试）。
   - 将新页面注册到 `docs/site/zh/distillation.md` 与 `docs/site/en/distillation.md` 的 `:hidden:` `toctree`（不要分散挂到 `engines.md`）。
   - 运行 `python3 scripts/build_docs.py` 及 `test_concept_atlas.py` / `test_docs_workflow.py` 严格双语验证；未读回远端前不得宣称站点已交付。
3. **GitHub Discussion 轻量决策卡**：Blog 作为单一事实源，Discussion 不重复拷贝整篇长文，只保留：
   - `TL;DR` 与核心结论（改变 DexLab 哪个现有选择、哪些已证实、哪些待测）；
   - 指向中英文 Blog 深度正文的链接；
   - 核心争议与会改变判断的证据条件；
   - 唯一合法的 `dexlab-intake:v1` JSON 机器块（见第 2 节）。
   先查找同主题既有 Discussion，同一研究的新证据优先追加，独立主题才新建；发布后读回目标、正文与 URL。
4. **Research Intake 同步入 Triage**：Blog 与 Discussion 读回后运行：

   ```bash
   python3 scripts/autoresearch.py intake check --discussion NUMBER
   python3 scripts/autoresearch.py intake sync --discussion NUMBER
   ```

   有可执行候选时，`intake sync` 幂等创建或更新 `[Research intake]` 伞形 Issue 并置入 Project 4 的 `Triage`；`watch` / `reject` 不创建 Issue。**Triage 伞形项不可执行，绝不添加 `auto:approved`。**

## 2. `dexlab-intake:v1` 机器块契约

Discussion 正文必须包含唯一一个机器块，并与相邻人读摘要保持同一结论：

```markdown
<!-- dexlab-intake:v1:start -->
```json
{
  "schema_version": 1,
  "discussion": 425,
  "slug": "stable-slug",
  "title": "Short decision title",
  "decision": "pilot",
  "summary": "One-sentence technical conclusion.",
  "current_work_impact": "How this relates to docs/current-work.md.",
  "candidates": [
    {
      "slug": "slice-slug",
      "kind": "experiment",
      "goal": "Concrete falsifiable goal.",
      "entrypoints": ["repo/relative/path"],
      "first_slice": "Smallest independently verifiable deliverable.",
      "acceptance": ["Concrete measurable acceptance criterion."],
      "depends_on": [],
      "non_goals": ["Explicit out-of-scope boundary."]
    }
  ]
}
```
<!-- dexlab-intake:v1:end -->
```

- `decision` 取值：`adopt-existing`、`pilot`、`experiment`、`watch`、`reject`。
- `candidates[*].kind` 取值：`experiment`、`enhancement`、`bug`、`documentation`、`infrastructure`。
- `watch` / `reject` 的 `candidates` 必须为空数组；其余决策至少包含 1 个候选切片。
- `entrypoints` 仅允许仓库相对路径。

## 3. 从 Triage 进入执行队列

维护者审查伞形 Issue 后，仅对选定切片执行：

```bash
python3 scripts/autoresearch.py intake promote --umbrella NUMBER --slice SLUG --priority P1
```

`promote` 创建关联子 Issue（自动带合法的 `Depends on:` 字段与验证提示）并放入 `Todo`，**但绝不添加 `auto:approved`**。只有维护者另行添加 `auto:approved` 且通过作者门禁、依赖检查后，该子 Issue 才可被 `autodev` / `autoresearch` 领取。详见 [自动研究与版本发布](autoresearch.zh-CN.md#research-intake)。
