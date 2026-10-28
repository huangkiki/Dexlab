"""Read-only substep observations for the pinned mjlab public AMP lift.

The step hook retains the original CUDA graph. Contact forces are decoded by
the executing MuJoCo Warp version into a separate output buffer; no CPU solve
or host contact export is used. Native qualification is a separate obligation.
"""

import hashlib
import inspect
import json
from pathlib import Path

import numpy as np

from dexlab.libero_substeps import SubstepArchive


MODEL_ARRAYS = (
    "body_mass", "body_inertia", "body_ipos", "body_iquat", "body_parentid",
    "body_rootid", "body_weldid", "body_gravcomp", "geom_type", "geom_bodyid", "geom_size",
    "geom_pos", "geom_quat", "geom_contype", "geom_conaffinity", "geom_condim",
    "geom_priority", "geom_friction", "geom_solref", "geom_solimp", "geom_margin",
    "geom_gap", "jnt_type", "jnt_bodyid", "jnt_qposadr", "jnt_dofadr",
    "dof_armature", "dof_damping", "actuator_trntype", "actuator_trnid",
    "actuator_gainprm", "actuator_biasprm", "actuator_gear", "actuator_ctrllimited",
    "actuator_ctrlrange", "actuator_forcelimited", "actuator_forcerange",
    "pair_geom1", "pair_geom2", "pair_friction", "pair_margin", "pair_gap",
    "pair_dim", "pair_solref", "pair_solimp", "nxn_geom_pair", "nxn_pairid",
)
INPUT_ARRAYS = ("qpos", "qvel", "ctrl", "qfrc_applied", "xfrc_applied")
RESULT_ARRAYS = (
    "qpos", "qvel", "qacc", "qacc_warmstart", "actuator_force", "qfrc_actuator",
    "qfrc_constraint", "qfrc_bias", "qfrc_passive", "xpos", "xquat", "xipos", "ximat",
    "site_xpos", "site_xmat", "cvel", "subtree_com",
)
CONTACT_ARRAYS = (
    "geom", "dist", "pos", "frame", "worldid", "efc_address", "dim",
    "friction", "includemargin", "solref", "solimp",
)


def native_counts(data):
    """Reject capacity overflow before any exporter can silently truncate it."""
    count = np.asarray(data.nacon.numpy())
    constraints = np.asarray(data.nefc.numpy())
    if count.shape != (1,) or constraints.shape != (1,):
        raise ValueError("AMP recording requires exactly one native world")
    ncon, nefc = int(count[0]), int(constraints[0])
    if not 0 <= ncon <= data.naconmax or not 0 <= nefc <= data.njmax:
        raise ValueError("Native contact/constraint capacity overflow")
    return ncon, nefc


def single_world(array):
    values = array.numpy()
    if values.shape[0] != 1:
        raise ValueError("Expected a single-world native array")
    return values[0].copy()


def host_tensor(value):
    """Copy a source tensor without retaining an alias to resettable buffers."""
    return value.detach().cpu().numpy().copy()


def source_feedback(env):
    """Preserve the source predicate and endpoint, without assigning a new score."""
    state = {
        name: host_tensor(getattr(env, name)) for name in (
            "episode_length_buf", "success_hold_buf", "contact_settle_buf",
            "lift_start_step", "trajectory_start_pos_w", "trajectory_goal_pos_w",
            "assist_force_frac", "reset_terminated", "reset_time_outs", "reward_buf",
        )
    }
    state.update(
        object_lifted=host_tensor(env._object_lifted()),
        both_markers_found=host_tensor(env._both_marker_contacts()),
        object_root_pos_w=host_tensor(env.toaster.data.root_link_pos_w),
        hand_marker_offset_w=host_tensor(env._get_hand_toaster_dis()),
        source_success=host_tensor(env.success_hold_buf >= env.cfg.hold_steps),
        assistance_scale=float(env.virtual_pd_assistance_scale),
        reset_height_fraction=float(env.object_reset_height_frac),
        qpos=single_world(env.sim.wp_data.qpos),
        qvel=single_world(env.sim.wp_data.qvel),
        native_time=float(single_world(env.sim.wp_data.time)),
    )
    state["epochs"] = {
        "qpos_qvel_time": "Integrated native state before any automatic reset",
        "source_predicates_and_scene_buffers": "Original upstream feedback; derived positions and sensor fields retain their source compute epoch, not an asserted post-integration reconstruction",
    }
    state["sensors"] = {}
    for side in ("left", "right"):
        data = env.scene[f"{side}_hand_toaster_contact"].data
        state["sensors"][side] = {
            field: None if getattr(data, field) is None else host_tensor(getattr(data, field))
            for field in ("found", "force")
        }
    return state


class AmpEpisodeObserver:
    """Observe timeout feedback before the upstream auto-reset erases it.

    Install after the original wrapper's initial reset. Every call still runs
    the original wrapper step and reset exactly once. Returned observations
    keep their original post-reset meaning; ``feedback`` is the old episode.
    """

    def __init__(self, env):
        self.env = env
        self.original_reset = env._reset_idx
        self.terminal = None
        self.stepping = False

        def observed_reset(env_ids=None):
            if self.stepping:
                if self.terminal is not None:
                    raise ValueError("Multiple resets inside one AMP action")
                self.terminal = source_feedback(self.env)
            return self.original_reset(env_ids)

        self.observed_reset = observed_reset
        env._reset_idx = observed_reset

    def step(self, wrapper, actions):
        if self.stepping:
            raise ValueError("Nested AMP actions are not supported")
        self.terminal = None
        self.stepping = True
        try:
            result = wrapper.step(actions)
            feedback = self.terminal if self.terminal is not None else source_feedback(self.env)
            feedback["automatic_reset"] = self.terminal is not None
            return result, feedback
        finally:
            self.stepping = False

    def close(self):
        if self.env._reset_idx is self.observed_reset:
            self.env._reset_idx = self.original_reset


def save_model_snapshot(sim, directory):
    """Save randomized model readbacks equally for hooked and unhooked probes."""
    import mujoco
    import mujoco_warp

    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    if sim.wp_data.nworld != 1:
        raise ValueError("AMP recording requires exactly one native world")
    native_counts(sim.wp_data)
    model = sim.mj_model
    mujoco.mj_saveModel(model, str(directory / "compiled-template.mjb"))
    # The CPU template omits startup GPU mass, COM and friction randomization.
    arrays = {name: getattr(sim.wp_model, name).numpy().copy() for name in MODEL_ARRAYS}
    with (directory / "effective-model.npz").open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    options = {}
    for name in ("timestep", "gravity", "tolerance", "ls_tolerance", "ccd_tolerance",
                 "integrator", "cone", "solver", "iterations", "ls_iterations",
                 "ccd_iterations", "disableflags", "enableflags"):
        value = getattr(sim.wp_model.opt, name)
        options[name] = value.numpy().tolist() if hasattr(value, "numpy") else int(value)
    source = Path(inspect.getsourcefile(mujoco_warp.contact_force))
    metadata = {
        "schema_version": 1, "task": "Mjlab-G1-DualArm", "native_qualified": False,
        "use_cuda_graph": bool(sim.use_cuda_graph), "options": options,
        "time_dtype": str(sim.wp_data.time.numpy().dtype),
        "force_decoder_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "body_names": [model.body(i).name for i in range(model.nbody)],
        "geom_names": [model.geom(i).name for i in range(model.ngeom)],
        "joint_names": [model.joint(i).name for i in range(model.njnt)],
        "site_names": [model.site(i).name for i in range(model.nsite)],
        "actuator_names": [model.actuator(i).name for i in range(model.nu)],
        "epochs": {
            "before": "After scene/action/assistance writes, immediately before the original sim.step",
            "after": "Immediately after sim.step; qpos/qvel integrated, derived fields retain their native compute epoch",
            "contacts": "Native solved step fields before scene update and environment auto-reset",
        },
        "force_order": "force XYZ, torque XYZ in the contact frame; on geom[1]",
        "status": "model-only", "task_success": None,
    }
    (directory / "recording.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    return metadata


class AmpLiftRecorder:
    """Bound memory to one action and preserve observed prefixes on failure."""

    def __init__(self, simulation, directory):
        import mujoco_warp
        import warp as wp

        self.sim = simulation
        self.directory = Path(directory)
        self.metadata = save_model_snapshot(simulation, self.directory)
        self.metadata["status"] = "recording"
        self.archive = SubstepArchive(self.directory / "substeps")
        self.original_step = self.sim.step
        self._write_metadata()
        with wp.ScopedDevice(self.sim.wp_device):
            self.contact_ids = wp.array(np.arange(self.sim.wp_data.naconmax, dtype=np.int32), dtype=int)
            self.contact_forces = wp.zeros(self.sim.wp_data.naconmax, dtype=wp.spatial_vector)

        def recorded_step():
            if self.archive.action is None:
                raise ValueError("Start an archive action before stepping")
            data = self.sim.wp_data
            native_counts(data)
            before = {name: single_world(getattr(data, name)) for name in INPUT_ARRAYS}
            before["time"] = float(single_world(data.time))
            result = self.original_step()
            ncon, nefc = native_counts(data)
            contacts = {name: getattr(data.contact, name).numpy()[:ncon].copy()
                        for name in CONTACT_ARRAYS}
            if np.any(contacts["worldid"] != 0):
                raise ValueError("Unexpected contact world")
            with wp.ScopedDevice(self.sim.wp_device):
                mujoco_warp.contact_force(self.sim.wp_model, data, self.contact_ids,
                                           False, self.contact_forces)
            contacts["local_force"] = self.contact_forces.numpy()[:ncon].copy()
            after = {name: single_world(getattr(data, name)) for name in RESULT_ARRAYS}
            after["time"] = float(single_world(data.time))
            self.archive.append({
                "sequence": self.archive.substeps, "before": before, "after": after,
                "contacts": contacts, "nefc": nefc,
                "efc_force": single_world(data.efc.force)[:nefc],
                "solver_niter": int(single_world(data.solver_niter)),
            })
            return result

        self.recorded_step = recorded_step
        self.sim.step = recorded_step

    def start_action(self, action):
        self.archive.start_action(action)

    def flush(self):
        self.archive.flush()

    def _write_metadata(self):
        temporary = self.directory / ".recording.json.tmp"
        temporary.write_text(json.dumps(self.metadata, indent=2, allow_nan=False) + "\n")
        temporary.replace(self.directory / "recording.json")

    def close(self, *, completed=False):
        if self.sim.step is self.recorded_step:
            self.sim.step = self.original_step
        if self.archive.action is not None:
            self.archive.flush()
        self.metadata.update(status="completed" if completed else "partial",
                             substeps=self.archive.substeps, chunks=self.archive.chunks)
        self._write_metadata()
