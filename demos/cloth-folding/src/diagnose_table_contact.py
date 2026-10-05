"""Static table-edge contact counterexample. No integration or robot control."""

import argparse
import base64
import hashlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from cloth_model import CLOTH_RADIUS, add_table, numbers
from dexlab.cloth_table_audit import triangle_box_depth


def subdivide(triangle):
    """Four coplanar triangles covering exactly the original surface."""
    points = np.vstack((triangle, (triangle + triangle[[1, 2, 0]]) / 2))
    return points, np.array([[0, 3, 5], [3, 1, 4], [5, 4, 2], [3, 4, 5]])


def query(points, triangles, witness_ids, *, disable_midphase=False):
    """Evaluate collision detection at prescribed coordinates, not dynamics."""
    root = ET.Element("mujoco")
    ET.SubElement(root, "compiler", fusestatic="false")
    world = ET.SubElement(root, "worldbody")
    add_table(world)
    flex = ET.SubElement(world, "flexcomp", name="cloth", type="direct", dim="2",
                         mass=".015", radius=str(CLOTH_RADIUS), point=numbers(points),
                         element=numbers(triangles))
    ET.SubElement(flex, "edge", equality="true")
    ET.SubElement(flex, "contact", selfcollide="none",
                  **({"internal": "false"} if mujoco.mj_version() < 315 else {}),
                  contype="1", conaffinity="3", condim="3", friction="1 .005 .0001",
                  solref=".002 1", solimp=".99 .999 .001")
    model = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding="unicode"))
    if disable_midphase:
        model.opt.disableflags |= int(mujoco.mjtDisableBit.mjDSBL_MIDPHASE)
    data = mujoco.MjData(model)
    mujoco.mj_fwdPosition(model, data)
    if not np.allclose(data.flexvert_xpos, points, atol=1e-14, rtol=0):
        raise ValueError("Compiled geometry differs from prescribed coordinates")
    contacts = [
        {"element": int(c.elem[1]), "table": model.geom(int(c.geom[0])).name,
         "distance_m": float(c.dist), "position_m": c.pos.tolist(),
         "normal": c.frame[:3].tolist()}
        for c in data.contact if c.elem[1] in witness_ids
    ]
    return {"all_contacts": data.ncon, "witness_contacts": contacts,
            "witness_max_native_penetration_m": max([0.0, *(-c["distance_m"] for c in contacts)]),
            "physical_time_s": data.time, "table_geometries": model.ngeom}


def engine_identity():
    distribution = importlib.metadata.distribution("mujoco")
    entry = next(p for p in distribution.files if p.name.startswith("libmujoco.so."))
    raw = distribution.locate_file(entry).read_bytes()
    digest = hashlib.sha256(raw).digest()
    matches = (entry.hash is not None and entry.hash.mode == "sha256"
               and entry.hash.value == base64.urlsafe_b64encode(digest).rstrip(b"=").decode())
    if not matches:
        raise ValueError("Native MuJoCo library does not match its wheel RECORD")
    return {"version": mujoco.__version__, "library_sha256": digest.hex(),
            "wheel_record_matches": matches}


def diagnose(reference):
    reference = Path(reference)
    before = hashlib.sha256(reference.read_bytes()).hexdigest()
    with np.load(reference, allow_pickle=False) as data:
        points, triangles, bounds = data["vertices"][0], data["triangles"], data["bounds"]
        frame, time = int(data["frame_index"][0]), float(data["time_s"][0])
        expected = float(data["expected_depth_m"][0])
        original_hashes = {key: str(data[key]) for key in ("source_model_sha256", "source_states_sha256")}
    depths = [triangle_box_depth(t, *bounds) for t in points[triangles]]
    index = int(np.argmax(depths))
    witness = points[triangles[index]]
    if not np.isclose(depths[index], expected, atol=1e-8, rtol=0):
        raise ValueError("Independent geometry no longer matches the historical reference")
    refined, faces = subdivide(witness)
    raised = witness + [0, 0, 0.02]
    cases = {
        "single_witness": (witness, np.array([[0, 1, 2]]), {0}, False),
        "whole_panel": (points, triangles, {index}, False),
        "midphase_disabled": (witness, np.array([[0, 1, 2]]), {0}, True),
        "refined_witness": (refined, faces, set(range(4)), False),
        "raised_witness": (raised, np.array([[0, 1, 2]]), {0}, False),
    }
    results = {}
    for name, (vertices, elements, selected, disable) in cases.items():
        result = query(vertices, elements, selected, disable_midphase=disable)
        result["witness_interior_depth_m"] = max(
            triangle_box_depth(vertices[elements[i]], *bounds) for i in selected
        )
        results[name] = result
    if hashlib.sha256(reference.read_bytes()).hexdigest() != before:
        raise ValueError("Reference changed during analysis")
    return {
        "schema_version": 1, "classification": "static_contact_coverage_diagnostic",
        "engine": engine_identity(), "physics_steps_executed": 0,
        "input_sha256": before, "original_record_hashes": original_hashes,
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [Path(__file__), Path(__file__).with_name("cloth_model.py"),
                                    Path(inspect.getfile(triangle_box_depth))]},
        "frame_index": frame, "recorded_time_s": time, "triangle_id": index,
        "triangle_vertices_m": witness.tolist(), "table_bounds_m": bounds.tolist(),
        "collision_radius_m": CLOTH_RADIUS,
        "vertex_interior_depth_m": np.maximum(np.minimum(witness - bounds[0], bounds[1] - witness)
                                              .min(axis=1), 0).tolist(),
        "cases": results,
        "limits": ["Static rebuilt geometry only; no settling, grasp or release validation",
                   "No robot, bending response or self-contact in the reduced queries",
                   "Subdivision preserves this surface, not dynamic degrees of freedom or material response",
                   "Box interior depth and native contact distance are different metrics",
                   "No physical success criterion or published threshold changed"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; use a new file")
    result = diagnose(args.reference)
    with args.output.open("x") as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write("\n")


if __name__ == "__main__":
    main()
