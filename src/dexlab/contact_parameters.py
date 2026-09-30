"""Check declared fixture parameters against archived native engine readbacks.

These checks compare measured metadata with the independent case definition.
They do not replace archive hashes or prove the cooked collision surface.
"""

import json

import numpy as np


def normal_parameters(engine, overrides=None):
    """Resolve explicit native parameters; their numerical values are not portable."""
    defaults = {
        "mujoco": {"solref": [0.005, 1.0], "solimp": [0.95, 0.99, 0.001, 0.5, 2.0]},
        "superdex": {
            "penalty_coefficient": 1e9,
            "penalty_threshold_default": 0.0001,
            "penalty_smoothing_half_distance": 0.00005,
            "normal_viscous_damping_coefficient": 0.0,
        },
        "physx": {"compliant_contact_stiffness": 0.0, "compliant_contact_damping": 0.0},
    }
    if engine not in defaults:
        raise ValueError(f"Unknown engine: {engine}")
    overrides = {} if overrides is None else overrides
    if (
        not isinstance(overrides, dict)
        or not overrides.keys() <= defaults[engine].keys()
    ):
        raise ValueError("Unknown normal contact parameter")
    values = defaults[engine] | overrides
    for name, value in values.items():
        array = np.asarray(value)
        if array.dtype.kind not in "fiu" or not np.isfinite(array).all():
            raise ValueError(f"Expected finite numeric {name}")
    if engine == "mujoco":
        ref, imp = np.asarray(values["solref"]), np.asarray(values["solimp"])
        if ref.shape != (2,) or imp.shape != (5,):
            raise ValueError("Expected solref[2] and solimp[5]")
        if not (np.all(ref > 0) or (ref[0] < 0 and ref[1] <= 0)):
            raise ValueError("Use positive time constants or negative direct solref")
        if not (
            0 < imp[0] <= imp[1] < 1 and imp[2] > 0 and 0 < imp[3] < 1 and imp[4] >= 1
        ):
            raise ValueError("Invalid impedance curve")
        return {k: np.asarray(v, dtype=float).tolist() for k, v in values.items()}
    if any(np.shape(v) or float(v) < 0 for v in values.values()):
        raise ValueError("Expected nonnegative scalar native parameters")
    if engine == "superdex" and values["penalty_coefficient"] <= 0:
        raise ValueError("Penalty coefficient must be positive")
    if engine == "physx" and overrides:
        if overrides.keys() != defaults[engine].keys():
            raise ValueError("Specify both compliant stiffness and damping")
        if (
            values["compliant_contact_stiffness"] == 0
            and values["compliant_contact_damping"] != 0
        ):
            raise ValueError("Rigid contact cannot have compliant damping")
    return {k: float(v) for k, v in values.items()}


def normal_readback_matches(engine, declared, native):
    """Validate the normal profile independently from trace response matching."""
    try:
        expected = normal_parameters(engine, declared)
        actual = native["normal_parameters_readback"]
        return actual.keys() == expected.keys() and all(
            _matches(actual[k], v) for k, v in expected.items()
        )
    except (KeyError, TypeError, ValueError):
        return False


def required_native_files(engine, *, cylinder=False):
    if engine == "mujoco":
        return {"model.xml"}
    if engine == "superdex":
        return {"geometry.npz"}
    if engine == "physx":
        names = ("left", "right", "cylinder") if cylinder else ("box", "table")
        return {
            "native-records.json",
            "layout.json",
            "import-report.json",
            "worker-exit.json",
            "worker-stderr.log",
            "scene/sensors.xml",
            *(f"scene/{name}.xml" for name in names),
        }
    raise ValueError(f"Unknown native engine: {engine}")


def _matches(actual, expected):
    actual, expected = (
        np.asarray(actual, dtype=float),
        np.asarray(expected, dtype=float),
    )
    # Legacy archives include rounded MJCF values; current inertials retain full
    # export precision before native float32 conversion. Keep the frozen
    # tolerance for historical scoring; it is not a material accuracy limit.
    return bool(
        actual.shape == expected.shape
        and np.isfinite(actual).all()
        and np.allclose(actual, expected, rtol=3e-6, atol=1e-12)
    )


def native_checks(directory, receipt, case, *, cylinder=False):
    """Fail closed on absent/malformed mass, inertia, friction or worker records."""
    checks = dict.fromkeys(
        ("native_mass_matches", "native_inertia_matches", "native_friction_matches"),
        False,
    )
    engine = receipt["engine"]
    if engine == "physx":
        checks.update(native_layout_matches=False, clean_worker_exit=False)
    try:
        meta = receipt["native"]
        if cylinder:
            from dexlab.contact_pinch import PAD_HALF, PAD_MASS

            pad_inertia = (
                PAD_MASS
                / 3
                * np.array(
                    [
                        PAD_HALF[1] ** 2 + PAD_HALF[2] ** 2,
                        PAD_HALF[0] ** 2 + PAD_HALF[2] ** 2,
                        PAD_HALF[0] ** 2 + PAD_HALF[1] ** 2,
                    ]
                )
            )
            masses = np.array([PAD_MASS, PAD_MASS, case.mass])
            inertias = np.array([pad_inertia, pad_inertia, case.inertia])
            bodies = [("left", "pad"), ("right", "pad"), ("cylinder", "body")]
        else:
            masses, inertias = np.array([case.mass]), np.array([case.inertia])
            bodies = [("box", "body")]

        if engine == "mujoco":
            mass = np.asarray(meta["mass_readback"])
            inertia = np.asarray(meta["inertia_readback"])
            if cylinder:
                mass, inertia = mass[1:], inertia[1:]
            else:
                mass, inertia = mass.reshape(1), inertia.reshape(1, 3)
            checks["native_mass_matches"] = _matches(mass, masses)
            checks["native_inertia_matches"] = _matches(inertia, inertias)
            count = 3 if cylinder else 2
            checks["native_friction_matches"] = _matches(
                meta["friction_readback"], [[case.friction, 0, 0]] * count
            )
        elif engine == "superdex":
            checks["native_mass_matches"] = _matches(
                np.asarray(meta["mass_readback"]).reshape(-1), masses
            )
            expected = np.zeros((len(masses), 6))
            expected[:, [0, 3, 5]] = inertias
            checks["native_inertia_matches"] = _matches(
                np.asarray(meta["inertia_readback"]).reshape(-1, 6), expected
            )
            checks["native_friction_matches"] = _matches(
                meta["contact"]["coulomb_friction_coefficient"], case.friction
            )
            if "friction_readback" in meta:
                checks["native_friction_matches"] &= _matches(
                    meta["friction_readback"], [case.friction] * (3 if cylinder else 2)
                )
        elif engine == "physx":
            records = json.loads((directory / "native-records.json").read_text())
            layout = json.loads((directory / "layout.json").read_text())
            entities = {entity["name"]: entity for entity in layout["entities"]}
            ids, native_mass, native_inertia = [], [], []
            for entity_name, body_name in bodies:
                entity = entities[entity_name]
                index = entity["body_names"].index(body_name)
                ids.append(entity["body_ids"][index])
                record = records[entity_name]
                native_mass.append(record["body_mass"][0][index])
                native_inertia.append(record["body_inertia"][0][index])
            checks["native_layout_matches"] = bool(
                len(ids) == len(set(ids))
                and (not cylinder or meta["body_ids"] == ids)
                and layout["nu"] == 0
            )
            checks["native_mass_matches"] = _matches(native_mass, masses) and _matches(
                np.asarray(meta["mass_readback"])[0, ids], masses
            )
            checks["native_inertia_matches"] = _matches(
                native_inertia, np.array([np.diag(inertia) for inertia in inertias])
            )
            count = 3 if cylinder else 2
            friction = [[case.friction, case.friction, 0]] * count
            checks["native_friction_matches"] = _matches(
                meta["friction_readback"], [friction]
            ) and all(
                _matches(record["geom_friction"], [[[case.friction, case.friction, 0]]])
                for record in records.values()
            )
            checks["clean_worker_exit"] = json.loads(
                (directory / "worker-exit.json").read_text()
            ) == {"terminated": True, "returncode": 0}
    except (OSError, KeyError, IndexError, TypeError, ValueError):
        # Earlier independent checks remain useful even when a later field is bad.
        pass
    return checks
