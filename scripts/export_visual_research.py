"""Export existing native records to replay media and full-rate plotted channels.

Input mappings are local paths keyed by the source IDs in sources.json. Download
and verify the linked release archives first; no engine is stepped by this tool.
"""

import argparse
import gzip
import io
import itertools
import json
import os
import shutil
import tarfile
from pathlib import Path

import numpy as np
from visual_research import (
    COLORS,
    ROOT,
    digest,
    nearest_indices,
    validate_bundle,
    write_json,
)

OUT = ROOT / "docs/evidence/visual"


def read_json(path):
    return json.loads(Path(path).read_text())


def source(path, url, *, relative=None):
    return {
        "path": relative or str(path.relative_to(ROOT)),
        "sha256": digest(path),
        "url": url,
        "repository": relative is None,
    }


def channel(
    key, unit, times, values, epoch="Recorded post-integration state", reference=None
):
    result = {
        "key": key,
        "unit": unit,
        "epoch": epoch,
        "points": np.column_stack([times, values]).tolist(),
    }
    if reference is not None:
        result["reference"] = np.column_stack(
            [times, np.broadcast_to(reference, np.shape(times))]
        ).tolist()
    return result


def load_incline(entry, mappings):
    directory = Path(mappings[entry["source_id"]]) / entry["record"]
    metadata = read_json(directory / "metadata.json")
    case = metadata["case"]
    provenance = [
        source(
            directory / "metadata.json",
            entry["archive"],
            relative=entry["record"] + "/metadata.json",
        )
    ]

    def verified(name):
        path = directory / name
        expected = metadata.get("hashes", {}).get(name) or metadata.get(
            name.replace(".", "_") + "_sha256"
        )
        if name == "trace.npz":
            expected = expected or metadata.get("trace_sha256")
        if expected is None and "ledger_sha256" in metadata:
            expected = metadata["ledger_sha256"].get(name)
        if expected != digest(path):
            raise ValueError(
                f"Unverified source file {entry['source_id']}/{entry['record']}/{name}"
            )
        provenance.append(
            source(path, entry["archive"], relative=entry["record"] + "/" + name)
        )
        return path

    if (directory / "trace.npz").exists():
        with np.load(verified("trace.npz")) as data:
            trace = {k: data[k] for k in data.files}
    elif (directory / "steps.jsonl.gz").exists():
        with gzip.open(verified("steps.jsonl.gz"), "rt") as stream:
            rows = [json.loads(line) for line in stream]
        trace = {
            "states": np.array([rows[0]["pre_state"]] + [r["state"] for r in rows]),
            "forces": np.array([r["net_force"] for r in rows]),
        }
        trace["force_times"] = trace["states"][:-1, 0]
    else:
        with gzip.open(verified("native.jsonl.gz"), "rt") as stream:
            records = [json.loads(line) for line in stream]
        admission = records[0]
        rows = [r for r in records if r["kind"] == "step"]
        # Decode the immutable native stream; retain its original published validity.
        # Do not reclassify a historical record with a different current scorer.
        if (
            len(rows) != round(2 / case["timestep"])
            or records[-1]["kind"] != "completion"
        ):
            raise ValueError("Incomplete PhysX record")
        forces = []
        for row in rows:
            impulse = np.zeros(3)
            for pair in row["pairs"]:
                if type(pair["cube_first"]) is not bool:
                    raise ValueError("Missing body-order convention")
                sign = 1 if pair["cube_first"] else -1
                if pair["declared_contacts"] != len(pair["contacts"]):
                    raise ValueError("Truncated native contacts")
                for contact in pair["contacts"] + pair["friction_anchors"]:
                    impulse += sign * np.asarray(contact["impulse"])
            forces.append(impulse / admission["effective_timestep"])
        states = np.array([admission["initial_state"]] + [r["state"] for r in rows])
        trace = {
            "states": states,
            "forces": np.array(forces),
            "force_times": states[:-1, 0],
        }
    score_path = ROOT / entry["score"]
    score = next(r for r in read_json(score_path)["results"] if r["id"] == case["id"])
    provenance.append(
        source(
            score_path,
            "https://github.com/huangkiki/Dexlab/blob/main/" + entry["score"],
        )
    )
    states, forces = trace["states"], trace["forces"]
    times, pos, quat = states[:, 0], states[:, 1:4], states[:, 4:8]
    angle = np.deg2rad(case["angle_deg"])
    tangent = np.array([np.cos(angle), 0, -np.sin(angle)])
    normal = np.array([np.sin(angle), 0, np.cos(angle)])
    accel = 9.81 * max(0, np.sin(angle) - case["friction"] * np.cos(angle))
    # Oriented-box distance to the authored reference plane, not native contact depth.
    corners = np.array(list(itertools.product([-0.02, 0.02], repeat=3)))
    q = quat / np.linalg.norm(quat, axis=1)[:, None]
    v = np.broadcast_to(corners, (len(q), 8, 3))
    rotated = v + 2 * np.cross(
        q[:, None, 1:], np.cross(q[:, None, 1:], v) + q[:, None, :1] * v
    )
    overlap = np.maximum(0, -np.min((rotated + pos[:, None, :]) @ normal, axis=1))
    valid = score.get("record_valid", True)
    channels = [
        channel(
            "displacement",
            "m",
            times,
            (pos - pos[0]) @ tangent,
            reference=0.5 * accel * times**2,
        ),
        channel(
            "velocity", "m/s", times, states[:, 8:11] @ tangent, reference=accel * times
        ),
        channel(
            "support",
            "N",
            trace["force_times"],
            forces @ normal,
            metadata.get(
                "force_epoch",
                "Native impulse / actual update interval; plotted at interval start",
            ),
            0.064 * 9.81 * np.cos(angle),
        ),
        channel(
            "overlap",
            "mm",
            times,
            overlap * 1000,
            "Geometric diagnostic from normalized recorded quaternion; original scoring unchanged",
        ),
    ]
    result = {
        "id": entry["id"],
        "engine": entry["engine"],
        "configuration": entry["configuration"],
        "sources": provenance,
        "valid": valid,
        "verdict": "pass" if score["passed"] else ("fail" if valid else "invalid"),
        "channels": channels,
        "score": score,
        "missing_channels": [],
    }
    return result, {"times": times, "pose": states[:, 1:8], "angle": case["angle_deg"]}


def load_normal(entry, mappings):
    with tarfile.open(mappings[entry["source_id"]]) as archive:
        prefix = entry["record"]
        receipt_bytes = archive.extractfile(prefix + "/run.json").read()
        receipt = json.loads(receipt_bytes)
        raw = archive.extractfile(prefix + "/states.npz").read()
        import hashlib

        if hashlib.sha256(raw).hexdigest() != receipt["artifact_sha256"]["states.npz"]:
            raise ValueError(
                "Normal-response archive hash differs from original receipt"
            )
        with np.load(io.BytesIO(raw)) as data:
            trace = {k: data[k] for k in data.files}
    report_path = ROOT / entry["score"]
    report = next(
        r for r in read_json(report_path)["results"] if r["id"] == entry["id"]
    )
    if hashlib.sha256(receipt_bytes).hexdigest() != report["receipt_sha256"]:
        raise ValueError("Historical normal receipt differs from published report")
    times = trace["time"]
    loaded = times <= 0.6
    channels = [
        channel(
            "indentation_loaded",
            "mm",
            times[loaded],
            (0.02 - trace["pose"][loaded, 2]) * 1000,
        ),
        channel("indentation", "mm", times, (0.02 - trace["pose"][:, 2]) * 1000),
        channel(
            "normal_force",
            "N",
            times[:-1],
            trace["contact_force"][:, 2],
            "Contact force for [t_i,t_i+1], plotted at interval start",
        ),
        channel(
            "load",
            "N",
            times[:-1],
            trace["downward_load"],
            "Command for the integration interval",
        ),
        channel("velocity_z", "m/s", times, trace["velocity"][:, 2]),
    ]
    sources = [
        {
            "path": prefix + "/states.npz",
            "sha256": receipt["artifact_sha256"]["states.npz"],
            "url": entry["archive"],
            "repository": False,
        },
        {
            "path": prefix + "/run.json",
            "sha256": report["receipt_sha256"],
            "url": entry["archive"],
            "repository": False,
        },
        source(
            report_path,
            "https://github.com/huangkiki/Dexlab/blob/main/" + entry["score"],
        ),
    ]
    return {
        "id": entry["id"],
        "engine": entry["engine"],
        "configuration": entry["configuration"],
        "sources": sources,
        "valid": True,
        "verdict": "pass" if report["result"]["passed"] else "fail",
        "channels": channels,
        "effective_parameters": receipt["normal_parameters"],
        "score": report["result"],
        "missing_channels": [],
    }, {"times": times, "pose": trace["pose"], "angle": 0}


def load_pinch(entry, mappings):
    from dexlab.genesis_pinch_score import score_force_record

    directory = ROOT / entry["record"]
    raw = directory / (
        "open_negative-0.json.gz" if entry["id"] == "dev-open" else "pinch-0.json.gz"
    )
    with gzip.open(raw, "rt") as stream:
        record = json.load(stream)
    manifest = read_json(ROOT / "demos/contact-benchmark/force-limit-v1.json")
    case = next(c for c in manifest["cases"] if c["id"] == entry["id"])
    result = score_force_record(record, case, include_timeline=True)
    published = next(
        c["result"]
        for c in read_json(ROOT / entry["score"])["cases"]
        if c["case"]["id"] == entry["id"]
    )
    if any(result[k] != published[k] for k in published if k in result):
        raise ValueError("Pinch offline score differs from published evidence")
    rows, timeline = record["samples"], result.pop("timeline")
    times = np.array([r["time"] for r in rows])
    channels = [
        channel(
            "height",
            "mm",
            times,
            [r["object_pos"][2] * 1000 for r in rows],
            reference=60,
        ),
        channel(
            "relative_slip",
            "mm",
            times,
            [(r["object_pos"][2] - 0.02 - r["q"][0]) * 1000 for r in rows],
        ),
        channel(
            "pad_force",
            "N",
            times,
            [sum(r["pad_abs_x_force_proxy_N"]) for r in timeline],
            "Native contact solve associated with this post-step sample; sum absolute pad x projections",
            0.064 * 9.81 / 0.5,
        ),
    ]
    result.pop("scope", None)
    return {
        "id": entry["id"],
        "engine": entry["engine"],
        "configuration": entry["configuration"],
        "sources": [
            source(
                raw,
                "https://github.com/huangkiki/Dexlab/blob/main/"
                + entry["record"]
                + "/"
                + raw.name,
            ),
            source(
                ROOT / entry["score"],
                "https://github.com/huangkiki/Dexlab/blob/main/" + entry["score"],
            ),
        ],
        "valid": result["numerically_valid"],
        "verdict": "pass" if result["passed"] else "fail",
        "channels": channels,
        "score": result,
        "missing_channels": [],
    }, {
        "times": times,
        "pose": np.array([r["object_pos"] + r["object_quat"] for r in rows]),
        "angle": 0,
    }


def render(variant_id, series, poses, duration):
    """Common authored box/plane geometry, measured poses only, fixed camera per preset."""
    import imageio.v2 as imageio
    from PIL import Image, ImageDraw, ImageFont

    os.environ.setdefault("MUJOCO_GL", "egl")
    import mujoco

    fps = 30
    frames = np.arange(round(duration * fps) + 1) / fps
    columns = min(len(series), 3)
    rows = (len(series) + columns - 1) // columns
    width, height = 480, 320
    targets = [nearest_indices(p["times"], frames) for p in poses]
    allpos = np.concatenate([p["pose"][:, :3] for p in poses])
    center = (allpos.min(axis=0) + allpos.max(axis=0)) / 2
    max(0.12, float(np.ptp(allpos, axis=0).max()) + 0.08)
    camera = mujoco.MjvCamera()
    camera.lookat[:] = center
    camera.distance, camera.azimuth, camera.elevation = 0.20, 90, -25
    video = OUT / (variant_id + ".mp4")
    poster = OUT / (variant_id + ".png")
    models, datas = [], []
    for s, p in zip(series, poses):
        color = COLORS[s["engine"]]
        rgb = " ".join(str(int(color[i : i + 2], 16) / 255) for i in (1, 3, 5))
        a = np.deg2rad(p["angle"]) / 2
        xml = f'<mujoco><visual><global offwidth="480" offheight="320"/></visual><worldbody><light pos="0 -2 4"/><geom type="plane" size="8 8 .01" quat="{np.cos(a)} 0 {np.sin(a)} 0" rgba=".88 .9 .91 1"/><body><freejoint/><geom type="box" size=".02 .02 .02" rgba="{rgb} 1"/></body></worldbody></mujoco>'
        model = mujoco.MjModel.from_xml_string(xml)
        models.append(model)
        datas.append(mujoco.MjData(model))
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    mappings = []
    with (
        mujoco.Renderer(models[0], height=height, width=width) as renderer,
        imageio.get_writer(
            video,
            fps=fps,
            codec="libx264",
            quality=7,
            macro_block_size=1,
            ffmpeg_params=["-threads", "1", "-filter_threads", "1"],
        ) as writer,
    ):
        # Renderer contexts are model-specific. One model suffices: only display colors and plane rotation differ.
        model, data = models[0], datas[0]
        for frame, t in enumerate(frames):
            canvas = Image.new("RGB", (width * columns, height * rows + 100), "#142632")
            draw = ImageDraw.Draw(canvas)
            sample_map = {}
            for i, (s, p, indices) in enumerate(zip(series, poses, targets)):
                j = int(indices[frame])
                data.qpos[:] = p["pose"][j]
                q = data.qpos[3:7]
                q[:] /= np.linalg.norm(
                    q
                )  # display-only normalization, labelled in provenance
                color = COLORS[s["engine"]]
                model.geom_rgba[1] = [
                    int(color[k : k + 2], 16) / 255 for k in (1, 3, 5)
                ] + [1]
                model.geom_quat[0] = models[i].geom_quat[0]
                mujoco.mj_forward(model, data)
                camera.lookat[:] = p["pose"][j, :3]
                renderer.update_scene(data, camera=camera)
                tile = Image.fromarray(renderer.render())
                td = ImageDraw.Draw(tile)
                td.rectangle((0, 0, width, 46), fill="#142632")
                td.text(
                    (10, 5),
                    s["engine"] + " | " + s["verdict"].upper(),
                    fill="white",
                    font=font,
                )
                td.text((10, 25), s["configuration"][:54], fill="white", font=font)
                td.text(
                    (10, height - 24),
                    f"x={p['pose'][j, 0]:.4f} m  z={p['pose'][j, 2]:.4f} m",
                    fill="#142632",
                    font=font,
                )
                canvas.paste(tile, ((i % columns) * width, (i // columns) * height))
                sample_map[s["id"]] = {"index": j, "time_s": float(p["times"][j])}
            draw.text(
                (14, height * rows + 10),
                f"t = {t:.3f} s | Same body-follow camera / scale | Recorded poses; no physics step",
                fill="white",
                font=font,
            )
            # Shared world-coordinate ruler retains the motion hidden by body-follow cameras.
            left, right = 50, width * columns - 50
            lo, hi = float(allpos[:, 0].min()), float(allpos[:, 0].max())
            hi = max(hi, lo + 0.04)
            baseline = height * rows + 65
            draw.line((left, baseline, right, baseline), fill="white", width=2)
            for i, (s, p, indices) in enumerate(zip(series, poses, targets)):
                xx = left + (right - left) * (
                    p["pose"][int(indices[frame]), 0] - lo
                ) / (hi - lo)
                draw.ellipse(
                    (xx - 5, baseline - 5, xx + 5, baseline + 5),
                    fill=COLORS[s["engine"]],
                    outline="white",
                )
            draw.text(
                (left, baseline + 10), f"World x: {lo:.3f} m", fill="white", font=font
            )
            draw.text(
                (right - 110, baseline + 10), f"{hi:.3f} m", fill="white", font=font
            )
            writer.append_data(np.asarray(canvas))
            if frame == len(frames) // 2:
                canvas.save(poster)
            mappings.append({"frame": frame, "time_s": float(t), "samples": sample_map})
    return {
        "path": video.name,
        "sha256": digest(video),
        "poster": poster.name,
        "poster_sha256": digest(poster),
        "fps": fps,
        "series": [s["id"] for s in series],
        "frames": mappings,
        "renderer": "MuJoCo "
        + mujoco.__version__
        + " display only; no mj_step; quaternion normalized for display",
        "camera": {
            "mode": "Same body-follow policy for each recorded pose; shared world-x ruler",
            "distance": 0.20,
            "azimuth": 90,
            "elevation": -25,
        },
        "sampling": "Nearest recorded state; no state interpolation; full episode; spatial scale unchanged",
    }


def pinch_videos(entries, series):
    videos = []
    import hashlib

    for entry, s in zip(entries, series):
        p = ROOT / entry["replay"]
        provenance = read_json(p / "provenance.json")
        if digest(p / "replay.mp4") != provenance["video_sha256"]:
            raise ValueError("Changed historical pinch video")
        raw = (
            ROOT
            / entry["record"]
            / (
                "open_negative-0.json.gz"
                if entry["id"] == "dev-open"
                else "pinch-0.json.gz"
            )
        )
        with gzip.open(raw, "rb") as f:
            if hashlib.sha256(f.read()).hexdigest() != provenance["record_sha256"]:
                raise ValueError("Pinch video and measured states are not the same run")
        name = "pinch-" + entry["id"]
        shutil.copyfile(p / "replay.mp4", OUT / (name + ".mp4"))
        shutil.copyfile(p / "frame-060.png", OUT / (name + ".png"))
        videos.append(
            {
                "path": name + ".mp4",
                "sha256": digest(OUT / (name + ".mp4")),
                "poster": name + ".png",
                "poster_sha256": digest(OUT / (name + ".png")),
                "fps": provenance["fps"],
                "series": [s["id"]],
                "renderer": provenance["renderer"],
                "camera": provenance["camera"],
                "sampling": provenance["sampling"],
                "frames": [
                    {
                        "frame": f["frame"],
                        "time_s": f["frame"] / provenance["fps"],
                        "samples": {
                            s["id"]: {"index": f["sample"], "time_s": f["time_s"]}
                        },
                    }
                    for f in provenance["frames"]
                ],
            }
        )
    return videos


def plot(bundle, variant_id, language="en"):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    zh = language == "zh"
    if zh:
        font_manager.fontManager.addfont(
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        )
    plt.rcParams["font.family"] = "Noto Sans CJK JP" if zh else "DejaVu Sans"
    plt.rcParams["svg.hashsalt"] = "dexlab-visual-v1"
    chinese = {
        "displacement": "沿斜面位移",
        "velocity": "沿斜面速度",
        "support": "法向支撑力",
        "overlap": "参考平面几何重叠",
        "indentation_loaded": "加载窗口压入量",
        "indentation": "全程压入与离面",
        "normal_force": "法向接触力",
        "load": "外加载荷",
        "velocity_z": "竖直速度",
        "height": "物体高度",
        "relative_slip": "相对夹具滑移",
        "pad_force": "指面力 x 分量绝对值之和",
    }
    keys = list(
        dict.fromkeys(c["key"] for s in bundle["series"] for c in s["channels"])
    )
    fig, axes = plt.subplots(
        (len(keys) + 1) // 2,
        2,
        figsize=(10, 3 * ((len(keys) + 1) // 2) + 1.1),
        squeeze=False,
    )
    for ax, key in zip(axes.flat, keys):
        if hold := bundle["condition"].get("hold_window_s"):
            ax.axvspan(*hold, color="#0072B2", alpha=0.08)
        reference_drawn = False
        for i, s in enumerate(bundle["series"]):
            c = next(c for c in s["channels"] if c["key"] == key)
            points = np.array(c["points"])
            label = s["engine"] + " " + s["id"]
            if not s["valid"]:
                label += " [invalid record]"
            ax.plot(
                points[:, 0],
                points[:, 1],
                color=COLORS[s["engine"]],
                ls=["-", "--", ":"][i % 3]
                if len({x["engine"] for x in bundle["series"]}) == 1
                else ("-" if s["valid"] else ":"),
                label=label,
                lw=1.4,
            )
            if "reference" in c and not reference_drawn:
                ref = np.array(c["reference"])
                ax.plot(
                    ref[:, 0],
                    ref[:, 1],
                    "k--",
                    lw=0.9,
                    label="解析／已声明参照"
                    if zh
                    else "Analytical / declared reference",
                )
                reference_drawn = True
        ax.set(
            title=chinese.get(key, key) if zh else key.replace("_", " "),
            xlabel="仿真时间 (s)" if zh else "Simulation time (s)",
            ylabel=c["unit"],
        )
        ax.grid(alpha=0.2)
    for ax in list(axes.flat)[len(keys) :]:
        ax.set_visible(False)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8)
    fig.subplots_adjust(bottom=0.16, wspace=0.25, hspace=0.5, top=0.92)
    fig.suptitle(
        "已有记录观测 · 保留原验收结果 · 不构成引擎性能排名"
        if zh
        else "Recorded observations | original verdicts retained | no performance ranking",
        fontsize=11,
    )
    for suffix in ("svg", "png"):
        fig.savefig(
            OUT / (variant_id + "-curves" + (".zh" if zh else "") + "." + suffix),
            dpi=160,
            bbox_inches="tight",
            metadata={"Date": None} if suffix == "svg" else None,
        )
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-map", type=Path, required=True)
    parser.add_argument("--only", choices=["pinch", "normal", "incline"])
    args = parser.parse_args()
    mappings = read_json(args.input_map)
    specs = read_json(OUT / "sources.json")
    OUT.mkdir(exist_ok=True, parents=True)
    for variant in specs["variants"]:
        if args.only and variant["kind"] != args.only:
            continue
        print("export", variant["id"], flush=True)
        loader = {"incline": load_incline, "normal": load_normal, "pinch": load_pinch}[
            variant["kind"]
        ]
        loaded = [loader(e, mappings) for e in variant["entries"]]
        series, poses = map(list, zip(*loaded))
        for item, pose in zip(series, poses):
            item["state_times_s"] = pose["times"].tolist()
        duration = min(float(p["times"][-1]) for p in poses)
        videos = (
            pinch_videos(variant["entries"], series)
            if variant["kind"] == "pinch"
            else [render(variant["id"], series, poses, duration)]
        )
        bundle = {
            "schema_version": 1,
            "id": variant["id"],
            "duration_s": duration,
            "series": series,
            "videos": videos,
            "source_spec_sha256": digest(OUT / "sources.json"),
            "exporter_sha256": digest(Path(__file__)),
            "condition": variant["condition"],
            "references": variant.get("references", []),
        }
        validate_bundle(bundle)
        write_json(OUT / (variant["id"] + ".json.gz"), bundle)
        plot(bundle, variant["id"])
        plot(bundle, variant["id"], "zh")


if __name__ == "__main__":
    main()
