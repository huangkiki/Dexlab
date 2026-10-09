"""Record the preregistered SuperDex half of the paired incline campaign."""

import argparse
import json
import platform
from pathlib import Path
import time

import numpy as np

from dexlab.contact_plane import PlaneCase
from dexlab.contact_plane_native import SuperDexPlane
from dexlab.incline_run import axes
from dexlab.incline_score import file_hash


def solver_readback(value):
    """Copy the native parameter struct, including enum identities, into JSON."""
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    if hasattr(value, 'name') and hasattr(value, 'value'):
        return dict(name=value.name, value=value.value)
    return {name: solver_readback(getattr(value, name)) for name in dir(value)
            if not name.startswith('_') and not callable(getattr(value, name))}


def configure_profile(native, profile, negative=False):
    """Apply only preregistered solver choices before any duration is advanced."""
    p = native.p
    settings = native.scene.get_solver_params()
    settings.non_linear_solver.solver_type = p.NonLinearSolverType.__members__[profile['nonlinear']]
    settings.linear_solver.solver_type = p.LinearSolverType.__members__[profile['linear']]
    settings.experimental_eval.friction_model = p.CoulombFrictionModel.__members__[profile['friction']]
    if profile.get('preconditioner') is not None:
        settings.linear_solver.preconditioner_type = p.PreconditionerType.__members__[profile['preconditioner']]
    native.scene.set_solver_params(settings)
    if negative:
        native.scene.enable_actor_contact_symmetric(
            native.box.get_handle(), native.plane.get_handle(), False,
            native.p.IncludeNestedActors.__members__['NO'])


def admit(native, protocol, case):
    """Reject incorrect setup before any positive-duration native step."""
    from dexlab.incline_compare_score import validate_admission

    pose, velocity = native.observe()
    _, normal, _ = axes(case['angle_deg'])
    points = np.array([normal * distance for distance in (-.03, 0., .03)])
    distances = np.empty(3)
    native.plane.get_points_distance_to_surface(points, distances)
    record = dict(pose=pose.tolist(), velocity=velocity.tolist(), time_s=native.clock(),
                  metadata=native.metadata, geometry=native.record_geometry(),
                  double_precision=bool(native.p.uses_double_precision()),
                  gravity=np.asarray(native.scene.get_gravity()).tolist(),
                  plane_query_points=points.tolist(), plane_distances=distances.tolist())
    if 'solver_profile' in protocol:
        record.update(effective_solver=solver_readback(native.scene.get_solver_params()),
                      box_com_local=np.asarray(native.box.get_rigid_center_of_mass_local()).tolist(),
                      box_dofs=native.box.get_num_dofs(), plane_dofs=native.plane.get_num_dofs(),
                      contact_pair_disabled_command=bool(case.get('negative_no_floor', False)))
    validate_admission(protocol, case, record)
    return record


def run_case(protocol, case, destination, *, admission_only=False):
    destination.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    config = protocol['comparison']
    fixture = PlaneCase(name=case['id'], mass=protocol['mass_kg'],
                        half_size=protocol['side_m']/2, friction=case['friction'],
                        initial_speed=0, gravity=protocol['gravity_m_s2'],
                        timestep=case['timestep'], settle=0, duration=protocol['duration_s'])
    native = SuperDexPlane(fixture, destination,
                          normal_parameters=config['normal_parameters'],
                          solver_parameters={'iterations': config['solver_iterations'],
                                             'absolute_tolerance': config['absolute_tolerance'],
                                             'relative_tolerance': config['relative_tolerance']},
                          measure_step_timing=True, incline_angle_deg=case['angle_deg'])
    try:
        if 'solver_profile' in protocol:
            configure_profile(native, protocol['solver_profile'], case.get('negative_no_floor', False))
        admission = admit(native, protocol, case)
        (destination/'admission.json').write_text(json.dumps(admission, indent=2)+'\n')
        if admission_only:
            return
        setup_s = time.perf_counter()-started
        states = np.zeros((fixture.steps+1, 14))
        states[0] = np.r_[0, admission['pose'], admission['velocity']]
        forces = np.zeros((fixture.steps, 3))
        distances = np.zeros(fixture.steps)
        counts = np.zeros(fixture.steps, dtype=int)
        statuses = []
        solver_stats = []
        contact_ledger = []
        torques = np.zeros_like(forces)
        contact_force_errors = np.zeros(fixture.steps)
        loop_started = time.perf_counter()
        completed = 0
        error = None
        try:
            for index in range(fixture.steps):
                pose, velocity, force, contacts, _, status = native.step()
                states[index+1] = np.r_[native.clock(), pose, velocity]
                forces[index] = force
                counts[index] = len(contacts)
                distances[index] = min([0.]+[point['distance'] for point in contacts])
                summed = np.sum([point['force_on_box'] for point in contacts], axis=0) if contacts else np.zeros(3)
                contact_force_errors[index] = np.linalg.norm(summed-force)
                statuses.append(status)
                if 'solver_profile' in protocol:
                    contact_ledger.append(contacts)
                    solver_stats.append(solver_readback(native.scene.get_solver_stats()))
                    torques[index] = native.box.get_contact_torque_world()
                completed += 1
        except BaseException as failure:
            error = dict(type=type(failure).__name__, message=str(failure))
            raise
        finally:
            loop_finished = time.perf_counter()
            np.savez_compressed(destination/'trace.npz', states=states[:completed+1], forces=forces[:completed],
                                contact_distance=distances[:completed], contact_count=counts[:completed],
                                force_times=states[1:completed+1, 0], statuses=np.asarray(statuses[:completed]),
                                contact_force_errors=contact_force_errors[:completed],
                                contact_torques=torques[:completed])
            if 'solver_profile' in protocol:
                # Raw nonfinite observations must survive for independent rejection.
                (destination/'contacts.json').write_text(json.dumps(contact_ledger[:completed])+'\n')
                (destination/'solver-stats.json').write_text(json.dumps(solver_stats[:completed])+'\n')
            (destination/'completion.json').write_text(json.dumps(dict(
                completed_steps=completed, requested_steps=fixture.steps, error=error), indent=2)+'\n')
        loop_wall_s = loop_finished-loop_started
        timing = native.step_timing
        meta = dict(case=case, admission_sha256=file_hash(destination/'admission.json'),
                    trace_sha256=file_hash(destination/'trace.npz'),
                    geometry_sha256=file_hash(destination/'geometry.npz'),
                    state_writes_after_initialization=0, setup_s=setup_s, loop_wall_s=loop_wall_s,
                    recorder_overhead_s=loop_wall_s-timing['native_call_seconds']-timing['observation_seconds'],
                    native_step_s=timing['native_call_seconds'], observation_s=timing['observation_seconds'],
                    total_case_wall_s=time.perf_counter()-started,
                    force_epoch='Postsolve query, paired with states[i+1]-states[i] velocity increment',
                    combined_friction_readback=None)
        if 'solver_profile' in protocol:
            meta['ledger_sha256'] = {name: file_hash(destination/name)
                                    for name in ('contacts.json', 'solver-stats.json', 'completion.json')}
        (destination/'metadata.json').write_text(json.dumps(meta, indent=2)+'\n')
    finally:
        native.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--admission-only', action='store_true')
    args = parser.parse_args()
    protocol = json.loads(args.manifest.read_text())
    if 'solver_profile' not in protocol and len(protocol['cases']) != 9:
        raise ValueError('Expected nine preregistered cases')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'manifest.json').write_bytes(args.manifest.read_bytes())
    cpu_models = sorted({line.split(':', 1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')})
    for case in protocol['cases']:
        run_case(protocol, case, args.output/case['id'], admission_only=args.admission_only)
    (args.output/'campaign.json').write_text(json.dumps(dict(
        completed_cases=len(protocol['cases']), admission_only=args.admission_only,
        manifest_sha256=file_hash(args.manifest), runner_sha256=file_hash(Path(__file__)),
        fixture_sha256=file_hash(Path(__file__).with_name('contact_plane_native.py')),
        hardware=dict(cpu_models=cpu_models, architecture=platform.machine(),
                      execution='CPU, one scene, native worker threads=0; cgroup budget in resource receipt')), indent=2)+'\n')


if __name__ == '__main__':
    main()
