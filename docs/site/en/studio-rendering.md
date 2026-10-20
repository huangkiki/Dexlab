# Render recorded experiments

Studio replays make contact, material surfaces and object motion easier to see. They reuse saved states: rendering never advances a physics engine, changes a task score or repairs a failed grasp.

The homepage gathers the experiments in one preview table. Cut-push uses repaired linked-volume surfaces with RTX path tracing, and cloth uses the recorded mesh studio views. Rigid scenes use the official MuJoCo USD exporter and OVRTX path tracing. RSS uses its separately pinned upstream RTX replay. These are different presentation paths with explicit source records, not a claim of one unified physical model.

## Actual replay gallery

These 13 complete replays retain the source times and scale. Apple uses two independently verified 14 s regression records; the other scenes retain the published historical records. The six incline panels use the same body-follow camera, with world position printed below to retain the motion reference.

```{raw} html
<table><tr><th>Experiment</th><th>Replay</th><th>Video</th></tr>
<tr><td>Apple grasp: MuJoCo / SuperDex</td><td><a href="_static/studio/apple.mp4"><img src="_static/studio/apple.gif" width="500" alt="Apple grasp: MuJoCo / SuperDex"></a></td><td><a href="_static/studio/apple.mp4">MP4</a></td></tr>
<tr><td>Genesis: 0.4 N / 0.8 N limits</td><td><a href="_static/studio/pinch.mp4"><img src="_static/studio/pinch.gif" width="500" alt="Genesis: 0.4 N / 0.8 N limits"></a></td><td><a href="_static/studio/pinch.mp4">MP4</a></td></tr>
<tr><td>LIBERO demo 0</td><td><a href="_static/studio/libero.mp4"><img src="_static/studio/libero.gif" width="500" alt="LIBERO demo 0"></a></td><td><a href="_static/studio/libero.mp4">MP4</a></td></tr>
<tr><td>Six-engine incline</td><td><a href="_static/studio/incline.mp4"><img src="_static/studio/incline.gif" width="500" alt="Six-engine incline"></a></td><td><a href="_static/studio/incline.mp4">MP4</a></td></tr>
<tr><td>Initial / calibrated normal response</td><td><a href="_static/studio/normal.mp4"><img src="_static/studio/normal.gif" width="500" alt="Initial / calibrated normal response"></a></td><td><a href="_static/studio/normal.mp4">MP4</a></td></tr></table>
<p><a href="_static/studio/manifest.json">13-scene manifest</a></p>
```

[Cutting surface reconstruction](cutting-surface.md) and [cloth studio comparisons](cloth-comparison.md) retain their separate geometry and provenance. [RSS matched tiled/RTX views](rss-wiping.md) remain available.

## Replay a rigid scene

Use the optional render environment with Python 3.12, MuJoCo 3.12.0, OpenUSD, NumPy, Pillow, imageio/FFmpeg and OVRTX `0.4.0.346409`, plus an RTX-capable NVIDIA GPU/driver. These are display dependencies; each source record retains its original physics engine version. The first render includes shader and renderer startup costs.

```bash
PYTHONPATH=src python scripts/prepare_studio_replays.py apple PATH_TO_VERIFIED_RUN OUTPUT
PYTHONPATH=src python scripts/prepare_studio_replays.py pinch dev-cap-0.4 OUTPUT
PYTHONPATH=src python scripts/prepare_studio_replays.py incline INPUT_MAP_JSON OUTPUT
PYTHONPATH=src python scripts/prepare_studio_replays.py normal INPUT_MAP_JSON OUTPUT
```

The apple run contains `trajectory.npz`, `display.xml`, engine identity, a passing independent summary and its referenced assets. The input map resolves the immutable release records listed in the existing visual-comparison source manifest. Existing loaders check record hashes and published scores. Outputs must be new directories; add `--pilot` for beginning/middle/end frames.

LIBERO keeps an additional compatibility check. In its original MuJoCo 2.3.7 environment, freeze every recorded frame's native geometry:

```bash
python scripts/studio_libero_reference.py RAW_DIRECTORY REFERENCE.npz
```

Then, in the RTX environment:

```bash
PYTHONPATH=src python scripts/prepare_studio_replays.py libero RAW_DIRECTORY OUTPUT \
  --reference REFERENCE.npz
```

The adapter checks every mesh vertex in world coordinates at every source frame against the original runtime, with a 10 µm maximum tolerance. A mismatch stops rendering. The original robosuite collision group remains hidden as in the historical display.

## What changes in the picture

Three large area lights and ambient illumination replace the display lights. Geometry, textures and dimensions come from the saved scene; cameras follow the existing close-up or body-follow conventions. Frames select existing timestamps without interpolating motion. Shader materials describe appearance, not measured friction or compliance.

Each output includes `replay.mp4`, three stills, a USD stage and `provenance.json`: input and output hashes, frame indices/native timestamps, camera transforms, renderer settings, measured wall time and runtime transform readback. All exported object and camera matrices are checked at every rendered frame. Float normalization of quaternions is limited to `1e-14` during kinematics; original state arrays and source files remain unchanged. Path-tracing history resets for every frame and motion blur is disabled.

The reconstruction, lighting, denoising and 20 fps sampling are presentation choices. Fine penetration, force timing and task validity must be read from the original full-rate records and reports. Render time is not physics throughput or a real-time benchmark.
