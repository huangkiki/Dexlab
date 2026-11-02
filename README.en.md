# DexLab

**Robot manipulation involving contact, deformation and material separation.** DexLab uses fixed tasks, native contact records and independent scoring to distinguish failures caused by policies, scene configuration and physical computation.

[简体中文](README.md) · [Documentation](https://huangkiki.github.io/Dexlab/en/latest/) · [Experiments](https://huangkiki.github.io/Dexlab/en/latest/experiments.html) · [Paper guide](https://huangkiki.github.io/Dexlab/en/latest/newton-reading-guide.html) · [Quick start](#quickstart)

## Experiment previews

These animations come from DexLab simulation recordings or recorded-state replays. Every result applies only to its reported version, material assumptions, and acceptance protocol.

<table>
<tr>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/en/latest/wuji-contact.html">
<img src="docs/evidence/wuji-contact/comparison.gif" width="100%" alt="Wuji point contact and torsional contact comparison" loading="lazy">
</a>
<strong>Grasp and slip resistance</strong><br>
Under the same control, replacing point contact with synthetic torsional contact reduces two-second hold drift from <strong>2.734 mm</strong> to <strong>1.025 mm</strong>.
</td>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html">
<img src="docs/evidence/studio/rss.gif" width="100%" alt="Assisted sponge wiping replay" loading="lazy">
</a>
<strong>Sponge wiping and grasp dependence</strong><br>
Assisted retention passes <strong>3/3</strong>; removing assistance gives <strong>0/3</strong>, with final cleaning around <strong>95.47% / 39.92%</strong>.
</td>
</tr>
<tr>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/en/latest/cloth-comparison.html">
<img src="demos/cloth-folding/media/compliance-grasp.gif" width="100%" alt="Robot grasping a deformable cloth in recorded simulation" loading="lazy">
</a>
<strong>Deformable manipulation</strong><br>
The robot can pinch and move a cloth patch, but complete folding still fails: the current record reaches <strong>12.55%</strong> edge strain against a 5% limit.
</td>
<td width="50%">
<a href="https://huangkiki.github.io/Dexlab/en/latest/cut-push.html">
<img src="docs/evidence/cutting/showcase.gif" width="100%" alt="Tofu and banana cutting recorded-state surface replay" loading="lazy">
</a>
<strong>Cutting and topology change</strong><br>
Continuous cutting and blade-face pushing change the simulated topology; the full report records contact force, material separation, and retained failures beyond the visual replay.
</td>
</tr>
</table>

<a id="quickstart"></a>
## Quick start

The shortest simulation entry is apple-stem grasping. On Linux x86_64 with [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh --mujoco-profile historical-3.11.0
bash demos/apple-stem-grasp/run.sh \
  --backend mujoco \
  --output demos/apple-stem-grasp/runs/first-mujoco
.venv/bin/python demos/apple-stem-grasp/src/verify_sdf_grasp.py \
  demos/apple-stem-grasp/runs/first-mujoco
```

The verifier writes `summary.json`; when all checks pass, `passed: true`. Fourteen seconds is simulation time, not expected wall time. Add `--headless` without a display and use a fresh output directory for every run.

To inspect the evidence chain without installing a simulator, start with the [GPU-free wiping rescore](https://huangkiki.github.io/Dexlab/en/latest/rss-wiping.html#offline-evidence). Full dependencies, assets, and commands are in the [installation guide](https://huangkiki.github.io/Dexlab/en/latest/quickstart.html).

<a id="architecture"></a>
## Continue on the website

- [Research approach and architecture](https://huangkiki.github.io/Dexlab/en/latest/index.html#architecture): recording, attributing and rescoring failures, and the research direction of improving simulation and models together.
- [Results and failures](https://huangkiki.github.io/Dexlab/en/latest/results.html): full conditions, metrics, source evidence and reproduction paths.
- [Model-evaluation protocol](https://huangkiki.github.io/Dexlab/en/latest/model-evaluation.html): remote execution and public leaderboards remain under construction; [Uranus](https://huangkiki.github.io/Dexlab/en/latest/uranus-backend.html) is a documented candidate backend.
- [External references](https://huangkiki.github.io/Dexlab/en/latest/references.html): topic guides for all 35 Newton papers, the full bibliography and other research references.

Results apply to their stated configurations and protocols; they do not establish hardware validity or a universal engine ranking. The website maintains research and usage details. [Contributing](https://huangkiki.github.io/Dexlab/en/latest/contributing.html) · [Current work](docs/current-work.md) · [Citation](https://huangkiki.github.io/Dexlab/en/latest/index.html#documentation-and-citation).
