"""Isaac Lab hooks for Sharpa state before automatic reset.

Import only after AppLauncher. Reads existing native buffers at the control
boundary; it neither advances physics nor recomputes the virtual controller.
Recorder-on/off parity must be measured before interpreting these records.
"""

import json
from pathlib import Path
from collections.abc import Mapping

import torch
from isaaclab.managers import RecorderTerm, RecorderTermCfg
from isaaclab.managers.recorder_manager import DatasetExportMode, RecorderManagerBaseCfg
from isaaclab.utils import configclass


def json_value(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, Mapping):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    return value


class NativeRecord(RecorderTerm):
    def __init__(self, cfg, env):
        super().__init__(cfg, env)
        self.stream = Path(cfg.path).open("x")
        self.control_step = 0

    def write(self, epoch, values):
        row = {"epoch": epoch, "control_step": self.control_step, **values}
        self.stream.write(json.dumps(json_value(row), allow_nan=False) + "\n")
        self.stream.flush()

    def record_pre_step(self):
        env = self._env
        command = env.command_manager.get_term("dual_hands_object_tracking_command")
        self.write("pre_step", {
            "reference_index": command.timestep_counter,
            "reference_object_position_e": command.object_body_position_command_e,
            "reference_object_wxyz_e": command.object_body_wxyz_command_e,
            "reference_left_wrist_pose_e": command.left_hand_wrist_pose_command_e,
            "reference_right_wrist_pose_e": command.right_hand_wrist_pose_command_e,
            "reference_left_finger_joint_position_rad": command.left_hand_finger_joint_pos_command,
            "reference_right_finger_joint_position_rad": command.right_hand_finger_joint_pos_command,
            "policy_observation": env.obs_buf["policy"],
            "action": env.action_manager.action,
        })
        return None, None

    def record_post_step(self):
        env = self._env
        command = env.command_manager.get_term("dual_hands_object_tracking_command")
        contacts = {}
        for side in ("left", "right"):
            for index, sensor in enumerate(getattr(command, f"object_to_{side}_hand_contact_sensors")):
                data = sensor.data
                positions = data.contact_pos_w
                contacts[f"{side}_{index}"] = {
                    "force_matrix_w_history_N": data.force_matrix_w_history,
                    "net_forces_w_N": data.net_forces_w,
                    "contact_position_w_m": torch.nan_to_num(positions, nan=0.0),
                    "contact_position_valid": torch.isfinite(positions).all(dim=-1),
                }
        processed = {name: env.action_manager.get_term(name).processed_actions
                     for name in env.action_manager.active_terms}
        self.write("post_step_before_reset", {
            "reference_index": command.timestep_counter,
            "episode_control_step": env.episode_length_buf,
            "state_e": env.scene.get_state(is_relative=True),
            "object_position_e": command.object_position_e,
            "object_wxyz_e": command.object_orientation_e,
            "left_wrist_position_e": command.left_hand_wrist_position_e,
            "right_wrist_position_e": command.right_hand_wrist_position_e,
            "contacts": contacts,
            "processed_action_terms": processed,
            "voc_scale": command.virtual_object_controller_scale_factor_per_env,
            "reward": env.reward_buf,
            "terminated": env.reset_terminated,
            "time_out": env.reset_time_outs,
            "termination_terms": {name: env.termination_manager.get_term(name)
                                  for name in env.termination_manager.active_terms},
        })
        self.control_step += 1
        return None, None

    def record_post_physics_decimation_step(self):
        env = self._env
        virtual = {}
        for name in env.action_manager.active_terms:
            term = env.action_manager.get_term(name)
            if type(term).__name__ in ("VirtualRigidObjectControl", "VirtualArticulatedObjectControl"):
                virtual[name] = term.processed_actions
        # This hook precedes scene.update: record only controller outputs that
        # were just submitted, never label stale scene buffers as post-physics.
        self.write("applied_virtual_control_after_physics", {
            "physics_step_count": env._sim_step_counter,
            "virtual_control_body_frame_N_Nm": virtual,
        })
        return None, None

    def record_post_reset(self, env_ids):
        self.write("post_reset", {"env_ids": None if env_ids is None else env_ids,
                                  "state_e": self._env.scene.get_state(is_relative=True)})
        return None, None

    def close(self, file_path=None):
        stream = getattr(self, "stream", None)
        if stream is not None and not stream.closed:
            stream.close()


@configclass
class NativeRecordCfg(RecorderTermCfg):
    class_type: type[RecorderTerm] = NativeRecord
    path: str = ""


@configclass
class NativeRecorderCfg(RecorderManagerBaseCfg):
    dataset_export_mode: DatasetExportMode = DatasetExportMode.EXPORT_NONE
    native = NativeRecordCfg()
