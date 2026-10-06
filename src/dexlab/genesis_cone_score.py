"""Independent standard-library diagnostics; no engine state or success shortcuts."""
import argparse
import json
import math
from pathlib import Path


def summarize(record: dict) -> dict:
    """Reject incomplete/nonfinite traces before computing conditional discrepancies."""
    samples = record["samples"]
    if len(samples) != 40:
        raise ValueError("Expected all 40 samples at 5ms")
    for row in [record["before"], record["after"], *samples]:
        for key, size in (("position", 3), ("velocity", 3), ("quaternion", 4)):
            values = row[key]
            if len(values) != size or not all(math.isfinite(x) for x in values):
                raise ValueError(f"Invalid {key}")
        force = row["force"]
        if len(force) != 1 or len(force[0]) != 3 or not all(math.isfinite(x) for x in force[0]):
            raise ValueError("Invalid contact force")
    initial_vx = record["after"]["velocity"][0]
    return {
        "first_velocity_m_s": samples[0]["velocity"],
        "first_contact_force_N": samples[0]["force"][0],
        "initial_vertical_speed_m_s": record["before"]["velocity"][2],
        "max_abs_vertical_speed_m_s": max(abs(r["velocity"][2]) for r in samples),
        "max_conditional_vx_error_m_s": max(
            abs(r["velocity"][0] - max(initial_vx - 0.5 * 9.81 * (i + 1) * 0.005, 0))
            for i, r in enumerate(samples)),
    }


def validate_manifest(manifest: dict) -> None:
    expected = {
        "schema": 1, "dt_s": 0.005, "steps": 40, "mu": 0.5,
        "gravity_m_s2": [0, 0, -9.81], "cube_size_m": [0.05] * 3,
        "density_kg_m3": 1000, "initial_position_m": [0, 0, 0.025],
        "noslip_iterations": 0, "settling_steps": 100,
        "engine": "1.4.3", "backend": "cpu", "precision": "64",
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"Unsupported protocol: {key}")


def score(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text())
    validate_manifest(manifest)
    results = {}
    for cone in ("pyramidal", "elliptic"):
        for condition in ("no_write", "zero_all", "kick_all", "kick_x_only"):
            name = f"{cone}-{condition}"
            record = json.loads((directory / f"{name}.json").read_text())
            if record["cone"] != cone or record["condition"] != condition:
                raise ValueError("Mislabeled trace")
            results[name] = summarize(record)
    return {"scope": "0.2s primitive diagnostic, not physical-accuracy certification",
            "reference_assumptions": "Flat translating Coulomb block; rotation violates the reference",
            "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(score(parser.parse_args().directory), indent=2))
