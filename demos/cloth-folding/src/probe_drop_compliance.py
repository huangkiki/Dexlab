"""Four development controls for floor-contact and edge-constraint compliance.

Run under the repository resource guard. This removes the robot and table and
changes the initial pose: it is a minimal impact probe, not a grasp replay.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

TIMESTEP = 0.000125
STEPS = 8000
CONTROLS = (
    ('baseline', None, None),
    ('floor', 0.0005, None),
    ('edge', None, 0.0005),
    ('both', 0.0005, 0.0005),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def required(parent: ET.Element, query: str) -> ET.Element:
    element = parent.find(query)
    if element is None:
        raise ValueError(f'Missing source element: {query}')
    return element


def make_model(source: ET.Element, floor_tc, edge_tc) -> ET.Element:
    root = ET.Element('mujoco')
    for name in ('compiler', 'option', 'default'):
        root.append(copy.deepcopy(required(source, name)))
    # No external assets are used by this minimal model. Avoid copying private
    # deployment paths into the portable XML evidence.
    compiler = required(root, 'compiler')
    for attribute in ('meshdir', 'texturedir', 'assetdir'):
        compiler.attrib.pop(attribute, None)
    required(root, 'option').set('timestep', str(TIMESTEP))
    world = ET.SubElement(root, 'worldbody')
    floor = copy.deepcopy(required(source, "worldbody/geom[@name='floor']"))
    cloth = copy.deepcopy(required(source, "worldbody/flexcomp[@name='cloth']"))
    world.extend((floor, cloth))
    points = np.fromstring(cloth.attrib['point'], sep=' ').reshape(-1, 3)
    angle = np.deg2rad(45)
    rotation = np.array([[1, 0, 0], [0, np.cos(angle), -np.sin(angle)],
                         [0, np.sin(angle), np.cos(angle)]])
    points = (points - points.mean(axis=0)) @ rotation.T + [0, 0, 0.6]
    cloth.set('point', ' '.join(format(float(x), '.17g') for x in points.ravel()))
    if floor_tc is not None:
        floor.set('solref', f'{floor_tc} 1')
        floor.set('priority', '1')
    if edge_tc is not None:
        required(cloth, 'edge').set('solref', f'{edge_tc} 1')
    return root


def simulate(xml: Path) -> dict:
    model = mujoco.MjModel.from_xml_path(str(xml))
    data = mujoco.MjData(model)
    peaks = dict(edge_strain=0.0, floor_penetration_m=0.0,
                 self_penetration_m=0.0, solver_iterations=0)
    trace = []
    started = time.monotonic()
    for tick in range(STEPS):
        mujoco.mj_step(model, data)
        if (np.any(data.warning.number) or not np.isfinite(data.qpos).all()
                or not np.isfinite(data.qvel).all()):
            raise RuntimeError(f'Invalid native state at step {tick + 1}')
        # Contact and flex geometry describe the force evaluation at the start
        # of this integration step; do not label these as post-step geometry.
        row = dict(time_s=tick * TIMESTEP,
                   edge_strain=float(np.abs(data.flexedge_length /
                                            model.flexedge_length0 - 1).max()),
                   floor_penetration_m=0.0, self_penetration_m=0.0,
                   solver_iterations=int(np.max(data.solver_niter, initial=0)))
        for contact in data.contact:
            key = ('self_penetration_m' if np.all(contact.flex >= 0)
                   else 'floor_penetration_m')
            row[key] = max(row[key], -float(contact.dist))
        for key in peaks:
            peaks[key] = max(peaks[key], row[key])
        if tick % 8 == 0:
            trace.append(row)
    trace_path = xml.with_name('trace.json')
    trace_path.write_text(json.dumps(trace) + '\n')
    return {'wall_s': time.monotonic() - started, 'maximums': peaks,
            'steps': STEPS, 'xml_sha256': digest(xml),
            'trace_sha256': digest(trace_path)}


def run(record: Path, output: Path) -> None:
    if mujoco.__version__ != '3.14.0' or mujoco.mj_versionString() != '3.14.0':
        raise ValueError('This dated development probe requires MuJoCo 3.14.0')
    source_path = record / 'model.xml'
    source_hash = digest(source_path)
    source = ET.parse(source_path).getroot()
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    for name, floor_tc, edge_tc in CONTROLS:
        folder = output / name
        folder.mkdir()
        xml = folder / 'model.xml'
        ET.ElementTree(make_model(source, floor_tc, edge_tc)).write(xml, encoding='unicode')
        result = simulate(xml)
        result.update(floor_time_constant_s=floor_tc, edge_time_constant_s=edge_tc)
        results[name] = result
        print(json.dumps({name: result}), flush=True)
    if digest(source_path) != source_hash:
        raise RuntimeError('Source model changed during the controls')
    report = {
        'engine_version': mujoco.mj_versionString(),
        'source_model_sha256': source_hash, 'script_sha256': digest(Path(__file__)),
        'timestep_s': TIMESTEP, 'duration_s': STEPS * TIMESTEP,
        'results': results,
        'scope': ('Minimal 45-degree planar cloth drop, centered at 0.6 m, zero '
                  'initial velocity, no robot or table. Original cloth, floor, '
                  'defaults and solver options retained except listed controls. '
                  'No material calibration, full-grasp or independent collision '
                  'validation claim. Peaks sampled every native step; traces '
                  'every eight steps. Floor priority 1 selects its changed solref; '
                  'native reference safety remains enabled.'),
    }
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.record, args.output)
