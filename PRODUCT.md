# DexLab public website

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users and purpose

The primary reader researches robot learning or embodied intelligence. Their primary task is to read findings, understand the evidence and limits, and take away implications for their own research. Reading must not depend on installing an environment or rerunning an experiment. DexLab focuses on contact-rich manipulation, including grippers and dexterous hands. The research direction is reciprocal improvement: agent failures expose simulation gaps; improved simulation helps improve agents.

## Confirmed publishing brief

The November 2026 ten-question interview established these choices:

- Humans set goals and boundaries. Agents should both execute experiments and help discover questions, hypotheses and subsequent experiments. This is a direction, not a claim of completed autonomous RSI.
- Open with the research guide. Within each case, show the finding first, then its evidence, implications and scope. Keep task improvement supported by failure attribution. Installation and reproduction are optional deeper paths, not the homepage conversion goal.
- Keep README minimal: the project name, one-line RSI direction, the approved architecture image and a primary Blog link. Detailed findings, cases, learning and reproduction belong on the website.
- Give the website clear reading paths and explicit connections between questions, experiments, findings and further work. The learning-map reference is https://rl-robotics.github.io/. The homepage now follows the existing dexterous-simulation guide’s reading style: warm paper, serif opening title, restrained green links and quiet separators.
- Organize Blog articles around specific research questions, connected by persistent topics. Make the existing long-form research guide the main first-screen reading entry, with its full title and a direct link. Avoid unnecessary secondary labels and descriptions; let layout explain the hierarchy.
- Show the learning map, prerequisites and complete existing courses on this site. Reading links stay within DexLab; canonical learning repositories remain the authored sources and source-code references. Publish pinned snapshots through the shared documentation reader and sync upstream changes explicitly rather than editing two copies.
- This revision covers README and the website entrance. Existing articles, research evidence and technical documentation stay available; it is not a redesign of every report.

The learning entrance extends this reading identity with a MuJoCo-first, question-led route: foundations, stepping, contact, MuJoCo 4 changes, performance and diagnosis. It borrows the learning interaction logic of the [RL × Robotics introduction](https://rl-robotics.github.io/#/learn/intro): read, adjust an example, explain the result and continue. Native explanations, self-checks and explicit browser reading bookmarks support this route; bookmarks do not certify competence. Teaching calculations and sourced release changes remain distinct from native measurements. The existing detailed courses retain their pinned 3.15.0 baseline and stay available as deeper reading.

## Evidence and constraints

Wuji's existing point-versus-synthetic-torsional-contact comparison is the representative case. The report and original replay determine all claims and limitations. Do not present that controlled simulation experiment as an autonomous agent run, hardware calibration or general solver result. Keep both languages aligned, retain published anchors and reuse actual evidence assets. The browser claw machine remains accessible through the technical overview, outside the main research story.
