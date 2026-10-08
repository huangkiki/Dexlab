# Impact stiffness protocol

[English](impact-stiffness-protocol.md) | [简体中文](impact-stiffness-protocol.zh-CN.md)

This study adds a separate1mm overlap budget (1% diameter) to the unchanged v0.44.0 elastic final-state thresholds. It is an engineering geometry budget, not a measured material parameter or complete grasp acceptance.

Reuse9 published equal-mass cases at stiffness10000s^-2; run18 new cases at100000/1000000s^-2 × incident speeds0.5/1/2m/s × steps1/.5/.25ms. All other settings match the [elastic protocol](elastic-impact-protocol.md). Exact cases, baseline hashes and limits are in the [manifest](evidence/impact-stiffness/manifest.json). Official MuJoCo3.15.0 CPU FP64, Intel Core i9-14900K;16GiB/twoCPU/128tasks/swap0/1800s envelope, one exclusive research window, data-volume outputs. No formal development trial or outcome tuning.

Compare all27 cases using an engine-free report. Preserve original verdicts, then test the additional sampled full-rate geometric overlap limit. Report peak force with its timestep, signed impulse error, contact duration and setup/native/observation/total costs. Existing baseline timings belong to the previous sequential campaign on the same hardware; there is no timing randomization/repetition or established speedup. Three steps provide sensitivity, not a universal convergence order. No required positive joint result, no post hoc threshold relaxation.

Higher direct stiffness is an acceleration-space solver parameter, not material Young's modulus. The scale u/sqrt(k) is a diagnostic under the simple scalar compliant model; the full transient law is not independently validated here. Changing stiffness can reduce overlap while increasing discretization error. Verify both objectives rather than selecting only accurate endpoints.

Sources / 来源: [MuJoCo solver reference](https://mujoco.readthedocs.io/en/stable/modeling.html#reference), [OpenStax conservation](https://openstax.org/books/university-physics-volume-1/pages/9-4-types-of-collisions), [v0.44.0 evidence](https://github.com/huangkiki/Dexlab/releases/tag/v0.44.0).
