"""Fixed MuJoCo parameter-construction controls, not a dynamics benchmark.

References: official modeling/contact-parameters and mjMINMU in mjmodel.h.
Expected values are declared independently of the native readback.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path

import mujoco
import numpy as np

from dexlab.apple_admission import observe_runtime, refresh_inventory
from dexlab.engine_versions import validate_versions
from dexlab.official_wheels import verify_official_wheel

PLANE = 'friction=".2 .01 .002" solref=".004 1" solimp=".8 .9 .002 .5 2" condim="3" solmix="1"'
BOX = 'friction=".6 .003 .004" solref=".012 .5" solimp=".9 .99 .006 .5 2" condim="6" solmix="3"'
EXPECTED = {'dimension': 6, 'friction': [.6, .6, .01, .004, .004],
            'solref': [.010, .625], 'solimp': [.875, .9675, .005, .5, 2]}
CASES = [
    {'name': 'equal-priority-weighted', 'expected': EXPECTED},
    {'name': 'plane-priority', 'plane_extra': 'priority="1"',
     'expected': {'dimension': 3, 'friction': [.2, .2, .01, .002, .002],
                  'solref': [.004, 1], 'solimp': [.8, .9, .002, .5, 2]}},
    {'name': 'direct-solref-minimum', 'direct': True,
     'expected': EXPECTED | {'solref': [-2000, -20]}},
    {'name': 'explicit-anisotropic-pair', 'pair': True,
     'expected': {'dimension': 6, 'friction': [.15, .25, .001, .002, .003],
                  'solref': [.003, 1], 'solimp': [.9, .95, .003, .5, 2]}},
    {'name': 'global-override', 'override': True,
     'expected': {'dimension': 6, 'friction': [.7, .7, .05, .006, .006],
                  'solref': [.006, 1], 'solimp': [.85, .97, .004, .5, 2]}},
    {'name': 'separated-negative', 'height': 1.0, 'expected': None},
]


def xml_for(case):
    plane = PLANE.replace('.004 1', '-2000 -20') if case.get('direct') else PLANE
    options = ('o_friction=".7 .7 .05 .006 .006" o_solref=".006 1" '
               'o_solimp=".85 .97 .004 .5 2"') if case.get('override') else ''
    flag = '<flag override="enable"/>' if case.get('override') else ''
    pair = ('<contact><pair geom1="plane" geom2="box" condim="6" '
            'friction=".15 .25 .001 .002 .003" solref=".003 1" '
            'solimp=".9 .95 .003 .5 2"/></contact>') if case.get('pair') else ''
    return f'''<mujoco><option timestep=".0005" solver="Newton" cone="elliptic" {options}>{flag}</option>
<worldbody><geom name="plane" type="plane" size="2 2 .1" {plane} {case.get('plane_extra', '')}/>
<body pos="0 0 {case.get('height', .0199)}"><freejoint/><geom name="box" type="box" size=".02 .02 .02" mass=".2" {BOX}/></body>
</worldbody>{pair}</mujoco>'''


def matches(observed, expected):
    if expected is None:
        return not observed
    return bool(observed) and all(
        all(np.asarray(row[k]).shape == np.asarray(v).shape
            and np.isfinite(row[k]).all()
            and np.allclose(row[k], v, atol=1e-12, rtol=1e-12)
            for k, v in expected.items()) for row in observed)


def run(output, wheel_dir):
    output.mkdir(parents=True, exist_ok=False)
    script = Path(__file__).resolve()
    source = script.read_bytes()
    (output / script.name).write_bytes(source)
    report = {'scope': 'Six static native contact-construction controls; no integration or grasp',
              'cases': CASES, 'source_sha256': hashlib.sha256(source).hexdigest(),
              'status': 'admitting', 'rows': []}
    def save():
        (output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    save()
    runtime, inventory = observe_runtime(), refresh_inventory()
    validate_versions(inventory, runtime['installed'], runtime['native'])
    official = next(row for row in inventory if row['package'] == 'mujoco')
    wheels = [(wheel_dir / n, sha) for n, sha in official['distribution_sha256'].items()
              if n.endswith('.whl') and (wheel_dir / n).is_file()]
    if len(wheels) != 1:
        raise ValueError('Exactly one official MuJoCo wheel required')
    report['wheel'] = verify_official_wheel(wheels[0][0], package='mujoco',
        version=runtime['installed']['mujoco'], official_sha256=wheels[0][1],
        installed_code_sha256=runtime['package_code_sha256']['mujoco'])
    report.update(runtime=runtime, inventory=inventory, status='running')
    save()
    for case in CASES:
        xml = xml_for(case)
        (output / (case['name'] + '.xml')).write_text(xml)
        start = time.perf_counter()
        model = mujoco.MjModel.from_xml_string(xml)
        data = mujoco.MjData(model)
        mujoco.mj_forward(model, data)
        observed = [{'dimension': int(c.dim), 'friction': c.friction.tolist(),
                     'solref': c.solref.tolist(), 'solimp': c.solimp.tolist()}
                    for c in data.contact]
        report['rows'].append({'name': case['name'], 'xml_sha256': hashlib.sha256(xml.encode()).hexdigest(),
                               'observed': observed, 'expected': case['expected'],
                               'matched': matches(observed, case['expected']),
                               'construction_forward_s': time.perf_counter() - start,
                               'simulation_time': float(data.time)})
        save()
    report['source_unchanged'] = script.read_bytes() == source
    report['status'] = 'completed'
    save()
    if not report['source_unchanged'] or not all(row['matched'] for row in report['rows']):
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--wheel-dir', required=True, type=Path)
    args = parser.parse_args()
    run(args.output.resolve(), args.wheel_dir.resolve())
