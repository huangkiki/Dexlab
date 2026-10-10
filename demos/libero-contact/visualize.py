#!/usr/bin/env python3
"""Build the existing DexLab player bundle from full-rate LIBERO evidence."""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from dexlab.libero_workflow import file_hash
from visual_research import validate_bundle, write_json
from events import events


def build(campaign, media, demo, output):
    import numpy as np

    selection = json.loads((campaign / "selection.json").read_text())
    ids = ("baseline", selection["candidate"])
    rows = {}
    for path in sorted((campaign / "attempts").glob("*/result.json")):
        result = json.loads(path.read_text())
        if (
            result["demo"] == demo
            and result["candidate"]["id"] in ids
            and result["outcome"] == "recorded"
        ):
            rows[result["candidate"]["id"]] = (path, result)
    if set(rows) != set(ids):
        raise ValueError("Both complete action-executed records are required")
    identity = "libero-" + demo.replace("_", "")
    series, videos, entries = [], [], []
    duration = None
    for name in ids:
        path, result = rows[name]
        raw = path.parent / "raw"
        run = json.loads((raw / "run.json").read_text())
        with np.load(raw / "trajectory.npz", allow_pickle=False) as data:
            t0 = run["initial_time_s"]
            states = np.vstack((data["initial"], data["state"]))
            times = states[:, 0] - t0
            physics, measure = data["physics"], data["measurements"]
            configuration = f"LIBERO 8f1084e / robosuite 1.4.0 / MuJoCo 2.3.7 Newton elliptic / {name}"
            channels = [
                dict(
                    key="height",
                    unit="mm",
                    epoch="Recorded qpos, post-integration; native clock = display + 0.25 s",
                    points=np.column_stack(
                        (times, states[:, 1 + run["object_qpos_adr"] + 2] * 1000)
                    ).tolist(),
                ),
                dict(
                    key="gripper_relative_z",
                    unit="mm",
                    epoch="Native gripper-frame object z; pre-integration, includes rotation/release",
                    points=np.column_stack(
                        (measure[:, 0] - t0, measure[:, 9] * 1000)
                    ).tolist(),
                ),
                dict(
                    key="finger_normal",
                    unit="N",
                    epoch="Sum of native target/finger contact normals before integration; not drive command",
                    points=np.column_stack(
                        (physics[:, 0] - t0, physics[:, 15])
                    ).tolist(),
                ),
                dict(
                    key="contact_overlap",
                    unit="mm",
                    epoch="Maximum native contact penetration touching target before integration",
                    points=np.column_stack(
                        (physics[:, 0] - t0, physics[:, 16] * 1000)
                    ).tolist(),
                    reference=[[0, 1], [float(times[-1]), 1]],
                ),
            ]
        score = dict(
            result["score"],
            passed=result["score"]["physical_acceptance"] == "diagnostic-pass",
            record_valid=result["score"]["observation_valid"],
        )
        sources = [
            dict(
                path=f"cases/{name}-{demo}/{f}",
                sha256=file_hash(raw / f),
                url="https://github.com/huangkiki/Dexlab/releases/download/v0.60.0/libero-native-v1.tar.gz",
            )
            for f in ("trajectory.npz", "contacts.jsonl")
        ]
        item = dict(
            id=name,
            engine="MuJoCo",
            configuration=configuration,
            valid=score["record_valid"],
            verdict="pass" if score["passed"] else "fail",
            score=score,
            sources=sources,
            state_times_s=times.tolist(),
            channels=channels,
            missing_channels=[],
            effective_parameters=json.loads(
                (raw / "parameters-effective.json").read_text()
            ),
            events=events(raw),
        )
        series.append(item)
        entries.append({k: item[k] for k in ("id", "engine", "configuration")})
        stem = identity + "-" + name
        for suffix in (".mp4", ".png"):
            shutil.copyfile(media / (stem + suffix), output / (stem + suffix))
        frames = json.loads((media / (stem + ".frames.json")).read_text())
        if len(frames) != len(times) or not np.allclose(
            [f["native_time_s"] for f in frames], states[:, 0], atol=1e-10, rtol=0
        ):
            raise ValueError("Renderer mapping differs from recorded states")
        videos.append(
            dict(
                path=stem + ".mp4",
                poster=stem + ".png",
                sha256=file_hash(output / (stem + ".mp4")),
                poster_sha256=file_hash(output / (stem + ".png")),
                fps=20,
                series=[name],
                renderer="MuJoCo 2.3.7 mj_forward only; no integration",
                camera=dict(
                    lookat=[0, 0, 0.13], distance=1.35, azimuth=135, elevation=-45
                ),
                frames=[
                    dict(
                        frame=f["frame"],
                        time_s=f["time_s"],
                        samples={
                            name: dict(
                                index=f["state_index"],
                                time_s=float(times[f["state_index"]]),
                            )
                        },
                    )
                    for f in frames
                ],
            )
        )
        if duration is not None and abs(duration - times[-1]) > 1e-8:
            raise ValueError("Different action duration")
        duration = float(times[-1])
    condition = dict(
        task=run["task"],
        demo=demo,
        native_time_origin_s=0.25,
        control_period_s=0.05,
        action_comparison=True,
        policy_comparison=False,
        physical_recommendation=False,
    )
    spec_path = output / (identity + "-sources.json")
    write_json(
        spec_path,
        dict(variants=[dict(id=identity, condition=condition, entries=entries)]),
    )
    bundle = dict(
        schema_version=1,
        id=identity,
        duration_s=duration,
        condition=condition,
        series=series,
        videos=videos,
        source_spec_path=str(spec_path.relative_to(ROOT)),
        source_spec_sha256=file_hash(spec_path),
        references=[
            "1 mm overlap is a declared numerical screen, not real-material truth. Gripper-relative height is not pure slip."
        ],
    )
    validate_bundle(bundle)
    write_json(output / (identity + ".json.gz"), bundle)
    from export_visual_research import plot

    for language in ("en", "zh"):
        plot(bundle, identity, language)
    for path in output.glob(identity + "*.svg"):
        path.write_text(
            "\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("media", type=Path)
    parser.add_argument("--demo", default="demo_0")
    args = parser.parse_args()
    build(args.campaign, args.media, args.demo, ROOT / "docs/evidence/visual")
