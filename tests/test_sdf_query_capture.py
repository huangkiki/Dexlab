"""API-shaped test doubles verify ordering/failures, never native provenance."""
import itertools
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import numpy as np

from dexlab.sdf_query_capture import capture_box_queries, EXPECTED_ROTATION_XYZW
from dexlab.sdf_near_surface import HALF_SIZE, TRANSLATION, box_reference, query_cohort


class SyntheticActor:
    def __init__(self, output):
        self.output = output
        self.name = "synthetic-ordering-fixture"
        self.collider = "SDF"
        self.has_root = True
        self.translation = TRANSLATION.copy()
        self.rotation = EXPECTED_ROTATION_XYZW.copy()
        self.bounds = np.array([-HALF_SIZE, HALF_SIZE])
        # Closed outward box mesh; this object is still a test double, not native.
        self.vertices = np.array(list(itertools.product((-1., 1.), repeat=3))) * HALF_SIZE
        self.faces = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5],
                               [0, 4, 5], [0, 5, 1], [2, 3, 7], [2, 7, 6],
                               [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]], dtype=np.int32)
        self.calls = 0
        self.effect = None

    def get_name(self): return self.name
    def get_collider_type(self): return SimpleNamespace(name=self.collider)
    def has_root_transform(self): return self.has_root
    def get_root_transform(self):
        return SimpleNamespace(translation=self.translation, rotation=self.rotation)
    def get_aabb_local(self):
        return SimpleNamespace(min=self.bounds[0], max=self.bounds[1])
    def get_mesh(self):
        return SimpleNamespace(coordinates=self.vertices.ravel(),
                               connectivity=self.faces.ravel(), nodes_per_element=3)

    def get_points_distance_to_surface(self, points, distances):
        self.calls += 1
        assert (self.output / "before-manifest.json").is_file()
        before = np.load(self.output / "before.npz", allow_pickle=False)
        np.testing.assert_array_equal(points, before["world_m"])
        assert int(before["interior_mask"].sum()) == 2214
        assert int(before["boundary_mask"].sum()) == 702
        distances[:] = box_reference(query_cohort()["local_m"])[0]
        if self.effect:
            self.effect(distances)


class CaptureOrderingTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "capture"
        self.actor = SyntheticActor(self.output)
        self.vertices = self.actor.vertices.copy()
        self.faces = self.actor.faces.copy()

    def capture(self):
        return capture_box_queries(self.actor, self.output,
            expected_name="synthetic-ordering-fixture",
            vertices_m=self.vertices, faces=self.faces)

    def test_before_query_artifacts_and_complete_denominators(self):
        report = self.capture()
        self.assertEqual(self.actor.calls, 1)
        self.assertEqual(report["expected_query_count"], 5130)
        self.assertEqual(len(report["unsupported_query_indices"]), 2916)
        self.assertEqual(report, json.loads((self.output / "score.json").read_text()))
        self.assertFalse((self.output / "capture-failure.json").exists())

    def test_wrong_actor_source_pose_or_bounds_stops_before_query(self):
        changes = [
            ("name", "different-actor"), ("collider", "CONVEX"), ("has_root", False),
            ("translation", TRANSLATION + [0, 0, .001]),
            ("rotation", np.array([0, 0, 0, 1.])),
            ("bounds", np.array([-HALF_SIZE, HALF_SIZE / 2])),
            ("vertices", self.vertices * 2), ("faces", self.faces[:, ::-1]),
        ]
        for index, (key, value) in enumerate(changes):
            with self.subTest(key=key):
                self.output = Path(self.temp.name) / str(index)
                self.actor = SyntheticActor(self.output)
                setattr(self.actor, key, value)
                with self.assertRaises(ValueError): self.capture()
                self.assertEqual(self.actor.calls, 0)
                self.assertFalse((self.output / "distances.npz").exists())
                self.assertEqual(json.loads((self.output / "capture-failure.json").read_text())["stage"],
                                 "identity-before-query")

    def test_changed_pose_after_query_keeps_distances_but_has_no_score(self):
        self.actor.effect = lambda _: self.actor.translation.__setitem__(0, .123)
        with self.assertRaisesRegex(ValueError, "identity changed"): self.capture()
        self.assertTrue((self.output / "distances.npz").is_file())
        self.assertTrue((self.output / "after.json").is_file())
        self.assertFalse((self.output / "score.json").exists())

    def test_invalid_source_is_rejected_even_when_actor_matches_it(self):
        for variant in ("open", "inward", "scaled"):
            with self.subTest(variant=variant):
                self.output = Path(self.temp.name) / variant
                self.actor = SyntheticActor(self.output)
                if variant == "open": self.actor.faces = self.actor.faces[:-1]
                if variant == "inward": self.actor.faces = self.actor.faces[:, ::-1]
                if variant == "scaled": self.actor.vertices *= 2
                self.vertices, self.faces = self.actor.vertices.copy(), self.actor.faces.copy()
                with self.assertRaisesRegex(ValueError, "Source must"): self.capture()
                self.assertEqual(self.actor.calls, 0)
                self.assertEqual(json.loads((self.output / "capture-failure.json").read_text())["stage"],
                                 "source-geometry")

    def test_unwritten_or_nonfinite_distances_are_retained_and_rejected(self):
        self.actor.effect = lambda values: values.__setitem__(12, np.nan)
        with self.assertRaisesRegex(ValueError, "nonfinite"): self.capture()
        with np.load(self.output / "distances.npz", allow_pickle=False) as saved:
            self.assertTrue(np.isnan(saved["distances_m"][12]))
        self.assertFalse((self.output / "score.json").exists())

    def test_native_call_failure_preserves_partial_output(self):
        def fail(values):
            values[17:] = np.nan
            raise RuntimeError("synthetic interruption")
        self.actor.effect = fail
        with self.assertRaisesRegex(RuntimeError, "synthetic interruption"): self.capture()
        with np.load(self.output / "distances.npz", allow_pickle=False) as saved:
            self.assertTrue(np.isfinite(saved["distances_m"][:17]).all())
            self.assertTrue(np.isnan(saved["distances_m"][17:]).all())
        failure = json.loads((self.output / "capture-failure.json").read_text())
        self.assertEqual(failure["stage"], "distance-query")

    def test_changed_pre_query_artifact_is_detected(self):
        for name in ("before.json", "before-manifest.json"):
            with self.subTest(name=name):
                self.output = Path(self.temp.name) / name.removesuffix(".json")
                self.actor = SyntheticActor(self.output)
                self.actor.effect = lambda _: (self.output / name).write_text("{}\n")
                with self.assertRaisesRegex(ValueError, "artifact changed"): self.capture()
                self.assertFalse((self.output / "score.json").exists())

    def test_reusing_an_output_is_rejected_without_overwriting(self):
        self.output.mkdir()
        marker = self.output / "capture-failure.json"
        marker.write_text("existing evidence\n")
        with self.assertRaises(FileExistsError): self.capture()
        self.assertEqual(marker.read_text(), "existing evidence\n")
        self.assertEqual(self.actor.calls, 0)


if __name__ == "__main__":
    unittest.main()
