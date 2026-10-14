import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.research_experience import ROOT, load_experiences, update
from scripts.physx_precision_diagnostics import projection_residual, analyze_case


class ResearchExperienceTests(unittest.TestCase):
    def test_bilingual_pages_current_and_historical_tasks_unchanged(self):
        update(check=True)
        self.assertEqual(len(load_experiences()),8)

    def test_broken_reference_and_unknown_task_fail_closed(self):
        original=json.loads((ROOT/'docs/research-experiences.json').read_text())
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'docs').mkdir()
            for mutation in ('task','hash','translation'):
                manifest=json.loads(json.dumps(original))
                row=manifest['experiences'][0]
                if mutation=='task': row['task_ids']=['invented-task']
                if mutation=='hash': row['evidence'][0]['sha256']='0'*64
                if mutation=='translation': row['en']['observation']=''
                (root/'docs/research-experiences.json').write_text(json.dumps(manifest))
                with patch('scripts.research_experience.load_inventory',return_value=json.loads((ROOT/'docs/task-coverage.json').read_text())):
                    with self.assertRaises(ValueError): load_experiences(root)

    def test_projection_distinguishes_reference_direction(self):
        self.assertLess(projection_residual([1.,0.,1.],[1.,0.,1.]),1e-14)
        self.assertEqual(projection_residual([1.,0.,1.],[0.,0.,1.]),1.)

    def test_impulse_epoch_uses_pre_and_post_velocity(self):
        admission=dict(mass=1.,effective_timestep=.1,gravity=[0,0,-10.])
        pre=[0.]*14;post=pre.copy();post[10]=-1.
        row=dict(pairs=[],pre_state=pre,state=post,step=0,interval_end_s=.1)
        result=analyze_case(admission,[row],dict(angle_deg=0),nominal_mass=1.,nominal_gravity=10.)
        self.assertEqual(result['peaks']['residual_norm_ns']['residual_norm_ns'],0.)
        self.assertIsNone(result['first_original_momentum_exceedance'])
        row['state'][10]=0.
        self.assertIsNotNone(analyze_case(admission,[row],dict(angle_deg=0),nominal_mass=1.,nominal_gravity=10.)['first_original_momentum_exceedance'])
