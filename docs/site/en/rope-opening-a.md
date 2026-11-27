# Opening A with libuipc

Two palm guides move apart and spread an already-threaded rope loop into two nearly horizontal strands. libuipc computes the stretch, bending, self-contact and guide contact. The rope has 160 vertices and zero fixed vertices. The replay projects its recorded centerline and draws hand illustrations at the measured guide centers.

```{raw} html
<video controls playsinline preload="metadata" width="1280" height="720"
       style="width:100%;height:auto" poster="_static/rope-opening-a/opening-a.png"
       aria-label="Opening A replay from the libuipc rope trajectory">
  <source src="_static/rope-opening-a/opening-a.mp4" type="video/mp4">
  <a href="_static/rope-opening-a/opening-a.mp4">Download the Opening A replay</a>
</video>
```

## What ran on the RTX 4090

libuipc 0.0.30 ran 240 steps at 120 Hz. The rope uses axial Hookean elasticity and Kirchhoff bending. The schematic palms use smooth, grooved affine-body guides with IPC contact and friction. The guides move apart for 1.2 s and then hold. The independent scorer checks the 49 sampled states from 1.6 to 2.0 s, including both endpoints.

| Check | Rope–guide contact enabled | Acceptance |
| --- | --- | --- |
| Rope topology | One closed loop | One connected cycle |
| Minimum guide separation | 490.0 mm | ≥ 440 mm |
| Minimum reach outside both guide centers | 27.7 mm | ≥ 18 mm |
| Strands through each of nine vertical sections | Two | Two in every hold frame |
| Vertical separation | 79.91–79.96 mm | 45–100 mm |
| Largest strand deviation from its chord | 1.46 mm | ≤ 6 mm |
| Peak absolute edge strain over all frames | 0.79% | ≤ 10% |

The control reused the same loop, gravity, palm commands and rope self-contact, with only rope–guide contact disabled. Gravity pulled the loop down while the guides continued opening. By 0.217 s its highest vertex was 50.0 mm below the original guide centers, at a guide span of 388.7 mm. With contact enabled the highest vertex was 40.0 mm above those centers at the same time. The disabled-contact loop lost the guides and failed the two-strand hold check.

This scene covers the opening pose from a pre-threaded loop with scripted palm motion. Finger pickups, hand articulation and real-string material calibration are outside this run.

{download}`Replay MP4 <../../evidence/rope-opening-a/opening-a.mp4>` · {download}`Metrics and hashes <../../evidence/rope-opening-a/metrics.json>` · [Raw trajectories and settings](https://github.com/huangkiki/Dexlab/releases/tag/milestone-2026-11-27-libuipc-opening-a)

## Reproduce

From the DexLab checkout, install Python 3.12, a compatible NVIDIA CUDA driver and FFmpeg with libx264. The optional package extra is `dexlab[uipc]`. The standalone commands below isolate the demo dependencies.

```bash
uv venv --python 3.12 .venv-uipc
uv pip install --python .venv-uipc/bin/python 'pyuipc==0.0.30' 'Pillow>=10.1'
.venv-uipc/bin/python demos/rope-opening-a/simulate.py rope-contact-on
.venv-uipc/bin/python demos/rope-opening-a/evaluate.py rope-contact-on/trajectory.npz
.venv-uipc/bin/python demos/rope-opening-a/render.py rope-contact-on/trajectory.npz rope-replay
.venv-uipc/bin/python demos/rope-opening-a/simulate.py rope-contact-off --no-guide-contact
.venv-uipc/bin/python demos/rope-opening-a/evaluate.py rope-contact-off/trajectory.npz
```

Use fresh output directories. The final command exits with code 1 for the expected failed hold.

[Demo source](https://github.com/huangkiki/Dexlab/tree/main/demos/rope-opening-a) · [libuipc 0.0.30](https://github.com/spiriMirror/libuipc/releases/tag/v0.0.30)
