"""Generate detailed experiment pages from the coverage and experience indexes."""

import argparse
import html
import json
import re
from pathlib import Path

from visual_research import ROOT, check, read_bundle

MARKERS = ("<!-- visual-research:start -->", "<!-- visual-research:end -->")
CATALOGUE_GROUPS = {
    "rigid-contact": {"zh": "刚体接触与摩擦", "en": "Rigid contact and friction"},
    "grasping": {"zh": "夹持与灵巧操作", "en": "Grasping and manipulation"},
    "deformables": {"zh": "布料与软体操作", "en": "Cloth and soft manipulation"},
    "cutting": {"zh": "切割与刀面推动", "en": "Cutting and blade-driven pushing"},
    "execution": {"zh": "仿真运行路径", "en": "Simulation execution paths"},
}
HIGHLIGHT_ANCHORS = {
    "six-engine-incline": "incline",
    "normal-response": "normal",
    "pinch-load": "pinch",
    "libero-workflow": "libero",
}


def catalogue(index, language):
    rows = index["catalogue"]
    ids = {row["id"] for row in rows}
    if len(ids) != len(rows) or {row["group"] for row in rows} != set(CATALOGUE_GROUPS):
        raise ValueError("Expected unique catalogue entries in the published task groups")
    links = " · ".join(
        f"[{titles[language]}](#tasks-{key})" for key, titles in CATALOGUE_GROUPS.items()
    )
    lines = ["(full-experiment-catalogue)=", links, ""]
    labels = ["任务与所用仿真", "实验结果"] if language == "zh" else ["Task and simulator", "Observed outcome"]
    for key, titles in CATALOGUE_GROUPS.items():
        lines += [f"(tasks-{key})=", "## " + titles[language], "", "```{raw} html",
                  '<div class="task-register">',
                  '<div class="task-register-labels" aria-hidden="true">'
                  + "".join(f"<span>{label}</span>" for label in labels) + "</div>"]
        for row in rows:
            if row["group"] != key:
                continue
            engine = row["engines"]
            if isinstance(engine, dict):
                engine = engine[language]
            alias = HIGHLIGHT_ANCHORS.get(row["id"])
            anchor = f' id="experiment-highlight-{alias}"' if alias else ""
            lines += [
                f'<article class="task-register-entry"{anchor}>',
                '<div><h3><a href="' + html.escape(row["link"]) + '">'
                + html.escape(row["title"][language]) + "</a></h3>",
                '<p class="task-register-engines">' + html.escape(engine) + "</p></div>",
                '<p class="task-register-result">' + html.escape(row["finding"][language]) + "</p>",
                "</article>",
            ]
        lines += ["</div>", "```", ""]
    lines += [
        "[切割任务全集](cutting-experiments.md) · [完整任务盘点](https://github.com/huangkiki/Dexlab/blob/main/docs/inventory/README.zh-CN.md)"
        if language == "zh"
        else "[All cutting tasks](cutting-experiments.md) · [Complete task inventory](https://github.com/huangkiki/Dexlab/blob/main/docs/inventory/README.md)",
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
    previews = {
        "incline": "_static/visual/incline-sliding-0.001.gif",
        "normal": "_static/visual/normal-calibration.gif",
        "pinch": "_static/force-limit/comparison.gif",
        "libero": "_static/visual/libero-demo0-baseline.gif",
    }
    caption = (
        "静态图表与完整数据（无需 JavaScript）"
        if language == "zh"
        else "Static figures and full data (no JavaScript required)"
    )
    downloads = []
    for variant, _ in zip(variants, case["variants"]):
        curve = variant["url"].removesuffix(".json.gz") + (
            "-curves.zh.svg" if language == "zh" else "-curves.svg"
        )
        links = [
            f'<a href="{variant["url"]}">JSON.gz</a>',
            f'<a href="{curve}">SVG</a>',
        ]
        downloads.append(
            f"<li>{html.escape(variant['label'])}: " + " · ".join(links) + "</li>"
        )
    return "\n".join(
        [
            "```{raw} html",
            '<div class="gif-evidence">',
            f'<div class="visual-hero"><img loading="lazy" src="{previews[case["id"]]}" alt="{html.escape(case["title"][language])}"></div>',
            f'<details class="replay-fallback"><summary>{caption}</summary><img loading="lazy" src="_static/visual/{stem}-curves{".zh" if language == "zh" else ""}.svg" alt="{caption}"><ul>{"".join(downloads)}</ul></details>',
            "</div>",
            "```",
            "",
        ]
    )


COMPARISON_CLAIMS = {
    "incline": {
        "zh": "九种公开配置中，没有配置通过全部九例。新增记录显示，Chaos 三个名义零摩擦工况通过，Bullet 两个静止工况通过，SOFA 的滑动轨迹接近参考时，接触力仍可能超出门槛。",
        "en": "None of the nine published profiles passed all nine cases. Chaos passed all three nominal-zero-friction cases. Bullet passed two static cases. SOFA could stay close to the sliding reference while exceeding the contact-force limit.",
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
            "zh": "GIF 相似不等于物理等价；通过或失败仍由同时间轴的力、位移和速度判据决定。",
            "en": "A similar GIF does not establish physical equivalence; force, displacement and velocity criteria on the shared clock decide the result.",
        },
    },
    "normal": {
        "watch": {
            "zh": "先看加载窗的压入量，再看卸载、离面段和其他质量下的响应是否仍接近目标。",
            "en": "Inspect indentation during loading, then whether unloading, separation and other masses remain close to the target.",
        },
        "limit": {
            "zh": "GIF 不能证明材料真实刚度；有效响应只在声明的夹具、载荷和合成目标内成立。",
            "en": "The GIF does not establish real material stiffness; the response is limited to the declared fixture, loads and synthetic target.",
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
            "zh": "原任务成功不能替代物理筛查；GIF 也不能唯一解释 5/10 到 3/10 的退化。",
            "en": "Native task success does not replace physical screening, and the GIF does not uniquely explain the 5/10 → 3/10 regression.",
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
            + ("GIF 阅读说明" if zh else "Recorded GIF guide")
            + '">',
            f'  <p><strong>{"画面顺序" if zh else "Pane order"}</strong> {html.escape(" / ".join(names))}</p>',
            f'  <p><strong>{"看什么" if zh else "What to watch"}</strong> {html.escape(COMPARISON_GUIDES[case["id"]]["watch"][language])}</p>',
            f'  <p><strong>{"不要直接推出" if zh else "Do not infer"}</strong> {html.escape(COMPARISON_GUIDES[case["id"]]["limit"][language])}</p>',
            "</div>",
            "",
        ]
    )


def incline_extension_rows(root):
    evidence = root / "docs/evidence/incline-extension"
    profiles = [
        ("chaos", "Chaos", "UE 5.7.1 · Linux Editor"),
        ("bullet", "Bullet", "PyBullet 3.2.7 · CPU DIRECT"),
        ("sofa", "SOFA", "26.06.00 · rigid OBB / block GS"),
    ]
    for key, label, configuration in profiles:
        rows = json.loads((evidence / f"{key}-results.json").read_text())["cases"]
        positive = [row for row in rows if row["id"] != "negative-no-floor-1ms"]
        groups = [[row for row in positive if row["regime"] == name]
                  for name in ("static", "sliding", "frictionless")]
        if len(positive) != 9 or any(
            {row["timestep"] for row in group} != {.002, .001, .0005} for group in groups
        ):
            raise ValueError(f"Incomplete published incline extension: {key}")
        cells = []
        for group in [*groups, positive]:
            passed = sum(row["status"] == "pass" for row in group)
            invalid = sum(row["status"] == "invalid" for row in group)
            if passed == len(group):
                state = "pass"
            elif invalid == len(group):
                state = "invalid"
            else:
                state = "mixed" if passed else "fail"
            cells.append((f"{passed} / {len(group)}" + ("†" if invalid else ""), state))
        yield label, configuration, cells


def comparison_table(case, language, root):
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
        rows.extend(incline_extension_rows(root))
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


def comparisons(index, experiences, language, root):
    zh = language == "zh"
    lines = [
        "# "
        + ("对比实验：从画面到判据" if zh else "Comparative experiments: from visible motion to criteria"),
        "",
        (
            "每个实验按同一顺序阅读：先看结论与判据，再看同条件的记录 GIF，随后用结果矩阵定位差异。最后才进入协议、解释和边界。"
            if zh
            else "Read every experiment in the same order: conclusion and criteria first, then the recorded GIF under shared conditions, then a result matrix that locates the differences. Protocols, explanation and limits follow."
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
            comparison_table(case, language, root),
        ]
        if case["id"] == "incline":
            lines += [
                (
                    "GIF 保留原六引擎回放。九引擎曲线使用同一 1 ms 工况，点线标记数值记录无效。"
                    if zh else
                    "The GIF retains the original six-engine replay. The nine-engine curves use the same 1 ms conditions. Dotted lines mark invalid records."
                ),
                "",
                (
                    "```{raw} html\n"
                    '<p><a href="_static/incline-extension/static-1ms-curves.zh.svg">静止曲线</a> · '
                    '<a href="_static/incline-extension/sliding-1ms-curves.zh.svg">滑动曲线</a> · '
                    '<a href="_static/incline-extension/frictionless-1ms-curves.zh.svg">名义零摩擦曲线</a></p>\n'
                    "```\n\n[新增工况报告与原始数据](incline-extension.md)"
                    if zh else
                    "```{raw} html\n"
                    '<p><a href="_static/incline-extension/static-1ms-curves.svg">Static curves</a> · '
                    '<a href="_static/incline-extension/sliding-1ms-curves.svg">Sliding curves</a> · '
                    '<a href="_static/incline-extension/frictionless-1ms-curves.svg">Nominal-zero-friction curves</a></p>\n'
                    "```\n\n[New cases and original data](incline-extension.md)"
                ),
                "",
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


def update(root=ROOT, check_only=False):
    manifest = json.loads((root / "docs/research-experiences.json").read_text())
    index = check(root)
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
        block = catalogue(index, lang)
        save(path, before + start + "\n" + block + "\n" + end + after)
        save(
            root / f"docs/site/{lang}/visual-comparisons.md",
            comparisons(index, manifest["experiences"], lang, root),
        )
    if check_only and stale:
        raise ValueError("Stale visual pages: " + ", ".join(stale))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    update(check_only=args.check)
