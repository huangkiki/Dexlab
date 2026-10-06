"""Replay saved cloth and prismatic pad states with a fixed camera; no physics."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def render(raw, out, prefix):
    record = json.loads(raw)
    if record.get("completed") is not True:
        raise ValueError("Require a completed recorded trajectory")
    out.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(10, 5.5), layout="constrained")
    axes = [
        fig.add_subplot(121, projection="3d"),
        fig.add_subplot(122, projection="3d"),
    ]
    cloth_art = []
    pad_art = []
    box_signs = np.array(
        [
            [-1, -1, -1],
            [1, -1, -1],
            [1, 1, -1],
            [-1, 1, -1],
            [-1, -1, 1],
            [1, -1, 1],
            [1, 1, 1],
            [-1, 1, 1],
        ]
    )
    box_faces = np.array(
        [
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [0, 1, 5, 4],
            [1, 2, 6, 5],
            [2, 3, 7, 6],
            [3, 0, 4, 7],
        ]
    )
    for axis, scene in zip(axes, record["scenes"]):
        axis.set(
            xlim=(-0.05, 0.05),
            ylim=(-0.035, 0.035),
            zlim=(-0.005, 0.15),
            xlabel="x (m)",
            ylabel="y (m)",
            zlabel="z (m)",
        )
        axis.set_xlabel("")
        axis.set_ylabel("")
        axis.set_xticks([-0.04, 0, 0.04])
        axis.set_yticks([-0.03, 0, 0.03])
        axis.set_box_aspect((0.1, 0.07, 0.155))
        axis.view_init(elev=15, azim=-45)
        cloth = Poly3DCollection(
            [], facecolor="#E69F00", edgecolor="#7A5200", linewidth=0.25, alpha=0.9
        )
        axis.add_collection3d(cloth)
        cloth_art.append(cloth)
        pads = Poly3DCollection(
            [], facecolor="#0072B2", edgecolor="black", linewidth=0.3, alpha=0.5
        )
        axis.add_collection3d(pads)
        pad_art.append(pads)
        axis.plot([-0.05, 0.05], [0, 0], [0, 0], color="gray", linewidth=1)
    fig.suptitle("Fixed camera: x/y/z coordinates in metres", fontsize=11)
    steps = list(range(0, 2001, 25))

    def update(frame):
        for i, scene in enumerate(record["scenes"]):
            row = scene["episodes"][0]["rows"][steps[frame]]
            p = np.asarray(row["pos"])
            faces = np.asarray(scene["native"]["faces"])
            cloth_art[i].set_verts(p[faces])
            boxes = []
            for center in row["pad_pos"]:
                vertices = np.asarray(center) + box_signs * np.array([0.01, 0.03, 0.02])
                boxes.extend(vertices[box_faces])
            pad_art[i].set_verts(boxes)
            visible = (
                (p[:, 0] >= -0.05)
                & (p[:, 0] <= 0.05)
                & (p[:, 1] >= -0.035)
                & (p[:, 1] <= 0.035)
                & (p[:, 2] >= -0.005)
                & (p[:, 2] <= 0.15)
            )
            axes[i].set_title(
                ("Coupled" if scene["coupled"] else "Coupling disabled")
                + f" | t={steps[frame] * 0.002:.2f} s\n{np.count_nonzero(~visible)}/{len(p)} particles outside fixed view"
            )
        return cloth_art + pad_art

    animation = FuncAnimation(fig, update, frames=len(steps), interval=50, blit=False)
    animation.save(out / f"{prefix}-replay.gif", writer=PillowWriter(fps=20))
    update(44)
    fig.savefig(out / f"{prefix}-hold.png", dpi=140)
    plt.close(fig)
    (out / f"{prefix}-replay.json").write_text(
        json.dumps(
            {
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "frame_steps": steps,
                "fps": 20,
                "native_duration_s": 4,
                "last_frame_hold_s": 0.05,
                "scope": "Fixed camera measured-state replay; no physics/render engine integration; repeat0 each condition. Out-of-view particle count is displayed; no moving camera or hidden recentering. Sampled video does not replace every-step scoring.",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--prefix", default="gripper")
    args = parser.parse_args()
    if not args.prefix.replace("-", "").replace("_", "").isalnum():
        parser.error(
            "prefix must contain only letters, numbers, hyphens and underscores"
        )
    raw = args.record.read_bytes()
    if args.record.suffix == ".gz":
        raw = gzip.decompress(raw)
    render(raw, args.output, args.prefix)
