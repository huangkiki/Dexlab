"""Mixed native identities must not collapse sites, joints or multiple objects."""

from copy import deepcopy
from types import SimpleNamespace as Namespace
import unittest
import xml.etree.ElementTree as ET

from dexlab.libero_bindings import bind_task


DEFINITION = {
    "objects": {"pot": "pot", "basket": "basket"},
    "fixtures": {"main_table": "table", "cabinet": "wooden_cabinet"},
    "regions": {"cabinet_middle": {"target": "cabinet", "target_declared": True},
                "main_table_zone": {"target": "main_table", "target_declared": True},
                "basket_inside": {"target": "basket", "target_declared": True},
                "absent_unused": {"target": "absent", "target_declared": False}},
    "objects_of_interest": ["cabinet_middle", "pot", "basket"],
    "goal": ["and", ["open", "cabinet_middle"], ["in", "pot", "basket_inside"]],
}


def fixture():
    model = Namespace(nbody=6, njnt=2, nq=8, nv=7, nsite=3, ngeom=4,
                      body_parentid=[0, 0, 0, 2, 0, 0], geom_bodyid=[1, 3, 4, 5],
                      jnt_type=[2, 0], jnt_bodyid=[3, 4], jnt_qposadr=[0, 1], jnt_dofadr=[0, 1],
                      site_bodyid=[3, 1, 5])
    for kind, names in {"body": ["world", "table", "cabinet_root", "drawer", "pot_root", "basket_root"],
                        "joint": ["drawer_joint", "pot_joint"],
                        "site": ["cabinet_middle", "main_table_zone", "basket_inside"]}.items():
        setattr(model, kind + "_name2id", lambda name, names=names: names.index(name))
        setattr(model, kind + "_id2name", lambda index, names=names: names[index])
    objects = {"pot": Namespace(root_body="pot_root", joints=["pot_joint"]),
               "basket": Namespace(root_body="basket_root", joints=[])}
    fixtures = {"cabinet": Namespace(root_body="cabinet_root", joints=["drawer_joint"])}
    sites = {name: Namespace(name=name, parent_name=parent, joints=joints)
             for name, parent, joints in (("cabinet_middle", "cabinet", ["drawer_joint"]),
                                          ("main_table_zone", None, None),
                                          ("basket_inside", "basket", []))}
    states = {name: Namespace(object_name=name, object_state_type="object", is_fixture=name in fixtures)
              for name in objects.keys() | fixtures.keys()}
    states.update({name: Namespace(object_name=name, object_state_type="site", parent_name=site.parent_name)
                   for name, site in sites.items()})
    parsed = {"goal_state": deepcopy(DEFINITION["goal"][1:]),
              "obj_of_interest": deepcopy(DEFINITION["objects_of_interest"])}
    for field in ("objects", "fixtures"):
        parsed[field] = {}
        for name, category in DEFINITION[field].items():
            parsed[field].setdefault(category, []).append(name)
    return Namespace(sim=Namespace(model=model), parsed_problem=parsed, workspace_name="main_table",
                     objects_dict=objects, fixtures_dict=fixtures, object_sites_dict=sites,
                     object_states_dict=states, obj_body_id={"pot": 4, "basket": 5, "cabinet": 2},
                     model=Namespace(mujoco_arena=Namespace(table_body=ET.fromstring('<body name="table"/>'))))


class LiberoBindingTests(unittest.TestCase):
    def test_preserves_two_objects_arena_joint_region_and_unresolved_source(self):
        result = bind_task(fixture(), DEFINITION)
        entities = result["entities"]
        self.assertEqual(set(entities), set(DEFINITION["objects"]) | set(DEFINITION["fixtures"]) | set(DEFINITION["regions"]))
        self.assertEqual(entities["main_table"]["kind"], "arena")
        self.assertEqual(entities["cabinet"]["body_ids"], [2, 3])
        self.assertEqual(entities["cabinet_middle"]["body_id"], 3)
        self.assertEqual(entities["cabinet_middle"]["query_joint_ids"], [0])
        self.assertEqual(entities["pot"]["joints"][0]["qpos_indices"], list(range(1, 8)))
        self.assertEqual(entities["pot"]["joints"][0]["dof_indices"], list(range(1, 7)))
        self.assertEqual(entities["absent_unused"]["status"], "unresolved-source-target")
        self.assertEqual(result["goal"], DEFINITION["goal"])

    def test_wrong_object_id_is_rejected(self):
        env = fixture(); env.obj_body_id["pot"] = 5
        with self.assertRaisesRegex(ValueError, "binding disagrees"):
            bind_task(env, DEFINITION)

    def test_required_site_cannot_disappear_or_point_to_another_owner(self):
        env = fixture(); del env.object_sites_dict["basket_inside"]
        with self.assertRaisesRegex(ValueError, "required task region"):
            bind_task(env, DEFINITION)
        env = fixture(); env.sim.model.site_bodyid[2] = 4
        with self.assertRaisesRegex(ValueError, "site owner"):
            bind_task(env, DEFINITION)

    def test_wrong_joint_and_missing_articulated_observation_are_rejected(self):
        for joints in (["pot_joint"], []):
            env = fixture(); env.object_sites_dict["cabinet_middle"].joints = joints
            with self.subTest(joints=joints), self.assertRaisesRegex(ValueError, "joint"):
                bind_task(env, DEFINITION)

    def test_site_joint_must_drive_that_body_not_another_drawer(self):
        env = fixture()
        # Move site onto root while its queried joint remains on the child drawer.
        env.sim.model.site_bodyid[0] = 2
        with self.assertRaisesRegex(ValueError, "does not drive"):
            bind_task(env, DEFINITION)

    def test_body_aliases_are_rejected(self):
        env = fixture(); env.objects_dict["basket"].root_body = "pot_root"; env.obj_body_id["basket"] = 4
        with self.assertRaisesRegex(ValueError, "alias"):
            bind_task(env, DEFINITION)

    def test_missing_secondary_object_or_native_goal_is_rejected(self):
        env = fixture(); del env.objects_dict["basket"]
        with self.assertRaisesRegex(ValueError, "providers"):
            bind_task(env, DEFINITION)
        env = fixture(); env.parsed_problem["goal_state"].pop()
        with self.assertRaisesRegex(ValueError, "goals differ"):
            bind_task(env, DEFINITION)

    def test_coordinate_addresses_are_not_interchangeable(self):
        env = fixture(); env.sim.model.nq = 7
        with self.assertRaisesRegex(ValueError, "coordinate widths"):
            bind_task(env, DEFINITION)

    def test_site_state_cannot_alias_body_state(self):
        env = fixture(); env.object_states_dict["cabinet_middle"].object_state_type = "object"
        with self.assertRaisesRegex(ValueError, "site owner"):
            bind_task(env, DEFINITION)

    def test_unused_missing_region_is_reported_without_inventing_body(self):
        env = fixture(); del env.object_sites_dict["main_table_zone"]; del env.object_states_dict["main_table_zone"]
        self.assertEqual(bind_task(env, DEFINITION)["entities"]["main_table_zone"]["status"], "not-materialized")


if __name__ == "__main__":
    unittest.main()
