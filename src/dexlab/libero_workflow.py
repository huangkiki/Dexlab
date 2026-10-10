"""LIBERO-specific source/observation utilities; never changes task physics."""
from pathlib import Path
import hashlib
import xml.etree.ElementTree as ET

TASK = 'pick_up_the_cream_cheese_and_place_it_in_the_basket'
UPSTREAM = '8f1084e3132a39270c3a13ebe37270a43ece2a01'


def file_hash(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def relocate_assets(xml, libero_root, robosuite_root):
    """Only relocate existing asset filenames; retain every physical attribute."""
    tree = ET.fromstring(xml)
    changes = []
    for element in tree.findall('./asset/*'):
        original = element.get('file')
        if original is None:
            continue
        parts = Path(original).parts
        if 'robosuite' in parts:
            index = max(i for i, part in enumerate(parts) if part == 'robosuite')
            root, relative = Path(robosuite_root), Path(*parts[index + 1:])
            provider = 'robosuite'
        elif 'assets' in parts and any('libero' in p.lower() for p in parts):
            index = max(i for i, part in enumerate(parts) if part == 'assets')
            root, relative = Path(libero_root) / 'libero/libero/assets', Path(*parts[index + 1:])
            provider = 'libero'
        else:
            raise ValueError(f'Unrecognized asset provenance: {element.tag}/{element.get("name")}')
        resolved = (root / relative).resolve(strict=True)
        if not resolved.is_relative_to(root.resolve()):
            raise ValueError('Asset escapes its official source root')
        element.set('file', str(resolved))
        changes.append({'provider': provider, 'path': str(relative), 'sha256': file_hash(resolved)})
    return ET.tostring(tree, encoding='unicode'), changes


def settle_observation(env, initial_observation, *, steps=5):
    """Return the final native observation, matching LIBERO's metric.py path."""
    import numpy as np
    observation = initial_observation
    for _ in range(steps):
        observation, _, _, _ = env.step(np.zeros(env.action_dim))
    return observation


def observation_difference(stale, fresh):
    import numpy as np
    result = {}
    if set(stale) != set(fresh):
        raise ValueError('Observation channels changed during settling')
    for key in stale:
        a, b = np.asarray(stale[key]), np.asarray(fresh[key])
        if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError(f'Invalid observation channel: {key}')
        result[key] = float(np.max(np.abs(a.astype(float) - b.astype(float)))) if a.size else 0.
    return result
