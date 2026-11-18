"""Concept atlas source and generated-page regression tests."""

import tempfile
import unittest
from pathlib import Path

from scripts.concept_atlas import (
    _normalize_relations,
    load_atlas,
    prepare_concept_pages,
    render_dialog,
    render_field,
)


class ConceptAtlasTests(unittest.TestCase):
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
        for item in self.atlas["concepts"]:
            for field in ("name", "summary", "body", "example", "confusions"):
                self.assertTrue(item[field]["zh"], (item["id"], field, "zh"))
                self.assertTrue(item[field]["en"], (item["id"], field, "en"))
            for relation in item["relations"]:
                self.assertIn(relation["target"], ids)

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
        self.assertIn('data-concept="solver-fp64"', rendered)
        self.assertIn('data-name="FP64"', rendered)
        self.assertNotIn("<small>SuperDex</small>", rendered)
        self.assertIn("data-relations=", rendered)
        self.assertIn(f"{len(self.atlas['concepts'])} 个词条", rendered)

    def test_concept_field_words_open_their_matching_atlas_entry(self):
        rendered = render_field(self.atlas, "zh")
        self.assertEqual(rendered.count("data-concept-open"), len(self.atlas["concepts"]))
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
            fp64 = (language_dir / "concepts/solver-fp64.md").read_text()
            self.assertIn("# FP64", fp64)
            self.assertIn("## 登记上下文", fp64)
            self.assertIn("**SuperDex**", fp64)
            self.assertNotIn("SuperDex · 进阶", fp64)
            self.assertTrue((language_dir / "concepts/index.md").exists())
            self.assertEqual(
                len(list((language_dir / "concepts").glob("*.md"))),
                len(self.atlas["concepts"]) + 1,
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
