"""Measured event localization; stage labels are diagnostic hypotheses, never scores."""

import json
from pathlib import Path


def events(raw):
    import numpy as np

    raw = Path(raw)
    run = json.loads((raw / "run.json").read_text())
    params = json.loads((raw / "parameters-effective.json").read_text())
    names = params["geom_names"]
    with np.load(raw / "trajectory.npz") as record:
        states = record["state"]
        qadr = run["object_qpos_adr"]
        height = states[:, 1 + qadr + 2]
        initial = record["initial"][1 + qadr + 2]
        lifted = np.flatnonzero(height > initial + 0.01)
        success = np.flatnonzero(record["success"])
    contacts = [
        json.loads(line) for line in (raw / "contacts.jsonl").read_text().splitlines()
    ]
    finger = []
    basket = []
    other = []
    for frame in contacts:
        for contact in frame["contacts"]:
            if contact["local_wrench"][0] <= 1e-4:
                continue
            pair = [names[contact[k]] or "" for k in ("geom1", "geom2")]
            time = frame["time_s"]
            if contact["finger"]:
                finger.append(time)
            elif any("basket_" in n for n in pair):
                basket.append(time)
            elif not any("table" in n or n == "floor" for n in pair):
                other.append(dict(time_s=time, geoms=pair))
    first_lift = float(states[lifted[0], 0]) if len(lifted) else None
    first_basket = min(basket) if basket else None
    collision = next(
        (e for e in other if first_lift is not None and e["time_s"] >= first_lift), None
    )
    # Absence of contact is not enough to infer accidental slip rather than a release.
    if run["native_success_final"]:
        stage = "native-success"
    elif not finger:
        stage = "no-recorded-finger-contact"
    elif first_lift is None:
        stage = "no-measured-lift"
    elif first_basket is not None:
        stage = "placement-failure-candidate"
    elif collision:
        stage = "transport-collision-candidate"
    else:
        stage = "post-lift-failure-unresolved-slip-or-release"
    return dict(
        classification=stage,
        first_finger_contact_s=min(finger) if finger else None,
        first_lift_s=first_lift,
        first_basket_contact_s=first_basket,
        first_other_contact_after_lift=collision,
        first_native_success_s=float(states[success[0], 0]) if len(success) else None,
        last_finger_contact_s=max(finger) if finger else None,
        thresholds=dict(lift_above_initial_m=0.01, contact_normal_n=1e-4),
        interpretation="Descriptive event thresholds, not task or physics acceptance. Post-lift contact loss needs action/control and geometry review before calling it slip.",
    )
