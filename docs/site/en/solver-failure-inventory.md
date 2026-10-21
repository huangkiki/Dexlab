# Complete solver-audit inventory

[Back to conclusions](solver-failure-audit.md)

## All 50 public RSS entrypoints

Forty entries have task-scoped assertions; ten are tutorials, rendering or hardware mocks. Goal wrappers and their scene may share a trajectory: these are not fifty independent manipulation types. A passing expected-failure control is not successful manipulation.

| Entrypoint | Current outcome | Scope | Upstream test |
|---|---|---|---|
| [00_getting_started/ 00_hello_world.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/00_getting_started/00_hello_world.py) | Scoped assertions pass | Original scene, controller and assertions; no hardware calibration | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rigid.py) |
| [00_getting_started/ 01_core_concepts.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/00_getting_started/01_core_concepts.py) | Scoped assertions pass | Original scene, controller and assertions; no hardware calibration | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rigid.py) |
| [01_cloth/ 00_towel.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/01_cloth/00_towel.py) | Scoped assertions pass | MuJoCo/VBD one_way; cloth reactions are not applied to the arm | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_cloth.py) |
| [01_cloth/ 01_fabrics.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/01_cloth/01_fabrics.py) | Scoped assertions pass | Construction and 20 steps; no manipulation acceptance | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_new_examples.py) |
| [01_cloth/ 02_engines.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/01_cloth/02_engines.py) | Scoped assertions pass | Default Newton construction and 20 steps; not every external engine | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_examples.py) |
| [01_cloth/ 03_scrub_a_stain.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/01_cloth/03_scrub_a_stain.py) | Scoped assertions pass | one_way plus force readback only; stain removal is not calibrated wear | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_scrub_a_stain.py) |
| [01_cloth/ 04_your_own_cloth.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/01_cloth/04_your_own_cloth.py) | Scoped assertions pass | MuJoCo/VBD one_way; cloth reactions are not applied to the arm | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_cloth.py) |
| [02_soft/ 00_sponge.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/02_soft/00_sponge.py) | Scoped assertions pass | SuperDex soft body; lift/hold without latch, distinct from loaded wiping | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_soft.py) |
| [02_soft/ 01_tet_mesh.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/02_soft/01_tet_mesh.py) | Scoped assertions pass | Tetrahedral import; construction and 20 steps | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_examples.py) |
| [02_soft/ 02_your_own_soft.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/02_soft/02_your_own_soft.py) | Scoped assertions pass | Custom soft-body type; construction and 20 steps | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_new_examples.py) |
| [03_materials/ 00_rope.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/00_rope.py) | Scoped assertions pass | VBD contact history and sticky contact; gripper friction 60 | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rope.py) |
| [03_materials/ 01_rope_memory.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/01_rope_memory.py) | Scoped assertions pass | Friction grasp and plastic memory; elastic negative control retained separately | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_cable_robot.py) |
| [03_materials/ 02_twist.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/02_twist.py) | Scoped assertions pass | Friction-driven twist; stiff-rope slipping is an expected control outcome | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_cable_robot.py) |
| [03_materials/ 03_knot.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/03_knot.py) | Scoped assertions pass | SuperDex with reaction feedback off; no-self-contact negative control retained | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_knot_pull.py) |
| [03_materials/ 04_band.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/04_band.py) | Scoped assertions pass | SuperDex closed-loop rope, reaction feedback off; broken-band control retained | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_band_on_pegs.py) |
| [03_materials/ 05_paper.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/05_paper.py) | Scoped assertions pass | VBD one_way plus slide_feedback; prismatic-joint feedback gives no net arm reaction | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_fold_paper_robot.py) |
| [03_materials/ 06_bag.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/06_bag.py) | Scoped assertions pass | SuperDex self-contacting shell; grasp does not pin nodes | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_open_a_bag.py) |
| [03_materials/ 07_brush.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/07_brush.py) | Scoped assertions pass | Original brushing task and local cleaning model | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_scrub_bench.py) |
| [03_materials/ 08_tape.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/08_tape.py) | Scoped assertions pass | 30 g rigid pull tab attached to cloth; not direct thin-film grasping | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_peel_a_label.py) |
| [03_materials/ 09_adhesion.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/09_adhesion.py) | Scoped assertions pass | Original adhesion and pressing task; no calibration to real adhesive | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_stick_a_label.py) |
| [03_materials/ 10_cutting.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/10_cutting.py) | Scoped assertions pass | Original cutting model; blunt-blade negative control retained | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_cut_tofu.py) |
| [03_materials/ 11_granular.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/11_granular.py) | Scoped assertions pass | MPM grains; original rice-sweeping task | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_sweep_rice.py) |
| [03_materials/ 12_liquid.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/12_liquid.py) | Scoped assertions pass | MPM viscous liquid; grasp and tilt a cup | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_pour_honey.py) |
| [03_materials/ 13_dough.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/13_dough.py) | Scoped assertions pass | MPM plasticity; retained deformation after pressing | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_press_dough.py) |
| [03_materials/ 14_water.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/14_water.py) | Scoped assertions pass | Genesis SPH cup pouring; shallow-tilt and offset negative controls retained | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_pour_water.py) |
| [04_extending/ 00_add_a_robot.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/04_extending/00_add_a_robot.py) | Scoped assertions pass | Original scene, controller and assertions; no hardware calibration | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rigid.py) |
| [04_extending/ 01_new_kind.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/04_extending/01_new_kind.py) | Scoped assertions pass | Custom chain type; construction and 20 steps | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_examples.py) |
| [04_extending/ 02_suction.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/04_extending/02_suction.py) | Scoped assertions pass | Default suction weld; separate wrench load-threshold checks, not pure friction | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_suction_pick.py) |
| [05_studio/ 00_your_own_panel.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/05_studio/00_your_own_panel.py) | Scoped assertions pass | Original scene, controller and assertions; no hardware calibration | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rigid.py) |
| [05_studio/ 01_render.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/05_studio/01_render.py) | Scoped assertions pass | Still/video file validity, not visual control | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_new_examples.py) |
| [06_tasks/ 00_your_first_task.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/00_your_first_task.py) | Scoped assertions pass | Original scene, controller and assertions; no hardware calibration | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rigid.py) |
| [06_tasks/ 01_goals_and_rewards.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/01_goals_and_rewards.py) | Scoped assertions pass | Goal evaluation tutorial, not a manipulation episode | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [06_tasks/ 02_episodes.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/02_episodes.py) | Scoped assertions pass | Initial-state sampling/reset tutorial | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [06_tasks/ 03_granular_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/03_granular_scored.py) | Scoped assertions pass | Original task-goal assertions | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_sweep_rice.py) |
| [06_tasks/ 04_brush_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/04_brush_scored.py) | Scoped assertions pass | Original task-goal assertions | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_scrub_bench.py) |
| [06_tasks/ 05_suction_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/05_suction_scored.py) | Scoped assertions pass | Original task-goal assertions with suction retention | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_suction_pick.py) |
| [06_tasks/ 06_bag_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/06_bag_scored.py) | Scoped assertions pass | Original task-goal assertions | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_open_a_bag_scored.py) |
| [06_tasks/ 07_band_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/07_band_scored.py) | Scoped assertions pass | Original task-goal assertions | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_band_on_pegs.py) |
| [06_tasks/ 08_tape_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/08_tape_scored.py) | Scoped assertions pass | Original task-goal assertions; rigid pull tab | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_peel_a_label_scored.py) |
| [06_tasks/ 09_cutting_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/09_cutting_scored.py) | Scoped assertions pass | Original task-goal assertions | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_cut_tofu_scored.py) |
| [06_tasks/ 10_water_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/10_water_scored.py) | Scoped assertions pass | Original task-goal assertions | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_pour_water.py) |
| [07_policies/ 00_pick_and_place.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/07_policies/00_pick_and_place.py) | Scoped assertions pass | Fixed GaP action graph; no training | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [07_policies/ 01_check_and_retry.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/07_policies/01_check_and_retry.py) | Scoped assertions pass | Fixed GaP graph; at least 3 successes in 4 episodes | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [07_policies/ 02_without_privilege.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/07_policies/02_without_privilege.py) | Scoped assertions pass | Example camera perception graph; not a general visual policy | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [07_policies/ 03_many_worlds.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/07_policies/03_many_worlds.py) | Scoped assertions pass | Fixed graph; at least 14 successes in 16 worlds | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [08_demos/ fold_the_towel/ fold_the_towel.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/fold_the_towel/fold_the_towel.py) | Scoped assertions pass | one_way; documented model/geometry differences from the paper reference | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_demo_fold_the_towel.py) |
| [08_demos/ route_the_cable/ route_the_cable.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/route_the_cable/route_the_cable.py) | Scoped assertions pass | Friction and contact history, gripper friction 60; port orientation differs from reference | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_demo_route_the_cable.py) |
| [08_demos/ wipe_the_bar/ wipe_the_bar.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/wipe_the_bar/wipe_the_bar.py) | Scoped assertions pass | Latch-assisted retention after contact readiness; not pure-friction wiping | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_demo_wipe_the_bar.py) |
| [09_teleop/ 00_leader_arm.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/09_teleop/00_leader_arm.py) | Scoped assertions pass | Mocked hardware and simulated follower grasp checks; no hardware motion | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_teleop_examples.py) |
| [09_teleop/ 01_force_feedback.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/09_teleop/01_force_feedback.py) | Scoped assertions pass | Mocked force-feedback interface; no hardware force-feedback acceptance | [Original test](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_teleop_examples.py) |

## Paper showcases and public examples have different denominators

The README splash description separately mentions 48 tasks, but no one-to-one executable manifest for that number was found in the inspected public checkout. The 50 entrypoints, 18 paper showcases and splash count are not interchangeable.

[Paper v2, Figure 5](https://arxiv.org/pdf/2610.18835v2) shows 18 tasks. The frozen public repository has 50 executable example entrypoints and 12 helpers; these are not the same set. No shipped `.task`/`.suite` task content or additional configured task roots were found. The four related public demonstrations below explicitly differ from the paper/reference scenes and cannot establish exact reproduction.

The project website's old pipeline has drivers but depends on unavailable gallery recordings and side directories. Its README-linked `robosimstudio/demo` repository returns 404; this does not reveal whether it is private or removed. All 18 exact paper-scene identities remain unverified and blocked by unavailable scenes/original data, rather than classified as solver failures.

| Paper showcase | Related accessible code |
|---|---|
| Tool sorting | Website syringe driver; original scene/data unavailable |
| Sharps disposal | Syringe driver describes tool_sort/syringe into a sharps box; paper identity unverified |
| Basket packing | Complete scene/acceptance entry not located |
| Gear meshing | Website gears driver; original scene/data unavailable |
| Tool hanging | Website scissors driver; original scene/data unavailable |
| Plate racking | Website plates driver; original scene/data unavailable |
| USB-C insertion | Website USB-C driver; original scene/data unavailable |
| Cable routing | Website weave driver; related public route-the-cable example |
| Drawer unlocking | Complete scene/acceptance entry not located |
| Conduit threading | Website conduit driver; original scene/data unavailable |
| Crate flipping | Website crate driver; original scene/data unavailable |
| Leaf pressing | Complete scene/acceptance entry not located |
| Towel folding | Website towel driver; related public fold-the-towel example |
| Phone film peeling | Website peel driver; public tape example uses a rigid tab |
| Carton tape cutting | Complete scene/acceptance entry not located |
| Sponge wiping | Website wipe driver; related public wipe-the-bar example |
| Strip polishing | Complete scene/acceptance entry not located |
| Heat transfer printing | Complete scene/acceptance entry not located |

The website's separate prerecorded interaction pipeline explicitly latches the film tab, maintains ParticleDragger pins for the towel, and pins the whip. Its README distinguishes that pipeline/site from the currently published www frontend. These source facts do **not** establish how every current published video was produced. Neither rendered appearance nor unavailable state provenance proves friction-only retention.

Sources: [public demo differences](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/README.md), [website README](https://github.com/robosimstudio/robosimstudio.github.io/blob/47b0796e9bc41103c05d089cb3aeb483ebd40b76/README.md), [reconstruction dependency](https://github.com/robosimstudio/robosimstudio.github.io/blob/47b0796e9bc41103c05d089cb3aeb483ebd40b76/pipeline/demos/_bench.py), [film pipeline](https://github.com/robosimstudio/robosimstudio.github.io/blob/47b0796e9bc41103c05d089cb3aeb483ebd40b76/pipeline/demos/peel.py).

The pipeline also preserves author-reported historical regressions. The conduit driver says the rebuilt scene changed from 54 to 59 bodies; two 30 September attempts failed acquisition or advanced only 21 mm. The weave driver says the old weave5 scene was replaced; the nearest port_medium variant completed three of four pegs and missed the port, reward 0.5. These are reported scene/controller regressions, not local reproductions or uniquely attributed solver defects. Sources: [conduit](https://github.com/robosimstudio/robosimstudio.github.io/blob/47b0796e9bc41103c05d089cb3aeb483ebd40b76/pipeline/demos/conduit.py), [weave](https://github.com/robosimstudio/robosimstudio.github.io/blob/47b0796e9bc41103c05d089cb3aeb483ebd40b76/pipeline/demos/weave.py).


## All existing evidence directories

The following 30 directories were reviewed at DexLab `c0c0aa6`. They include successful controls, rejected records and incomplete qualification. This is a review of existing evidence, not a new execution of every historical trajectory.

| Evidence directory | Assessment |
|---|---|
| cloth-studio | Old online grasp criteria passed despite table intrusion found by a separate geometry check; later settling development is a separate cohort. |
| cutting | Index and presentation of synthetic TLMPM references; not an additional six-engine comparison. |
| drake-contact-paths | Six contact paths. Lagged friction is explained by its previous elastic normal force; five small impulse discrepancies remain unresolved. |
| drake-incline | Historical kLagged/hydroelastic configuration passes 6/9; later path diagnostics explain part of its difference from ideal Coulomb friction. |
| elastic-impact | MuJoCo 3.15 passes 18/18 terminal checks; these do not check every intermediate penetration. |
| engine-qualification | Version/API admission; MuJoCo 3.16 cloth settling still exposes local table intrusion. |
| force-limit | Low actuator force fails retention; larger force holds and releases. Expected load failure, not a solver defect. |
| framework-mjwarp | Native and wrapper paths remain different after core/parameter alignment; unique cause unresolved. |
| genesis-cloth | Missing legacy PBD–rigid tangential friction, delayed reaction and failed cloth retention. |
| genesis-incline | Effective friction floor and numerical stopping effects are partly explained; failed configurations remain retained. |
| impact-discrete | 54/54 stored trajectories match the reconstructed discrete equations; this does not establish continuous-time physical accuracy. |
| impact-phase | 30/36 terminal passes but 14/36 joint passes; arrival phase matters. Nine records are reused history. |
| impact-stiffness | 24/27 terminal passes but 2/27 joint passes; stiffness, step size and penetration interact. Nine records are reused. |
| incline-comparison | Matched geometry, different contact models; no calibrated-material accuracy ranking. |
| incline-diagnosis | Twelve MuJoCo impratio diagnostics do not satisfy every frozen requirement. |
| incline-friction | Nine of eighteen MuJoCo configurations pass; soft-contact drift and sliding error retained. |
| libero | Task replay success and contact consistency differ. A stale post-settling observation is a wrapper defect, not a core solver defect. The 130-task parent scope remains incomplete. |
| mujoco-incline | Six fixed native configurations and numerical rejections; no universal inability claim. |
| newton-incline | Seven CPU FP32 profiles; 49 positive numerical/representation rejections. The engineering guard is not a derived floating-point error bound. |
| newton-xpbd | Sphere/plane positive, repeat and disabled-contact controls pass. |
| physx-incline | PGS/TGS fixed profiles, with thirteen positive numerical rejections; small TGS residuals are not fully explained. |
| pinch-impulse | Tighter stopping reduces force/momentum residual while creep persists. |
| pinch-load | Eighteen MuJoCo records: three passes, nine physical failures and six numerical rejections. |
| rss-wiping | Three matched original/no-latch pairs demonstrate retention assistance dependence. |
| studio | Replays existing records; creates no independent physical result. |
| superdex-incline | Twelve configurations retain static creep; some CG steps stop without closure. BFGS/SR1 with assembly=1 do not constitute distinct effective methods here. |
| synthetic-tactile | Gravity compensation masks support in batch 1; endpoint failure in batch 2; bounded success after settling in batch 3. Control/observation semantics, not validated tactile sensing. |
| unisim-contact-migration | Twenty-one native/adapter rescoring pairs agree, including low-force failures. |
| unisim-reuse | Native grasp, open-hand controls and force bookkeeping support adapter reuse, not a new solver. |
| visual | Media/state provenance, not additional task-success trials. |

All directories: [frozen evidence tree](https://github.com/huangkiki/Dexlab/tree/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/docs/evidence).

## All 15 demo directories

| Demo directory | Assessment |
|---|---|
| apple-stem-grasp | Historical complete 14 s MuJoCo/SuperDex scripted checks; not Wuji in-hand or real-apple qualification. |
| banana-cut | Synthetic three-cut/four-piece TLMPM reference, with original failures retained. |
| banana-force | Sampling and sensitivity records exist; 64× particle run does not reach support within 0.5 s and fails acceptance. Normalized force RMSE 2.05054 is not convergence. |
| cloth-benchmark | Seven configurations, 105 historical trials; nominal materials are not calibrated equivalents. |
| cloth-folding | Old table intrusion and bimanual failures retained; a later 9 s single-grasp development passes. Bimanual folding remains unqualified. |
| contact-benchmark | Thirty-eight development experiments, twenty-five passes and thirteen failures; includes edge discretization, normal response, transient cost and transfer diagnostics. |
| cut-push | Blade-driven pushing with no-push and material controls; synthetic reference, not real-food accuracy. |
| cutting-refinement | Mechanical checks for refined tofu/banana scenes; no general material convergence claim. |
| libero-contact | Native demonstration-action replay and contact diagnostics; no trained-policy or real-robot result. |
| physx-contact | Native primitive contact checks pass; missing UniSim contact reporting was repaired in the adapter. Separate cloth records include surface crossing and unavailable force APIs. |
| rss-wiping | Matched latch ablation; compliant node assistance is neither friction-only grasping nor a rigid weld. |
| tofu-comparison | Historical two-cut and one-sided velocity diagnostic; a different protocol from blade pushing. |
| tofu-cut | Single cut with uncut/partial-cut controls and dynamic reaction. |
| tofu-knife-push | Four pushing/control conditions with matched pre-push states. |
| tofu-scoring | Shallow crossing cuts preserve connectivity, with uncut and continuous-cut controls; not arbitrary free-form cutting. |

[Demo source and reports](https://github.com/huangkiki/Dexlab/tree/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/demos). The eight registered research experiences map into these same records. In particular, the 30 fixed-parameter mass/size-transfer conditions produce one engineering pass and no joint transient pass; that is a parameter-transfer result, not proof that the engine cannot perform the tasks.

A separate output-lifecycle defect is tracked by [#243](https://github.com/huangkiki/Dexlab/issues/243): reusing the apple default output directory can mix a new manifest with an old success summary. This is an evidence-integrity risk, not a solver failure. No contamination of the published records reviewed here has been established; the issue remains open.
