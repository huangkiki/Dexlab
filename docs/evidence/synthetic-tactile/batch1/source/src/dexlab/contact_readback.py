"""Diagnose observed planar contact parameters without changing physics verdicts.

This is limited to the declared equal-material box/plane fixture. It does not
infer SuperDex's unexposed pair law or validate general mesh cooking.
"""

import numpy as np


def _equal(actual, expected):
    actual, expected = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    return bool(actual.shape == expected.shape and np.isfinite(actual).all()
                and np.allclose(actual, expected, rtol=1e-12, atol=1e-12))


def audit_plane_parameters(engine, native, contacts, case):
    """Return scoped evidence; missing pair readback remains unknown, never a pass."""
    if engine == "superdex":
        actors = native.get("actor_contact_parameters", {})
        fields = ("penalty_coefficient", "penalty_threshold_default",
                  "penalty_smoothing_half_distance", "coulomb_friction_coefficient",
                  "friction_falloff_vel", "normal_viscous_damping_coefficient",
                  "viscous_friction_coefficient")
        try:
            left, right = actors["box"], actors["plane"]
            equal = all(_equal(left[k], right[k]) for k in fields)
        except (KeyError, TypeError, ValueError):
            equal = False
        return {"actor_profiles_equal": equal, "pair_parameters_match": None,
                "geometry_matches": None, "status": "pair_readback_unavailable"}
    if engine != "mujoco":
        raise ValueError("Only the MuJoCo/SuperDex planar fixture is supported")
    count, missing, mismatched = 0, 0, 0
    try:
        geometry = native["geometry_readback"]
        geometry_ok = (_equal(geometry["type"], [0, 6])  # mjGEOM_PLANE, mjGEOM_BOX
                       and _equal(geometry["size"], [[2, 2, .1], [case.half_size] * 3]))
        profile_ok = (_equal(geometry["priority"], [0, 0])
                      and _equal(geometry["solmix"], [1, 1])
                      and _equal(geometry["condim"], [3, 3])
                      and _equal(native["friction_readback"], [[case.friction, 0, 0]] * 2))
        normal = native["normal_parameters_readback"]
        profile_ok &= all(_equal(geometry[k], [normal[k]] * 2) for k in ("solref", "solimp"))
    except (KeyError, TypeError, ValueError):
        geometry_ok, profile_ok = False, False
        normal = {}
    # MuJoCo mjMINMU clamps every native friction component, including inactive
    # torsion/rolling dimensions. These are parameter values, not force estimates.
    expected_friction = [max(case.friction, 1e-5)] * 2 + [1e-5] * 3
    if not isinstance(contacts, (list, tuple)):
        contacts = [None]
    for row in contacts:
        if not isinstance(row, (list, tuple)):
            missing += 1
            continue
        for contact in row:
            count += 1
            try:
                p = contact["parameters"]
                valid = (sorted([contact["geom1"], contact["geom2"]]) == [0, 1]
                         and p["dimension"] == 3
                         and _equal(p["friction"], expected_friction)
                         and _equal(p["solref"], normal["solref"])
                         and _equal(p["solimp"], normal["solimp"])
                         and _equal(p["include_margin"], 0))
                mismatched += not valid
            except (KeyError, TypeError, ValueError):
                missing += 1
    matched = bool(count and profile_ok and missing == 0 and mismatched == 0)
    return {"geometry_matches": geometry_ok, "actor_profiles_equal": profile_ok,
            "pair_parameters_match": matched, "contacts": count,
            "missing": missing, "mismatched": mismatched,
            "status": "consistent" if geometry_ok and matched else "incomplete_or_mismatch"}


def diagnose_archive(directory):
    """Verify full archive integrity first; retain physical failure separately."""
    import json
    from pathlib import Path
    from dexlab.contact_archive import read_contacts
    from dexlab.contact_plane import PlaneCase
    from dexlab.contact_plane_native import verify

    directory = Path(directory)
    acceptance = verify(directory)
    integrity = ("native_run_completed", "source_unchanged",
                 "archived_source_hashes_match", "clean_shutdown",
                 "declared_limits", "artifact_hashes_match", "contact_ledger_matches")
    if not all(acceptance["checks"].get(key, False) for key in integrity):
        return {"status": "untrusted_archive", "archive_acceptance": acceptance,
                "readback": None}
    receipt = json.loads((directory / "run.json").read_text())
    result = audit_plane_parameters(receipt["engine"], receipt["native"],
                                    read_contacts(directory, receipt), PlaneCase(**receipt["case"]))
    return {"status": "available", "archive_acceptance": acceptance, "readback": result}


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    args = parser.parse_args()
    report = diagnose_archive(args.directory)
    print(json.dumps(report, indent=2, allow_nan=False))
    readback = report["readback"]
    complete = readback is not None and readback["status"] == "consistent"
    raise SystemExit(0 if complete and report["archive_acceptance"]["passed"] else 1)


if __name__ == "__main__":
    main()
