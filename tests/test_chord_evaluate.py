"""The VOC-off contract must hold before the first native physics step."""

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

import torch

HERE = Path(__file__).resolve().parents[1] / "demos/chord"
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("chord_evaluate", HERE / "evaluate.py")
evaluate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluate)
sys.path.pop(0)


class InitialAssistanceTests(unittest.TestCase):
    def command(self, target=0.0, decay=0):
        return SimpleNamespace(
            cfg=SimpleNamespace(initial_virtual_object_control_curriculum_scale=target,
                                virtual_object_control_decay_steps=decay),
            virtual_object_controller_scale_factor=torch.tensor([target]),
            virtual_object_controller_scale_factor_per_env=torch.ones(2, 1),
        )

    def test_upstream_reset_is_corrected_without_advancing_a_simulator(self):
        command = self.command()
        self.assertEqual(evaluate.disable_initial_reset_assistance(command), [[1.0], [1.0]])
        self.assertEqual(command.virtual_object_controller_scale_factor_per_env.tolist(), [[0.0], [0.0]])

    def test_an_assisted_configuration_is_rejected_before_mutation(self):
        for command in (self.command(target=0.5), self.command(decay=1)):
            with self.assertRaisesRegex(ValueError, "zero VOC target"):
                evaluate.disable_initial_reset_assistance(command)
            self.assertEqual(command.virtual_object_controller_scale_factor_per_env.tolist(), [[1.0], [1.0]])


if __name__ == "__main__":
    unittest.main()
