# Learning 名称与引用迁移记录

[当前范围](current-work.md) · [验收](learning-migration-acceptance.md) · [迁移任务 #1](https://github.com/huangkiki/sim-learning/issues/1)

记录日期：2026-10-14。仓库名称已经修改；文档变更的 PR、默认分支内容与最后的跨仓链接验收分别记录，不能用仓库重定向替代内容发布。

## 仓库身份与交付入口

| 原名称 | 当前名称 | GitHub repository ID（改名前后相同） | 本批 PR |
|---|---|---|---|
| sim-atlas | sim-learning | 1411403514 | [#7](https://github.com/huangkiki/sim-learning/pull/7) |
| mujoco-atlas | mujoco-learning | 1411263627 | [#9](https://github.com/huangkiki/mujoco-learning/pull/9) |
| superdex-atlas | superdex-learning | 1411266838 | [#9](https://github.com/huangkiki/superdex-learning/pull/9) |
| genesis-atlas | genesis-learning | 1411267350 | [#9](https://github.com/huangkiki/genesis-learning/pull/9) |
| newton-atlas | newton-learning | 1411268002 | [#9](https://github.com/huangkiki/newton-learning/pull/9) |
| physx-atlas | physx-learning | 1411268563 | [#9](https://github.com/huangkiki/physx-learning/pull/9) |
| drake-atlas | drake-learning | 1411269026 | [#9](https://github.com/huangkiki/drake-learning/pull/9) |
| robot-learning-atlas | robot-learning | 1411468483 | [#8](https://github.com/huangkiki/robot-learning/pull/8) |

八个旧仓库首页均已核对 HTTP 301 跳转至对应新名称，最终响应 200。课程本轮没有配置 GitHub Pages，因此没有宣称另一个课程网站已迁移或部署。现有 GitHub Project #2/#3 的名称和入口已更新，任务与历史状态保留。

## 当前文本扫描范围

以本次账号清单的 43 个仓库为发现范围：八个 Learning 仓逐仓审校；DexLab 单独维护双语入口；另外 31 个非空仓库从默认分支 Git tree 定位并读取 **5,464 个候选文本文件**，未发现本次八个旧 slug 或系列品牌的匹配；两个仓库 API 返回空 Git 仓库。Obsidian 是保留的历史归档范围，本次不迁移或同步。

跨仓扫描使用 Git blob 身份读取正文，不以 GitHub 搜索零结果代替扫描。包含 Markdown、RST、TXT、HTML、SVG、YAML、JSON、TOML、Python、JS/TS/JSX/TSX、INI/CFG 与 shell；单文件上限 1 MB。排除 vendored/submodules/third_party、node_modules、环境、build/dist 与第三方 colmap 路径。未扫描二进制、LFS 内容、其他扩展名、所有历史分支、Issue/Discussion 历史正文和外部网站，因此不宣称这些范围绝无旧名称。扫描只读，没有修改其他研究仓的实验或上游代码。

DexLab 当前页面源文件中的旧 Sim Atlas 入口已在独立工作树改为 Sim Learning，README 与分类页另加教材/教程导航。入口放在生成块外的页面源文本，重新生成后四个首页逐字节保持；严格中英文站点构建通过。该改动尚有独立 PR/门禁与合入验收，不能据此宣称已部署。

## 明确保留的旧身份

- 过去的 E1–E6 验收记录、日期、提交与实验版本保留；各引擎的迁移验收页列出旧 URL/品牌例外。Genesis 历史记录只迁移 Issue URL，原始结论与时间不变。
- 示例模型 ID、原生 namespace、官方上游仓名和源码路径不做无关重命名。
- 本页的旧新名称映射和教材引用中的历史名称用于追溯，不是失效导航。
- 本地历史目录、缓存、未提交的其他工作和 Obsidian 归档不属于本次远端名称迁移。

## 集成顺序

先合入总仓的共同先修/教程页面，再合入依赖这些 main 链接的六引擎与 Robot Learning PR，随后验证各默认分支的真实文件和中英文导航。DexLab 入口按其独立门禁交付，并检查部署后的实际页面。Issue #1 在完整约定范围交付前保持开放；PR 检查通过不等于已经合并。

## English summary

All eight repositories retain their original IDs under Learning names; old home URLs redirect to the renamed repositories. Current-reference scanning separately covers the course repositories, DexLab and 5,464 selected text files in 31 other nonempty repositories. Excluded assets, archived notes, history and unscanned formats are explicit. Default-branch integration and deployment remain separate from rename and static validation.
