"""Record SuperDex SDF contacts at every physics step for offline acceptance."""

import importlib.metadata
import json

import numpy as np
from physics_utils import actor_poses, physics
from scipy.spatial.transform import Rotation
from verify_sdf_grasp import verify_grasp


class GraspRecorder:
    def __init__(
        self, destination, body, table, links, names, fruit_vertices, table_top, dt
    ):
        self.destination = destination
        self.body, self.table = body, table
        self.links, self.names = links, names
        self.vertices, self.table_top, self.dt = fruit_vertices, table_top, dt
        self.lookup = {link.get_handle().value: i for i, link in enumerate(links)}
        self.wrist = links[names.index("r_wrist")]
        self.base = links[names.index("openarm_body_link0")]
        self.hand = [link for name, link in zip(names, links) if name.startswith("r_")]
        self.rows = []
        self.contacts = []
        self.engine = {
            "backend": "superdex",
            "fp64": bool(physics.uses_double_precision()),
            "dt": dt,
            "mass_kg": body.get_mass(),
            "apple_dynamic": not body.is_static(),
            "body_names": names,
            "completed": False,
            "grasp_collider_types": {
                n: links[names.index(n)].get_collider_type().name
                for n in ("r_thumb_pad", "r_index_finger_pad")
            },
            "contact_normal_column": "Zero placeholder; acceptance uses recorded world-force vectors.",
            "control": "Known settled object pose, scripted joint-target prior, native contact dynamics.",
        }
        for key, package in (
            ("version", "superdex-physics"),
            ("robotics_version", "superdex-robotics"),
        ):
            try:
                self.engine[key] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                self.engine[key] = "source build; distribution metadata unavailable"
        self.engine["grasp_collider_types"]["apple"] = body.get_collider_type().name
        (destination / "engine.json").write_text(json.dumps(self.engine, indent=2))

    def record(self, time, velocity_before, status):
        body, table = self.body, self.table
        poses = actor_poses([body, self.wrist, self.base])
        rotation = Rotation.from_quat(poses[0, 3:])
        total = np.array(body.get_contact_force_world())
        table_force = np.array(body.get_contact_force_from_actor_world(table))
        hand_force = sum(
            (
                np.asarray(body.get_contact_force_from_actor_world(link))
                for link in self.hand
            ),
            start=np.zeros(3),
        )
        penetration = 0.0
        for point in body.get_contact_points_world():
            on_a = point.actor_a == body.get_handle()
            other = point.actor_b if on_a else point.actor_a
            index = self.lookup.get(other.value)
            if index is None or not self.names[index].startswith("r_"):
                continue
            force = np.asarray(point.force) * (1 if on_a else -1)
            local = rotation.inv().apply(
                np.asarray(point.pos_a if on_a else point.pos_b) - poses[0, :3]
            )
            self.contacts.append([time, index, *local, point.distance, 0, *force])
            penetration = max(penetration, -float(point.distance))
        self.rows.append(
            {
                "time": time,
                "apple_pose": poses[0],
                "wrist_pose": poses[1],
                "base_pose": poses[2],
                "clearance": float(
                    (rotation.apply(self.vertices) + poses[0, :3])[:, 2].min()
                    - self.table_top
                ),
                "velocity_before": velocity_before,
                "velocity": np.array(body.get_linear_velocity()),
                "total": total,
                "hand": hand_force,
                "table": table_force,
                "other": total - table_force - hand_force,
                "penetration": penetration,
                "warnings": int(status == "DIVERGED"),
            }
        )

    def finish(self):
        np.savez_compressed(
            self.destination / "sdf-dynamics.npz",
            **{k: [r[k] for r in self.rows] for k in self.rows[0]},
        )
        np.savez_compressed(
            self.destination / "sdf-contacts.npz",
            contacts=np.asarray(self.contacts).reshape(-1, 10),
        )
        self.engine.update(
            completed=True, steps=len(self.rows), duration=len(self.rows) * self.dt
        )
        (self.destination / "engine.json").write_text(json.dumps(self.engine, indent=2))
        result = verify_grasp(self.destination)
        (self.destination / "summary.json").write_text(json.dumps(result, indent=2))
        return result
