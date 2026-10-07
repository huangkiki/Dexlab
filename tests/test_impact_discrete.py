import unittest
import numpy as np
from dexlab.impact_discrete import continuous, residuals, rollout, step, bind_records


class DiscreteImpactTests(unittest.TestCase):
    def test_phase_identity_and_detuning(self):
        for phase in (0., .25, .5, .75, 1.):
            # q=phase, v=1 at first overlapping step; z=1 gives A^3=-I.
            x = [0., .1-phase*.001]
            p, v, f = rollout(x, [1., 0.], [1., 1.], .05, 1e6, .001, 4)
            np.testing.assert_allclose(v[-1], [0., 1.], atol=1e-12, rtol=0)
            self.assertTrue(np.all(f[:, 0] <= 0))
        _, v, _ = rollout([0., .0995], [1., 0.], [1., 1.], .05, 1e6, .0005, 20)
        self.assertGreater(abs(v[-1, 1]-1), 1e-5)

    def test_force_epoch_and_separation(self):
        p, v, f = step([0., .099], [1., 0.], [1., 1.], .05, 1e6, .001)
        np.testing.assert_allclose(f, [-500., 500.], atol=1e-10)
        np.testing.assert_allclose(v, [.5, .5], atol=1e-12)
        _, _, f = step([0., .101], [0., 1.], [1., 1.], .05, 1e6, .001)
        np.testing.assert_array_equal(f, [0., 0.])

    def test_continuous_energy_and_endpoints(self):
        duration = np.pi/1000
        times = np.array([0., .02, .02+duration/2, .02+duration, .03])
        p, v, f = continuous([-.06, .06], [1., 0.], [1., 1.], .05, 1e6, times)
        np.testing.assert_allclose(v[[0, -1]], [[1., 0.], [0., 1.]], atol=1e-12)
        y = np.maximum(0., .1-(p[:, 1]-p[:, 0]))
        energy = .5*np.sum(v*v, axis=1)+.5*.5*1e6*y*y
        np.testing.assert_allclose(energy, .5, atol=1e-12)
        np.testing.assert_allclose(f[2], [-500., 500.], atol=1e-10)

    def test_reject_invalid_and_changed_predictions(self):
        for mass in ([0., 1.], [1.], [float('nan'), 1.]):
            with self.assertRaises(ValueError):
                step([0., .1], [1., 0.], mass, .05, 1e6, .001)
        a = rollout([-.06, .06], [1., 0.], [1., 1.], .05, 1e6, .001, 100)
        self.assertTrue(residuals(a, a)['passed'])
        b = tuple(x.copy() for x in a); b[1][5, 0] += 1e-4
        self.assertFalse(residuals(a, b)['passed'])
        b = tuple(x.copy() for x in a); b[2][:] = np.roll(b[2], 1, axis=0)
        self.assertFalse(residuals(a, b)['passed'])
        with self.assertRaises(ValueError):
            residuals(a, [np.array([np.nan]), a[1], a[2]])

    def test_published_binding_rejects_local_rehash(self):
        published = dict(results=[dict(id='a', trace_sha256='original', xml_sha256='xml')])
        bind_records(published, published, ['a'])
        altered = dict(results=[dict(id='a', trace_sha256='rehash', xml_sha256='xml')])
        with self.assertRaises(ValueError):
            bind_records(altered, published, ['a'])
        with self.assertRaises(ValueError):
            bind_records(published, published, ['a', 'a'])
        with self.assertRaises(ValueError):
            bind_records(published, published, ['missing'])

    def test_audit_rejects_epoch_and_coherent_wrong_law(self):
        import copy
        from test_impact import ImpactTests
        from dexlab.impact_discrete import audit_trace
        fixture = ImpactTests(); fixture.setUp()
        # A coherent instantaneous elastic impulse is not the compliant map.
        result = audit_trace(fixture.protocol, fixture.case, fixture.trace)
        self.assertFalse(result['full_rollout']['passed'])
        self.assertFalse(result['one_step']['passed'])
        for field in ('force_times', 'states', 'forces'):
            trace = copy.deepcopy(fixture.trace)
            trace[field].flat[10] += .01
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit_trace(fixture.protocol, fixture.case, trace)
