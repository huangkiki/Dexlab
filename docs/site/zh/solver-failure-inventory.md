# 求解器复盘完整清单

[回到结论](solver-failure-audit.md)

## RSS 全部 50 个公开入口

40 个入口有任务范围断言，10 个为教学、渲染或硬件 mock。目标评分与其对应场景可能共享一次回合，不是 50 种独立操作。以下通过仅指表中范围，预期失败负对照通过不等于操作成功。

| 入口 | 当前结果 | 验收范围与条件 | 上游测试 |
|---|---|---|---|
| [00_getting_started/ 00_hello_world.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/00_getting_started/00_hello_world.py) | 通过该范围断言 | 原版场景、控制与验收；非真机标定 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rigid.py) |
| [00_getting_started/ 01_core_concepts.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/00_getting_started/01_core_concepts.py) | 通过该范围断言 | 原版场景、控制与验收；非真机标定 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rigid.py) |
| [01_cloth/ 00_towel.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/01_cloth/00_towel.py) | 通过该范围断言 | MuJoCo/VBD one_way；手臂不接收布料反力 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_cloth.py) |
| [01_cloth/ 01_fabrics.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/01_cloth/01_fabrics.py) | 通过该范围断言 | 构建并走20步，不验收操作成功 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_new_examples.py) |
| [01_cloth/ 02_engines.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/01_cloth/02_engines.py) | 通过该范围断言 | 默认Newton；构建和20步检查，未穷举全部外部引擎 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_examples.py) |
| [01_cloth/ 03_scrub_a_stain.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/01_cloth/03_scrub_a_stain.py) | 通过该范围断言 | one_way + contact_forces只读回力；污渍模型不是物理磨损标定 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_scrub_a_stain.py) |
| [01_cloth/ 04_your_own_cloth.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/01_cloth/04_your_own_cloth.py) | 通过该范围断言 | MuJoCo/VBD one_way；手臂不接收布料反力 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_cloth.py) |
| [02_soft/ 00_sponge.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/02_soft/00_sponge.py) | 通过该范围断言 | SuperDex软体；无latch抬升保持，区别于承载擦拭 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_soft.py) |
| [02_soft/ 01_tet_mesh.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/02_soft/01_tet_mesh.py) | 通过该范围断言 | 四面体导入；构建和20步 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_examples.py) |
| [02_soft/ 02_your_own_soft.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/02_soft/02_your_own_soft.py) | 通过该范围断言 | 自定义软体类；构建和20步 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_new_examples.py) |
| [03_materials/ 00_rope.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/00_rope.py) | 通过该范围断言 | VBD历史接触＋sticky；mu_gripper=60 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rope.py) |
| [03_materials/ 01_rope_memory.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/01_rope_memory.py) | 通过该范围断言 | 机器人摩擦抓取，塑性记忆；弹性负对照另留 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_cable_robot.py) |
| [03_materials/ 02_twist.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/02_twist.py) | 通过该范围断言 | 机器人摩擦扭转；硬绳滑移是验收预期，不是失败 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_cable_robot.py) |
| [03_materials/ 03_knot.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/03_knot.py) | 通过该范围断言 | SuperDex，反馈关闭；自接触关闭负对照另留 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_knot_pull.py) |
| [03_materials/ 04_band.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/04_band.py) | 通过该范围断言 | SuperDex闭环绳；反馈关闭；断带负对照另留 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_band_on_pegs.py) |
| [03_materials/ 05_paper.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/05_paper.py) | 通过该范围断言 | VBD one_way＋slide_feedback；反馈只驱动滑动关节，整臂不受净反力 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_fold_paper_robot.py) |
| [03_materials/ 06_bag.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/06_bag.py) | 通过该范围断言 | SuperDex自接触薄壳；非固定节点抓取 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_open_a_bag.py) |
| [03_materials/ 07_brush.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/07_brush.py) | 通过该范围断言 | 原版刷擦任务与局部清洁模型 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_scrub_bench.py) |
| [03_materials/ 08_tape.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/08_tape.py) | 通过该范围断言 | 30g刚性拉片与布料连接；不是直接夹薄膜 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_peel_a_label.py) |
| [03_materials/ 09_adhesion.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/09_adhesion.py) | 通过该范围断言 | 原版黏附模型与按压任务；非真实胶材料标定 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_stick_a_label.py) |
| [03_materials/ 10_cutting.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/10_cutting.py) | 通过该范围断言 | 原版切割模型；刀钝负对照另留 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_cut_tofu.py) |
| [03_materials/ 11_granular.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/11_granular.py) | 通过该范围断言 | MPM颗粒；原版推米入托盘 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_sweep_rice.py) |
| [03_materials/ 12_liquid.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/12_liquid.py) | 通过该范围断言 | MPM黏性液体；夹杯倾倒 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_pour_honey.py) |
| [03_materials/ 13_dough.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/13_dough.py) | 通过该范围断言 | MPM塑性；按压后保留形变 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_press_dough.py) |
| [03_materials/ 14_water.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/03_materials/14_water.py) | 通过该范围断言 | Genesis SPH；夹杯倾倒；浅倾和偏移负对照另留 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_pour_water.py) |
| [04_extending/ 00_add_a_robot.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/04_extending/00_add_a_robot.py) | 通过该范围断言 | 原版场景、控制与验收；非真机标定 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rigid.py) |
| [04_extending/ 01_new_kind.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/04_extending/01_new_kind.py) | 通过该范围断言 | 自定义链条类；构建和20步 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_examples.py) |
| [04_extending/ 02_suction.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/04_extending/02_suction.py) | 通过该范围断言 | 吸盘默认weld保持；另有wrench负载阈值测试，非纯摩擦 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_suction_pick.py) |
| [05_studio/ 00_your_own_panel.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/05_studio/00_your_own_panel.py) | 通过该范围断言 | 原版场景、控制与验收；非真机标定 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rigid.py) |
| [05_studio/ 01_render.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/05_studio/01_render.py) | 通过该范围断言 | 图片/视频文件有效性，不是视觉控制 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_new_examples.py) |
| [06_tasks/ 00_your_first_task.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/00_your_first_task.py) | 通过该范围断言 | 原版场景、控制与验收；非真机标定 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_example_grasps_rigid.py) |
| [06_tasks/ 01_goals_and_rewards.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/01_goals_and_rewards.py) | 通过该范围断言 | 目标求值教学，不是操作回合 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [06_tasks/ 02_episodes.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/02_episodes.py) | 通过该范围断言 | 初态采样重置教学 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [06_tasks/ 03_granular_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/03_granular_scored.py) | 通过该范围断言 | 原版目标评分 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_sweep_rice.py) |
| [06_tasks/ 04_brush_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/04_brush_scored.py) | 通过该范围断言 | 原版目标评分 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_scrub_bench.py) |
| [06_tasks/ 05_suction_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/05_suction_scored.py) | 通过该范围断言 | 原版目标评分与吸附保持 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_suction_pick.py) |
| [06_tasks/ 06_bag_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/06_bag_scored.py) | 通过该范围断言 | 原版目标评分 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_open_a_bag_scored.py) |
| [06_tasks/ 07_band_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/07_band_scored.py) | 通过该范围断言 | 原版目标评分 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_band_on_pegs.py) |
| [06_tasks/ 08_tape_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/08_tape_scored.py) | 通过该范围断言 | 原版目标评分；刚性拉片 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_peel_a_label_scored.py) |
| [06_tasks/ 09_cutting_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/09_cutting_scored.py) | 通过该范围断言 | 原版目标评分 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_cut_tofu_scored.py) |
| [06_tasks/ 10_water_scored.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/06_tasks/10_water_scored.py) | 通过该范围断言 | 原版目标评分 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_pour_water.py) |
| [07_policies/ 00_pick_and_place.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/07_policies/00_pick_and_place.py) | 通过该范围断言 | 固定GaP动作图；不训练 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [07_policies/ 01_check_and_retry.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/07_policies/01_check_and_retry.py) | 通过该范围断言 | 固定GaP动作图；4回合至少3成功 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [07_policies/ 02_without_privilege.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/07_policies/02_without_privilege.py) | 通过该范围断言 | 示例相机感知图；不是通用视觉策略 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [07_policies/ 03_many_worlds.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/07_policies/03_many_worlds.py) | 通过该范围断言 | 固定图；16世界至少14成功 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_task_examples.py) |
| [08_demos/ fold_the_towel/ fold_the_towel.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/fold_the_towel/fold_the_towel.py) | 通过该范围断言 | one_way；模型/几何与论文参考存在明示差异 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_demo_fold_the_towel.py) |
| [08_demos/ route_the_cable/ route_the_cable.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/route_the_cable/route_the_cable.py) | 通过该范围断言 | 摩擦＋历史接触；mu_gripper60；端口方向与参考不同 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_demo_route_the_cable.py) |
| [08_demos/ wipe_the_bar/ wipe_the_bar.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/wipe_the_bar/wipe_the_bar.py) | 通过该范围断言 | 抓稳后latch辅助保持；非纯摩擦擦拭 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_demo_wipe_the_bar.py) |
| [09_teleop/ 00_leader_arm.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/09_teleop/00_leader_arm.py) | 通过该范围断言 | 硬件mock；另有模拟从臂抓取检查，无硬件动作 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_teleop_examples.py) |
| [09_teleop/ 01_force_feedback.py](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/09_teleop/01_force_feedback.py) | 通过该范围断言 | 力反馈接口mock；不构成真机力反馈验收 | [原版测试](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/tests/test_teleop_examples.py) |

## 论文场景与公开入口的范围差异

README 展示图的说明另写有 48 个任务，但所查公开 checkout 没有与该数字一一对应的可执行任务清单。50 个入口、18 个论文展示和这个图注数字不能相互替代。

论文 v2 图5的18项展示，与当前公开 examples 的50个入口不是同一分母。公开 source 没有 .task/.suite 内容目录；任务教学使用内嵌字符串。项目网站仓库的 pipeline 提供部分旧场景驱动，但依赖缺失的 gallery 原始回合、phone_demo 等旁路目录；网站 README 链接的 robosimstudio/demo 当前 API 返回404，不能据此判断私有还是已移除。公开示例只是部分同类重建，不能冒称精确复现全部论文场景。

| 论文展示任务 | 公开代码可支持的核查 | 本轮处理 |
|---|---|---|
| 工具归类 | 网站管线有驱动 syringe.py，依赖未发布场景/数据 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 锐器投放 | syringe.py 描述 tool_sort/syringe 投入锐器盒，论文身份仍未核对 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 篮子装载 | 未找到该完整场景与验收入口 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 齿轮啮合 | 网站管线有驱动 gears.py，依赖未发布场景/数据 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 工具悬挂 | 网站管线有驱动 scissors.py，依赖未发布场景/数据 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 盘子上架 | 网站管线有驱动 plates.py，依赖未发布场景/数据 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 插接USB-C | 网站管线有驱动 usbc.py，依赖未发布场景/数据 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 线缆布线 | 网站管线有驱动 weave.py，依赖未发布场景/数据；同类公开示例 examples/08_demos/route_the_cable/route_the_cable.py | 精确论文场景阻塞；保留来源，不记solver失败 |
| 抽屉解锁 | 未找到该完整场景与验收入口 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 穿过导管 | 网站管线有驱动 conduit.py，依赖未发布场景/数据 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 翻转箱体 | 网站管线有驱动 crate.py，依赖未发布场景/数据 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 按压叶片 | 未找到该完整场景与验收入口 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 毛巾折叠 | 网站管线有驱动 towel.py，依赖未发布场景/数据；同类公开示例 examples/08_demos/fold_the_towel/fold_the_towel.py | 精确论文场景阻塞；保留来源，不记solver失败 |
| 手机揭膜 | 网站管线有驱动 peel.py，依赖未发布场景/数据；同类公开示例 examples/03_materials/08_tape.py | 精确论文场景阻塞；保留来源，不记solver失败 |
| 割开纸箱胶带 | 未找到该完整场景与验收入口 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 海绵擦拭 | 网站管线有驱动 wipe.py，依赖未发布场景/数据；同类公开示例 examples/08_demos/wipe_the_bar/wipe_the_bar.py | 精确论文场景阻塞；保留来源，不记solver失败 |
| 条带抛光 | 未找到该完整场景与验收入口 | 精确论文场景阻塞；保留来源，不记solver失败 |
| 热转印 | 未找到该完整场景与验收入口 | 精确论文场景阻塞；保留来源，不记solver失败 |

网站另有交互预录管线，peel 明示 latch，towel 维护 ParticleDragger，whip 固定绳子。代码和 README 把这套 pipeline/site 与当前发布的 www 页面分开；这些事实不能自动证明当前网页的每一个视频用了相同夹持方式。已发布视频缺少原始轨迹/场景身份时，不从画面推断纯摩擦成功。

来源：[论文 v2 图 5](https://arxiv.org/pdf/2610.18835v2)、[公开示例与原场景差异](https://github.com/robosimstudio/robosimstudio/blob/b001cc7e10a83577261aac4471fa45e0ced6d415/examples/08_demos/README.md)、[网站 README](https://github.com/robosimstudio/robosimstudio.github.io/blob/47b0796e9bc41103c05d089cb3aeb483ebd40b76/README.md)、[重建数据依赖](https://github.com/robosimstudio/robosimstudio.github.io/blob/47b0796e9bc41103c05d089cb3aeb483ebd40b76/pipeline/demos/_bench.py)、[揭膜管线](https://github.com/robosimstudio/robosimstudio.github.io/blob/47b0796e9bc41103c05d089cb3aeb483ebd40b76/pipeline/demos/peel.py)。

网站管线还保留了作者报告的历史回归：conduit.py 记载场景从 54 变为 59 个刚体后，2026-09-30 两次新运行未夹住或仅前进 21 mm；weave.py 记载旧 weave5 被替换，近似 port_medium 只完成四个绕柱中的三个且未插入端口，reward 0.5。这些是作者记录的场景/控制回归，不是本轮独立重现，也未定位为 solver 缺陷。来源：[conduit](https://github.com/robosimstudio/robosimstudio.github.io/blob/47b0796e9bc41103c05d089cb3aeb483ebd40b76/pipeline/demos/conduit.py)、[weave](https://github.com/robosimstudio/robosimstudio.github.io/blob/47b0796e9bc41103c05d089cb3aeb483ebd40b76/pipeline/demos/weave.py)。


## 全部既有证据目录

目录来源：[冻结的证据树](https://github.com/huangkiki/Dexlab/tree/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/docs/evidence)、[全部 demo](https://github.com/huangkiki/Dexlab/tree/c0c0aa6e2a99c22d07ea4caddab7a427b35e10a3/demos)。以下路径均相对仓库根；“不构成solver失败”也属于本轮结论，不能删除这些成功或反例。

| docs/evidence目录 | 已有结果与本轮判断 | 归因层级 |
|---|---|---|
| cloth-studio | 旧夹布在线协议通过，但独立桌面几何检查揭示侵入；后续settling开发记录单独通过。旧评分不能当完整几何有效性 | 评分范围/碰撞几何，见cloth-folding |
| cutting | 各切割demo的展示与参考索引；与下表合并解读，不重复计数 | 自建TLMPM参考，不是六引擎横评 |
| drake-contact-paths | 6种路径，正例通过0–6/9；5条微小冲量残差未解释。Lagged摩擦逐面公式重构误差约1e-13N，解释额外切向支撑 | 接触模型机制 + 未解数值残差 |
| drake-incline | 历史kLagged/hydroelastic 6/9；滑动不符理想Coulomb，后续路径诊断承接 | 历史配置失败 |
| elastic-impact | MuJoCo3.15最初18/18终态通过 | 有限终态检查成功 |
| engine-qualification | 版本/API/原生路径准入；3.16布料静置第45个采样出现桌面侵入，不能说新版本已修好 | 准入与局部几何诊断 |
| force-limit | Genesis刚体0.2/0.4N不保持，0.8/10N保持释放 | 受限驱动力造成合理任务失败，非solver缺陷 |
| framework-mjwarp | 原生与框架参数/核心对齐后仍有轨迹与一致性差异；根因未唯一确定 | 框架路径/配置，不直接判核心算法 |
| genesis-cloth | 上述无切向摩擦、延迟动量；重力补偿后抬升79.988mm而布料仍在4mm高度，保持失败 | 最强局部耦合机制证据 |
| genesis-incline | Signorini6/9；convex3/9；其余0/9，7条CG一致性拒绝。零摩擦下限和停止条件已部分定位 | 接触表达/停止精度 |
| impact-discrete | 54/54原轨迹通过逐步离散方程重构 | 说明与离散模型一致，不等于连续物理精确 |
| impact-phase | 36条含9历史复用；终态30通过，联合穿透检查14通过 | 接触到达相位/离散误差 |
| impact-stiffness | 27条含9复用；终态24通过，联合检查2通过 | 刚度、步长与穿透的共同影响 |
| incline-comparison | MuJoCo/SuperDex同几何不同接触模型；保留各9条件，无同材料精度排名 | 固定配置比较 |
| incline-diagnosis | MuJoCo12条impratio诊断0全通过 | 单一参数调节不能消除整套要求失败 |
| incline-friction | MuJoCo18条9通过；软接触静漂与滑动误差保留 | 模型/配置失败 |
| libero | 数据集任务可成功但接触诊断失败；已定位settling后陈旧观测4.481mm，非核心solver证据。未完成的LIBERO父范围仍未完成 | 封装缺陷与物理诊断分开 |
| mujoco-incline | 6配置，elliptic各3/9，pyramidal各0/9；6条数值一致性拒绝未唯一归因 | 原生固定配置，不称普遍失效 |
| newton-incline | 7配置；XPBD/PADMM各1/9、DVI4/9，其余0；49正例及2负例被数值门禁拒绝。FP32门禁不是严格误差上界 | 数值/表示边界，不等于任务不可能 |
| newton-xpbd | 1.6.1球—平面正例、重复及禁用碰撞负例通过 | 成功的局部接触准入 |
| physx-incline | PGS两种各7/9，TGS两种各3/9；13正例数值门禁拒绝；TGS微小残差原因未完全解释 | 保留不确定性 |
| pinch-impulse | 6条诊断重现原始前缀；残差随停止容差下降，蠕滑未消除 | 数值闭合与物理保持分离 |
| pinch-load | MuJoCo18条：3通过、9物理失败、6数值拒绝；高阻抗减小蠕滑，临界载荷残差由后续诊断承接 | 固定夹具配置 |
| rss-wiping | 匹配3对latch对照；原版通过，无latch失败 | 辅助保持依赖，未唯一归因solver |
| studio | 从已有轨迹展示刚体/布料/力控结果 | 复用展示，不新增物理证据 |
| superdex-incline | 12配置：9种8/9、3种CG6/9；全部0.5ms静漂失败。CG部分步STOPPED且残差不闭合；BFGS/SR1当前assembly=1实际等效Newton | 摩擦正则化/数值停止/有效配置身份 |
| synthetic-tactile | 三批：重力补偿掩盖支撑→端点误差→延长跟踪后局部通过 | 控制与观测语义，非接触力传感器真实性 |
| unisim-contact-migration | 21对原生/适配器重评分一致，包含保留低力失败 | 适配正确性不等于每次任务成功 |
| unisim-reuse | 原生夹持与开爪负对照、力账本通过；框架修补另记 | 包装层可复用，不是新solver能力 |
| visual | 首页/视频来源与匹配回放记录 | 视觉证据来源，不新增任务成功 |

## 全部15个demo目录

| demo | 结论 / 关联 |
|---|---|
| apple-stem-grasp | MuJoCo/SuperDex完整14s脚本开发记录通过；不是Wuji手内操作或真实苹果标定 |
| banana-cut | 合成香蕉连续三刀、四段机械分离；自建TLMPM，原始失败保留 |
| banana-force | 20采样及一因子敏感性完成；64×粒子版本0.5s内未触及支撑，验收失败，力曲线归一化RMSE2.05054；不能声称细化收敛 |
| cloth-benchmark | 七配置105条历史记录：MuJoCo4/15、SuperDex7/15、Newton四种8/15、Style3D9/15；材料未做等效标定，不能排名 |
| cloth-folding | 旧单手桌面侵入、旧双手应变/释放/终放失败；新9s单手开发协议通过。真正双手折叠仍未验收 |
| contact-benchmark | 38开发实验25通过13失败；SuperDex边缘离散敏感性；法向、瞬态、响应成本、质量尺寸迁移各有独立协议 |
| cut-push | 刀面连续推动与无推对照、黏性与纯弹性分开；数值抖动及缩步影响不能包装成真实食材精度 |
| cutting-refinement | 豆腐/香蕉细化记录逐项通过机械检查；历史粗网格保持原样；不是真实材料收敛认证 |
| libero-contact | 官方任务示范动作回放和物理诊断分开；无固定策略/真机闭环结论 |
| physx-contact | 三种原生基元接触通过；UniSim接触报告API缺失由适配器修补。另15布料：10通过、1表面穿越、4外力接口不支持 |
| rss-wiping | 见三对latch对照；latch是柔顺附加节点约束，不是纯摩擦，也不是刚性焊接 |
| tofu-comparison | 历史两刀+单侧初速度诊断；与当前刀推不同协议，不能混成同一对照 |
| tofu-cut | 单刀、未切/部分切负对照及动态反力；独立合成参考任务 |
| tofu-knife-push | 四组刀面推动、半步长与无推对照；推动前状态一致性已检查 |
| tofu-scoring | 两侧浅切保持连通、无切负对照与连续切割回归；不是任意姿态自由切割 |

## 8项研究经验与额外证据

normal-response、transient-cost、mass-size-transfer归入contact-benchmark：静态法向刚度可匹配但质量迁移需明确补偿；瞬态阻尼模型不等效；30个固定参数尺寸/质量迁移只1个工程通过、0个联合瞬态通过。physx-observation、pinch-load、six-engine-incline、framework-path、libero-workflow已逐项落到上述对应行。README与经验注册表不应把固定参数失败改写成引擎无法完成。

docs/evidence根目录还包含版本迁移、成本、框架和历史归档JSON，属于上述cohort的附属证据；本轮147个注册绑定全部一致。不宣称逐个重算每个压缩轨迹、审查每一行源码或重跑所有旧任务。

另有输出生命周期问题 [#243](https://github.com/huangkiki/Dexlab/issues/243)：重复使用苹果默认输出目录可能混合新 manifest 与旧成功报告。它是证据记录风险，不是 solver 失败；尚未发现本轮核查的已发布证据因此污染，该 Issue 保持开放。
