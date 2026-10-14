"""Native evidence corruption checks; no PhysX installation is required."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from dexlab.incline_score import ImpulseConsistencyError, file_hash, measure_response
from dexlab.physx_incline import run
from dexlab.physx_incline_score import validate_admission, validate_protocol, validate_rows

FIXTURES = Path(__file__).parent / 'fixtures'


class PhysXEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads((FIXTURES / 'physx-incline-protocol.json').read_text())
        self.admission = json.loads((FIXTURES / 'physx-incline-admission.json').read_text())
        self.case = self.protocol['cases'][1]

    def records(self):
        a, c = self.admission, self.case
        h = a['effective_timestep']
        normal = np.array([np.sin(np.deg2rad(c['angle_deg'])), 0, np.cos(np.deg2rad(c['angle_deg']))])
        total = np.array([0, 0, self.protocol['mass_kg'] * self.protocol['gravity_m_s2'] * h])
        normal_impulse = (total @ normal) * normal
        rows = [deepcopy(a)]
        for i in range(2000):
            before, after = a['initial_state'].copy(), a['initial_state'].copy()
            before[0], after[0] = i * h, (i + 1) * h
            rows.append(dict(kind='step', step=i, scene_timestamp=i + 2,
                             pre_state=before, state=after, interval_start_s=before[0],
                             interval_end_s=after[0], errors=[], overflow=False, sleeping=False,
                             pairs=[dict(cube_first=True, normal_impulses_available=True,
                                         friction_impulses_available=True, patch_count=1, declared_contacts=1,
                                         contacts=[dict(position=[0, 0, 0], normal=normal.tolist(),
                                                        separation=0, impulse=normal_impulse.tolist())],
                                         friction_anchors=[dict(position=[0, 0, 0], impulse=(total-normal_impulse).tolist())])]))
        rows.append(dict(kind='completion', completed_steps=2000, state_writes_after_initialization=0, errors=[]))
        return rows

    def test_native_admission_and_protocol(self):
        validate_protocol(self.protocol)
        validate_admission(self.protocol, self.case, self.admission)

    def test_overrides_precision_and_reset_pollution(self):
        for key, value in [('mass', .065), ('inertia', [1e-5]*3), ('solver_type', 1),
                           ('gravity', [0, 0, -9.8]), ('static_friction', .6),
                           ('scene_flags', 0), ('dynamic_actors', 2), ('linear_damping', .1),
                           ('effective_timestep', .001)]:
            with self.subTest(key=key):
                changed = deepcopy(self.admission); changed[key] = value
                with self.assertRaises(ValueError):
                    validate_admission(self.protocol, self.case, changed)
        for index in (1, 5, 8):
            changed = deepcopy(self.admission); changed['initial_state'][index] += .001
            with self.assertRaises(ValueError):
                validate_admission(self.protocol, self.case, changed)

    def test_no_duplicate_cases_or_relaxed_limits(self):
        for change in ('case', 'limit'):
            p = deepcopy(self.protocol)
            if change == 'case': p['cases'][1] = p['cases'][0]
            else: p['limits']['rotation_rad'] = 1
            with self.assertRaises(ValueError): validate_protocol(p)

    def test_signed_normal_and_friction_channels(self):
        rows = self.records()
        trace = validate_rows(self.protocol, self.case, self.admission, rows)
        self.assertTrue(measure_response(self.protocol, self.case | {'timestep': self.admission['effective_timestep']}, trace)['passed'])
        for row in rows[1:-1]:
            pair = row['pairs'][0]; pair['cube_first'] = False
            for c in pair['contacts']:
                c['normal'] = (-np.array(c['normal'])).tolist(); c['impulse'] = (-np.array(c['impulse'])).tolist()
            for a in pair['friction_anchors']: a['impulse'] = (-np.array(a['impulse'])).tolist()
        reverse = validate_rows(self.protocol, self.case, self.admission, rows)
        np.testing.assert_array_equal(trace['forces'], reverse['forces'])

    def test_missing_stream_clock_injection_and_capacity(self):
        original = self.records()
        for change in ('clock', 'counter', 'state', 'capacity', 'channel', 'normal', 'point', 'completion'):
            with self.subTest(change=change):
                rows = deepcopy(original); row = rows[20]; pair = row['pairs'][0]
                if change == 'clock': row['interval_start_s'] += .001
                elif change == 'counter': row['scene_timestamp'] += 1
                elif change == 'state': row['state'][1] += .001
                elif change == 'capacity': pair['declared_contacts'] += 1
                elif change == 'channel': pair['friction_impulses_available'] = False
                elif change == 'normal': pair['contacts'][0]['normal'][2] *= -1
                elif change == 'point': pair['contacts'][0]['position'][0] = float('nan')
                else: rows.pop()
                with self.assertRaises(ValueError): validate_rows(self.protocol, self.case, self.admission, rows)

    def test_contact_loss_is_not_hidden(self):
        rows = self.records()
        rows[1500]['pairs'] = []
        trace = validate_rows(self.protocol, self.case, self.admission, rows)
        with self.assertRaises(ImpulseConsistencyError):
            measure_response(self.protocol, self.case | {'timestep': self.admission['effective_timestep']}, trace)

    def test_interrupted_child_and_raw_bytes_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); binary = root / 'binary'; binary.write_bytes(b'test recorder')
            p = self.protocol | {'binary_sha256': file_hash(binary)}
            protocol = root / 'protocol.json'; protocol.write_text(json.dumps(p))
            proof = root / 'proof.json'; proof.write_text(json.dumps({k: p[k] for k in ('binary_sha256','source_commit','recorder_sha256')}))
            class InterruptedChild:
                returncode = -15
                def __init__(self, command, stdout, stderr): stdout.write('{"kind":"partial"}\n'); self.terminated = False
                def wait(self, timeout=None):
                    if not self.terminated: raise KeyboardInterrupt()
                    return self.returncode
                def terminate(self): self.terminated = True
            with patch.object(subprocess, 'Popen', InterruptedChild):
                with self.assertRaises(KeyboardInterrupt): run(protocol, proof, binary, root / 'output', admission_only=True)
            campaign = json.loads((root / 'output/campaign.json').read_text())
            self.assertEqual(campaign['state'], 'interrupted')
            self.assertEqual(campaign['cases'][0]['returncode'], -15)
            raw = root / 'output' / self.protocol['cases'][0]['id'] / 'native.jsonl.gz'
            with gzip.open(raw, 'rt') as stream: self.assertEqual(stream.read(), '{"kind":"partial"}\n')


if __name__ == '__main__':
    unittest.main()
