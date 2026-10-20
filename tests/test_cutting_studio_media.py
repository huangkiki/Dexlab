"""The polished view must keep the independently checked measurements and frames."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

try:
    from PIL import Image
except ModuleNotFoundError as error:
    raise unittest.SkipTest('Install cutting render dependencies') from error

SPEC = importlib.util.spec_from_file_location(
    'cut_push_media', Path(__file__).resolve().parents[1] / 'demos/cut-push/verify_media.py')
media = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(media)


class StudioMediaIntegrity(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        gif = self.root / 'surface-rtx.gif'
        Image.new('RGB', (4, 4), 'red').save(
            gif, save_all=True, append_images=[Image.new('RGB', (4, 4), 'blue')],
            duration=120, loop=0)
        self.manifest = {'artifacts': {'states.npz': 'retained', 'trace.npz': 'retained'}}
        self.measured = {'frames': [
            {'state_frame': index * 5, 'time_s': index * .05,
             'knife_on_material_n': [0., 0., 0.], 'knife_material_force_n': 0.,
             'centroid_x_from_start_mm': [0., index * .1], 'dynamic_viscosity_pa_s': 0.}
            for index in range(2)]}
        self.receipt = {
            'source_artifacts': self.manifest['artifacts'], 'physics_steps': 0, 'fps': 20,
            'frames': [{'frame': index, 'sample': row['state_frame'], 'time_s': row['time_s'],
                        'metrics': json.loads(json.dumps(row))}
                       for index, row in enumerate(self.measured['frames'])],
            'assets': {gif.name: hashlib.sha256(gif.read_bytes()).hexdigest()}}

    def check_receipt(self):
        (self.root / 'studio-provenance.json').write_text(json.dumps(self.receipt))
        return media.verify_studio(self.root, self.manifest, self.measured)

    def test_complete_unchanged_derivative_passes(self):
        self.assertEqual(self.check_receipt()['frames_verified'], 2)

    def test_changed_force_is_rejected(self):
        self.receipt['frames'][1]['metrics']['knife_on_material_n'][0] = .01
        with self.assertRaises(AssertionError):
            self.check_receipt()

    def test_missing_frame_is_rejected(self):
        self.receipt['frames'].pop()
        with self.assertRaisesRegex(ValueError, 'frame schedule'):
            self.check_receipt()

    def test_changed_native_sample_is_rejected(self):
        self.receipt['frames'][1]['sample'] = 6
        with self.assertRaisesRegex(ValueError, 'frame mapping'):
            self.check_receipt()

    def test_replaced_gif_is_rejected(self):
        Image.new('RGB', (4, 4), 'green').save(self.root / 'surface-rtx.gif')
        with self.assertRaisesRegex(ValueError, 'artifact changed'):
            self.check_receipt()
