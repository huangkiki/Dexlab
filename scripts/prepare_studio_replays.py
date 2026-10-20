"""Read existing DexLab recordings for studio playback; no new physics cohort."""
import argparse
import gzip
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from render_studio_replay import render

ROOT = Path(__file__).resolve().parents[1]


def camera(distance, azimuth, elevation):
    import mujoco
    result = mujoco.MjvCamera()
    result.distance, result.azimuth, result.elevation = distance, azimuth, elevation
    return result


def model_sources(path):
    """Hash the consumed XML and every referenced mesh/texture asset."""
    path = Path(path)
    root = ET.parse(path).getroot()
    compiler = root.find('compiler')
    sources = [path]
    for node in root.findall('./asset/*'):
        if 'file' not in node.attrib:
            continue
        asset = Path(node.attrib['file'])
        if not asset.is_absolute():
            folder = compiler.get('meshdir' if node.tag == 'mesh' else 'texturedir', '') if compiler is not None else ''
            asset = path.parent / folder / asset
        sources.append(asset.resolve(strict=True))
    return sources


def apple(directory, output, pilot):
    import mujoco
    directory = Path(directory)
    with np.load(directory / 'trajectory.npz', allow_pickle=False) as record:
        frames, names, dt = record['frames'], record['names'].tolist(), float(record['dt'])
    model = mujoco.MjModel.from_xml_path(str(directory / 'display.xml'))
    expected = ['native_' + name for name in names]
    actual = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
              for i in np.argsort(model.body_mocapid) if model.body_mocapid[i] >= 0]
    if expected != actual:
        raise ValueError('Actor order differs from the saved display model')
    engine = json.loads((directory / 'engine.json').read_text())
    summary = json.loads((directory / 'summary.json').read_text())
    if not summary['passed'] or not engine['completed']:
        raise ValueError('Expected a fully verified apple recording')
    targets = frames[:, names.index('apple'), :3] + [0, 0, .035]
    states = {'mocap_pos': frames[:, :, :3], 'mocap_quat': frames[:, :, [6, 3, 4, 5]]}
    sources = [directory / p for p in ('trajectory.npz', 'display.xml', 'engine.json', 'summary.json')]
    sources += model_sources(directory / 'display.xml')[1:]
    return render(model, states, np.arange(len(frames)) * dt, camera(.24, 315, -8), targets, output,
                  sources=sources, label=engine['backend'] + ' ' + engine['version'] + ' | apple', fps=20, pilot=pilot)


def pinch(case, output, pilot):
    import mujoco
    from export_visual_research import load_pinch
    specs = json.loads((ROOT / 'docs/evidence/visual/sources.json').read_text())
    variant = next(v for v in specs['variants'] if v['id'] == 'pinch-retention')
    entry = next(e for e in variant['entries'] if e['id'] == case)
    load_pinch(entry, {})  # Verify the immutable published score before replay.
    directory = ROOT / entry['record']
    path = directory / 'pinch-0.json.gz'
    with gzip.open(path, 'rt') as stream:
        record = json.load(stream)
    rows = record['samples']
    root = ET.parse(directory / 'gripper.xml').getroot()
    world = root.find('worldbody')
    ET.SubElement(world, 'geom', type='plane', size='2 2 .01', rgba='.80 .82 .84 1')
    body = ET.SubElement(world, 'body', name='recorded_cube')
    ET.SubElement(body, 'freejoint')
    ET.SubElement(body, 'geom', type='box', size='.02 .02 .02', rgba='.95 .55 .15 1')
    for geom in world.findall('.//body[@name="left"]/geom') + world.findall('.//body[@name="right"]/geom'):
        geom.set('rgba', '.25 .65 .85 1')
    model = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding='unicode'))
    states = {'qpos': np.array([r['q'] + r['object_pos'] + r['object_quat'] for r in rows])}
    times = np.array([r['time'] for r in rows])
    return render(model, states, times, camera(.32, 90, -20), np.tile([0, 0, .065], (len(times), 1)), output,
                  sources=[path, directory / 'gripper.xml', ROOT / entry['score']], label='Genesis 1.4.3 | ' + case, pilot=pilot)


def primitive(kind, input_map, output, pilot):
    import mujoco
    from export_visual_research import load_incline, load_normal
    from visual_research import COLORS
    mappings = json.loads(Path(input_map).read_text())
    specs = json.loads((ROOT / 'docs/evidence/visual/sources.json').read_text())
    variant = next(v for v in specs['variants'] if v['id'] == {'incline': 'incline-sliding-0.001', 'normal': 'normal-calibration'}[kind])
    results = []
    for entry in variant['entries']:
        series, poses = {'incline': load_incline, 'normal': load_normal}[kind](entry, mappings)
        color = COLORS[entry['engine']]
        rgb = ' '.join(str(int(color[i:i+2], 16) / 255) for i in (1, 3, 5))
        angle = np.deg2rad(poses['angle']) / 2
        xml = f'<mujoco><worldbody><geom type="plane" size="8 8 .01" quat="{np.cos(angle)} 0 {np.sin(angle)} 0" rgba=".8 .82 .84 1"/><body><freejoint/><geom type="box" size=".02 .02 .02" rgba="{rgb} 1"/></body></worldbody></mujoco>'
        model = mujoco.MjModel.from_xml_string(xml)
        qpos = poses['pose'].copy()
        norms = np.linalg.norm(qpos[:, 3:], axis=1)
        if np.any(abs(norms - 1) > .001):
            raise ValueError('Non-unit recorded orientation')
        qpos[:, 3:] /= norms[:, None]  # Same explicitly declared display normalization as historical renderer.
        sources = [ROOT / 'docs/evidence/visual/sources.json', ROOT / entry['score']]
        if kind == 'incline':
            directory = Path(mappings[entry['source_id']]) / entry['record']
            sources.extend(directory / s['path'].split('/')[-1] for s in series['sources'] if not s['repository'])
        # load_normal already verifies both member hashes against the published receipt.
        targets = qpos[:, :3].copy()
        result = render(model, {'qpos': qpos}, poses['times'], camera(.22, 90, -25), targets,
                        Path(output) / entry['id'], sources=sources, label=entry['engine'] + ' | ' + entry['id'], pilot=pilot)
        result['historical_sources'] = series['sources']
        result['orientation_normalization_max_correction'] = float(np.max(abs(qpos - poses['pose'])))
        (Path(output) / entry['id'] / 'provenance.json').write_text(json.dumps(result, indent=2) + '\n')
        results.append(result)
    return results


def libero(directory, reference, output, pilot):
    import mujoco
    from render_studio_replay import digest
    directory, reference = Path(directory), Path(reference)
    manifest = json.loads(reference.with_suffix('.json').read_text())
    if manifest['native_version'] != '2.3.7' or digest(reference) != manifest['reference_sha256']:
        raise ValueError('Invalid native geometry reference')
    for name, expected in manifest['sources'].items():
        if digest(directory / name) != expected:
            raise ValueError('LIBERO source differs from native reference')
    model = mujoco.MjModel.from_xml_path(str(directory / 'effective-model.xml'))
    with np.load(directory / 'trajectory.npz', allow_pickle=False) as archive:
        recording = np.vstack((archive['initial'], archive['state']))
    with np.load(reference, allow_pickle=False) as archive:
        native = {key: archive[key] for key in archive.files}
    np.testing.assert_array_equal(native['times'], recording[:, 0])
    np.testing.assert_array_equal(native['geom_type'], model.geom_type)
    data = mujoco.MjData(model)
    max_error = 0.
    for frame, row in enumerate(recording):
        data.qpos[:] = row[1:1 + model.nq]
        mujoco.mj_fwdPosition(model, data)
        for geom in range(model.ngeom):
            old_rotation = native['rotations'][frame, geom].reshape(3, 3)
            new_rotation = data.geom_xmat[geom].reshape(3, 3)
            if model.geom_type[geom] == mujoco.mjtGeom.mjGEOM_MESH:
                old_id, new_id = native['geom_dataid'][geom], model.geom_dataid[geom]
                old_start, count = native['mesh_vertadr'][old_id], native['mesh_vertnum'][old_id]
                new_start = model.mesh_vertadr[new_id]
                if count != model.mesh_vertnum[new_id]:
                    raise ValueError('Mesh vertex count changed across runtimes')
                old_vertices = native['mesh_vert'][old_start:old_start + count]
                new_vertices = model.mesh_vert[new_start:new_start + count]
            else:
                np.testing.assert_allclose(native['geom_size'][geom], model.geom_size[geom], rtol=0, atol=1e-10)
                old_vertices = new_vertices = np.vstack((np.zeros(3), np.diag(model.geom_size[geom])))
            old_world = old_vertices @ old_rotation.T + native['positions'][frame, geom]
            new_world = new_vertices @ new_rotation.T + data.geom_xpos[geom]
            error = float(np.max(abs(old_world - new_world)))
            max_error = max(max_error, error)
            if error > 1e-5:
                raise ValueError(f'Native geometry changed at frame {frame}, geom {geom}: {error} m')
    # Hide the documented robosuite collision group, leaving visual group 1.
    model.geom_rgba[model.geom_group == 0, 3] = 0
    states = {'qpos': recording[:, 1:1 + model.nq]}
    sources = [directory / name for name in manifest['sources']] + [reference, reference.with_suffix('.json')]
    sources += model_sources(directory / 'effective-model.xml')[1:]
    receipt = render(model, states, recording[:, 0], camera(1.35, 135, -45),
                     np.tile([0, 0, .13], (len(recording), 1)), output, sources=sources,
                     label='LIBERO demo 0 | native MuJoCo 2.3.7', pilot=pilot)
    receipt['native_geometry_max_error_m'] = max_error
    receipt['native_geometry_checked_frames'] = len(recording)
    (Path(output) / 'provenance.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['apple', 'pinch', 'incline', 'normal', 'libero'])
    parser.add_argument('input', help='Apple recording, pinch case ID, or verified input-map.json')
    parser.add_argument('output', type=Path)
    parser.add_argument('--pilot', action='store_true')
    parser.add_argument('--reference', type=Path, help='Native LIBERO geometry reference')
    args = parser.parse_args()
    if args.kind == 'libero':
        if args.reference is None:
            parser.error('LIBERO requires --reference')
        libero(args.input, args.reference, args.output, args.pilot)
    elif args.kind in ('incline', 'normal'):
        primitive(args.kind, args.input, args.output, args.pilot)
    else:
        {'apple': apple, 'pinch': pinch}[args.kind](args.input, args.output, args.pilot)


if __name__ == '__main__':
    main()
