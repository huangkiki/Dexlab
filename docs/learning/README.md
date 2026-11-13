# Course publication sources

DexLab publishes the existing Sim Learning and six engine courses in its shared
documentation reader. The files in the seven course folders are unedited upstream
snapshots, with the upstream Apache-2.0 licenses and third-party notices retained.
`sources.json` records the repository, exact revision and SHA-256 of every file.
It is a publication snapshot, not a separate authored course.

`scripts/build_docs.py` verifies the snapshots and generates the Chinese and
English reading routes in `docs/site/{zh,en}/learn/`. These generated directories
are ignored by Git. Course text remains primarily Chinese in both shells, with
an explicit notice in English. Sphinx supplies search, contents, responsive
reading, math, code formatting and language switching. GitHub Markdown syntax
and relative/cross-course reading links are adapted without editing the originals.
Historical pinned citations keep their original version; official references and
source-code links stay at their source.

To restore a frozen snapshot (requires the authenticated GitHub CLI):

```bash
python scripts/sync_learning.py
```

To publish upstream course changes, explicitly update the selected source:

```bash
python scripts/sync_learning.py --repo mujoco --latest
python -m unittest tests.test_learning_docs
python scripts/build_docs.py
```

Review the source/manifest diff and rendered reading paths before publication.
Normal builds use only the committed snapshots and do not access GitHub. Diagram
and formula rendering uses the same browser-side pattern as the docs theme;
Mermaid is loaded only on pages containing diagrams, with the definition retained
if its renderer cannot load. Rebuilding courses does not run native simulations.
