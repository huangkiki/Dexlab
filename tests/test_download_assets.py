"""Exercise installation, cache recovery, integrity checks and safe extraction."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('download_assets', Path(__file__).resolve().parents[1] / 'scripts/download_assets.py')
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


class AssetInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'installed'
        self.cache = self.base / 'cache'
        self.archive = self.base / 'assets.tar.xz'
        self.manifest = self.base / 'assets.json'
        self.texture = self.base / 'texture.png'
        self.texture.write_bytes(b'texture')
        self.write_archive('robot/model.obj')

    def write_archive(self, name):
        with tarfile.open(self.archive, 'w:xz') as tar:
            member = tarfile.TarInfo(name)
            member.size = 4
            tar.addfile(member, io.BytesIO(b'mesh'))
        self.data = {'version': 1, 'archives': [{
            'url': self.archive.as_uri(), 'sha256': assets.sha256(self.archive),
            'files': {name: hashlib.sha256(b'mesh').hexdigest()},
        }], 'files': [{
            'path': 'apple/texture.png', 'url': self.texture.as_uri(),
            'sha256': assets.sha256(self.texture),
        }]}
        self.manifest.write_text(json.dumps(self.data))

    def install(self):
        assets.install(self.manifest, self.root, self.cache)

    def test_install_reuse_and_restore_missing_file_offline(self):
        self.install()
        self.archive.unlink()
        self.texture.unlink()
        self.install()
        (self.root / 'robot/model.obj').unlink()
        self.install()
        self.assertEqual((self.root / 'robot/model.obj').read_bytes(), b'mesh')

    def test_modified_asset_is_preserved(self):
        self.install()
        target = self.root / 'robot/model.obj'
        target.write_bytes(b'user edit')
        with self.assertRaisesRegex(ValueError, 'Modified asset'):
            self.install()
        self.assertEqual(target.read_bytes(), b'user edit')

    def test_bad_download_does_not_install(self):
        self.archive.write_bytes(b'truncated')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            self.install()
        self.assertFalse((self.root / 'robot/model.obj').exists())

    def test_bad_member_hash_does_not_install(self):
        self.data['archives'][0]['files']['robot/model.obj'] = '0' * 64
        self.manifest.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, 'Asset checksum mismatch'):
            self.install()
        self.assertFalse((self.root / 'robot/model.obj').exists())

    def test_traversal_rejected(self):
        self.write_archive('../escape')
        with self.assertRaisesRegex(ValueError, 'Unsafe asset path'):
            self.install()
        self.assertFalse((self.base / 'escape').exists())

    def test_symlink_destination_rejected(self):
        self.root.mkdir()
        (self.root / 'robot').symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'escapes destination'):
            self.install()


if __name__ == '__main__':
    unittest.main()
