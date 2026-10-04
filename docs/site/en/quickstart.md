# Installation and first reproduction

## Historical demo environment

The released setup reproduces the original pinned environment, **not a latest-stable comparison environment**. [#41](https://github.com/huangkiki/Dexlab/issues/41) tracks the new qualification. Upgrading packages does not preserve an old validation claim automatically.

On Linux x86_64, install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
git clone https://github.com/huangkiki/Dexlab.git
cd Dexlab
bash scripts/setup.sh
bash demos/apple-stem-grasp/run.sh --backend mujoco
# Or use official SuperDex FP64
bash demos/apple-stem-grasp/run.sh --backend superdex
```

Add `--headless` without a display. SDF preparation and planning take time; a visible window does not establish physics acceptance. No model API key is required. Full experiments and bulk rendering run on the experiment server; desktop work is lightweight and resource-bounded.

## Evidence and acceptance

Retain configurations, actual joint/object states, native contacts, independent scores, logs and continuous close-ups. Acceptance requires complete lift, support, retention, penetration and momentum checks, not a final pose or GIF.

[Detailed installation](https://github.com/huangkiki/Dexlab/blob/main/docs/installation.md) · [Commands and output directories](https://github.com/huangkiki/Dexlab/blob/main/demos/apple-stem-grasp/README.md) · [Asset terms and provenance](https://github.com/huangkiki/Dexlab/blob/main/docs/ASSETS.md)

## Build documentation only

This environment does not install DexLab, PyTorch, MuJoCo or robot assets:

```bash
uv venv --python 3.12 .venv-docs
uv pip install --python .venv-docs/bin/python -r docs/site/requirements.txt
.venv-docs/bin/python scripts/build_docs.py
.venv-docs/bin/python -m http.server 8000 --directory docs/_build/html
```

Open `http://localhost:8000`; Chinese is the default with an English switch. Warnings fail the build. No physics is executed.
