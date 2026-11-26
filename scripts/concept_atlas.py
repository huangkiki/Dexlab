"""Build the bilingual concept atlas from one reviewed source of truth."""

import html
import json
import re
import shutil
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATLAS_PATH = ROOT / "docs/concept-atlas.json"
DETAILS_PATH = ROOT / "docs/site/concept-details"
TAXONOMY_PATH = ROOT / "docs/solver-taxonomy.json"
TOPIC_TAXONOMY_PATH = ROOT / "docs/topic-taxonomy.json"
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
CONCEPT_PAGE_KINDS = {"concept", "solver"}
ITEM_KINDS = CONCEPT_PAGE_KINDS | {"synthesis"}
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
    "fp64": (
        "FP64 表示双精度浮点计算或读回路径；是否启用取决于具体引擎、构建和配置，不是某一引擎专属能力。",
        "FP64 denotes a double-precision computation or readback path. Whether it is active depends on the engine, build and profile; it is not specific to one engine.",
    ),
    "semiimplicit": (
        "半隐式推进用当前状态推进位置，并对部分速度相关项作隐式处理。",
        "Semi-implicit stepping advances position from the current state and treats selected velocity-dependent terms implicitly.",
    ),
}
SOLVER_KEY_ALIASES = {
    "semi_implicit": "semiimplicit",
    "semiimplicit": "semiimplicit",
}
SOLVER_CANONICAL_LABELS = {
    "cg": "CG",
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


def _solver_concept(key, label, registrations, roles):
    summary = CANONICAL_SOLVER_DEFS.get(
        key,
        (
            f"{label} 是一个求解或运行选项；它的角色和生效条件由具体配置决定。",
            f"{label} is a solver or runtime option whose role and activation conditions are determined by the full profile.",
        ),
    )
    relations = []
    relation_keys = set()
    for registration in registrations:
        for target in ROLE_TO_CONCEPTS.get(registration["role"], ()):
            relation_key = ("related", target)
            if relation_key not in relation_keys:
                relations.append({"type": "related", "target": target})
                relation_keys.add(relation_key)
    contexts = []
    context_keys = set()
    for registration in registrations:
        context_key = (registration["engine"], registration["role"])
        if context_key in context_keys:
            continue
        context_keys.add(context_key)
        contexts.append(
            {
                "engine": registration["engine"],
                "token": registration["token"],
                "role": registration["role"],
                "role_name": roles[registration["role"]],
            }
        )
    aliases = []
    for registration in registrations:
        for alias in (registration["token"], registration["label"]):
            if alias.casefold() not in {value.casefold() for value in aliases}:
                aliases.append(alias)
    sources = []
    source_urls = set()
    for registration in registrations:
        engine = registration["engine"]
        source_entries = []
        for source in registration["sources"]:
            if source.startswith("http"):
                source_entry = {
                    "zh": f"{engine} 官方来源",
                    "en": f"{engine} official source",
                    "url": source,
                }
            else:
                source_entry = {
                    "zh": f"DexLab {engine} 记录",
                    "en": f"DexLab {engine} record",
                    "url": f"https://github.com/huangkiki/Dexlab/blob/main/{source}",
                }
            source_entries.append(source_entry)
        for source_entry in source_entries:
            if source_entry["url"] not in source_urls:
                sources.append(source_entry)
                source_urls.add(source_entry["url"])
    context_zh = "、".join(
        f"{context['engine']}（{context['role_name']['zh']}）" for context in contexts
    )
    context_en = ", ".join(
        f"{context['engine']} ({context['role_name']['en']})" for context in contexts
    )
    return {
        "id": f"solver-{_slug(key)}",
        "group": "solver",
        "level": "advanced",
        "kind": "solver",
        "token": key,
        "contexts": contexts,
        "name": {"zh": label, "en": label},
        "aliases": {"zh": aliases, "en": aliases},
        "summary": {"zh": summary[0], "en": summary[1]},
        "body": {
            "zh": f"这个概念把 `{label}` 作为独立 token 组织。它目前登记于 {context_zh}；跨配置出现不表示语义、实现、精度或计算预算相同。",
            "en": f"This concept treats `{label}` as an independent token. It is currently registered in {context_en}; shared naming does not imply shared semantics, implementation, precision or computational budget.",
        },
        "example": {
            "zh": f"先读取具体配置、实际运行路径与角色，再讨论 `{label}` 是否执行以及执行的是哪一种版本。",
            "en": f"Read the full profile, actual runtime path and role before claiming that `{label}` executed or that two occurrences are equivalent.",
        },
        "confusions": {
            "zh": ["同名 token 不保证语义相同；引擎登记项也不能替代 token 本身。"],
            "en": ["Equal token names do not guarantee equal semantics, and an engine registration does not define the token by itself."],
        },
        "relations": relations,
        "sources": sources,
        "related_pages": ["solver-taxonomy"],
    }


def _load_solver_concepts(taxonomy):
    registrations = {}
    token_count = 0
    for engine, engine_data in taxonomy["engines"].items():
        for token, (role, label) in engine_data["tokens"].items():
            key = SOLVER_KEY_ALIASES.get(token, token)
            registrations.setdefault(key, []).append(
                {
                    "engine": engine,
                    "token": token,
                    "role": role,
                    "label": label,
                    "sources": engine_data.get("sources", []),
                }
            )
            token_count += 1
    concepts = []
    for key, items in registrations.items():
        label = SOLVER_CANONICAL_LABELS.get(key, items[0]["label"])
        concepts.append(_solver_concept(key, label, items, taxonomy["roles"]))
    expected = sum(len(data["tokens"]) for data in taxonomy["engines"].values())
    if token_count != expected:
        raise ValueError("Solver taxonomy expansion is incomplete")
    return concepts, token_count


def _load_topic_taxonomy(path):
    data = json.loads(Path(path).read_text())
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported topic taxonomy schema")
    topics = data.get("topics", [])
    ids = [topic.get("id") for topic in topics]
    if not topics or len(ids) != len(set(ids)):
        raise ValueError("Topic taxonomy must contain unique topics")
    for topic in topics:
        if not topic.get("id"):
            raise ValueError("Topic taxonomy contains an empty identifier")
        for field in ("name", "description"):
            value = topic.get(field)
            if not isinstance(value, dict) or not value.get("zh") or not value.get("en"):
                raise ValueError(f"{topic['id']} lacks bilingual {field}")
    return topics


def load_atlas(
    path=ATLAS_PATH,
    taxonomy_path=TAXONOMY_PATH,
    topic_taxonomy_path=TOPIC_TAXONOMY_PATH,
):
    atlas = json.loads(Path(path).read_text())
    taxonomy = json.loads(Path(taxonomy_path).read_text())
    topics = _load_topic_taxonomy(topic_taxonomy_path)
    topic_ids = {topic["id"] for topic in topics}
    if atlas.get("schema_version") != 1:
        raise ValueError("Unsupported concept-atlas schema")
    concepts = list(atlas["concepts"])
    ids = set()
    aliases = {"zh": set(), "en": set()}
    for item in concepts:
        if item["id"] in ids:
            raise ValueError(f"Duplicate concept identifier {item['id']}")
        ids.add(item["id"])
        item.setdefault("kind", "concept")
        if item["kind"] not in ITEM_KINDS:
            raise ValueError(f"{item['id']} has an unknown kind")
        if item.get("distillation") and (
            item["kind"] != "synthesis"
            or not re.fullmatch(r"[a-z0-9-]+\.html", item.get("href", ""))
        ):
            raise ValueError(f"{item['id']} is not a local distillation article")
        if item["kind"] == "synthesis":
            if not item.get("href"):
                raise ValueError(f"{item['id']} is a synthesis without a target href")
            try:
                date.fromisoformat(item.get("updated", ""))
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"{item['id']} has an invalid synthesis update date"
                ) from error
            if item.get("topic") not in topic_ids:
                raise ValueError(f"{item['id']} has an unknown research topic")
            tags = item.get("tags")
            if (
                not isinstance(tags, dict)
                or not tags.get("zh")
                or not tags.get("en")
            ):
                raise ValueError(f"{item['id']} lacks bilingual research tags")
        required_fields = (
            ("name", "summary")
            if item["kind"] == "synthesis"
            else ("name", "summary", "body", "example", "confusions")
        )
        for field in required_fields:
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
    solver_concepts, solver_registrations = _load_solver_concepts(taxonomy)
    for item in solver_concepts:
        if item["id"] in ids:
            raise ValueError(f"Duplicate generated solver concept {item['id']}")
        ids.add(item["id"])
        concepts.append(item)
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
        "topics": topics,
        "sources": atlas["sources"],
        "concepts": concepts,
        "solver_concepts": len(solver_concepts),
        "solver_registrations": solver_registrations,
    }


def _concept_by_id(atlas):
    return {item["id"]: item for item in atlas["concepts"]}


def distillation_groups(atlas, language):
    topics = {topic["id"]: topic["name"][language] for topic in atlas["topics"]}
    articles = sorted(
        (item for item in atlas["concepts"] if item.get("distillation")),
        key=lambda item: item["updated"],
        reverse=True,
    )
    grouped = {}
    for article in articles:
        grouped.setdefault(article["topic"], []).append(article)
    return [
        (f"distill-{topic_id}", topics[topic_id], articles)
        for topic_id, articles in grouped.items()
    ]


def distillation_markdown(groups, language):
    lines = []
    for anchor, title, articles in groups:
        lines.extend([f"({anchor})=", f"## {title}", ""])
        for article in articles:
            doc = article["href"].removesuffix(".html") + ".md"
            lines.extend([
                f"- [{article['name'][language]}]({doc})",
                "",
                f"  {article['summary'][language]}",
                "",
            ])
    return "\n".join(lines)


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
    ordered = []
    for group_index, group in enumerate(atlas["groups"]):
        items = [
            item
            for item in grouped[group["id"]]
            if item["kind"] != "synthesis"
        ]
        if not items:
            continue
        for item_index, item in enumerate(items):
            progress = (item_index + .5) / len(items)
            ordered.append((progress, group_index, item))
    ordered.sort(key=lambda entry: entry[:2])
    words = []
    for _, _, item in ordered:
        label = item["name"][language]
        length = len(label)
        if item["level"] == "core":
            scale = (
                "xl" if length <= 2 else
                "lg" if length <= 4 else
                "md" if length <= 8 else
                "sm" if length <= 14 else
                "xs"
            )
        else:
            scale = (
                "lg" if length <= 2 else
                "md" if length <= 4 else
                "sm" if length <= 8 else
                "xs"
            )
        words.append(
            f'<span class="concept-field-size-{scale}" '
            f'data-concept-wall-item data-concept-open data-concept-target="{item["id"]}">'
            f"{html.escape(label)}</span>"
        )
    topic_links = []
    topics_by_id = {topic["id"]: topic for topic in atlas["topics"]}
    featured = (
        "complementarity-contact-models.html",
        "cloth-comparison.html",
        "cut-push.html",
    )
    by_route = {item["href"]: item for item in grouped["synthesis"]}
    topic_items = [by_route[route] for route in featured]
    for item in topic_items:
        updated = date.fromisoformat(item["updated"])
        updated_label = (
            f"更新于 {updated.isoformat()}"
            if language == "zh"
            else f"Updated {updated.isoformat()}"
        )
        topic = topics_by_id[item["topic"]]
        tags = list(
            dict.fromkeys(
                [topic["name"][language], *item["tags"][language]]
            )
        )
        tag_html = "".join(
            f'<span class="concept-topic-tag{" is-topic" if index == 0 else ""}">'
            f"{html.escape(tag)}</span>"
            for index, tag in enumerate(tags)
        )
        topic_links.append(
            '<a class="concept-topic-link" '
            f'href="{html.escape(item["href"], quote=True)}">'
            '<span class="concept-topic-head">'
            f"<strong>{html.escape(item['name'][language])}</strong>"
            f'<span class="concept-topic-action">'
            f'{"阅读全文 ↗" if language == "zh" else "Read article ↗"}</span></span>'
            f'<span class="concept-topic-summary">'
            f"{html.escape(item['summary'][language])}</span>"
            '<span class="concept-topic-footer">'
            f'<span class="concept-topic-tags">{tag_html}</span>'
            f'<time datetime="{item["updated"]}">{html.escape(updated_label)}</time>'
            "</span></a>"
        )
    return (
        '<div class="concept-field-band">'
        '<div class="concept-field" id="concept-field" role="navigation" '
        f'aria-label="{"概念词" if language == "zh" else "Concepts"}">'
        '<div class="concept-field-inner">'
        f'<div class="concept-field-words">{"".join(words)}</div>'
        "</div></div>"
        '<a class="concept-atlas-trigger" href="concepts/index.html" data-concept-open>'
        f'{"打开交互星图" if language == "zh" else "Open the interactive atlas"}</a>'
        '<section class="concept-topics" aria-labelledby="concept-topics-title">'
        '<header class="concept-topics-head">'
        f'<h2 id="concept-topics-title">{"精选文章" if language == "zh" else "Selected articles"}</h2>'
        f'<a href="distillation.html">{"浏览蒸馏" if language == "zh" else "Browse distillations"}</a>'
        '</header>'
        f'<div class="concept-topics-grid">{"".join(topic_links)}</div>'
        "</section></div>"
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
            contexts = item.get("contexts", [])
            context_label = " · ".join(
                f"{context['engine']} {context['role_name'][language]}"
                for context in contexts
            )
            href = item.get("href", f"concepts/{item['id']}.html")
            search = " ".join(
                [
                    item["name"][language],
                    *item.get("aliases", {}).get(language, []),
                    context_label,
                ]
            )
            terms.append(
                f'<a class="concept-term concept-level-{item["level"]} concept-kind-{item["kind"]}" '
                f'href="{html.escape(href, quote=True)}" '
                f'data-concept="{item["id"]}" '
                f'data-name="{html.escape(item["name"][language], quote=True)}" '
                f'data-search="{html.escape(search.casefold(), quote=True)}" '
                f'data-summary="{html.escape(item["summary"][language], quote=True)}" '
                f'data-context="{html.escape(context_label, quote=True)}" '
                f'data-kind="{item["kind"]}" '
                f'data-relations="{_render_relation_data(item)}">'
                f'{html.escape(item["name"][language])}</a>'
            )
        groups.append(
            f'<section class="concept-map-group" data-concept-group="{group["id"]}">'
            f'<h3>{html.escape(group[language])}</h3>'
            f'<div class="concept-map-terms">{"".join(terms)}</div>'
            "</section>"
        )
    default = next(item for item in atlas["concepts"] if item["level"] == "core")
    default_href = default.get("href", f'concepts/{default["id"]}.html')
    if default["kind"] == "synthesis":
        default_link_label = (
            "阅读研究总论 →" if language == "zh" else "Read the research synthesis →"
        )
    else:
        default_link_label = "打开完整词条 →" if language == "zh" else "Open full entry →"
    empty_relations = (
        "鼠标悬停或键盘聚焦一个词，查看关系与对照。"
        if language == "zh"
        else "Hover or focus a term to reveal relations and contrasts."
    )
    close_label = "关闭概念星图" if language == "zh" else "Close concept atlas"
    search_label = "搜索概念、别名或 Solver token" if language == "zh" else "Search concepts, aliases or solver tokens"
    title = "概念星图" if language == "zh" else "Concept atlas"
    intro = (
        "物理概念、数值方法和 Solver token 在一张可读的关系图里；跨实验研究总论单独标记，引擎登记上下文不写进 token 名称。"
        if language == "zh"
        else "Physical concepts, numerical methods and solver tokens share one readable graph; cross-experiment syntheses are marked separately and engine registrations remain context rather than part of the token name."
    )
    syntheses = sum(item["kind"] == "synthesis" for item in atlas["concepts"])
    concepts = len(atlas["concepts"]) - syntheses
    status = (
        f"{concepts} 个概念 · {syntheses} 篇研究总论"
        if language == "zh"
        else f"{concepts} concepts · {syntheses} "
        + ("synthesis" if syntheses == 1 else "syntheses")
    )
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
        f'<a class="concept-lens-link" href="{html.escape(default_href, quote=True)}">'
        + default_link_label
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
        "concept_solver_count": atlas["solver_concepts"],
        "concept_solver_registration_count": atlas["solver_registrations"],
    }


def _related_line(relation, target, language):
    by_id = target["by_id"]
    relation_labels = target["relation_labels"]
    target_item = by_id[relation["target"]]
    labels = relation_labels[relation["type"]]
    label = labels[0] if language == "zh" else labels[1]
    link = (
        _generated_link(target_item, target_item["name"][language])
        if target_item["kind"] == "synthesis"
        else f"[{target_item['name'][language]}]({relation['target']}.md)"
    )
    return f"- **{label}** · {link}"


def _page_markdown(item, atlas, language):
    zh = language == "zh"
    by_id = _concept_by_id(atlas)
    group = next(group for group in atlas["groups"] if group["id"] == item["group"])
    aliases = item.get("aliases", {}).get(language, [])
    meta = [group[language], LEVEL_LABELS[item["level"]][0 if zh else 1]]
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
    ]
    details = DETAILS_PATH / language / f"{item['id']}.md"
    if details.is_file():
        lines += [details.read_text(encoding="utf-8").strip(), ""]
    if item.get("contexts"):
        lines += ["## " + ("登记上下文" if zh else "Registered contexts"), ""]
        lines.extend(
            f"- **{context['engine']}** · {context['role_name'][language]}"
            for context in item["contexts"]
        )
        lines += [""]
    lines += [
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
    syntheses = sum(item["kind"] == "synthesis" for item in atlas["concepts"])
    concepts = len(atlas["concepts"]) - syntheses
    lines = [
        "# " + ("概念星图" if zh else "Concept atlas"),
        "",
        (
            "[求解器、积分器与接触配置](../solver-taxonomy.md) · [物理引擎与模型](../engines.md)"
            if zh
            else "[Solvers, integrators and contact models](../solver-taxonomy.md) · [Physics engines and models](../engines.md)"
        ),
        "",
        (
            "从物理量、接触、动力学、数值推进、验证证据与 Solver 配置进入词条；跨实验研究总论与概念分开标记。"
            if zh
            else "Browse concepts through physics, contact, dynamics, numerical stepping, evidence and solver configurations, with cross-experiment syntheses marked separately."
        ),
        "",
        (
            f"共 {concepts} 个概念和 {syntheses} 篇研究总论；其中 {atlas['solver_concepts']} 个是独立 Solver／数值概念，覆盖 {atlas['solver_registrations']} 个引擎登记项。"
            if zh
            else f"{concepts} concepts and {syntheses} research "
            + ("synthesis" if syntheses == 1 else "syntheses")
            + f", including {atlas['solver_concepts']} independent solver or numerical concepts across {atlas['solver_registrations']} engine registrations."
        ),
        "",
    ]
    for group in atlas["groups"]:
        lines += [f"## {group[language]}", ""]
        for item in grouped[group["id"]]:
            link = (
                _generated_link(item, item["name"][language])
                if item["kind"] == "synthesis"
                else f"[{item['name'][language]}]({item['id']}.md)"
            )
            marker = ""
            if item["kind"] == "synthesis":
                marker = " · 研究总论" if zh else " · Research synthesis"
            lines.append(
                f"- {link} — {item['summary'][language]}{marker}"
            )
        lines.append("")
    lines += ["```{toctree}", ":hidden:", ":maxdepth: 1", ""]
    lines.extend(
        f"{item['name'][language]} <{item['id']}>"
        for item in atlas["concepts"]
        if item["kind"] in CONCEPT_PAGE_KINDS
    )
    lines += ["```", ""]
    return "\n".join(lines)


def _generated_target(item):
    """Keep static HTML links intact and map Sphinx pages to Markdown sources."""
    href = item["href"]
    if href.startswith("_static/"):
        return "../" + href
    return "../" + href.replace(".html", ".md")


def _generated_link(item, label):
    """Use raw HTML for static assets so MyST does not resolve them as documents."""
    href = _generated_target(item)
    if href.startswith("../_static/"):
        return (
            f'<a href="{html.escape(href, quote=True)}">'
            f"{html.escape(label)}</a>"
        )
    return f"[{label}]({href})"


def prepare_concept_pages(language_dir):
    atlas = load_atlas()
    language = "zh" if language_dir.name == "zh" else "en"
    output = language_dir / "concepts"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / "index.md").write_text(_index_markdown(atlas, language))
    for item in atlas["concepts"]:
        if item["kind"] == "synthesis":
            continue
        (output / f"{item['id']}.md").write_text(_page_markdown(item, atlas, language))
    return atlas
