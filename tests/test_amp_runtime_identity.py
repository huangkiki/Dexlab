"""Native admission binds installed code to an archive, not optional URL metadata."""

import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ENTRY = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'demos/amp-box-lift/run.py'))


class AmpRuntimeIdentityTests(unittest.TestCase):
    def test_official_bytes_qualify_without_installer_archive_hash_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            wheel = Path(tmp) / 'mujoco_warp-3.8.0.3-py3-none-any.whl'
            code = b'VERSION = "fixture"\n'
            with zipfile.ZipFile(wheel, 'w') as archive:
                archive.writestr('mujoco_warp/__init__.py', code)
                archive.writestr('mujoco_warp-3.8.0.3.dist-info/METADATA',
                                 'Name: mujoco-warp\nVersion: 3.8.0.3\n')
            code_hash = hashlib.sha256(json.dumps({
                'mujoco_warp/__init__.py': hashlib.sha256(code).hexdigest()}, sort_keys=True).encode()).hexdigest()
            protocol = {'runtime': {'mujoco-warp': '3.8.0.3'}, 'dependency_sources': {},
                        'runtime_revision': {'wheel_sha256': hashlib.sha256(wheel.read_bytes()).hexdigest()}}
            with patch('importlib.metadata.version', return_value='3.8.0.3'), \
                 patch('importlib.metadata.distributions', return_value=[]), \
                 patch('dexlab.cloth_engines.package_identity', return_value={'code_sha256': code_hash}), \
                 patch('importlib.metadata.distribution', side_effect=AssertionError('Do not require PEP 610 hash')):
                result = ENTRY['runtime_identity'](protocol, wheel)
                self.assertEqual(result['mujoco_warp_wheel']['code_files'], 1)
                wheel.write_bytes(wheel.read_bytes() + b'changed')
                with self.assertRaisesRegex(ValueError, 'official distribution SHA256'):
                    ENTRY['runtime_identity'](protocol, wheel)

    def test_resolver_version_drift_stops_before_native_admission(self):
        protocol = {'runtime': {'mujoco': '3.10.0'}}
        with patch('importlib.metadata.version', return_value='3.17.0'):
            with self.assertRaisesRegex(ValueError, 'versions differ'):
                ENTRY['runtime_identity'](protocol, Path('unused.whl'))


if __name__ == '__main__':
    unittest.main()
