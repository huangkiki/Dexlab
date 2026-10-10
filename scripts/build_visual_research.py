"""Generate bilingual visual entry points from the coverage and experience indexes."""

import argparse
import html
import json
import re
from pathlib import Path

from task_coverage import load_inventory
from visual_research import ROOT, check, read_bundle

MARKERS = ("<!-- visual-research:start -->", "<!-- visual-research:end -->")
SITE = "https://huangkiki.github.io/Dexlab/"
ENGINES = ("MuJoCo", "SuperDex", "Genesis", "Newton Physics", "PhysX", "Drake")


def solver_summary(engine, rows):
    """Derive the compact inventory from actual registered configurations."""
    names = {
        r["solver"]
        for r in rows
        if not any(
            word in r["solver"].lower()
            for word in ("unqualified", "not qualified", "pending", "historical")
        )
        and not r["solver"].startswith("MJWarp")
    }
    aliases = {
        "NEWTON": "Newton",
        "xpbd": "XPBD",
        "vbd": "VBD",
        "semi_implicit": "SemiImplicit",
        "featherstone": "Featherstone",
        "style3d": "Style3D",
    }
    primary = sorted(
        {aliases.get(n.split("/")[0].strip(), n.split("/")[0].strip()) for n in names}
        - {"experimental-shell"}
    )
    tokens = {part.strip() for n in names for part in n.split("/")[1:]}
    if engine == "SuperDex":
        details = sorted(t for t in tokens if t != "FP64" and "CUDA" not in t)
        if any("CUDA" in t for t in tokens):
            details.append("GPU → matrix")
    elif engine == "Drake":
        details = sorted(tokens)
    elif engine == "Genesis":
        details = sorted(
            {
                t.lower()
                for t in tokens
                if t.lower()
                in ("elliptic", "pyramidal", "convex", "signorini", "rigid coupling")
            }
        )
    elif engine == "MuJoCo":
        details = sorted(tokens & {"elliptic", "pyramidal"})
    elif engine == "Newton Physics":
        details = sorted(tokens & {"PADMM", "DVI"})
    else:
        details = sorted(tokens)
    return " · ".join(primary) + ("; " + " / ".join(details) if details else "")


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
            "引擎 | 已登记比较对象 | 实验版本与路径 |"
            if zh
            else "Engine | Registered comparison configurations | Experiment versions and paths |"
        ),
        "| --- | --- | --- |",
    ]
    for engine in ENGINES:
        rows = [r for r in inventory["rows"] if r["engine"] == engine]
        if not rows:
            raise ValueError("Engine missing from coverage: " + engine)
        solvers = solver_summary(engine, rows)
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
    lines += [
        "**MJWarp 运行路径对照（归入 MuJoCo 核心）**"
        if zh
        else "**MJWarp path comparison (MuJoCo core)**",
        "",
        "| 运行路径 | 实际物理核心 | solver／接触路径 | 任务验收状态 |"
        if zh
        else "| Runtime path | Actual physics core | Solver / contact path | Task acceptance |",
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
        "已有模型与时钟诊断；可靠任务验收仍按矩阵状态记录。[路径差异 #152](https://github.com/huangkiki/Dexlab/issues/152) 保留独立研究范围。"
        if zh
        else "Model/clock diagnostics already exist; task acceptance retains the matrix state. [Path differences #152](https://github.com/huangkiki/Dexlab/issues/152) remain a separate research question.",
        "",
    ]
    return "\n".join(lines)


def catalogue(index, language, site):
    zh = language == "zh"
    lines = ["## " + ("做了哪些实验" if zh else "What experiments have we run?"), ""]
    if site:
        lines.insert(0, "(visual-experiment-catalogue)=")
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
            "**待开展／未完成：** 推动、手内旋转、主动折布及更广抓取迁移分别见现有 Issue。预折叠下落不等于主动折布成功；重复、步长扫描和框架切换不增加任务类型。"
            if zh
            else "**Pending / incomplete:** pushing, in-hand rotation, active folding and broader grasp transfer remain in their existing Issues. Folded drop is not active folding; repeats, timestep sweeps and framework switches do not add task types."
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
            f'<div class="dexlab-replay" data-language="{language}" data-variants="{attrs}">',
            f'<div class="visual-hero"><img loading="lazy" src="_static/visual/{video["poster"]}" alt="{html.escape(case["title"][language])}"></div>',
            f'<details class="replay-fallback" open><summary>{caption}</summary><img loading="lazy" src="_static/visual/{stem}-curves{".zh" if language == "zh" else ""}.svg" alt="{caption}"><ul>{"".join(downloads)}</ul></details>',
            "</div>",
            "```",
            "",
        ]
    )


def comparisons(index, experiences, language):
    zh = language == "zh"
    lines = [
        "# "
        + ("从画面到物理差异" if zh else "From visible motion to physical differences"),
        "",
        (
            "同步查看记录状态、原生观测与物理参照。所有图表来自已有实验；这里没有重新运行物理，也没有改变评分或容差。"
            if zh
            else "Inspect recorded states, native observations and physical references together. These are existing experiments; no physics was rerun and no scores or tolerances were changed."
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
            replay_html(case, language),
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
    if site and zh:
        lines.insert(0, "(research-findings)=")
    for case in index["cases"]:
        target = (
            case["id"]
            if site
            else site_url(language, "visual-comparisons.html#" + case["id"])
        )
        first = case["variants"][0]["data"]["path"]
        bundle = read_bundle(ROOT / first)
        poster = "docs/evidence/visual/" + bundle["videos"][0]["poster"]
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
            lines.append(f"(visual-highlight-{case['id']})=")
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

    for lang, readme in [("zh", "README.md"), ("en", "README.en.md")]:
        for path, site in [
            (root / readme, False),
            (root / f"docs/site/{lang}/index.md", True),
        ]:
            text = path.read_text()
            start, end = MARKERS
            if text.count(start) != 1 or text.count(end) != 1:
                raise ValueError("Expected generated visual marker pair")
            before, rest = text.split(start)
            _, after = rest.split(end)
            block = (
                engine_table(inventory, lang, site)
                + "\n"
                + catalogue(index, lang, site)
                + "\n"
                + highlights(index, lang, site)
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
