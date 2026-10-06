"""Offline checks for the preregistered contact-onset factorial contrast."""

import gzip
import json
from dataclasses import asdict
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

from dexlab.contact_plane import PlaneCase, reference, score
from dexlab.physx_baseline import digest

PROTOCOL_SHA256 = "11833036123c60de572cfd8e6325d0b181328f33a19250430f42d3985f906a52"

TIMESTEPS = (0.001, 0.0005, 0.00025)
CONES = ("elliptic", "pyramidal")
TIME_CONSTANTS = (0.005, 0.02)
IMPEDANCE = [0.95, 0.99, 0.001, 0.5, 2.0]


def jobs():
    """Ordering and exact-repeat identities were declared before outcomes."""
    rows = [
        {"friction": mu, "timestep": dt, "timeconst": tc, "cone": cone}
        for mu in (0.3, 0.0)
        for dt in TIMESTEPS
        for tc in TIME_CONSTANTS
        for cone in CONES
    ]
    return [dict(row, id=f"case-{i:02d}") for i, row in enumerate(rows + rows[:2])]


def case_for(job):
    return PlaneCase(
        name="dev-cone-timeconst",
        friction=job["friction"],
        timestep=job["timestep"],
        settle=0,
    )


def verify(directory):
    """Recompute the score from full records; never accept the stored verdict."""
    directory = Path(directory)
    receipt = json.loads((directory / "receipt.json").read_text())
    job = receipt["job"]
    expected = {row["id"]: row for row in jobs()}
    if job.get("id") not in expected or job != expected[job["id"]]:
        raise ValueError("Record is outside the frozen matrix")
    case = case_for(job)
    required = {"states.npz", "contacts.jsonl.gz", "native.json", "model.xml"}
    hashes = receipt.get("hashes", {})
    if hashes.keys() != required or not all(
        digest(directory / k) == v for k, v in hashes.items()
    ):
        raise ValueError("Missing or changed raw artifact")
    with np.load(directory / "states.npz", allow_pickle=False) as archive:
        data = dict(archive)
    engineering = score(case, data)
    checks = {"case_matches": receipt.get("case") == asdict(case)}
    for key in (
        "complete_shapes",
        "finite_states_and_forces",
        "complete_contact_coverage",
        "native_steps_completed",
        "uniform_time_grid",
        "declared_initial_velocity",
        "unit_quaternions",
        "momentum_balance",
    ):
        checks[key] = engineering["checks"].get(key) is True
    if not checks["complete_shapes"] or not checks["finite_states_and_forces"]:
        return {
            "valid": False,
            "checks": checks,
            "engineering": engineering,
            "metrics": {},
        }
    checks["identical_initial_pose"] = bool(
        np.array_equal(data["pose"][0], [0, 0, 0.02, 1, 0, 0, 0])
    )
    checks["identical_initial_velocity"] = bool(
        np.array_equal(data["velocity"][0], [0.25, 0, 0, 0, 0, 0])
    )
    checks["zero_external_action"] = bool(
        data.get("external_force", np.ones(1)).shape == (case.steps, 3)
        and np.all(data["external_force"] == 0)
    )
    native = json.loads((directory / "native.json").read_text())
    checks["native_identity"] = (
        native.get("engine") == "mujoco"
        and native.get("identity", {}).get("version") == "3.15.0"
        and native.get("identity", {}).get("compatibility_profile")
        == "qualification-3.15.0"
    )
    checks["native_simulation"] = native.get("simulation_options") == {
        "timestep": case.timestep,
        "gravity": [0, 0, -case.gravity],
        "actuator_count": 0,
    }
    solver = native.get("solver", {})
    checks["native_solver"] = all(
        solver.get(k) == v
        for k, v in {
            "integrator": 0,
            "algorithm": 2,
            "cone": 1 if job["cone"] == "elliptic" else 0,
            "iterations": 100,
            "tolerance": 1e-10,
            "impratio": 1.0,
            "disableflags": 0,
            "enableflags": 0,
        }.items()
    )
    normal = {"solref": [job["timeconst"], 1.0], "solimp": IMPEDANCE}
    checks["native_normal_profile"] = native.get("normal_parameters_readback") == normal
    checks["native_mass_inertia"] = bool(
        native.get("mass_readback") == case.mass
        and np.allclose(
            native.get("inertia_readback", [0, 0, 0]),
            case.inertia,
            rtol=1e-12,
            atol=1e-15,
        )
    )
    geom = native.get("geometry_readback", {})
    checks["native_geometry"] = (
        geom.get("type") == [0, 6]
        and geom.get("size") == [[2, 2, 0.1], [0.02, 0.02, 0.02]]
        and geom.get("priority") == [0, 0]
        and geom.get("solmix") == [1, 1]
        and geom.get("condim") == [3, 3]
        and geom.get("solref") == [normal["solref"]] * 2
        and geom.get("solimp") == [IMPEDANCE] * 2
        and native.get("friction_readback") == [[case.friction, 0, 0]] * 2
    )
    xml = ET.parse(directory / "model.xml").getroot()
    option = xml.find("option")
    default = xml.find("default/geom")
    checks["authored_options"] = bool(
        option is not None
        and default is not None
        and option.get("cone") == job["cone"]
        and option.get("integrator") == "Euler"
        and option.get("solver") == "Newton"
        and float(option.get("timestep")) == case.timestep
        and float(option.get("iterations")) == 100
        and float(option.get("tolerance")) == 1e-10
        and list(map(float, option.get("gravity").split())) == [0, 0, -case.gravity]
        and list(map(float, default.get("solref").split())) == normal["solref"]
        and list(map(float, default.get("solimp").split())) == IMPEDANCE
    )
    ledger = []
    warnings_ok = True
    parameters_ok = True
    with gzip.open(directory / "contacts.jsonl.gz", "rt") as stream:
        for line in stream:
            row = json.loads(line)
            warnings_ok &= bool(row["warnings"]) and not any(row["warnings"])
            force = np.zeros(3)
            for point in row["contacts"]:
                force += np.asarray(point["force_on_box"])
                params = point["parameters"]
                parameters_ok &= (
                    params["dimension"] == 3
                    and params["solref"] == normal["solref"]
                    and params["solimp"] == IMPEDANCE
                )
            ledger.append(force)
    checks["native_warnings"] = warnings_ok
    checks["contact_parameters"] = parameters_ok
    checks["raw_force_ledger"] = bool(
        len(ledger) == case.steps
        and np.allclose(ledger, data["contact_force"], rtol=1e-6, atol=1e-7)
    )
    early = round(0.01 / case.timestep)
    onset = data["time"] <= 0.05 + 1e-12
    _, vx = reference(case, data["time"])
    error = data["velocity"][onset, 0] - vx[onset]
    metrics = {
        "first10ms_excess_normal_impulse_ns": float(
            (data["contact_force"][:early, 2].sum() - early * case.mass * case.gravity)
            * case.timestep
        ),
        "maximum_abs_vertical_speed_m_s": float(np.abs(data["velocity"][:, 2]).max()),
        "first50ms_vx_reference_max_m_s": float(np.abs(error).max()),
        "first50ms_vx_reference_rms_m_s": float(np.sqrt(np.mean(error**2))),
    }
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "engineering": engineering,
        "metrics": metrics,
    }


def verify_matrix(directory):
    """Require every declared case, source integrity and repeat comparisons."""
    directory = Path(directory)
    expected = jobs()
    actual = sorted(p.name for p in directory.glob("case-*") if p.is_dir())
    if actual != [row["id"] for row in expected]:
        raise ValueError("Missing, duplicate or undeclared case")
    if digest(directory / "protocol.json") != PROTOCOL_SHA256:
        raise ValueError("Protocol changed")
    source_hashes = json.loads((directory / "source-hashes.json").read_text())
    required_sources = {
        "contact_cone.py",
        "contact_cone_run.py",
        "contact_plane.py",
        "contact_plane_native.py",
        "physx_baseline.py",
        "contact_parameters.py",
        "engine_versions.py",
        "cloth_engines.py",
    }
    if not required_sources <= source_hashes.keys() or not all(
        Path(name).name == name and digest(directory / "source" / name) == value
        for name, value in source_hashes.items()
    ):
        raise ValueError("Source snapshot changed")
    results = [
        {"job": job, "result": verify(directory / job["id"])} for job in expected
    ]
    repeats = []
    for a, b in (("case-00", "case-24"), ("case-01", "case-25")):
        with (
            np.load(directory / a / "states.npz", allow_pickle=False) as x,
            np.load(directory / b / "states.npz", allow_pickle=False) as y,
        ):
            repeats.append(
                {
                    "pair": [a, b],
                    "exact_arrays": x.files == y.files
                    and all(np.array_equal(x[k], y[k]) for k in x.files),
                }
            )
    contrasts = []
    repeatable = all(row["exact_arrays"] for row in repeats)
    for factor in ("cone", "timeconst"):
        other = {"friction", "timestep", "timeconst", "cone"} - {factor}
        for i, left in enumerate(results[:24]):
            for right in results[i + 1 : 24]:
                a, b = left["job"], right["job"]
                if a[factor] == b[factor] or any(a[key] != b[key] for key in other):
                    continue
                comparable = (
                    repeatable and left["result"]["valid"] and right["result"]["valid"]
                )
                contrasts.append(
                    {
                        "factor": factor,
                        "pair": [a["id"], b["id"]],
                        "comparable": comparable,
                        "right_minus_left": {
                            key: right["result"]["metrics"][key] - value
                            for key, value in left["result"]["metrics"].items()
                        }
                        if comparable
                        else None,
                    }
                )
    return {
        "cases": results,
        "contrasts": contrasts,
        "repeats": repeats,
        "valid_count": sum(r["result"]["valid"] for r in results),
        "engineering_pass_count": sum(
            r["result"]["valid"] and r["result"]["engineering"]["passed"]
            for r in results
        ),
    }
