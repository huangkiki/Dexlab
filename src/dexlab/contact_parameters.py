"""Check declared fixture parameters against archived native engine readbacks.

These checks compare measured metadata with the independent case definition.
They do not replace archive hashes or prove the cooked collision surface.
"""

import json

import numpy as np


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
    # Native PhysX records pass through six-significant-digit MJCF import fields.
    # This tolerance covers that conversion, not a physical calibration error.
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
