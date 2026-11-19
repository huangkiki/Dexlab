"""Concept atlas source and generated-page regression tests."""

import re
import tempfile
import unittest
from datetime import date
from pathlib import Path

from scripts.concept_atlas import (
    _normalize_relations,
    load_atlas,
    prepare_concept_pages,
    render_dialog,
    render_field,
)


class ConceptAtlasTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    @classmethod
    def setUpClass(cls):
        cls.atlas = load_atlas()

    def test_solver_tokens_are_canonical_concepts_with_separate_registrations(self):
        solver_entries = [item for item in self.atlas["concepts"] if item["group"] == "solver"]
        self.assertEqual(len(solver_entries), 54)
        self.assertEqual(self.atlas["solver_concepts"], 54)
        self.assertEqual(self.atlas["solver_registrations"], 63)
        self.assertEqual(len({item["id"] for item in solver_entries}), 54)

    def test_cross_engine_tokens_are_merged_without_losing_context(self):
        by_id = {item["id"]: item for item in self.atlas["concepts"]}
        newton = by_id["solver-newton"]
        self.assertEqual(
            {context["engine"] for context in newton["contexts"]},
            {"Genesis", "MuJoCo", "SuperDex"},
        )
        self.assertEqual(newton["name"]["zh"], "Newton")

        cg = by_id["solver-cg"]
        self.assertEqual(
            {context["role"] for context in cg["contexts"]},
            {"constraint", "linear"},
        )
        self.assertEqual(cg["name"]["zh"], "CG")

        semi = by_id["solver-semiimplicit"]
        self.assertEqual(len(semi["contexts"]), 1)
        self.assertEqual(semi["name"]["zh"], "SemiImplicit")

        fp64 = by_id["solver-fp64"]
        self.assertEqual(fp64["name"]["zh"], "FP64")
        self.assertEqual([context["engine"] for context in fp64["contexts"]], ["SuperDex"])
        self.assertNotIn("SuperDex", fp64["name"]["zh"])

    def test_all_entries_are_bilingual_and_related_targets_exist(self):
        ids = {item["id"] for item in self.atlas["concepts"]}
        topic_ids = {topic["id"] for topic in self.atlas["topics"]}
        for item in self.atlas["concepts"]:
            fields = (
                ("name", "summary")
                if item["kind"] == "synthesis"
                else ("name", "summary", "body", "example", "confusions")
            )
            for field in fields:
                self.assertTrue(item[field]["zh"], (item["id"], field, "zh"))
                self.assertTrue(item[field]["en"], (item["id"], field, "en"))
            for relation in item["relations"]:
                self.assertIn(relation["target"], ids)
            if item["kind"] == "synthesis":
                date.fromisoformat(item["updated"])
                self.assertIn(item["topic"], topic_ids)

    def test_synthesis_titles_match_full_article_headings(self):
        for item in self.atlas["concepts"]:
            if item["kind"] != "synthesis":
                continue
            for language in ("zh", "en"):
                if item["href"].startswith("_static/") and language == "en":
                    continue
                if item["href"].startswith("_static/"):
                    path = self.root / "docs/site" / item["href"]
                    heading = re.search(
                        r"<h1[^>]*>(.*?)</h1>",
                        path.read_text(errors="ignore"),
                        re.S,
                    )
                    title = re.sub(r"<[^>]+>", " ", heading.group(1))
                else:
                    path = (
                        self.root
                        / "docs/site"
                        / language
                        / item["href"].replace(".html", ".md")
                    )
                    heading = re.search(r"^# (.+)$", path.read_text(), re.M)
                    title = heading.group(1)
                self.assertEqual(
                    re.sub(r"\s+", "", item["name"][language]),
                    re.sub(r"\s+", "", title),
                    (item["id"], language),
                )

    def test_dangling_or_self_relations_are_rejected(self):
        concepts = [
            {
                "id": "one",
                "relations": [{"type": "related", "target": "missing"}],
            }
        ]
        with self.assertRaisesRegex(ValueError, "missing concept"):
            _normalize_relations(concepts)
        concepts = [{"id": "one", "relations": [{"type": "related", "target": "one"}]}]
        with self.assertRaisesRegex(ValueError, "itself"):
            _normalize_relations(concepts)

    def test_dialog_reuses_the_full_source_and_exposes_relation_data(self):
        rendered = render_dialog(self.atlas, "zh")
        self.assertEqual(rendered.count('class="concept-term '), len(self.atlas["concepts"]))
        self.assertIn('data-concept="penetration"', rendered)
        self.assertIn('data-kind="synthesis"', rendered)
        self.assertIn('href="failure-root-cause-atlas.html"', rendered)
        self.assertIn('data-concept="solver-fp64"', rendered)
        self.assertIn('data-name="FP64"', rendered)
        self.assertNotIn("<small>SuperDex</small>", rendered)
        self.assertIn("data-relations=", rendered)
        syntheses = sum(item["kind"] == "synthesis" for item in self.atlas["concepts"])
        self.assertIn(
            f"{len(self.atlas['concepts']) - syntheses} 个概念 · {syntheses} 篇研究总论",
            rendered,
        )

    def test_concept_field_keeps_topics_in_separate_article_band(self):
        rendered = render_field(self.atlas, "zh")
        syntheses = sum(item["kind"] == "synthesis" for item in self.atlas["concepts"])
        self.assertEqual(
            rendered.count("data-concept-wall-item"),
            len(self.atlas["concepts"]) - syntheses,
        )
        self.assertNotIn('class="concept-field-synthesis"', rendered)
        self.assertEqual(rendered.count('class="concept-topic-link"'), syntheses)
        self.assertEqual(rendered.count("data-topic-filter="), len(self.atlas["topics"]) + 1)
        self.assertEqual(rendered.count('class="concept-topic-label"'), syntheses)
        self.assertEqual(rendered.count('<time datetime="'), syntheses)
        self.assertLess(
            rendered.index('class="concept-field"'),
            rendered.index('class="concept-topics"'),
        )
        rendered_dates = re.findall(r'<time datetime="([^"]+)">', rendered)
        self.assertEqual(rendered_dates, sorted(rendered_dates, reverse=True))
        self.assertLess(
            rendered.index("NeuralActuator：执行器误差要单独建模，接触仍要交给物理"),
            rendered.index("当我们在讨论灵巧操作仿真时，我们在讨论什么？"),
        )
        self.assertIn('data-topic="sim2real"', rendered)
        self.assertIn('href="failure-root-cause-atlas.html"', rendered)
        self.assertIn(
            "当我们在讨论仿真 Sim-to-Real Gap 问题时，我们在讨论什么？",
            rendered,
        )
        self.assertIn('data-concept-target="solver-fp64">FP64</span>', rendered)

    def test_generated_pages_keep_the_source_of_truth_and_fix_local_links(self):
        with tempfile.TemporaryDirectory() as directory:
            language_dir = Path(directory) / "zh"
            language_dir.mkdir()
            prepare_concept_pages(language_dir)
            page = (language_dir / "concepts/penetration.md").read_text()
            self.assertIn("# 穿模", page)
            self.assertIn("../failure-root-cause-atlas.md", page)
            self.assertNotIn("](failure-root-cause-atlas.html)", page)
            evidence = (language_dir / "concepts/evidence-boundary.md").read_text()
            self.assertIn("../failure-root-cause-atlas.md", evidence)
            self.assertNotIn("](sim-to-real-gap.md)", evidence)
            fp64 = (language_dir / "concepts/solver-fp64.md").read_text()
            self.assertIn("# FP64", fp64)
            self.assertIn("## 登记上下文", fp64)
            self.assertIn("**SuperDex**", fp64)
            self.assertNotIn("SuperDex · 进阶", fp64)
            self.assertTrue((language_dir / "concepts/index.md").exists())
            index = (language_dir / "concepts/index.md").read_text()
            self.assertIn("../failure-root-cause-atlas.md", index)
            self.assertNotIn("](failure-root-cause-atlas.html)", index)
            static_link = '<a href="../_static/research/dexterous-simulation.html">'
            self.assertIn(static_link, index)
            self.assertNotIn("dexterous-simulation.md", index)
            self.assertIn("FP64 <solver-fp64>", index)
            contact = (language_dir / "concepts/contact.md").read_text()
            self.assertIn(static_link, contact)
            self.assertNotIn("dexterous-simulation.md", contact)
            for item in self.atlas["concepts"]:
                if item["kind"] in {"concept", "solver"}:
                    self.assertIn(f"<{item['id']}>", index)
            self.assertEqual(
                len(list((language_dir / "concepts").glob("*.md"))),
                sum(
                    item["kind"] in {"concept", "solver"}
                    for item in self.atlas["concepts"]
                ) + 1,
            )
            self.assertFalse(
                (language_dir / "concepts/sim-to-real-gap.md").exists()
            )

    def test_user_vocabulary_and_energy_aliases_route_to_canonical_terms(self):
        data = self.atlas
        self.assertIn("energy-exchange", {item["id"] for item in data["concepts"]})
        energy = next(item for item in data["concepts"] if item["id"] == "energy-exchange")
        self.assertIn("能量传递", energy["aliases"]["zh"])
        self.assertIn("能力交换", energy["aliases"]["zh"])
        inertia = next(item for item in data["concepts"] if item["id"] == "inertia")
        self.assertNotIn("质量矩阵", inertia["aliases"]["zh"])


if __name__ == "__main__":
    unittest.main()
