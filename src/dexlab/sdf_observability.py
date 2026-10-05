"""Offline evidence checks for a fixed static SDF construction-path comparison."""
import numpy as np
from scipy.spatial.transform import Rotation

HALF_SIZE = np.array([.02, .015, .01])
TRANSLATION = np.array([.1, .2, .3])
ANGLE = .7


def reference_points():
    return np.array(np.meshgrid(*[np.linspace(-b*.9, b*.9, 9) for b in HALF_SIZE],
                               indexing='ij')).reshape(3, -1).T


def summarize(metadata, grid, queries):
    """Report discrepancies, without turning an arbitrary tolerance into accuracy.

    1e-12 comparisons qualify serialized FP64 coordinates/configuration only.
    Exact construction-path equality is reported separately from valid evidence.
    """
    local = np.asarray(queries['local'], dtype=float)
    world = np.asarray(queries['world'], dtype=float)
    automatic = np.asarray(queries['automatic'], dtype=float)
    precomputed = np.asarray(queries['precomputed'], dtype=float)
    dims, values = np.asarray(grid['dims']), np.asarray(grid['values'])
    if (local.shape != (729, 3) or world.shape != local.shape
            or automatic.shape != (729,) or precomputed.shape != (729,)
            or dims.shape != (3,) or not np.issubdtype(dims.dtype, np.integer)
            or (dims < 2).any() or values.size != int(np.prod(dims))):
        raise ValueError('Incomplete query cohort or grid dimensions')
    if not all(np.isfinite(x).all() for x in (local, world, automatic, precomputed, values)):
        raise ValueError('Nonfinite native evidence')
    from dexlab.contact_transfer import box_mesh_matches

    declaration = metadata.get('grid', {})
    lower = np.asarray(declaration.get('bounds_min', []), dtype=float)
    upper = np.asarray(declaration.get('bounds_max', []), dtype=float)
    if (lower.shape != (3,) or upper.shape != (3,)
            or not np.isfinite([lower, upper]).all()
            or not np.array_equal(declaration.get('dims'), dims)
            or declaration.get('values_shape') != list(values.shape)
            or (lower > -HALF_SIZE).any() or (upper < HALF_SIZE).any()
            or ((upper-lower)/(dims-1) > .002+1e-12).any()):
        raise ValueError('Grid declaration does not match the fixed geometry or spacing')
    vertices = np.asarray(grid.get('vertices', []))
    faces = np.asarray(grid.get('faces', []))
    if vertices.shape != (8, 3) or not box_mesh_matches(vertices/HALF_SIZE, faces, 1):
        raise ValueError('Input mesh does not match the declared closed box')
    rotation = Rotation.from_euler('z', ANGLE)
    if not np.allclose(local, reference_points(), rtol=0, atol=1e-12):
        raise ValueError('Changed or missing probe points')
    if not np.allclose(world, rotation.apply(local)+TRANSLATION, rtol=0, atol=1e-12):
        raise ValueError('Incorrect query coordinate frame')
    if metadata['actual_colliders'] != ['SDF', 'SDF'] or metadata['time_s'] != 0:
        raise ValueError('Wrong collider or nonstatic protocol')
    if metadata['requested_spacing_m'] != [.002]*3:
        raise ValueError('Changed requested grid spacing')
    poses = np.asarray(metadata['actual_poses'], dtype=float)
    if poses.shape != (2, 7) or not np.isfinite(poses).all():
        raise ValueError('Missing actual native transforms')
    for pose in poses:
        if (not np.allclose(pose[:3], TRANSLATION, rtol=0, atol=1e-12)
                or not np.isclose(np.linalg.norm(pose[3:]), 1, rtol=0, atol=1e-12)
                or not np.allclose(Rotation.from_quat(pose[3:]).as_matrix(), rotation.as_matrix(), rtol=0, atol=1e-12)):
            raise ValueError('Actual native pose differs from requested pose')
    q = np.abs(local)-HALF_SIZE
    analytic = np.linalg.norm(np.maximum(q, 0), axis=1)+np.minimum(q.max(axis=1), 0)
    return {
        'evidence_complete': True,
        'query_count': len(local), 'grid_value_count': int(values.size),
        'sampled_paths_exactly_equal': bool(np.array_equal(automatic, precomputed)),
        'maximum_pair_difference_m': float(np.max(np.abs(automatic-precomputed))),
        'maximum_analytic_difference_m': {
            'automatic': float(np.max(np.abs(automatic-analytic))),
            'precomputed': float(np.max(np.abs(precomputed-analytic))),
        },
        'scope': 'Static sampled SDF discrepancy; not hidden-grid identity, dynamics or hardware accuracy',
    }


def verify_directory(directory):
    """Recompute static evidence from immutable raw arrays; no native simulation."""
    import json
    from pathlib import Path
    from dexlab.physx_baseline import digest

    directory = Path(directory).resolve()
    metadata = json.loads((directory/'comparison.json').read_text())
    manifest = json.loads((directory/'manifest.json').read_text())
    required = {'comparison.json', 'baked-grid.npz', 'queries.npz'}
    sources = metadata.get('source_sha256', {})
    if not sources or metadata.get('source_unchanged') is not True:
        raise ValueError('Missing frozen-source evidence')
    if any(Path(name).is_absolute() or '..' in Path(name).parts for name in sources):
        raise ValueError('Invalid source path')
    required.update('source/'+name for name in sources)
    if not required <= manifest.keys():
        raise ValueError('Incomplete artifact manifest')
    for name, expected in manifest.items():
        relative = Path(name)
        if (relative.is_absolute() or '..' in relative.parts
                or not (directory/relative).resolve().is_relative_to(directory)
                or digest(directory/relative) != expected):
            raise ValueError('Changed or invalid artifact')
    if any(digest(directory/'source'/name) != expected for name,expected in sources.items()):
        raise ValueError('Frozen source hash mismatch')
    with np.load(directory/'baked-grid.npz', allow_pickle=False) as grid, np.load(directory/'queries.npz', allow_pickle=False) as queries:
        summary = summarize(metadata, grid, queries)
    if summary != metadata.get('independent_summary'):
        raise ValueError('Stored summary differs from independently recomputed result')
    return summary


if __name__ == '__main__':
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    args = parser.parse_args()
    print(json.dumps(verify_directory(args.directory), indent=2))
