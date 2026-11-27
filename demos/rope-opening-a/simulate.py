"""Run the native libuipc Opening A rope scene and record the raw trajectories."""

import argparse
from importlib.metadata import version
import json
from pathlib import Path

import numpy as np

DT = 1 / 120
STEPS = 240
START_HALF_SPAN = 0.192
END_HALF_SPAN = 0.245
OPEN_STEPS = 144
GUIDE_RADII = np.array([0.025, 0.037])
ROPE_RADIUS = 0.0014
CONTACT_DISTANCE = 0.0014


def initial_loop():
    """Sample two bowed spans and two open semicircles as one closed curve."""
    along = np.linspace(0.0, 1.0, 501)
    pitch = GUIDE_RADII + ROPE_RADIUS + 0.0008
    nominal_length = 2 * END_HALF_SPAN - 0.002
    low, high = 0.0, 0.25
    for _ in range(32):
        bow = (low + high) / 2
        x = START_HALF_SPAN * (2 * along - 1)
        y = pitch[1] + bow * np.sin(np.pi * along) ** 2
        length = np.linalg.norm(np.diff(np.column_stack((x, y)), axis=0), axis=1).sum()
        if length < nominal_length:
            low = bow
        else:
            high = bow
    upper = np.column_stack((x[:-1], y[:-1]))
    angles = np.linspace(np.pi / 2, -np.pi / 2, 241)[:-1]
    right = np.column_stack((START_HALF_SPAN + pitch[0] * np.cos(angles), pitch[1] * np.sin(angles)))
    path = np.vstack((upper, right, -upper, -right, upper[:1]))
    lengths = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    samples = np.linspace(0.0, lengths[-1], 160, endpoint=False)
    vertices = np.column_stack([np.interp(samples, lengths, axis) for axis in path.T] +
                               [np.zeros(samples.size)])
    indices = np.arange(len(vertices), dtype=np.int32)
    return vertices, np.column_stack((indices, np.roll(indices, -1)))


def guide_surface():
    """Build a closed elliptical spool with raised rims on both depth sides."""
    count = 32
    angles = 2 * np.pi * np.arange(count) / count
    ring = np.column_stack((np.cos(angles), np.sin(angles))) * GUIDE_RADII
    rings = [(-0.026, 1.20), (-0.019, 1.30), (-0.008, 1.02), (0.0, 1.0),
             (0.008, 1.02), (0.019, 1.30), (0.026, 1.20)]
    points = np.vstack([np.column_stack((scale * ring, np.full(count, z))) for z, scale in rings])
    faces = []
    for layer in range(len(rings) - 1):
        for index in range(count):
            a = layer * count + index
            b = layer * count + (index + 1) % count
            faces.extend(((a, b, a + count), (b, b + count, a + count)))
    front = len(points) - count
    for index in range(1, count - 1):
        faces.extend(((0, index + 1, index), (front, front + index, front + index + 1)))
    return points, np.asarray(faces, dtype=np.int32)


def half_span(frame):
    progress = min(frame / OPEN_STEPS, 1.0)
    easing = progress**3 * (10 - 15 * progress + 6 * progress**2)
    return START_HALF_SPAN + easing * (END_HALF_SPAN - START_HALF_SPAN)


def simulate(output, guide_contact):
    from uipc import Logger, builtin, view
    from uipc.constitution import AffineBodyConstitution, HookeanSpring, KirchhoffRodBending, SoftTransformConstraint
    from uipc.core import Engine, Scene, World
    from uipc.geometry import label_surface, linemesh, trimesh

    output.mkdir(parents=True)
    Logger.set_level(Logger.Level.Warn)
    workspace = output / "engine"
    workspace.mkdir()
    engine = Engine("cuda", str(workspace))
    world = World(engine)
    config = Scene.default_config()
    config["dt"] = DT
    config["contact"]["d_hat"] = CONTACT_DISTANCE
    config["newton"].update(max_iter=128, velocity_tol=0.005)
    scene = Scene(config)

    contacts = scene.contact_tabular()
    contacts.default_model(0.20, 1e8)
    rope_element = contacts.default_element()
    guide_element = contacts.create("palm guides")
    contacts.insert(rope_element, guide_element, 0.24, 1e8, guide_contact)

    rest, edges = initial_loop()
    rope = linemesh(rest, edges)
    HookeanSpring().apply_to(rope, moduli=1.5e7, mass_density=1100.0, thickness=ROPE_RADIUS)
    KirchhoffRodBending().apply_to(rope, 5.0e5)
    rope_element.apply_to(rope)
    label_surface(rope)
    rope_slot, _ = scene.objects().create("closed rope").geometries().create(rope)
    rope_geometry = rope_slot.geometry()
    fixed = view(rope_geometry.vertices().find(builtin.is_fixed))
    if np.any(fixed):
        raise RuntimeError("Opening A requires an unpinned rope")

    guide_vertices, guide_faces = guide_surface()
    guide_slots = []
    for side in (-1, 1):
        guide = trimesh(guide_vertices, guide_faces)
        label_surface(guide)
        AffineBodyConstitution().apply_to(guide, 1e8, mass_density=2000.0)
        SoftTransformConstraint().apply_to(guide, np.array([80.0, 80.0]))
        guide_element.apply_to(guide)
        view(guide.transforms())[0, 0, 3] = side * half_span(0)
        obj = scene.objects().create(f"palm guide {side:+}")
        slot, _ = obj.geometries().create(guide)
        guide_slots.append(slot)

        def move_guide(info, direction=side):
            instances = info.geo_slots()[0].geometry().instances()
            view(instances.find(builtin.is_constrained))[0] = 1
            target = np.eye(4)
            target[0, 3] = direction * half_span(info.frame())
            view(instances.find(builtin.aim_transform))[0] = target

        scene.animator().insert(obj, move_guide)

    settings = {
        "pyuipc": version("pyuipc"),
        "backend": "cuda",
        "scene": config,
        "guide_contact": guide_contact,
        "rope_fixed_vertices": int(np.count_nonzero(fixed)),
    }
    (output / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")
    world.init(scene)
    if not world.is_valid():
        raise RuntimeError("libuipc rejected the initial scene")
    positions, guide_transforms = [], []
    try:
        for frame in range(STEPS + 1):
            if frame:
                world.advance()
                world.retrieve()
                if not world.is_valid() or world.frame() != frame:
                    raise RuntimeError(f"libuipc did not advance to frame {frame}")
            points = rope_geometry.positions().view().reshape(-1, 3).copy()
            guides = np.stack([slot.geometry().transforms().view()[0].copy() for slot in guide_slots])
            if not np.isfinite(points).all() or not np.isfinite(guides).all():
                raise RuntimeError(f"Non-finite native state at frame {frame}")
            positions.append(points)
            guide_transforms.append(guides)
            if frame % 60 == 0:
                print(f"libuipc frame {frame}/{STEPS}", flush=True)
    finally:
        np.savez_compressed(
            output / "trajectory.npz", positions=positions, edges=edges,
            transforms=guide_transforms, guide_vertices=guide_vertices, guide_faces=guide_faces,
            times=DT * np.arange(len(positions)), guide_contact=guide_contact,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New output directory")
    parser.add_argument("--no-guide-contact", action="store_true", help="Disable only rope–guide contact")
    args = parser.parse_args()
    simulate(args.output, not args.no_guide_contact)
