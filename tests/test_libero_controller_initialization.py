"""Exercise restoration against the real pinned robosuite OSC, without a dataset."""

from types import SimpleNamespace
import unittest

import numpy as np

from dexlab.libero_initialization import initialize_demo

try:
    import mujoco
    import robosuite
    from robosuite.controllers.osc import OperationalSpaceController
    from robosuite.utils.binding_utils import MjSim
except ImportError:
    mujoco = robosuite = None


def arm_xml():
    links = ''.join(
        f'<body pos="0 0 .12"><joint name="j{i}" axis="{axis}"/>'
        '<geom type="capsule" size=".02 .05" mass=".2"/>'
        for i, axis in enumerate(('0 0 1', '0 1 0', '1 0 0', '0 1 0', '1 0 0', '0 1 0', '0 0 1'))
    )
    return ('<mujoco><option timestep=".002"/><worldbody>' + links
            + '<site name="eef" pos=".05 0 .1"/>' + '</body>' * 7
            + '<body pos="1 0 1"><freejoint/><geom size=".1"/></body>'
            + '</worldbody></mujoco>')


class ControllerEnvironment:
    """Native model reset recreates OSC before the source state is restored."""

    def __init__(self):
        self.sim = None
        self.reset_from_xml_string(arm_xml())

    def reset(self):
        pass

    def reset_from_xml_string(self, xml):
        if self.sim is not None:
            self.sim.free()
        self.sim = MjSim.from_xml_string(xml)
        controller = OperationalSpaceController(
            self.sim, 'eef', {'joints': list(range(7)), 'qpos': list(range(7)), 'qvel': list(range(7))},
            (-np.ones(7) * 80, np.ones(7) * 80),
        )
        self.robots = [SimpleNamespace(controller=controller,
            gripper=SimpleNamespace(current_action=np.array([-.25, .25])))]

    def _post_process(self):
        pass

    def _update_observables(self, force):
        pass


@unittest.skipUnless(mujoco is not None and mujoco.__version__ == '2.3.7'
                     and robosuite.__version__ == '1.4.0',
                     'Requires the pinned LIBERO MuJoCo2.3.7 / robosuite1.4.0 runtime')
class LiberoControllerInitializationTests(unittest.TestCase):
    def setUp(self):
        self.env = ControllerEnvironment()
        self.addCleanup(lambda: self.env.sim.free())
        self.initial = self.env.sim.get_state().flatten().copy()
        self.initial[0] = .25
        self.initial[1:8] = [.3, -.2, .1, .4, -.3, .2, -.1]
        self.initial[1 + self.env.sim.model.nq:1 + self.env.sim.model.nq + 7] = .05
        # The unrelated free-body quaternion also exercises native normalization.
        self.initial[11:15] = [2., .5, 0., 0.]

    def test_first_relative_goal_uses_restored_native_pose_and_joint_cache(self):
        record = {}
        initialize_demo(self.env, arm_xml(), self.initial, record)
        controller = self.env.robots[0].controller
        native_pos = self.env.sim.data.site_xpos[0].copy()
        native_ori = self.env.sim.data.site_xmat[0].reshape(3, 3).copy()
        controller.set_goal(np.array([.2, -.4, .1, 0., 0., 0.]))
        np.testing.assert_array_equal(controller.joint_pos, self.env.sim.data.qpos[:7])
        np.testing.assert_array_equal(controller.joint_vel, self.env.sim.data.qvel[:7])
        np.testing.assert_allclose(controller.goal_pos, native_pos + [.01, -.02, .005], rtol=0, atol=1e-15)
        np.testing.assert_array_equal(controller.goal_ori, native_ori)

    def test_zero_action_holds_restored_orientation_without_changing_missing_history(self):
        record = {}
        initialize_demo(self.env, arm_xml(), self.initial, record)
        robot = self.env.robots[0]
        native_pos = self.env.sim.data.site_xpos[0].copy()
        native_ori = self.env.sim.data.site_xmat[0].reshape(3, 3).copy()
        state = self.env.sim.get_state().flatten().copy()
        robot.controller.set_goal(np.zeros(6))
        np.testing.assert_array_equal(robot.controller.goal_pos, native_pos)
        np.testing.assert_array_equal(robot.controller.goal_ori, native_ori)
        np.testing.assert_array_equal(robot.controller.initial_joint, np.zeros(7))
        np.testing.assert_array_equal(robot.gripper.current_action, [-.25, .25])
        np.testing.assert_array_equal(self.env.sim.get_state().flatten(), state)


if __name__ == '__main__':
    unittest.main()
