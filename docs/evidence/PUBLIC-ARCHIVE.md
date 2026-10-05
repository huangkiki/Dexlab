# Historical cloth evidence: portable reproduction

[简体中文](PUBLIC-ARCHIVE.zh-CN.md)

<!-- repository-only:start -->
Download the [versioned evidence archive](https://github.com/huangkiki/Dexlab/releases/download/v0.19.1/dexlab-historical-evidence-v1.tar.gz).

<!-- repository-only:end -->
This bundle supplies the two previously missing raw cohorts: 105 material/cloth records and one robot-cloth record. It preserves every selected failure. The frozen historical scorer produces 52 passes and 53 failures for the cloth cohort, and `geometry_review_required` for robot-cloth. This is offline historical reproduction, not a new dynamics run or latest-stable qualification.

<!-- repository-only:start -->
All 106 record objects match after archive extraction; [verification report](public-archive-verification.json). Archive size: 655,361,836 bytes.

SHA-256: `09c4da563ffefa3635b0830d7b9334ab6f97e9f83e4f0fba731d56e9a349ad82`

<!-- repository-only:end -->
## Run without the repository or robot asset download

Extract the archive into `dexlab-historical-evidence-v1`. From its parent directory:

```bash
uv venv --python 3.12 .offline
uv pip install --python .offline/bin/python -r dexlab-historical-evidence-v1/requirements.txt
.offline/bin/python dexlab-historical-evidence-v1/reproduce.py \
  dexlab-historical-evidence-v1 --output historical-reproduction
```

Keep the environment and output outside the extracted bundle. The runner rejects missing, changed or undeclared files and symlinks, checks exact historical package versions, then uses only the included scoring code. It does not launch simulation. A successful exit requires equality of all 106 record objects with the frozen reference, including metrics, checks, failures and sample coverage. `verification.json` records the result; differences fail rather than overwrite the reference. No API key, UniLab installation or external robot assets are needed. The exact old MuJoCo version is necessary to read the recorded binary model; it is not recommended for new experiments.

## What changed for public distribution

Raw trajectories, contact records, scientific parameters and source snapshots retain their original bytes. Deployment commands, local installation origins and local suite filenames are removed from JSON metadata. Copied cohort receipts explicitly rebind hashes to these public files. The original tracked historical report is unchanged.

The robot binary model contains absolute asset paths. Its public projection replaces only strings in the native path table, preserving byte length and offsets. Every byte outside that table is identical; the official historical loader verifies that native numerical arrays are identical. This changes a model artifact, not MuJoCo source or binaries, geometry, contact parameters or recorded states.

`manifest.json` lists public hashes, original hashes and transformations. Original hashes record provenance; they cannot independently prove redacted content to a reader without the private original. The published archive hash anchors the distributed bundle. Third-party robot geometry retains the included OpenArm Apache-2.0 and Wuji MIT licenses and notices. No apple assets are included.

Geometry scoring also requires `trimesh==5.1.0`. This version is verified for public replay; the original historical environment field did not record a trimesh version, so this additional pin is not an original runtime record.

## Limits

The scorer snapshot matches the 61 source hashes in the historical report and uses its recorded NumPy, SciPy and MuJoCo versions. Later robot-cloth scoring requires additional floor evidence that this old record does not contain. Reproducing its historical assessment does not grant a pass under the newer protocol. The newer repaired development case and its limits remain a separate result. These data do not establish material calibration, hardware accuracy or engine superiority.
