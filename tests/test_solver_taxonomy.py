"""Protect role distinctions without importing or executing a physics engine."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.solver_taxonomy import classify_profiles, load_taxonomy, summarize_roles


def rows(engine, *names):
    return [{"engine": engine, "solver": name} for name in names]


class SolverTaxonomyTests(unittest.TestCase):
    def test_cg_role_depends_on_the_declared_engine(self):
        mj = classify_profiles("MuJoCo", rows("MuJoCo", "CG / elliptic / Euler"))
        sd = classify_profiles("SuperDex", rows("SuperDex", "Newton / CG / FP64"))
        self.assertEqual(mj["constraint"], ["CG (nonlinear)"])
        self.assertEqual(sd["nonlinear"], ["Newton"])
        self.assertEqual(sd["linear"], ["CG"])
        self.assertNotIn("linear", mj)

    def test_newton_and_gmres_are_not_peers(self):
        result = classify_profiles("SuperDex", rows("SuperDex", "NEWTON / GMRES / C1_REGULARIZED"))
        self.assertEqual(result["nonlinear"], ["Newton"])
        self.assertEqual(result["linear"], ["GMRES"])
        self.assertEqual(result["friction"], ["C1_REGULARIZED"])

    def test_mujoco_alternatives_remain_available(self):
        result = classify_profiles("MuJoCo", rows("MuJoCo", "PGS", "CG", "Newton"))
        self.assertEqual(result["constraint"], ["CG (nonlinear)", "Newton", "PGS"])

    def test_cloth_implementation_is_not_a_linear_solver(self):
        for engine, name in (("Genesis", "PBD / rigid coupling"), ("PhysX", "surface cloth"),
                             ("Newton Physics", "Style3D"), ("SuperDex", "experimental-shell")):
            with self.subTest(engine=engine):
                result = classify_profiles(engine, rows(engine, name))
                self.assertIn("deformable", result)
                self.assertNotIn("linear", result)
                self.assertNotIn("constraint", result)

    def test_drake_contact_approximation_is_separate(self):
        result = classify_profiles("Drake", rows("Drake", "SAP / kLagged / hydroelastic"))
        self.assertEqual(result["constraint"], ["SAP"])
        self.assertEqual(result["approximation"], ["kLagged"])
        self.assertEqual(result["contact"], ["hydroelastic"])

    def test_auto_does_not_infer_an_executed_branch(self):
        result = classify_profiles("SuperDex", rows("SuperDex", "Newton / AUTO"))
        self.assertIn("linear_selection", result)
        self.assertNotIn("linear", result)

    def test_unknown_and_historical_names_stay_visible(self):
        data = rows("PhysX", "historical readback incomplete (#126)", "unknown-new-option")
        result = classify_profiles("PhysX", data)
        self.assertEqual(len(result["unresolved"]), 2)
        self.assertIn("#126", summarize_roles("PhysX", data, "zh"))

    def test_does_not_mutate_status_counts_or_evidence(self):
        data = rows("SuperDex", "NEWTON / CUDA_CG / C1_REGULARIZED")
        data[0]["cells"] = {"incline": {"state": "unsupported", "count": 0, "hash": "preserve"}}
        before = copy.deepcopy(data)
        self.assertIn("CUDA_CG", summarize_roles("SuperDex", data))
        self.assertEqual(data, before)

    def test_mjwarp_remains_in_its_separate_path_table(self):
        result = classify_profiles("MuJoCo", rows("MuJoCo", "MJWarp Newton / pyramidal / Newton contacts"))
        self.assertEqual(result, {})

    def test_aliases_and_order_are_deterministic(self):
        data = rows("Newton Physics", "xpbd", "XPBD", "semi_implicit", "SemiImplicit")
        self.assertEqual(classify_profiles("Newton Physics", data)["implementation"], ["SemiImplicit", "XPBD"])
        self.assertEqual(summarize_roles("Newton Physics", data), summarize_roles("Newton Physics", reversed(data)))

    def test_bilingual_roles_and_html_escaping(self):
        data = rows("MuJoCo", "<unknown|value>")
        for language in ("en", "zh"):
            result = summarize_roles("MuJoCo", data, language)
            self.assertIn("&lt;unknown&#124;value&gt;", result)
            self.assertNotIn("<unknown", result)
        self.assertIn("约束求解", summarize_roles("MuJoCo", rows("MuJoCo", "PGS"), "zh"))

    def test_missing_and_mixed_labels_are_rejected(self):
        for data in ([{"solver": ""}], rows("Genesis", "CG"), rows("MuJoCo", "Newton /")):
            with self.assertRaises(ValueError):
                classify_profiles("MuJoCo", data)
        with self.assertRaises(ValueError):
            summarize_roles("MuJoCo", rows("MuJoCo", "PGS"), "xx")

    def test_catalogue_has_sources_and_rejects_unknown_roles(self):
        data = load_taxonomy()
        self.assertEqual(len(data["engines"]), 6)
        for item in data["engines"].values():
            self.assertTrue(item["sources"])
        data["engines"]["MuJoCo"]["tokens"]["cg"][0] = "invented-role"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "taxonomy.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "Invalid role mapping"):
                load_taxonomy(path)


if __name__ == "__main__":
    unittest.main()
