"""A failed native fixture reports its receipt once, before data-dependent tests."""

import io
import json
import unittest
from unittest.mock import patch

import numpy as np

import test_contact_indent
import test_contact_load
import test_contact_pinch


class NativeFixtureFailureTests(unittest.TestCase):
    def test_initialization_error_prevents_empty_record_cascade(self):
        original_error = "ValueError: historical-3.11.0 requires matching package and native MuJoCo 3.11.0"

        def failed_run(case, engine, output, **kwargs):
            output.mkdir()
            (output / "run.json").write_text(json.dumps({"status": "error", "error": original_error}))
            np.savez(output / "states.npz", time=np.array([]))
            return {"passed": False, "checks": {}, "metrics": {}}

        for module, case in (
            (test_contact_indent, test_contact_indent.IndentationTests),
            (test_contact_load, test_contact_load.NormalResponseTests),
            (test_contact_pinch, test_contact_pinch.CylinderEvidenceTests),
        ):
            with self.subTest(case=case.__name__), patch.object(module, "run", side_effect=failed_run):
                isolated = type("FailedFixture", (case,), {})
                suite = unittest.defaultTestLoader.loadTestsFromTestCase(isolated)
                result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
                self.assertEqual(result.testsRun, 0)
                self.assertEqual(len(result.errors), 1)
                self.assertIn(original_error, result.errors[0][1])
                self.assertFalse(result.failures)
