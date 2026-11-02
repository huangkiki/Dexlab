"""A checkpoint receipt must distinguish a real update from model-only weights."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "chord_checkpoint", Path(__file__).resolve().parents[1] / "demos/chord/checkpoint.py")
checkpoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkpoint)


class ChordCheckpointTests(unittest.TestCase):
    def test_real_cpu_update_and_scalar_buffers_survive_inspection(self):
        import torch
        model = torch.nn.Linear(2, 1)
        with torch.no_grad():
            model.weight.fill_(0.5)
            model.bias.zero_()
        model.register_buffer("sample_count", torch.tensor(1))
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.pt"
            def save():
                torch.save({"model_state_dict": model.state_dict(),
                            "optimizer_state_dict": optimizer.state_dict(), "iter": 0}, path)
            save()
            with self.assertRaisesRegex(ValueError, "update state"):
                checkpoint.inspect(path)
            model(torch.ones(1, 2)).square().sum().backward()
            optimizer.step()
            save()
            result = checkpoint.inspect(path)
            self.assertEqual(result["optimizer_step_min"], 1)
            self.assertGreater(result["nonzero_moment_elements"], 0)
            self.assertEqual(result["native_reload"], "requires_separate_evaluation")


if __name__ == "__main__":
    unittest.main()
