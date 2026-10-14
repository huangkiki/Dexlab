"""Fail closed on changed hypotheses, hidden overrides and interrupted trials."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from dexlab.contact_load import LIMITS, LoadCase
from dexlab.contact_parameters import normal_parameters
from dexlab.contact_trials import create, parameter_record, run_trial, command, recover
from dexlab.migration_budget import MigrationBudget, digest


class ContactTrialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.handle = {'cgroup':'/dexlab-bounded-00000000000000000000000000000000.service',
                       'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
        patcher=patch('dexlab.contact_trials.execution_cgroup',return_value=self.handle)
        patcher.start();self.addCleanup(patcher.stop)
        source = self.root/'prior.json'
        source.write_text('{"scope":"fixture only"}')
        self.parameters = normal_parameters('mujoco')
        self.manifest = dict(schema_version=1, purpose='development', engine='mujoco',
            runtime_profile='historical-3.11.0', case=asdict(LoadCase()), limits=LIMITS, baseline=self.parameters,
            work_package=dict(id='test', hypothesis='One diagnostic', max_starts=1, wall_s=10,
                              evidence_sha256=[digest(source.read_bytes())]),
            matrix=[dict(id='one', hypothesis='A falsifiable fixture hypothesis',
                expected_effect='Observe unchanged physics acceptance', physical_reference='Synthetic target',
                parameters=self.parameters, evidence=[dict(path=str(source),sha256=digest(source.read_bytes()))])])

    def test_missing_parameter_reference_and_changed_acceptance_rejected_before_creation(self):
        for mutation in ('parameters','evidence','limits','purpose','budget'):
            bad=deepcopy(self.manifest)
            if mutation=='parameters': del bad['matrix'][0]['parameters']['solimp']
            if mutation=='evidence': bad['matrix'][0]['evidence'][0]['sha256']='0'*64
            if mutation=='limits': bad['limits']['penetration_m']=1
            if mutation=='purpose': bad['purpose']='holdout'
            if mutation=='budget': bad['work_package']['max_starts']=65
            with self.assertRaises(ValueError): create(self.root/mutation,bad)
            self.assertFalse((self.root/mutation).exists())

    def test_overridden_and_missing_readbacks_never_pass(self):
        run=dict(normal_parameters=self.parameters,native=dict(normal_parameters_readback=self.parameters))
        self.assertTrue(parameter_record('mujoco',self.parameters,self.parameters,run)['readback_matches'])
        bad=deepcopy(run);bad['native']['normal_parameters_readback']['solref']=[.1,1.]
        result=parameter_record('mujoco',self.parameters,self.parameters,bad)
        self.assertFalse(result['readback_matches']);self.assertIn('solref',result['readback_differences'])
        self.assertIsNone(parameter_record('mujoco',self.parameters,self.parameters,{})['effective'])
        run['normal_parameters']={}
        self.assertFalse(parameter_record('mujoco',self.parameters,self.parameters,run)['declaration_matches'])

    def test_completed_physical_failure_is_retained_and_cannot_retry(self):
        root=self.root/'run';create(root,self.manifest)
        def fake(argv,destination,deadline,process_record,**kwargs):
            if '--output' in argv:
                raw=Path(argv[argv.index('--output')+1]);raw.mkdir()
                (raw/'run.json').write_text(json.dumps(dict(status='completed',normal_parameters=self.parameters,
                    native=dict(normal_parameters_readback=self.parameters))))
                destination.write_text('Fixture acquisition, not physics evidence')
            else: destination.write_text('{"passed":false,"checks":{"synthetic_fixture":false}}')
            return 1
        with patch('dexlab.contact_trials.command',side_effect=fake): result=run_trial(root,'one',timeout_s=5)
        self.assertFalse(result['passed']);self.assertEqual(result['outcome'],'recorded')
        self.assertTrue((root/'attempts/0000/result.json').is_file())
        with self.assertRaises(ValueError): run_trial(root,'one',timeout_s=5,retry_reason='try again')

    def test_timeout_is_accounted_and_unfinished_reservation_blocks_launch(self):
        root=self.root/'run';create(root,self.manifest)
        with patch('dexlab.contact_trials.command',side_effect=subprocess.TimeoutExpired('fixture',5)):
            result=run_trial(root,'one',timeout_s=5)
        self.assertEqual(result['outcome'],'interrupted')
        self.assertEqual(MigrationBudget(root).status()['starts_used'],1)
        with self.assertRaises(ValueError): run_trial(root,'one',timeout_s=5,retry_reason='bounded recovery')
        other=self.root/'other';budget=create(other,self.manifest)
        budget.reserve('one',{'parent_pid':99999999,**self.handle},timeout_s=5)
        with self.assertRaises(RuntimeError): run_trial(other,'one',timeout_s=5)
        recover(other)
        self.assertEqual(budget.status()['wall_charged_or_reserved_s'],5)

    def test_live_process_cannot_be_recovered(self):
        import os
        root=self.root/'run';budget=create(root,self.manifest)
        budget.reserve('one',{'parent_pid':os.getpid(),**self.handle},timeout_s=5)
        with self.assertRaises(RuntimeError): recover(root)

    def test_child_timeout_is_reaped(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            command([sys.executable,'-c','import time; time.sleep(30)'],self.root/'log',
                    time.monotonic()+.05,self.root/'process.json')
        pid=json.loads((self.root/'process.json').read_text())['pid']
        import os
        with self.assertRaises(ProcessLookupError): os.kill(pid,0)

    def test_source_change_requires_successor_without_resetting_budget(self):
        root=self.root/'run';budget=create(root,self.manifest)
        with patch('dexlab.contact_trials.sources',return_value={}):
            with self.assertRaisesRegex(ValueError,'Source changed'): run_trial(root,'one',timeout_s=5)
        self.assertEqual(budget.status()['starts_used'],0)

    def test_recovery_can_resume_after_receipt_before_ledger_settlement(self):
        root=self.root/'run';budget=create(root,self.manifest)
        budget.reserve('one',{'parent_pid':99999999,**self.handle},timeout_s=5)
        with patch.object(MigrationBudget,'finish',side_effect=OSError('simulated interruption')):
            with self.assertRaises(OSError): recover(root)
        self.assertTrue((root/'attempts/0000/recovery.json').is_file())
        self.assertIsNone(budget.status()['attempts'][0]['terminal'])
        recover(root)
        self.assertEqual(budget.status()['starts_used'],1)
        self.assertEqual(budget.status()['wall_charged_or_reserved_s'],5)
