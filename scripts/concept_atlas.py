"""Build the bilingual concept atlas from one reviewed source of truth."""

import html
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATLAS_PATH = ROOT / "docs/concept-atlas.json"
TAXONOMY_PATH = ROOT / "docs/solver-taxonomy.json"
RELATION_TYPES = {"depends_on", "related", "contrasts_with", "part_of"}
RELATION_LABELS = {
    "depends_on": ("依赖", "Depends on"),
    "related": ("相关", "Related"),
    "contrasts_with": ("对照", "Contrasts with"),
    "part_of": ("属于", "Part of"),
}
LEVEL_LABELS = {
    "core": ("核心", "Core"),
    "advanced": ("进阶", "Advanced"),
}
ROLE_TO_CONCEPTS = {
    "constraint": ("equality-constraint", "contact"),
    "contact": ("contact",),
    "cone": ("friction", "contact"),
    "coupling": ("equality-constraint", "contact"),
    "deformable": ("contact",),
    "dynamics": ("force", "mass-matrix"),
    "friction": ("friction", "contact"),
    "implementation": ("solver-iteration", "contact"),
    "integrator": ("integrator", "timestep"),
    "linear": ("solver-iteration", "residual"),
    "linear_selection": ("solver-iteration", "tolerance"),
    "nonlinear": ("solver-iteration", "residual"),
    "precision": ("precision", "readback"),
    "settings": ("solver-iteration", "tolerance"),
}
CANONICAL_SOLVER_DEFS = {
    "newton": (
        "Newton 类方法在当前记录中表示求解非线性约束或残差方程，而不是 Newton 物理引擎本身。",
        "Newton methods here solve nonlinear constraint or residual equations; they are not the Newton Physics engine.",
    ),
    "cg": (
        "共轭梯度用一组共轭方向迭代求解线性或局部线性化系统。",
        "Conjugate gradient iteratively solves a linear or locally linearized system with conjugacy constraints.",
    ),
    "pgs": (
        "PGS 逐行更新约束变量，常用于投影 Gauss-Seidel 接触求解。",
        "PGS updates constraint variables row by row and commonly denotes projected Gauss-Seidel contact solving.",
    ),
    "tgs": (
        "TGS 在子步中推进位置与速度求解，常与 PhysX 的刚度和子步语义一起出现。",
        "TGS advances position and velocity solving across substeps, often paired with PhysX stiffness and substep semantics.",
    ),
    "elliptic": (
        "椭圆摩擦锥让切向摩擦限额随方向连续变化，更接近各向同性锥。",
        "An elliptic friction cone varies the tangential limit continuously with direction and approximates an isotropic cone.",
    ),
    "pyramidal": (
        "棱锥摩擦锥用线性面近似圆摩擦锥，通常更便宜但方向误差不同。",
        "A pyramidal cone approximates the circular friction cone with planar faces, usually cheaper with different directional error.",
    ),
    "euler": (
        "Euler 是显式或半隐式的一阶时间推进选项；具体阻尼处理仍需读实现。",
        "Euler is a first-order explicit or semi-implicit time option; inspect the implementation for damping treatment.",
    ),
    "implicitfast": (
        "implicitfast 隐式处理主要速度相关导数，省略部分昂贵耦合项。",
        "implicitfast integrates major velocity-dependent derivatives implicitly while omitting selected costly coupling terms.",
    ),
    "approximate_implicitfast": (
        "approximate_implicitfast 是框架提供的近似隐式积分配置，不自动等价于 MuJoCo 同名积分器。",
        "approximate_implicitfast is a framework integration profile and is not automatically equivalent to MuJoCo's integrator.",
    ),
    "bfgs": (
        "BFGS 用低秩 Hessian 近似执行拟 Newton 更新。",
        "BFGS performs quasi-Newton updates through a low-rank Hessian approximation.",
    ),
    "sr1": (
        "SR1 用对称秩一公式更新二阶近似。",
        "SR1 updates a second-order approximation with a symmetric rank-one formula.",
    ),
    "gmres": (
        "GMRES 通过 Krylov 子空间最小化残差，适用于一般非对称线性系统。",
        "GMRES minimizes residuals in a Krylov subspace and targets general nonsymmetric linear systems.",
    ),
    "ldlt": (
        "LDLT 将对称系统分解为下三角矩阵、对角块和转置因子。",
        "LDLT factors a symmetric system into a lower-triangular matrix, diagonal block and transpose.",
    ),
    "lu": (
        "LU 将一般线性系统分解为下三角与上三角因子。",
        "LU factorization represents a general linear system with lower- and upper-triangular factors.",
    ),
    "minres": (
        "MINRES 面向对称不定的线性系统，以残差最小化为目标。",
        "MINRES targets symmetric indefinite linear systems by minimizing residuals.",
    ),
    "auto": (
        "AUTO 是分支选择策略，不是已执行算法或运行时遥测。",
        "AUTO is a branch-selection policy, not an executed algorithm or runtime trace.",
    ),
    "pbd": (
        "PBD 通过投影约束修正位置，再根据修正反推速度。",
        "PBD projects constraints in position and derives velocity from the correction.",
    ),
    "xpbd": (
        "XPBD 在 PBD 中加入柔度和时间步相关的约束乘子。",
        "XPBD extends PBD with compliance and timestep-dependent constraint multipliers.",
    ),
    "vbd": (
        "VBD 通过分块坐标和局部变分更新推进隐式刚体或软体动力学。",
        "VBD advances implicit rigid or soft dynamics through block-coordinate variational updates.",
    ),
    "featherstone": (
        "Featherstone 以递归 articulated-body 动力学处理关节树。",
        "Featherstone dynamics uses recursive articulated-body algorithms on kinematic trees.",
    ),
    "sap": (
        "SAP 是把非穿透与摩擦写成锥约束的接触求解路径。",
        "SAP formulates non-penetration and friction as cone constraints.",
    ),
    "hydroelastic": (
        "Hydroelastic 接触把几何侵入映射为体积或压力分布接触响应。",
        "Hydroelastic contact maps geometric intrusion into volumetric or pressure-distributed response.",
    ),
    "point": (
        "点接触只通过离散接触点传递力，缺少连续表面压力分布。",
        "Point contact transmits force through discrete contact points rather than a continuous surface-pressure field.",
    ),
}


def _slug(value):
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "item"


def _normalize_relations(concepts):
    by_id = {item["id"]: item for item in concepts}
    for item in concepts:
        outgoing = list(item.get("relations", []))
        for relation in outgoing:
            target = relation["target"]
            if target not in by_id:
                raise ValueError(f"{item['id']} refers to missing concept {target}")
            if target == item["id"]:
                raise ValueError(f"{item['id']} relates to itself")
            if relation["type"] not in RELATION_TYPES:
                raise ValueError(f"Invalid relation type {relation['type']}")
        item["relations"] = outgoing
    for item in concepts:
        additions = []
        for other in concepts:
            for relation in other.get("relations", []):
                if relation["target"] != item["id"]:
                    continue
                inverse = (
                    relation["type"]
                    if relation["type"] in {"related", "contrasts_with"}
                    else "related"
                )
                additions.append({"type": inverse, "target": other["id"]})
        existing = {(r["type"], r["target"]) for r in item["relations"]}
        for relation in additions:
            key = (relation["type"], relation["target"])
            if key not in existing and relation["target"] != item["id"]:
                item["relations"].append(relation)
                existing.add(key)


def _solver_concept(engine, token, role, label, roles, engine_data):
    role_name = roles[role]
    engine_id = _slug(engine)
    token_id = _slug(token)
    summary = CANONICAL_SOLVER_DEFS.get(
        token,
        (
            f"{label} 是 {engine} 固定配置中登记为“{role_name['zh']}”的求解或运行选项。",
            f"{label} is a solver or runtime option registered as “{role_name['en']}” in this fixed {engine} profile.",
        ),
    )
    relations = [
        {"type": "related", "target": target}
        for target in ROLE_TO_CONCEPTS.get(role, ())
    ]
    sources = []
    for source in engine_data.get("sources", []):
        if source.startswith("http"):
            sources.append(
                {
                    "zh": f"{engine} 官方来源",
                    "en": f"{engine} official source",
                    "url": source,
                }
            )
        else:
            sources.append(
                {
                    "zh": f"DexLab {engine} 记录",
                    "en": f"DexLab {engine} record",
                    "url": f"https://github.com/huangkiki/Dexlab/blob/main/{source}",
                }
            )
    return {
        "id": f"solver-{engine_id}-{token_id}",
        "group": "solver",
        "level": "advanced",
        "kind": "solver",
        "engine": engine,
        "token": token,
        "name": {"zh": label, "en": label},
        "aliases": {"zh": [token], "en": [token]},
        "summary": {"zh": summary[0], "en": summary[1]},
        "body": {
            "zh": f"这里的结论只指 {engine} 登记配置中的 `{token}`。同名 token 在其他引擎或上下文中可能承担不同角色，不能仅凭名称合并。",
            "en": f"This entry refers only to `{token}` in the registered {engine} profile. The same token can play another role in a different engine or context.",
        },
        "example": {
            "zh": f"先读取 {engine} 的编译后配置、实际运行路径与角色，再讨论该 `{token}` 是否执行。",
            "en": f"Read the compiled {engine} configuration, actual runtime path and role before claiming that `{token}` executed.",
        },
        "confusions": {
            "zh": ["登记名称不等于已执行算法，同名 token 也不保证语义相同。"],
            "en": ["A registered name does not prove execution, and equal tokens do not guarantee equal semantics."],
        },
        "relations": relations,
        "sources": sources,
        "related_pages": ["solver-taxonomy"],
    }


def load_atlas(path=ATLAS_PATH, taxonomy_path=TAXONOMY_PATH):
    atlas = json.loads(Path(path).read_text())
    taxonomy = json.loads(Path(taxonomy_path).read_text())
    if atlas.get("schema_version") != 1:
        raise ValueError("Unsupported concept-atlas schema")
    concepts = list(atlas["concepts"])
    ids = set()
    aliases = {"zh": set(), "en": set()}
    for item in concepts:
        if item["id"] in ids:
            raise ValueError(f"Duplicate concept identifier {item['id']}")
        ids.add(item["id"])
        for field in ("name", "summary", "body", "example", "confusions"):
            value = item.get(field)
            if not isinstance(value, dict) or not value.get("zh") or not value.get("en"):
                raise ValueError(f"{item['id']} lacks bilingual {field}")
        if item.get("level") not in LEVEL_LABELS:
            raise ValueError(f"{item['id']} has an unknown level")
        for source in item.get("sources", []):
            if isinstance(source, str) and source not in atlas["sources"]:
                raise ValueError(f"{item['id']} refers to missing source {source}")
        for language in ("zh", "en"):
            for alias in item.get("aliases", {}).get(language, []):
                key = alias.casefold()
                if key in aliases[language]:
                    raise ValueError(f"Duplicate concept alias {alias}")
                aliases[language].add(key)
    token_count = 0
    for engine, engine_data in taxonomy["engines"].items():
        for token, (role, label) in engine_data["tokens"].items():
            item = _solver_concept(
                engine,
                token,
                role,
                label,
                taxonomy["roles"],
                engine_data,
            )
            if item["id"] in ids:
                raise ValueError(f"Duplicate generated solver concept {item['id']}")
            ids.add(item["id"])
            concepts.append(item)
            token_count += 1
    expected = sum(len(data["tokens"]) for data in taxonomy["engines"].values())
    if token_count != expected:
        raise ValueError("Solver taxonomy expansion is incomplete")
    group_ids = {group["id"] for group in atlas["groups"]}
    for item in concepts:
        if item["group"] not in group_ids:
            raise ValueError(f"Unknown concept group {item['group']}")
    _normalize_relations(concepts)
    order = {group["id"]: index for index, group in enumerate(atlas["groups"])}
    concepts.sort(
        key=lambda item: (
            order[item["group"]],
            0 if item.get("level") == "core" else 1,
            item["name"]["en"].casefold(),
        )
    )
    return {
        "schema_version": 1,
        "groups": atlas["groups"],
        "sources": atlas["sources"],
        "concepts": concepts,
        "solver_tokens": token_count,
    }


def _concept_by_id(atlas):
    return {item["id"]: item for item in atlas["concepts"]}


def _group_items(atlas):
    grouped = {group["id"]: [] for group in atlas["groups"]}
    for item in atlas["concepts"]:
        grouped[item["group"]].append(item)
    return grouped


def _render_relation_data(item):
    relations = [
        {"id": relation["target"], "type": relation["type"]}
        for relation in item.get("relations", [])
    ]
    return html.escape(json.dumps(relations, ensure_ascii=False), quote=True)


def render_field(atlas, language):
    grouped = _group_items(atlas)
    groups = []
    for group in atlas["groups"]:
        words = "".join(
            "<span>"
            + html.escape(item["name"][language])
            + "</span>"
            for item in grouped[group["id"]]
        )
        groups.append(
            f'<section class="concept-field-group">'
            f'<span class="concept-field-group-name">{html.escape(group[language])}</span>'
            f'<div class="concept-field-words">{words}</div>'
            "</section>"
        )
    return (
        '<div class="concept-field" aria-hidden="true">'
        '<div class="concept-field-inner">'
        + "".join(groups)
        + "</div></div>"
    )


def render_dialog(atlas, language):
    grouped = _group_items(atlas)
    groups = []
    filter_buttons = [
        '<button type="button" data-concept-filter="all" aria-pressed="true">'
        + ("全部" if language == "zh" else "All")
        + "</button>"
    ]
    for group in atlas["groups"]:
        filter_buttons.append(
            f'<button type="button" data-concept-filter="{group["id"]}" aria-pressed="false">'
            f'{html.escape(group[language])}</button>'
        )
        terms = []
        for item in grouped[group["id"]]:
            search = " ".join(
                [item["name"][language], *item.get("aliases", {}).get(language, [])]
            )
            engine = f'<small>{html.escape(item["engine"])}</small>' if item.get("engine") else ""
            terms.append(
                f'<a class="concept-term concept-level-{item["level"]}" '
                f'href="concepts/{item["id"]}.html" '
                f'data-concept="{item["id"]}" '
                f'data-name="{html.escape(item["name"][language], quote=True)}" '
                f'data-search="{html.escape(search.casefold(), quote=True)}" '
                f'data-summary="{html.escape(item["summary"][language], quote=True)}" '
                f'data-relations="{_render_relation_data(item)}">'
                f'{html.escape(item["name"][language])}{engine}</a>'
            )
        groups.append(
            f'<section class="concept-map-group" data-concept-group="{group["id"]}">'
            f'<h3>{html.escape(group[language])}</h3>'
            f'<div class="concept-map-terms">{"".join(terms)}</div>'
            "</section>"
        )
    default = next(item for item in atlas["concepts"] if item["level"] == "core")
    empty_relations = (
        "鼠标悬停或键盘聚焦一个词，查看关系与对照。"
        if language == "zh"
        else "Hover or focus a term to reveal relations and contrasts."
    )
    close_label = "关闭概念星图" if language == "zh" else "Close concept atlas"
    search_label = "搜索概念、别名或 Solver token" if language == "zh" else "Search concepts, aliases or solver tokens"
    title = "概念星图" if language == "zh" else "Concept atlas"
    intro = (
        "所有物理概念与已登记 Solver 配置在一张可读的关系图里。先找词，再回到论文、课程和实验记录。"
        if language == "zh"
        else "A reading graph of physical concepts and every registered solver token, connected back to papers, lessons and experiment records."
    )
    status = f"{len(atlas['concepts'])} 个词条" if language == "zh" else f"{len(atlas['concepts'])} entries"
    return (
        '<dialog class="concept-dialog" id="concept-atlas" aria-labelledby="concept-atlas-title">'
        '<div class="concept-dialog-shell">'
        '<header class="concept-dialog-head">'
        f'<div><h2 id="concept-atlas-title">{title}</h2><p>{intro}</p></div>'
        f'<button class="concept-close" type="button" aria-label="{close_label}">'
        '<span aria-hidden="true">×</span></button>'
        '</header>'
        '<div class="concept-toolbar">'
        f'<label><span class="visually-hidden">{search_label}</span>'
        f'<input type="search" data-concept-search placeholder="{search_label}" autocomplete="off"></label>'
        f'<div class="concept-filters" aria-label="{search_label}">{"".join(filter_buttons)}</div>'
        f'<p class="concept-status" role="status">{status}</p>'
        '</div>'
        '<div class="concept-atlas-layout">'
        f'<div class="concept-map" data-concept-map>{"".join(groups)}'
        '<svg class="concept-lines" aria-hidden="true"></svg></div>'
        '<aside class="concept-lens" data-concept-lens aria-live="polite">'
        f'<p class="concept-lens-name">{html.escape(default["name"][language])}</p>'
        f'<p class="concept-lens-summary">{html.escape(default["summary"][language])}</p>'
        f'<p class="concept-lens-relations">{empty_relations}</p>'
        f'<a class="concept-lens-link" href="concepts/{default["id"]}.html">'
        + ("打开完整词条 →" if language == "zh" else "Open full entry →")
        + "</a></aside>"
        '</div>'
        '</div></dialog>'
    )


def home_context(language):
    atlas = load_atlas()
    return {
        "concept_field_html": render_field(atlas, language),
        "concept_dialog_html": render_dialog(atlas, language),
        "concept_count": len(atlas["concepts"]),
        "concept_solver_count": atlas["solver_tokens"],
    }


def _related_line(relation, target, language):
    by_id = target["by_id"]
    relation_labels = target["relation_labels"]
    target_item = by_id[relation["target"]]
    labels = relation_labels[relation["type"]]
    label = labels[0] if language == "zh" else labels[1]
    return (
        f"- **{label}** · [{target_item['name'][language]}]({relation['target']}.md)"
    )


def _page_markdown(item, atlas, language):
    zh = language == "zh"
    by_id = _concept_by_id(atlas)
    group = next(group for group in atlas["groups"] if group["id"] == item["group"])
    aliases = item.get("aliases", {}).get(language, [])
    meta = [group[language], LEVEL_LABELS[item["level"]][0 if zh else 1]]
    if item.get("engine"):
        meta.insert(0, item["engine"])
    if aliases:
        meta.append(("别名：" if zh else "Also: ") + " / ".join(aliases))
    lines = [
        f"# {item['name'][language]}",
        "",
        f'<p class="concept-page-summary">{html.escape(item["summary"][language])}</p>',
        f'<p class="concept-page-meta">{" · ".join(html.escape(value) for value in meta)}</p>',
        "",
        item["body"][language],
        "",
        "## " + ("看一个具体差别" if zh else "A concrete distinction"),
        "",
        item["example"][language],
        "",
        "## " + ("容易混淆" if zh else "Common confusion"),
        "",
    ]
    lines.extend(f"- {text}" for text in item.get("confusions", {}).get(language, []))
    if item.get("formula"):
        lines += ["", "## " + ("公式" if zh else "Formula"), "", f"`{item['formula']}`"]
    lines += ["", "## " + ("概念关系" if zh else "Relations"), ""]
    relation_context = {"by_id": by_id, "relation_labels": RELATION_LABELS}
    lines.extend(
        _related_line(relation, relation_context, language)
        for relation in item.get("relations", [])
    )
    lines += ["", "## " + ("依据与继续阅读" if zh else "Sources and further reading"), ""]
    for source in item.get("sources", []):
        if isinstance(source, str):
            source = atlas["sources"][source]
        url = source["url"]
        if not re.match(r"^[a-z]+:", url) and ".html" in url:
            url = "../" + url.replace(".html", ".md", 1)
        lines.append(f"- [{source[language]}]({url})")
    if "solver-taxonomy" in item.get("related_pages", []):
        lines.append(
            "- [" + ("DexLab 求解配置分层" if zh else "DexLab solver taxonomy") + "](../solver-taxonomy.md)"
        )
    lines += [
        "",
        f"[← {'返回概念星图' if zh else 'Back to concept atlas'}](index.md)",
        "",
    ]
    return "\n".join(lines)


def _index_markdown(atlas, language):
    zh = language == "zh"
    grouped = _group_items(atlas)
    lines = [
        "# " + ("概念星图" if zh else "Concept atlas"),
        "",
        (
            "从物理量、接触、动力学、数值推进、验证证据与 Solver 配置进入词条。"
            if zh
            else "Browse concepts through physics, contact, dynamics, numerical stepping, evidence and solver configurations."
        ),
        "",
        (
            f"共 {len(atlas['concepts'])} 个词条，其中 {atlas['solver_tokens']} 个来自已登记 Solver token。"
            if zh
            else f"{len(atlas['concepts'])} entries, including {atlas['solver_tokens']} registered solver tokens."
        ),
        "",
    ]
    for group in atlas["groups"]:
        lines += [f"## {group[language]}", ""]
        for item in grouped[group["id"]]:
            lines.append(
                f"- [{item['name'][language]}]({item['id']}.md) — {item['summary'][language]}"
            )
        lines.append("")
    lines += ["```{toctree}", ":hidden:", ":maxdepth: 1", ""]
    lines.extend(f"{item['name'][language]} <{item['id']}>" for item in atlas["concepts"])
    lines += ["```", ""]
    return "\n".join(lines)


def prepare_concept_pages(language_dir):
    atlas = load_atlas()
    language = "zh" if language_dir.name == "zh" else "en"
    output = language_dir / "concepts"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / "index.md").write_text(_index_markdown(atlas, language))
    for item in atlas["concepts"]:
        (output / f"{item['id']}.md").write_text(_page_markdown(item, atlas, language))
    return atlas
