"""Evaluation-only contact recorder for the pinned Isaac Lab 3 backflip case.

The upstream evaluator expects ``model``, ``floor``, ``feet``, ``save`` and
``close``. This implementation additionally retains every contact pair and the
state on both sides of the original MuJoCo Warp step, after Newton refreshes
its inputs. It never calls mj_forward.
"""

import hashlib
import inspect
import json
from pathlib import Path

import mujoco
import numpy as np

active_recorder = None


def native_contacts(model, data):
    """Copy geometry, activation and solved local force for every native contact."""
    pairs, distances, frames, addresses, forces = [], [], [], [], []
    for index in range(data.ncon):
        contact = data.contact[index]
        force = np.zeros(6)
        mujoco.mj_contactForce(model, data, index, force)
        pairs.append(np.asarray(contact.geom).copy())
        distances.append(float(contact.dist))
        frames.append(np.asarray(contact.frame).reshape(3, 3).copy())
        addresses.append(int(contact.efc_address))
        forces.append(force)
    return {
        "pairs": np.asarray(pairs, dtype=np.int64).reshape(-1, 2),
        "distances": np.asarray(distances, dtype=float),
        "frames": np.asarray(frames, dtype=float).reshape(-1, 3, 3),
        "efc_address": np.asarray(addresses, dtype=np.int64),
        "local_forces": np.asarray(forces, dtype=float).reshape(-1, 6),
    }


def ground_forces(contacts, floor, feet, threshold_n=.001):
    """Keep individual loaded-pair counts separate from summed force vectors."""
    forces = np.zeros((2, 3))
    counts = np.zeros(2, dtype=int)
    total, nonfoot = np.zeros(3), np.zeros(3)
    nonfoot_count = 0
    for pair, frame, local in zip(contacts["pairs"], contacts["frames"], contacts["local_forces"]):
        g1, g2 = map(int, pair)
        if g1 not in floor and g2 not in floor:
            continue
        world = frame.T @ local[:3]
        if g2 in floor:
            world, other = -world, g1
        else:
            other = g2
        total += world
        side = next((i for i, group in enumerate(feet) if other in group), None)
        loaded = np.linalg.norm(world) > threshold_n
        if side is None:
            nonfoot += world
            nonfoot_count += int(loaded)
        else:
            forces[side] += world
            counts[side] += int(loaded)
    return dict(forces=forces, contact_counts=counts, total_ground_force=total,
                nonfoot_force=nonfoot, nonfoot_contacts=nonfoot_count)


def _save_npz(path, **arrays):
    with Path(path).open("xb") as stream:
        np.savez_compressed(stream, **arrays)


def _contact_count(data):
    count = int(data.nacon.numpy()[0])
    constraints = int(data.nefc.numpy()[0])
    if count < 0 or count > data.naconmax or constraints < 0 or constraints > data.njmax:
        raise ValueError("Native contact/constraint capacity overflow; refusing truncated evidence")
    return count


def warp_candidates(data):
    """Retain candidates before get_data_into filters contact types or caps arrays."""
    count = _contact_count(data)
    rows = {name: getattr(data.contact, name).numpy()[:count].copy()
            for name in ("geom", "dist", "frame", "type", "worldid", "efc_address",
                         "dim", "friction", "includemargin", "solref", "solimp")}
    if np.any(rows["worldid"] != 0):
        raise ValueError("Unexpected second world in the single-world recorder")
    return rows


def warp_options(options):
    """Read the executing GPU options separately from the CPU model snapshot."""
    result = {name: int(getattr(options, name)) for name in (
        "integrator", "cone", "solver", "iterations", "ls_iterations", "ccd_iterations",
        "disableflags", "enableflags", "sdf_initpoints", "sdf_iterations",
        "broadphase", "broadphase_filter")}
    for name in ("run_collision_detection", "run_rne_postconstraint", "graph_conditional"):
        result[name] = bool(getattr(options, name))
    for name in ("timestep", "tolerance", "ls_tolerance", "ccd_tolerance", "gravity",
                 "impratio_invsqrt"):
        values = getattr(options, name).numpy()
        result[name] = {"values": values.tolist(), "dtype": str(values.dtype)}
    return result


class ContactRecorder:
    """Observe one native world; retain the upstream evaluator's small interface."""

    def __init__(self, env):
        import mujoco_warp

        global active_recorder
        if active_recorder is not None:
            raise ValueError("Only one active single-world recorder is supported")
        self.manager = env.sim.backend_manager
        if self.manager._cfg.use_cuda_graph:
            raise ValueError("Contact recording requires eager evaluation")
        self.solver = self.manager._solver
        if self.solver.mjw_data.nworld != 1:
            raise ValueError("This recorder qualifies exactly one native world")
        self.model = self.solver.mj_model
        self.data = mujoco.MjData(self.model)
        self.dt = float(self.manager.get_solver_dt())
        self.floor = set(np.flatnonzero(self.model.geom_type == mujoco.mjtGeom.mjGEOM_PLANE).tolist())
        self.feet = []
        for side in ("left", "right"):
            suffix = side + "_ankle_roll_link"
            bodies = [i for i in range(self.model.nbody)
                      if (self.model.body(i).name or "") == suffix
                      or (self.model.body(i).name or "").endswith(("/" + suffix, "_" + suffix))]
            if len(bodies) != 1:
                raise ValueError(f"Ambiguous {side} foot body: {bodies}")
            self.feet.append(set(np.flatnonzero(self.model.geom_bodyid == bodies[0]).tolist()))
        if not self.floor or not all(self.feet):
            raise ValueError("Ground and foot collision geometries must be present")
        self.samples, self.contacts = [], []
        self.candidates = []
        copy_source = Path(inspect.getsourcefile(mujoco_warp.get_data_into))
        self.copy_source_sha256 = hashlib.sha256(copy_source.read_bytes()).hexdigest()
        # Newton updates qpos/qvel from its own state at the outer step entry.
        # Observe the core boundary so "pre" is the state actually integrated.
        self.original = self.solver._mujoco_warp_step

        def recording_step(*args, **kwargs):
            _contact_count(self.solver.mjw_data)  # reject overflow before the copy helper clips it
            mujoco_warp.get_data_into(self.data, self.model, self.solver.mjw_data)
            before = {name: getattr(self.data, name).copy() for name in ("qpos", "qvel")}
            before_time = float(self.data.time)
            result = self.original(*args, **kwargs)
            candidates = warp_candidates(self.solver.mjw_data)
            mujoco_warp.get_data_into(self.data, self.model, self.solver.mjw_data)
            contacts = native_contacts(self.model, self.data)
            sample = {name: getattr(self.data, name).copy() for name in (
                "qpos", "qvel", "qfrc_actuator", "qfrc_applied", "xfrc_applied", "actuator_force", "ctrl",
                "qfrc_constraint", "qacc", "qacc_warmstart", "qfrc_bias", "qfrc_passive")}
            sample.update(ground_forces(contacts, self.floor, self.feet))
            sample.update(time=(len(self.samples) + 1) * self.dt,
                          native_time_before=before_time, native_time_after=float(self.data.time),
                          pre_qpos=before["qpos"], pre_qvel=before["qvel"],
                          native_candidates=len(candidates["dist"]), exported_contacts=int(self.data.ncon),
                          solver_niter=int(self.data.solver_niter[0]), nefc=int(self.data.nefc))
            self.samples.append(sample)
            self.contacts.append(contacts)
            self.candidates.append(candidates)
            return result

        self.recording_step = recording_step
        self.solver._mujoco_warp_step = recording_step
        active_recorder = self

    def save(self, path):
        if not self.samples:
            raise ValueError("No native substeps were recorded")
        path = Path(path)
        model_path = path.with_name("native_model.mjb")
        if model_path.exists():
            raise FileExistsError(model_path)
        mujoco.mj_saveModel(self.model, str(model_path))
        arrays = {key: np.asarray([row[key] for row in self.samples]) for key in self.samples[0]}
        names = [self.model.joint(i).name or "" for i in range(self.model.njnt)]
        _save_npz(path, dt=self.dt, mass=float(self.model.body_mass.sum()),
                  joint_names=np.asarray(names, dtype=str), **arrays)
        sizes = [len(row["pairs"]) for row in self.contacts]
        _save_npz(path.with_name("native_contacts.npz"), offsets=np.r_[0, np.cumsum(sizes)],
                  **{key: np.concatenate([row[key] for row in self.contacts]) for key in self.contacts[0]})
        sizes = [len(row["dist"]) for row in self.candidates]
        _save_npz(path.with_name("warp_candidates.npz"), offsets=np.r_[0, np.cumsum(sizes)],
                  **{key: np.concatenate([row[key] for row in self.candidates]) for key in self.candidates[0]})
        model = self.model
        gpu_model = self.solver.mjw_model
        gpu_parameters = {name: getattr(gpu_model, name).numpy().tolist() for name in (
            "body_mass", "body_inertia", "geom_type", "geom_bodyid", "geom_size",
            "geom_contype", "geom_conaffinity", "geom_condim", "geom_priority",
            "geom_friction", "geom_solref", "geom_solimp", "geom_margin", "geom_gap",
            "pair_geom1", "pair_geom2", "pair_friction", "pair_margin", "pair_gap",
            "actuator_gainprm", "actuator_biasprm")}
        metadata = {
            "schema_version": 1,
            "mujoco_version": mujoco.__version__,
            "physics_dt_s": self.dt,
            "floor": sorted(self.floor), "feet": [sorted(group) for group in self.feet],
            "joint_names": names,
            "geom_names": [model.geom(i).name or "" for i in range(model.ngeom)],
            "joint_qposadr": model.jnt_qposadr.tolist(), "joint_dofadr": model.jnt_dofadr.tolist(),
            "joint_type": model.jnt_type.tolist(),
            "geom_contype": model.geom_contype.tolist(), "geom_conaffinity": model.geom_conaffinity.tolist(),
            "geom_margin": model.geom_margin.tolist(), "geom_gap": model.geom_gap.tolist(),
            "geom_bodyid": model.geom_bodyid.tolist(),
            "actuator_forcelimited": model.actuator_forcelimited.tolist(),
            "actuator_forcerange": model.actuator_forcerange.tolist(),
            "actuator_ctrllimited": model.actuator_ctrllimited.tolist(),
            "actuator_ctrlrange": model.actuator_ctrlrange.tolist(),
            "joint_actuatorfrclimited": model.jnt_actfrclimited.tolist(),
            "joint_actuatorfrcrange": model.jnt_actfrcrange.tolist(),
            "gravity": model.opt.gravity.tolist(),
            "cone": int(model.opt.cone), "integrator": int(model.opt.integrator),
            "solver": int(model.opt.solver), "iterations": int(model.opt.iterations),
            "tolerance": float(model.opt.tolerance),
            "cpu_option_scope": "CPU model snapshot; executing GPU options are recorded separately",
            "warp_options": warp_options(self.solver.mjw_model.opt),
            "warp_model_parameters": gpu_parameters,
            "native_state_dtype": str(self.solver.mjw_data.qpos.numpy().dtype),
            "newton_update_data_interval": int(self.solver.update_data_interval),
            "recording_hook": "SolverMuJoCo._mujoco_warp_step, after _apply_mjc_control/_update_mjc_data",
            "source": "MuJoCo Warp data copied before and after the original solver step",
            "contact_copy_stage": "after solver step; collision evaluation epoch requires separate qualification",
            "solver_convergence_telemetry": "iteration count copied; residual and convergence status unavailable",
            "contact_copy_filter": "get_data_into exports CONSTRAINT|PASSIVE; all raw candidates retained separately",
            "copy_source_sha256": self.copy_source_sha256,
            "contact_capacity": int(self.solver.mjw_data.naconmax),
            "constraint_capacity": int(self.solver.mjw_data.njmax),
            "forces_recomputed": False,
        }
        with path.with_name("native_metadata.json").open("x") as stream:
            json.dump(metadata, stream, indent=2, allow_nan=False)
            stream.write("\n")

    def close(self):
        global active_recorder
        if self.solver._mujoco_warp_step is self.recording_step:
            self.solver._mujoco_warp_step = self.original
        if active_recorder is self:
            active_recorder = None
