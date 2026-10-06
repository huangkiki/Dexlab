"""Export actual PhysX poses for the existing continuous close-up renderer.

Only removed, massless fixed frames are reconstructed. Moving body poses are
native observations; target joint angles are never used to animate the robot.
"""

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation

from dexlab.physx_baseline import digest, write_json


def export(run: Path, display_run: Path, output: Path):
    receipt = json.loads((run / "run.json").read_text())
    if receipt.get("status") != "completed":
        raise ValueError("Replay requires a completed native record")
    if digest(run / "states.npz") != receipt["artifact_sha256"]["states.npz"]:
        raise ValueError("Native state archive has changed")
    dt = receipt["dt"]
    stride = round(0.05 / dt)
    if stride < 1 or not np.isclose(stride * dt, 0.05, rtol=0, atol=1e-10):
        raise ValueError("A 20 Hz replay requires an integer physics-step stride")
    with np.load(run / "states.npz", allow_pickle=False) as saved:
        states = dict(saved)
    with np.load(display_run / "trajectory.npz", allow_pickle=False) as saved:
        names = saved["names"].tolist()
    model = mujoco.MjModel.from_xml_path(str(run / "robot-model/kinematics.xml"))
    data = mujoco.MjData(model)
    transfer = json.loads((run / "robot-model/model-transfer.json").read_text())
    frames = []
    samples = np.arange(0, len(states["time"]), stride)
    for index in samples:
        data.qpos[:] = states["q"][index]
        mujoco.mj_kinematics(model, data)
        frame = []
        for name in names:
            local = "robot_world" if name == "world" else name
            full = "apple/apple" if local == "apple" else "robot/" + local
            if full in receipt["body_names"]:
                body = receipt["body_names"].index(full)
                position = states["position"][index, body]
                quaternion = states["quaternion"][index, body][[1, 2, 3, 0]]
            else:
                parent = transfer["collapsed_frames"][local]
                bid, sid = model.body(parent).id, model.site("frame_" + local).id
                original = Rotation.from_matrix(data.xmat[bid].reshape(3, 3))
                offset = original.inv().apply(data.site_xpos[sid] - data.xpos[bid])
                relative = original.inv() * Rotation.from_matrix(
                    data.site_xmat[sid].reshape(3, 3)
                )
                body = receipt["body_names"].index("robot/" + parent)
                rotation = Rotation.from_quat(
                    states["quaternion"][index, body][[1, 2, 3, 0]]
                )
                position = states["position"][index, body] + rotation.apply(offset)
                quaternion = (rotation * relative).as_quat()
            frame.append(np.r_[position, quaternion])
        frames.append(frame)
    output.mkdir(parents=True, exist_ok=False)
    assets = output / "assets"
    assets.mkdir()
    tree = ET.parse(display_run / "display.xml")
    for index, element in enumerate(tree.findall(".//*[@file]")):
        source = Path(element.get("file"))
        if not source.is_absolute():
            source = display_run / source
        destination = assets / f"{index}{source.suffix}"
        shutil.copyfile(source, destination)
        element.set("file", str(destination.relative_to(output)))
    tree.write(output / "display.xml", encoding="unicode")
    np.savez_compressed(
        output / "trajectory.npz", names=names, frames=np.asarray(frames), dt=0.05
    )
    write_json(
        output / "engine.json",
        {
            "backend": "physx",
            "scope": "Replay identity only; not an engine qualification receipt",
        },
    )
    write_json(
        output / "replay.json",
        {
            "source_states_sha256": digest(run / "states.npz"),
            "source_display_sha256": digest(display_run / "display.xml"),
            "exporter_sha256": digest(Path(__file__)),
            "sampled_physics_indices": samples.tolist(),
            "sampled_native_times_s": states["time"][samples].tolist(),
            "frame_count": len(frames),
            "presentation_duration_s": len(frames) * 0.05,
            "scope": __doc__.strip(),
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--display-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    export(args.run.resolve(), args.display_run.resolve(), args.output.resolve())
