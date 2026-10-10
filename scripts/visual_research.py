"""Validate and publish measured replay data. This module never advances physics."""

import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLORS = {
    "MuJoCo": "#0072B2",
    "SuperDex": "#009E73",
    "Genesis": "#CC79A7",
    "Newton Physics": "#D55E00",
    "PhysX": "#E69F00",
    "Drake": "#6B5B95",
}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    payload = (
        json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        + "\n"
    ).encode()
    if str(path).endswith(".gz"):
        Path(path).write_bytes(gzip.compress(payload, mtime=0))
    else:
        Path(path).write_bytes(payload)


def nearest_indices(times, targets):
    import numpy as np

    times, targets = np.asarray(times), np.asarray(targets)
    if len(times) < 2 or not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ValueError("Nonfinite, duplicate or reversed source clock")
    right = np.searchsorted(times, targets).clip(0, len(times) - 1)
    left = np.maximum(right - 1, 0)
    return np.where(
        abs(times[left] - targets) <= abs(times[right] - targets), left, right
    )


def validate_bundle(bundle):
    import math

    if bundle["schema_version"] != 1 or not bundle["series"] or not bundle["videos"]:
        raise ValueError("Empty or unsupported replay")
    duration = bundle["duration_s"]
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Invalid duration")
    names = set()
    state_clocks = {}
    for series in bundle["series"]:
        if series["id"] in names or series["engine"] not in COLORS:
            raise ValueError("Invalid series identity")
        names.add(series["id"])
        times = series["state_times_s"]
        if (
            not times
            or not all(math.isfinite(t) for t in times)
            or any(b <= a for a, b in itertools.pairwise(times))
        ):
            raise ValueError("Invalid source state clock")
        state_clocks[series["id"]] = times
        if (
            not series["sources"]
            or not series["configuration"]
            or not series["verdict"]
        ):
            raise ValueError("Missing provenance or original verdict")
        for source in series["sources"]:
            if len(source["sha256"]) != 64 or not source["path"] or not source["url"]:
                raise ValueError("Missing source hash or location")
        required = {
            "incline": {"displacement", "velocity", "support", "overlap"},
            "normal": {
                "indentation",
                "indentation_loaded",
                "normal_force",
                "load",
                "velocity_z",
            },
            "pinch": {"height", "relative_slip", "pad_force"},
            "libero": {
                "height",
                "gripper_relative_z",
                "finger_normal",
                "contact_overlap",
            },
        }[bundle["id"].split("-")[0]]
        keys = [c["key"] for c in series["channels"]]
        if len(keys) != len(set(keys)) or set(keys) != required:
            raise ValueError("Missing or duplicate measured channel")
        for channel in series["channels"]:
            points = channel["points"]
            if not channel["unit"] or not channel["epoch"] or not points:
                raise ValueError("Missing channel metadata")
            if any(len(p) != 2 or not all(math.isfinite(x) for x in p) for p in points):
                raise ValueError("Nonfinite samples cannot be silently plotted")
            if any(b[0] <= a[0] for a, b in itertools.pairwise(points)):
                raise ValueError("Channel clock must increase")
    mapped = []
    for video in bundle["videos"]:
        mapped.extend(video["series"])
        if (
            not math.isfinite(video["fps"])
            or video["fps"] <= 0
            or not video["frames"]
            or not video["sha256"]
        ):
            raise ValueError("Missing video mapping")
        frames = video["frames"]
        if abs((len(frames) - 1) / video["fps"] - duration) > 1 / video["fps"]:
            raise ValueError("Video mapping does not cover the complete episode")
        for index, frame in enumerate(frames):
            if frame["frame"] != index or set(frame["samples"]) != set(video["series"]):
                raise ValueError("Incomplete frame map")
            if abs(frame["time_s"] - index / video["fps"]) > 1 / video["fps"]:
                raise ValueError(
                    "Video and physics clocks differ by more than one frame"
                )
            if any(
                abs(sample["time_s"] - frame["time_s"]) > 1 / video["fps"]
                for sample in frame["samples"].values()
            ):
                raise ValueError("Source state outside the display frame")
            for name, sample in frame["samples"].items():
                times = state_clocks.get(name, [])
                offset = sample["index"]
                if (
                    not isinstance(offset, int)
                    or not 0 <= offset < len(times)
                    or abs(times[offset] - sample["time_s"]) > 1e-9
                ):
                    raise ValueError("Frame points to the wrong source state")
    if sorted(mapped) != sorted(names):
        raise ValueError("Video mapping must include every configuration exactly once")


def read_bundle(path):
    payload = Path(path).read_bytes()
    return json.loads(
        gzip.decompress(payload) if str(path).endswith(".gz") else payload
    )


def check(root=ROOT):
    index = json.loads((root / "docs/research-experiences.json").read_text())["visuals"]
    for card in index["catalogue"]:
        if (source := card.get("thumbnail_source")) and digest(
            root / source["path"]
        ) != source["sha256"]:
            raise ValueError("Changed original thumbnail media")
        if digest(root / card["thumbnail"]) != card["thumbnail_sha256"]:
            raise ValueError("Changed catalogue thumbnail")
        if (
            digest(
                root / "docs/evidence" / card["site_thumbnail"].removeprefix("_static/")
            )
            != card["thumbnail_sha256"]
        ):
            raise ValueError("Copied thumbnail differs from source")
    for case in index["cases"]:
        for variant in case["variants"]:
            path = root / variant["data"]["path"]
            if digest(path) != variant["data"]["sha256"]:
                raise ValueError(f"Changed visual data: {path}")
            bundle = read_bundle(path)
            validate_bundle(bundle)
            spec_path = root / bundle.get(
                "source_spec_path", "docs/evidence/visual/sources.json"
            )
            specs = json.loads(spec_path.read_text())
            spec = next(v for v in specs["variants"] if v["id"] == bundle["id"])
            if bundle["source_spec_sha256"] != digest(spec_path):
                raise ValueError("Changed frozen source specification")
            if bundle["condition"] != spec["condition"]:
                raise ValueError("Changed experiment condition")
            identities = [
                (s["id"], s["engine"], s["configuration"]) for s in bundle["series"]
            ]
            if identities != [
                (e["id"], e["engine"], e["configuration"]) for e in spec["entries"]
            ]:
                raise ValueError(
                    "Configuration identity differs from source specification"
                )
            for series in bundle["series"]:
                score = series["score"]
                valid = score.get("record_valid", score.get("numerically_valid", True))
                verdict = (
                    "pass" if score["passed"] else ("fail" if valid else "invalid")
                )
                if series["valid"] != valid or series["verdict"] != verdict:
                    raise ValueError("Display changed the original verdict")
                if score.get("trace_sha256"):
                    native = next(
                        s for s in series["sources"] if s["path"].endswith("/trace.npz")
                    )
                    if score["trace_sha256"] != native["sha256"]:
                        raise ValueError("Displayed trace differs from original score")
            for video in bundle["videos"]:
                for key in ("path", "poster"):
                    asset = root / "docs/evidence/visual" / video[key]
                    expected = video["sha256" if key == "path" else "poster_sha256"]
                    if digest(asset) != expected:
                        raise ValueError(f"Changed replay asset: {asset}")
            for source in (s for series in bundle["series"] for s in series["sources"]):
                if (
                    source.get("repository")
                    and digest(root / source["path"]) != source["sha256"]
                ):
                    raise ValueError(f"Changed evidence: {source['path']}")
    return index


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    check()
