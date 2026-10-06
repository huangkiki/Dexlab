"""The experimental cone choice must reach the actual compiled native model."""

import tempfile
import unittest
from pathlib import Path

from dexlab.contact_plane import PlaneCase
from dexlab.contact_plane_native import MuJoCoPlane


class ConeSettingsTests(unittest.TestCase):
    def test_cone_is_compiled_and_archived_without_other_xml_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            texts = []
            for cone, expected in (("elliptic", 1), ("pyramidal", 0)):
                output = root / cone
                output.mkdir()
                native = MuJoCoPlane(PlaneCase(), output, friction_cone=cone)
                try:
                    self.assertEqual(int(native.model.opt.cone), expected)
                    self.assertEqual(native.metadata["solver"]["cone"], expected)
                    texts.append((output / "model.xml").read_text())
                finally:
                    native.close()
            self.assertEqual(
                texts[0], texts[1].replace('cone="pyramidal"', 'cone="elliptic"')
            )

    def test_default_stays_elliptic_and_invalid_cone_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            native = MuJoCoPlane(PlaneCase(), output)
            try:
                self.assertEqual(int(native.model.opt.cone), 1)
            finally:
                native.close()
            for value in (None, "", "ELLIPTIC", "other", 0):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    MuJoCoPlane(PlaneCase(), output, friction_cone=value)
