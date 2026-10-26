"""Reject an invalid initial native scene before any integration step."""

import mujoco


def inspect_initial_state(model, data, maximum_penetration_m):
    mujoco.mj_forward(model, data)
    contacts = [dict(geom1=model.geom(c.geom1).name, geom2=model.geom(c.geom2).name,
                     distance_m=float(c.dist), position=c.pos.tolist()) for c in data.contact]
    contacts.sort(key=lambda contact: contact["distance_m"])
    invalid = [contact for contact in contacts if contact["distance_m"] < -maximum_penetration_m]
    return dict(pass_initial_geometry=not invalid, contacts=contacts, excessive_penetration=invalid,
                maximum_penetration_m=maximum_penetration_m,
                scope="All native initial contacts, including hand self-collision; no mj_step.")
