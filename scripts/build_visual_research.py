"""Generate detailed experiment pages from the coverage and experience indexes."""

import argparse
import html
import json
import re
from pathlib import Path

from solver_taxonomy import summarize_roles
from task_coverage import load_inventory
from visual_research import ROOT, check, read_bundle

MARKERS = ("<!-- visual-research:start -->", "<!-- visual-research:end -->")
SITE = "https://huangkiki.github.io/Dexlab/"
ENGINES = ("MuJoCo", "SuperDex", "Genesis", "Newton Physics", "PhysX", "Drake")


def solver_summary(engine, rows, language="en"):
    """Describe engine-specific roles without promoting names to peer algorithms."""
    return summarize_roles(engine, rows, language)


def site_url(language, path=""):
    return SITE + ("zh-cn" if language == "zh" else "en") + "/latest/" + path


def engine_table(inventory, language, site):
    zh = language == "zh"
    lines = [
        "## "
        + (
            "比较了哪些引擎与 solver"
            if zh
            else "Which engines and solvers are compared?"
        ),
        "",
    ]
    lines += [
        "| "
        + (
            "引擎 | 已登记配置的角色（非同级算法清单） | 实验版本与路径 |"
            if zh
            else "Engine | Roles in registered profiles (not peer algorithms) | Experiment versions and paths |"
        ),
        "| --- | --- | --- |",
    ]
    for engine in ENGINES:
        rows = [r for r in inventory["rows"] if r["engine"] == engine]
        if not rows:
            raise ValueError("Engine missing from coverage: " + engine)
        solvers = solver_summary(engine, rows, language)
        versions = sorted(
            {r["version"] for r in rows if r["runtime_path"].startswith("native")}
        )
        # Runtime labels and versions are displayed verbatim from the coverage source.
        if not versions:
            versions = sorted({r["version"] for r in rows})
        versions = [
            v
            for v in versions
            if v not in ("unknown", "unqualified", "pending", "not qualified")
        ]
        lines.append(
            f"| **{engine}** | {solvers} | "
            + ", ".join(versions)
            + "; native / "
            + ("历史路径详见矩阵" if zh else "historical paths in matrix")
            + " |"
        )
    target = "coverage.md" if site else site_url(language, "coverage.html")
    lines += [
        "",
        (
            "原生与框架 **MJWarp** 另列运行路径及实际核心。Newton Physics 是引擎项目，Newton 也是求解算法名。SuperDex BFGS／SR1 在已测 assembly period=1 时执行 Newton 等价步；配置名不计作独立算法。"
            if zh
            else "Native and framework **MJWarp** are separate paths with their actual core identified. Newton Physics is an engine project; Newton is also an algorithm name. Tested SuperDex BFGS/SR1 with assembly period=1 execute Newton-equivalent steps; configuration names are not independent algorithm counts."
        ),
        "",
        (
            "本表是研究对象概览，包含失败与未准入项；执行情况、CPU/GPU、精度、完整配置和不支持原因见"
            if zh
            else "This is a research inventory including failures and unqualified entries. Execution, CPU/GPU, precision, full profiles and unsupported reasons: "
        )
        + f" [完整矩阵 / Full matrix]({target})。",
        "",
    ]
    taxonomy_target = (
        "solver-taxonomy.md"
        if site
        else ("docs/solver-taxonomy.zh-CN.md" if zh else "docs/solver-taxonomy.md")
    )
    lines += [
        (
            "角色按各引擎的已记录名称解释，不代表这些算法求解同一问题，也不证明任意组合已经执行。AUTO 只是选择策略；未知身份不从默认值补写。"
            if zh
            else "Roles interpret recorded names within each engine, not identical mathematical problems or evidence that every combination ran. AUTO is a selection policy; missing identities are not filled from defaults."
        ),
        "",
        (
            "**比较边界：** 系统配置选型与受控算法归因分开；记录完整性、数值一致性、物理参照和任务结果分别阅读，原始评分与失败分母不变。"
            if zh
            else "**Comparison boundary:** distinguish system-profile selection from controlled algorithm attribution. Read record integrity, numerical consistency, physical references and task outcomes separately; original scores and failure denominators are unchanged."
        )
        + f" [{'分类与证据说明' if zh else 'Roles and evidence guide'}]({taxonomy_target})。",
        "",
        (
            "细 SDF 几何与材料响应仍需 [#178](https://github.com/huangkiki/Dexlab/issues/178) 资格核验；布料材料、碰撞/耦合与夹持分别由 [#179](https://github.com/huangkiki/Dexlab/issues/179) 补齐基线。既有开发案例通过不等于公平的跨引擎材料比较。"
            if zh
            else "Thin-feature SDF geometry/response qualification remains [#178](https://github.com/huangkiki/Dexlab/issues/178); cloth material, collision/coupling and grasp baselines remain [#179](https://github.com/huangkiki/Dexlab/issues/179). Existing development passes are not calibrated cross-engine material comparisons."
        ),
        "",
    ]
    lines += [
        (
            "**MJWarp 运行路径对照（归入 MuJoCo 核心）**"
            if zh
            else "**MJWarp path comparison (MuJoCo core)**"
        ),
        "",
        (
            "| 运行路径 | 实际物理核心 | solver／接触路径 | 任务验收状态 |"
            if zh
            else "| Runtime path | Actual physics core | Solver / contact path | Task acceptance |"
        ),
        "| --- | --- | --- | --- |",
    ]
    for row in inventory["rows"]:
        if row["solver"].startswith("MJWarp"):
            states = " / ".join(
                sorted({cell["state"] for cell in row["cells"].values()})
            )
            lines.append(
                f"| {row['runtime_path']} | {row['engine']} {row['version']} | {row['solver']} | [{states}]({target}) |"
            )
    lines += [
        "",
        (
            "已有模型与时钟诊断；可靠任务验收仍按矩阵状态记录。[路径差异 #152](https://github.com/huangkiki/Dexlab/issues/152) 保留独立研究范围。"
            if zh
            else "Model/clock diagnostics already exist; task acceptance retains the matrix state. [Path differences #152](https://github.com/huangkiki/Dexlab/issues/152) remain a separate research question."
        ),
        "",
    ]
    return "\n".join(lines)


def catalogue(index, language, site):
    zh = language == "zh"
    lines = ["## " + ("完整实验与历史记录" if zh else "Full experiment and historical index"), ""]
    if site:
        lines.insert(0, "(full-experiment-catalogue)=")
    if site:
        lines += ["```{raw} html", '<div class="experiment-grid">']
    else:
        lines += [
            "| "
            + (
                "实验画面／图表 | 比较对象与研究结论 |"
                if zh
                else "Experiment / figure | Comparisons and findings |"
            ),
            "| --- | --- |",
        ]
    for card in index["catalogue"]:
        image = ("../../.." if site else ".") + "/" + card["thumbnail"]
        link = card["link"] if site else site_url(language, card["link"])
        title = card["title"][language]
        if site:
            # Sphinx does not copy raw-HTML image sources; use stable repository raw URLs.
            image = card["site_thumbnail"]
            lines.append(
                '<article class="experiment-card"><a href="'
                + html.escape(link)
                + '"><img loading="lazy" src="'
                + html.escape(image)
                + '" alt="'
                + html.escape(title)
                + '"></a><div class="card-copy"><h3><a href="'
                + html.escape(link)
                + '">'
                + html.escape(title)
                + '</a></h3><p class="engines">'
                + html.escape(card["engines"])
                + "</p><p>"
                + html.escape(card["question"][language])
                + "</p><p>"
                + html.escape(card["finding"][language])
                + "</p></div></article>"
            )
        else:
            lines.append(
                f'| <a href="{link}"><img src="{image}" width="200" alt="{title}"></a> | **[{title}]({link})**<br>{card["engines"]}<br>{card["question"][language]}<br>{card["finding"][language]} |'
            )
    if site:
        lines += ["</div>", "```"]
    lines += [
        "",
        (
            "**待开展／未完成：** 更广推动、手内旋转、主动折布及抓取迁移分别见现有 Issue。已有刀面推动按其单独协议报告；预折叠下落不等于主动折布成功。"
            if zh
            else "**Pending / incomplete:** broader pushing, in-hand rotation, active folding and grasp transfer remain in their existing Issues. Existing knife-driven pushing has its own protocol; folded drop is not active folding."
        ),
        "",
    ]
    return "\n".join(lines)


def replay_html(case, language):
    variants = [
        {
            "label": v["label"][language],
            "url": "_static/"
            + Path(v["data"]["path"]).relative_to("docs/evidence").as_posix(),
        }
        for v in case["variants"]
    ]
    first = case["variants"][0]["data"]["path"]
    stem = Path(first).name.removesuffix(".json.gz")
    bundle = read_bundle(ROOT / first)
    video = bundle["videos"][0]
    attrs = html.escape(json.dumps(variants, ensure_ascii=False), quote=True)
    launch = {
        "incline": {
            "zh": "加载六引擎同步回放与逐帧曲线",
            "en": "Load the six-engine synchronized replay and frame-by-frame curves",
        },
        "normal": {
            "zh": "加载法向校准回放与响应曲线",
            "en": "Load the normal-response replay and curves",
        },
        "pinch": {
            "zh": "加载 0.4 N／0.8 N 夹持边界回放",
            "en": "Load the 0.4 N / 0.8 N pinch-boundary replay",
        },
        "libero": {
            "zh": "加载 LIBERO 原任务与 1 ms 对照回放",
            "en": "Load the LIBERO native-task and 1 ms comparison replay",
        },
    }[case["id"]][language]
    caption = (
        "静态图表与完整数据（无需 JavaScript）"
        if language == "zh"
        else "Static figures and full data (no JavaScript required)"
    )
    downloads = []
    for variant, item in zip(variants, case["variants"]):
        data = read_bundle(ROOT / item["data"]["path"])
        curve = variant["url"].removesuffix(".json.gz") + (
            "-curves.zh.svg" if language == "zh" else "-curves.svg"
        )
        links = [
            f'<a href="{variant["url"]}">JSON.gz</a>',
            f'<a href="{curve}">SVG</a>',
        ]
        links += [
            f'<a href="_static/visual/{v["path"]}">MP4 · {html.escape(" / ".join(v["series"]))}</a>'
            for v in data["videos"]
        ]
        downloads.append(
            f"<li>{html.escape(variant['label'])}: " + " · ".join(links) + "</li>"
        )
    return "\n".join(
        [
            "```{raw} html",
            f'<div class="dexlab-replay" data-language="{language}" data-launch="{html.escape(launch, quote=True)}" data-variants="{attrs}">',
            f'<div class="visual-hero"><img loading="lazy" src="_static/visual/{video["poster"]}" alt="{html.escape(case["title"][language])}"></div>',
            f'<details class="replay-fallback"><summary>{caption}</summary><img loading="lazy" src="_static/visual/{stem}-curves{".zh" if language == "zh" else ""}.svg" alt="{caption}"><ul>{"".join(downloads)}</ul></details>',
            "</div>",
            "```",
            "",
        ]
    )


COMPARISON_CLAIMS = {
    "incline": {
        "zh": "在这组固定配置中，没有任何引擎通过全部九例。差异集中在静止漂移、滑动受力响应，以及名义零摩擦时的有效接触。",
        "en": "Under these fixed settings, no engine passes all nine cases. The differences separate into static drift, sliding force response, and effective contact at nominal zero friction.",
    },
    "normal": {
        "zh": "参数校准可以把这组夹具的加载响应带到合成目标附近，但固定参数直接迁移到其他质量时会失效；明确写出质量补偿后，两个迁移载荷才重新接近目标。",
        "en": "Parameter calibration brings this fixture's loaded response close to the synthetic target, but fixed parameters do not transfer to other masses. A predeclared mass conversion restores both transfer loads.",
    },
    "pinch": {
        "zh": "在同一夹具中，保持边界位于 0.4 N 与 0.8 N 之间；±2 mm 初态偏移没有改变这条边界。",
        "en": "In this fixture, the retention boundary lies between 0.4 N and 0.8 N. A ±2 mm initial offset does not move that boundary.",
    },
    "libero": {
        "zh": "1 ms 没有改善原任务成功率，反而让物理诊断从 5/10 降到 3/10，并使原生步进成本约翻倍。",
        "en": "A 1 ms step does not improve native task success. It reduces physical screens from 5/10 to 3/10 and roughly doubles native stepping cost.",
    },
}

COMPARISON_GUIDES = {
    "incline": {
        "watch": {
            "zh": "在同一两秒窗口内，看方块是否保持、转动或失去支撑；每个画面同时标出运行状态。",
            "en": "In the same two-second window, see whether the cube holds, rotates or loses support; each pane also reports its outcome.",
        },
        "limit": {
            "zh": "画面相似不等于物理等价；通过或失败仍由同时间轴的力、位移和速度判据决定。",
            "en": "Similar video does not establish physical equivalence; force, displacement and velocity criteria on the shared clock decide the result.",
        },
    },
    "normal": {
        "watch": {
            "zh": "先看加载窗的压入量，再看卸载、离面段和其他质量下的响应是否仍接近目标。",
            "en": "Inspect indentation during loading, then whether unloading, separation and other masses remain close to the target.",
        },
        "limit": {
            "zh": "画面不能证明材料真实刚度；有效响应只在声明的夹具、载荷和合成目标内成立。",
            "en": "The video does not establish real material stiffness; the response is limited to the declared fixture, loads and synthetic target.",
        },
    },
    "pinch": {
        "watch": {
            "zh": "依次看闭合、抬升、保持和释放，重点确认物体相对指面是否持续滑移。",
            "en": "Watch closing, lift, hold and release in order, focusing on continued object slip relative to the fingers.",
        },
        "limit": {
            "zh": "抬起或离开画面不等于完成保持；张开负例与原生物体运动共同防止错误成功。",
            "en": "Lifting or leaving the frame is not valid retention; the open negative and native object motion prevent false success.",
        },
    },
    "libero": {
        "watch": {
            "zh": "先确认两种步长都完成原任务，再对照同一动作下的接触重叠、相对高度和法向力。",
            "en": "First verify both timesteps complete the native task, then compare overlap, relative height and normal force under the same actions.",
        },
        "limit": {
            "zh": "原任务成功不能替代物理筛查；画面也不能唯一解释 5/10 到 3/10 的退化。",
            "en": "Native task success does not replace physical screening, and the video does not uniquely explain the 5/10 → 3/10 regression.",
        },
    },
}

REPLAY_SERIES_LABELS = {
    "mujoco": ("MuJoCo", "MuJoCo"),
    "superdex": ("SuperDex", "SuperDex"),
    "genesis": ("Genesis", "Genesis"),
    "newton": ("Newton Physics", "Newton Physics"),
    "physx": ("PhysX", "PhysX"),
    "drake": ("Drake", "Drake"),
    "initial-mujoco": ("初始 MuJoCo", "Initial MuJoCo"),
    "validation-mujoco-reference": ("校准后 MuJoCo", "Calibrated MuJoCo"),
    "dev-cap-0.4": ("0.4 N 力限额", "0.4 N limit"),
    "dev-cap-0.8": ("0.8 N 力限额", "0.8 N limit"),
    "dev-open": ("张开负例", "Open negative"),
    "baseline": ("原版 2 ms", "Original 2 ms"),
    "step-1000us": ("对照 1 ms", "1 ms control"),
}


def comparison_summary(case, row, language):
    zh = language == "zh"
    claim = COMPARISON_CLAIMS[case["id"]][language]
    return "\n".join(
        [
            '<div class="comparison-summary">',
            f'  <p class="comparison-claim"><strong>{"结论" if zh else "Conclusion"}</strong> {html.escape(claim)}</p>',
            '  <div class="comparison-terms">',
            f'    <p><strong>{"实验条件" if zh else "Setup"}</strong> {html.escape(row[language]["condition"])}</p>',
            f'    <p><strong>{"结论边界" if zh else "Scope"}</strong> {html.escape(row[language]["boundary"])}</p>',
            "  </div>",
            "</div>",
            "",
        ]
    )


def replay_guide(case, language):
    zh = language == "zh"
    first = case["variants"][0]["data"]["path"]
    bundle = read_bundle(ROOT / first)
    names = []
    for video in bundle["videos"]:
        for name in video["series"]:
            pair = REPLAY_SERIES_LABELS.get(name.lower())
            names.append(pair[0 if zh else 1] if pair else name.replace("-", " "))
    return "\n".join(
        [
            '<div class="replay-guide" aria-label="'
            + ("同步回放阅读说明" if zh else "Synchronized replay reading guide")
            + '">',
            f'  <p><strong>{"画面顺序" if zh else "Pane order"}</strong> {html.escape(" / ".join(names))}</p>',
            f'  <p><strong>{"看什么" if zh else "What to watch"}</strong> {html.escape(COMPARISON_GUIDES[case["id"]]["watch"][language])}</p>',
            f'  <p><strong>{"不要直接推出" if zh else "Do not infer"}</strong> {html.escape(COMPARISON_GUIDES[case["id"]]["limit"][language])}</p>',
            "</div>",
            "",
        ]
    )


def comparison_table(case, language):
    zh = language == "zh"
    if case["id"] == "incline":
        caption = (
            "固定发布配置的分条件结果（通过数 / 该条件三例）"
            if zh
            else "Published fixed configurations by condition (passes / three cases per condition)"
        )
        headers = (
            ["引擎与配置", "静止", "滑动", "名义零摩擦", "总计"]
            if zh
            else ["Engine and configuration", "Static", "Sliding", "Nominal zero friction", "Total"]
        )
        rows = [
            ("MuJoCo", "3.15 · PGS / elliptic", [("0 / 3", "fail"), ("0 / 3", "fail"), ("3 / 3", "pass"), ("3 / 9", "fail")]),
            ("SuperDex", "1.0 · Newton / AUTO / C1", [("2 / 3", "mixed"), ("3 / 3", "pass"), ("3 / 3", "pass"), ("8 / 9", "mixed")]),
            ("Genesis", "1.4.3 · Newton / elliptic / Signorini", [("3 / 3", "pass"), ("3 / 3", "pass"), ("0 / 3", "fail"), ("6 / 9", "mixed")]),
            ("Newton Physics", "1.6.1 · XPBD / 100 sweeps", [("1 / 3", "mixed"), ("0 / 3†", "invalid"), ("0 / 3†", "invalid"), ("1 / 9†", "invalid")]),
            ("PhysX", "5.9.0 · PGS / patch friction", [("3 / 3", "pass"), ("2 / 3†", "mixed"), ("2 / 3", "mixed"), ("7 / 9†", "mixed")]),
            ("Drake", "1.57 · SAP / kLagged / hydroelastic", [("3 / 3", "pass"), ("0 / 3", "fail"), ("3 / 3", "pass"), ("6 / 9", "mixed")]),
        ]
        note = (
            "† 无效记录保留在分母中，不计为通过；不能解释成物理失败。"
            if zh
            else "† Invalid records remain in the denominator; they are not passes and are not physical failures."
        )
    elif case["id"] == "normal":
        caption = "加载窗口的有效响应（合成目标 20 kN/m）" if zh else "Effective loaded-window response against the synthetic 20 kN/m target"
        headers = ["阶段", "实测响应", "目标或检查", "读法"] if zh else ["Stage", "Measured response", "Target or check", "Reading"]
        rows = [
            ("初始配置", "MuJoCo · 0.2 kg", [("≈80 kN/m", "plain"), ("20 kN/m", "plain"), ("未校准", "fail")]),
            ("校准后", "同一夹具与载荷", [("≈20 kN/m", "plain"), ("20 kN/m", "plain"), ("目标区间", "pass")]),
            ("直接迁移", "0.1 kg / 0.4 kg", [("10.01 / 40.04 kN/m", "plain"), ("20 kN/m", "plain"), ("迁移失败", "fail")]),
            ("质量补偿", "预声明规则", [("20.04 / 19.93 kN/m", "plain"), ("20 kN/m", "plain"), ("重新接近", "pass")]),
        ] if zh else [
            ("Initial", "MuJoCo · 0.2 kg", [("≈80 kN/m", "plain"), ("20 kN/m", "plain"), ("uncalibrated", "fail")]),
            ("Calibrated", "same fixture and load", [("≈20 kN/m", "plain"), ("20 kN/m", "plain"), ("target range", "pass")]),
            ("Direct transfer", "0.1 kg / 0.4 kg", [("10.01 / 40.04 kN/m", "plain"), ("20 kN/m", "plain"), ("transfer fails", "fail")]),
            ("Mass conversion", "predeclared rule", [("20.04 / 19.93 kN/m", "plain"), ("20 kN/m", "plain"), ("restored", "pass")]),
        ]
        note = ""
    elif case["id"] == "pinch":
        caption = "指关节驱动力限额与保持结果" if zh else "Finger-joint force limit and retention outcome"
        headers = ["力限额", "保持", "释放检查", "读法"] if zh else ["Force limit", "Retention", "Release check", "Reading"]
        rows = [
            ("0.2 N", "", [("滑脱", "plain"), ("无有效保持", "plain"), ("失败", "fail")]),
            ("0.4 N", "", [("滑脱", "plain"), ("无有效保持", "plain"), ("失败", "fail")]),
            ("0.8 N", "", [("保持", "plain"), ("完成释放", "plain"), ("通过", "pass")]),
            ("10 N", "", [("保持", "plain"), ("完成释放", "plain"), ("通过", "pass")]),
        ] if zh else [
            ("0.2 N", "", [("slips", "plain"), ("no valid hold", "plain"), ("fail", "fail")]),
            ("0.4 N", "", [("slips", "plain"), ("no valid hold", "plain"), ("fail", "fail")]),
            ("0.8 N", "", [("holds", "plain"), ("released", "plain"), ("pass", "pass")]),
            ("10 N", "", [("holds", "plain"), ("released", "plain"), ("pass", "pass")]),
        ]
        note = ""
    else:
        caption = "原版 2 ms 与 1 ms 的同动作对照" if zh else "Original 2 ms and 1 ms execution under the same actions"
        headers = ["指标", "原版 2 ms", "对照 1 ms", "读法"] if zh else ["Measure", "Original 2 ms", "1 ms control", "Reading"]
        rows = [
            ("留出原任务", "", [("10 / 10", "plain"), ("10 / 10", "plain"), ("无法区分", "mixed")]),
            ("物理诊断", "", [("5 / 10", "plain"), ("3 / 10", "plain"), ("退化", "fail")]),
            ("原生步进成本", "", [("2.239 s", "plain"), ("4.481 s", "plain"), ("约翻倍", "fail")]),
        ] if zh else [
            ("Heldout native task", "", [("10 / 10", "plain"), ("10 / 10", "plain"), ("not discriminating", "mixed")]),
            ("Physical screen", "", [("5 / 10", "plain"), ("3 / 10", "plain"), ("regression", "fail")]),
            ("Native stepping cost", "", [("2.239 s", "plain"), ("4.481 s", "plain"), ("≈2×", "fail")]),
        ]
        note = ""
    lines = ['<div class="comparison-matrix">', "<table>", f"<caption>{html.escape(caption)}</caption>", "<thead><tr>"]
    lines += [f'<th scope="col">{html.escape(h)}</th>' for h in headers]
    lines += ["</tr></thead>", "<tbody>"]
    for name, detail, cells in rows:
        label = f"<strong>{html.escape(name)}</strong>"
        if detail:
            label += f"<small>{html.escape(detail)}</small>"
        lines.append("<tr><th scope=\"row\">" + label + "</th>")
        for text, state in cells:
            cls = "matrix-result" if state != "plain" else ""
            value = f'<span class="{cls} {state}">{html.escape(text)}</span>' if cls else html.escape(text)
            lines.append(f"<td>{value}</td>")
        lines.append("</tr>")
    lines += ["</tbody>", "</table>", "</div>"]
    if note:
        lines += [f'<p class="matrix-note">{html.escape(note)}</p>']
    lines.append("")
    return "\n".join(lines)


def comparisons(index, experiences, language):
    zh = language == "zh"
    lines = [
        "# "
        + ("对比实验：从画面到判据" if zh else "Comparative experiments: from visible motion to criteria"),
        "",
        (
            "每个实验按同一顺序阅读：先看结论与判据，再看同条件的同步回放，随后用结果矩阵定位差异。最后才进入协议、解释和边界。"
            if zh
            else "Read every experiment in the same order: conclusion and criteria first, then the synchronized replay under shared conditions, then a result matrix that locates the differences. Protocols, explanation and limits follow."
        ),
        "",
        (
            "画面采用实物比例；微小变化看局部曲线。虚线是案例声明的解析／工程参照，并不代表真实材料测量。不同历史协议的结果不汇总为引擎排行榜。"
            if zh
            else "Replay geometry keeps physical proportions; inspect small changes in the curves. Dashed lines are the declared analytical/engineering references, not measured material truth. Historical protocols do not form a universal engine ranking."
        ),
        "",
    ]
    labels = [
        ("condition", "条件", "Conditions"),
        ("observation", "观察", "Observation"),
        ("explanation", "解释", "Explanation"),
        ("advice", "建议", "Advice"),
        ("boundary", "边界", "Limits"),
    ]
    for case in index["cases"]:
        row = next(e for e in experiences if e["id"] == case["experience_id"])
        lines += [
            f"({case['id']})=",
            "## " + case["title"][language],
            "",
            case["intro"][language],
            "",
            comparison_summary(case, row, language),
            replay_guide(case, language),
            replay_html(case, language),
            comparison_table(case, language),
        ]
        for key, z, e in labels:
            lines += ["**" + (z if zh else e) + "：** " + row[language][key], ""]
        for key in ("selection", "reference", "parameters"):
            if key in case:
                lines += [case[key][language], ""]
        lines += [
            ("**证据与全部配置：** " if zh else "**Evidence and all configurations:** ")
            + re.sub(
                r"\(([^)]+)\.html(?:#([^)]+))?\)",
                lambda m: (
                    "(" + m[2] + ")"
                    if m[2] in ("mass-size-transfer", "transient-cost")
                    else "(" + m[1] + ".md)"
                ),
                case["evidence"][language],
            ),
            "",
        ]
        if case["id"] == "normal":
            lines += [
                "![Response and cost](../../evidence/response-cost-v1.png)",
                "",
                "![Mass / size transfer failures](../../evidence/contact-transfer-v1.png)",
                "",
            ]
    return "\n".join(lines)


def highlights(index, language, site):
    zh = language == "zh"
    lines = ["## " + ("我们已经知道什么" if zh else "What we already know"), ""]
    for case in index["cases"]:
        target = (
            case["id"]
            if site
            else site_url(language, "visual-comparisons.html#" + case["id"])
        )
        first = case["variants"][0]["data"]["path"]
        bundle = read_bundle(ROOT / first)
        poster = "docs/evidence/visual/" + bundle["videos"][0]["poster"]
        if case["id"] == "libero":
            poster = "docs/evidence/visual/libero-summary.png"
        if case["id"] == "pinch":
            poster = (
                "docs/evidence/visual/pinch-summary.png"
                if site
                else "docs/evidence/force-limit/comparison.gif"
            )
        figure = (
            f"normal-summary.{language}"
            if case["id"] == "normal"
            else Path(first).name.removesuffix(".json.gz")
            + "-curves"
            + (".zh" if zh else "")
        )
        prefix = "../../../" if site else ""
        if site:
            lines.append(f"(experiment-highlight-{case['id']})=")
        lines += [
            "### " + case["title"][language],
            "",
            case["intro"][language],
            "",
            f"![{case['title'][language]}]({prefix}{poster})",
            "",
            f"![{case['title'][language]} — curves]({prefix}docs/evidence/visual/{figure}.svg)",
            "",
            f"[{'同步回放、逐步曲线、参数与原始证据' if zh else 'Synchronized replay, full-rate curves, parameters and original evidence'}]({target})",
            "",
        ]
    return "\n".join(lines)


def update(root=ROOT, check_only=False):
    manifest = json.loads((root / "docs/research-experiences.json").read_text())
    index = check(root)
    inventory = load_inventory(root)
    stale = []

    def save(path, content):
        old = path.read_text() if path.exists() else ""
        if content != old:
            stale.append(str(path.relative_to(root)))
            if not check_only:
                path.write_text(content)

    for lang in ("zh", "en"):
        # Homepages are curated reading paths; detailed indexes stay reproducible.
        path = root / f"docs/site/{lang}/experiments.md"
        text = path.read_text()
        start, end = MARKERS
        if text.count(start) != 1 or text.count(end) != 1:
            raise ValueError("Expected generated visual marker pair")
        before, rest = text.split(start)
        _, after = rest.split(end)
        block = (
            catalogue(index, lang, True)
            + "\n"
            + highlights(index, lang, True)
            + "\n"
            + engine_table(inventory, lang, True)
        )
        save(path, before + start + "\n" + block + "\n" + end + after)
        save(
            root / f"docs/site/{lang}/visual-comparisons.md",
            comparisons(index, manifest["experiences"], lang),
        )
    if check_only and stale:
        raise ValueError("Stale visual pages: " + ", ".join(stale))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    update(check_only=args.check)
