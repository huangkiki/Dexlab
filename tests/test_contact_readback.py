"""Missing/contradictory observations must not establish pair-law equivalence."""
import copy
import unittest
from dexlab.contact_plane import PlaneCase
from dexlab.contact_readback import audit_plane_parameters


class ContactReadbackTests(unittest.TestCase):
    def setUp(self):
        self.case = PlaneCase()
        self.normal = {'solref': [.005, 1], 'solimp': [.95, .99, .001, .5, 2]}
        self.meta = {'normal_parameters_readback': self.normal,
                     'friction_readback': [[self.case.friction, 0, 0]] * 2,
                     'geometry_readback': {'type': [0, 6],
                         'size': [[2, 2, .1], [self.case.half_size] * 3],
                         'priority': [0, 0], 'solmix': [1, 1], 'condim': [3, 3],
                         **{k: [v, v] for k, v in self.normal.items()}}}
        self.contact = {'geom1': 0, 'geom2': 1, 'parameters': {
            'dimension': 3, 'friction': [self.case.friction] * 2 + [1e-5] * 3,
            'include_margin': 0, **copy.deepcopy(self.normal)}}

    def audit(self, rows):
        return audit_plane_parameters('mujoco', self.meta, rows, self.case)

    def test_observed_pair_and_geometry_agree(self):
        self.assertEqual(self.audit([[self.contact]])['status'], 'consistent')

    def test_no_contacts_or_missing_parameters_is_not_success(self):
        for rows in ([], [[]], [[{'geom1': 0, 'geom2': 1}]]):
            self.assertFalse(self.audit(rows)['pair_parameters_match'])

    def test_malformed_frames_do_not_pass_or_hide_valid_contacts(self):
        for malformed in (None, 7, "missing", {"parameters": {}}):
            with self.subTest(frame=malformed):
                result = self.audit([[self.contact], malformed])
                self.assertFalse(result['pair_parameters_match'])
                self.assertEqual(result['missing'], 1)
        self.assertFalse(self.audit(None)['pair_parameters_match'])

    def test_malformed_contact_does_not_pass(self):
        for malformed in (None, 7, "missing", {"parameters": None}):
            with self.subTest(contact=malformed):
                result = self.audit([[self.contact, malformed]])
                self.assertFalse(result['pair_parameters_match'])
                self.assertEqual(result['missing'], 1)

    def test_actor_friction_does_not_excuse_wrong_contact_friction(self):
        self.contact['parameters']['friction'][0] *= 2
        result = self.audit([[self.contact]])
        self.assertTrue(result['actor_profiles_equal'])
        self.assertFalse(result['pair_parameters_match'])
        self.assertEqual(result['mismatched'], 1)

    def test_geometry_and_priority_mismatch_remain_distinct(self):
        self.meta['geometry_readback']['size'][1][0] *= 2
        self.assertFalse(self.audit([[self.contact]])['geometry_matches'])
        self.assertTrue(self.audit([[self.contact]])['pair_parameters_match'])
        self.meta['geometry_readback']['priority'][0] = 1
        self.assertFalse(self.audit([[self.contact]])['pair_parameters_match'])

    def test_nonfinite_contact_parameters_fail(self):
        self.contact['parameters']['solref'][0] = float('nan')
        self.assertFalse(self.audit([[self.contact]])['pair_parameters_match'])

    def test_superdex_unobserved_pair_law_stays_unknown(self):
        result = audit_plane_parameters('superdex', {}, [], self.case)
        self.assertIsNone(result['pair_parameters_match'])
        self.assertIsNone(result['geometry_matches'])
        self.assertFalse(result['actor_profiles_equal'])


if __name__ == '__main__':
    unittest.main()
