"""Record a free cube on an incline using optional, unmodified pydrake."""

import argparse
import gzip
import json
from pathlib import Path
import time

import numpy as np

from dexlab.apple_admission import file_hash, record_native_file
from dexlab.cloth_engines import package_identity


def write_json(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def runtime_identity(proof):
    """Bind actually mapped Drake libraries to the previously audited wheel."""
    import pydrake
    from pydrake.multibody.plant import MultibodyPlant  # Load the native bindings.

    del MultibodyPlant
    root = Path(pydrake.__file__).resolve().parent
    identity = package_identity('drake')
    if (identity['version'] != proof['version']
            or identity['code_sha256'] != proof['package_code_sha256']):
        raise ValueError('Drake version differs from the frozen official proof')
    version = (root / 'doc/drake/VERSION.TXT').read_text().strip()
    if version != proof['native_version_file']:
        raise ValueError('Native build identity changed')
    mapped = {}
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) != 6 or not fields[5].startswith('/'):
            continue
        path = Path(fields[5]).resolve()
        if path.is_relative_to(root) and '.so' in path.name:
            name = str(path.relative_to(root.parent))
            if name not in mapped:
                mapped[name] = record_native_file('drake', path)
                if mapped[name] != proof['native_files'].get(name):
                    raise ValueError('Loaded Drake payload differs from official wheel')
    if not any(Path(name).name == 'libdrake.so' for name in mapped):
        raise ValueError('No actually mapped libdrake.so')
    return dict(package=identity, native_version_file=version, loaded_files=mapped,
                precision='float64', execution='native CPU', engine_patches=False)


def properties_readback(properties):
    result = {}
    for group in properties.GetGroupNames():
        values = {}
        for name in properties.GetPropertiesInGroup(group):
            try:
                value = properties.GetProperty(group, name)
            except RuntimeError as error:
                if name != 'compliance_type' or 'HydroelasticType' not in str(error):
                    raise
                values[name] = dict(native_readback=None,
                                    reason='HydroelasticType has no Python value binding')
                continue
            if hasattr(value, 'static_friction'):
                value = dict(static=value.static_friction(), dynamic=value.dynamic_friction())
            elif hasattr(value, 'name'):
                value = value.name
            elif not isinstance(value, (float, int, str, bool)):
                raise TypeError(f'Unrecorded native material type: {group}/{name}')
            values[name] = value
        result[group] = values
    return result


class DrakeIncline:
    """One native scene; state writes are confined to initialization."""

    def __init__(self, protocol, case):
        from pydrake.geometry import (
            AddCompliantHydroelasticPropertiesForHalfSpace, AddContactMaterial,
            AddRigidHydroelasticProperties, Box, HalfSpace, ProximityProperties,
        )
        from pydrake.math import RigidTransform, RotationMatrix
        from pydrake.multibody.plant import (
            AddMultibodyPlantSceneGraph, CalcContactFrictionFromSurfaceProperties,
            ContactModel, CoulombFriction, DiscreteContactApproximation,
        )
        from pydrake.multibody.tree import SpatialInertia, UnitInertia
        from pydrake.systems.analysis import Simulator
        from pydrake.systems.framework import DiagramBuilder

        builder = DiagramBuilder()
        self.plant, self.graph = AddMultibodyPlantSceneGraph(builder, case['timestep'])
        plant, config = self.plant, protocol['drake']
        plant.set_discrete_contact_approximation(getattr(DiscreteContactApproximation, config['approximation']))
        plant.set_contact_model(getattr(ContactModel, config.get('contact_model', 'kHydroelastic')))
        self.point_contact = config.get('effective_contact', 'hydroelastic') == 'point'
        self.record_surface_geometry = config.get('record_surface_geometry', False)
        plant.SetUseSampledOutputPorts(True)
        plant.set_stiction_tolerance(config['stiction_tolerance_m_s'])
        plant.set_sap_near_rigid_threshold(config['near_rigid_threshold'])
        plant.mutable_gravity_field().set_gravity_vector([0, 0, -protocol['gravity_m_s2']])
        self.instance = plant.AddModelInstance('cube_model')
        side = protocol['side_m']
        self.body = plant.AddRigidBody('cube', self.instance, SpatialInertia(
            protocol['mass_kg'], np.zeros(3), UnitInertia.SolidBox(side, side, side)))
        friction = CoulombFriction(case['friction'], case['friction'])
        cube_props, plane_props = ProximityProperties(), ProximityProperties()
        for props in (cube_props, plane_props):
            AddContactMaterial(properties=props, dissipation=config['dissipation_s_m'],
                               friction=friction, point_stiffness=config.get('point_stiffness_n_m'))
            if 'relaxation_time_s' in config:
                props.AddProperty('material', 'relaxation_time', config['relaxation_time_s'])
        AddRigidHydroelasticProperties(config['resolution_hint_m'], cube_props)
        AddCompliantHydroelasticPropertiesForHalfSpace(
            config['slab_thickness_m'], config['hydroelastic_modulus_pa'], plane_props)
        self.cube_id = plant.RegisterCollisionGeometry(
            self.body, RigidTransform(), Box(side, side, side), 'cube', cube_props)
        rotation = RotationMatrix.MakeYRotation(np.deg2rad(case['angle_deg']))
        self.normal = rotation.matrix()[:, 2]
        self.plane_id = None
        if not case.get('negative_no_floor', False):
            self.plane_id = plant.RegisterCollisionGeometry(
                plant.world_body(), RigidTransform(rotation), HalfSpace(), 'incline', plane_props)
        plant.Finalize()
        self.diagram = builder.Build()
        self.simulator = Simulator(self.diagram)
        self.context = self.simulator.get_mutable_context()
        self.plant_context = plant.GetMyMutableContextFromRoot(self.context)
        plant.SetFreeBodyPose(self.plant_context, self.body,
                              RigidTransform(rotation, self.normal * (
                                  side / 2 + protocol.get('initial_clearance_m', 0.))))
        plant.SetVelocities(self.plant_context, np.zeros(6))
        # Preserve the initial state before the first native update event.
        inspector = self.graph.model_inspector()
        inertia = self.body.CalcSpatialInertiaInBodyFrame(self.plant_context)
        shape = inspector.GetShape(self.cube_id)
        combined = CalcContactFrictionFromSurfaceProperties(friction, friction)
        self.admission = dict(
            state=self.state().tolist(), timestep=plant.time_step(),
            solver=plant.get_discrete_contact_solver().name,
            approximation=plant.get_discrete_contact_approximation().name,
            contact_model=plant.get_contact_model().name,
            sampled_output=plant.has_sampled_output_ports(),
            near_rigid_threshold=plant.get_sap_near_rigid_threshold(),
            gravity=plant.gravity_field().gravity_vector().tolist(),
            mass=inertia.get_mass(), com=inertia.get_com().tolist(),
            inertia=inertia.CalcRotationalInertia().CopyToFullMatrix3().tolist(),
            cube_dimensions=[shape.width(), shape.depth(), shape.height()],
            cube_pose_in_body=inspector.GetPoseInFrame(self.cube_id).GetAsMatrix4().tolist(),
            plane_pose_in_world=None if self.plane_id is None else inspector.GetPoseInFrame(self.plane_id).GetAsMatrix4().tolist(),
            cube_properties=properties_readback(inspector.GetProximityProperties(self.cube_id)),
            plane_properties=None if self.plane_id is None else properties_readback(inspector.GetProximityProperties(self.plane_id)),
            combined_friction_api=dict(static=combined.static_friction(), dynamic=combined.dynamic_friction()),
            stiction_tolerance=dict(authored=config['stiction_tolerance_m_s'], native_readback=None,
                                   reason='No public pydrake getter in the qualified release'),
            solver_statistics=None, solver_statistics_reason='No public per-step SAP statistics/parameter getter',
            num_positions=plant.num_positions(), num_velocities=plant.num_velocities(),
        )

    def state(self):
        pose = self.plant.GetFreeBodyPose(self.plant_context, self.body)
        velocity = self.body.EvalSpatialVelocityInWorld(self.plant_context)
        return np.r_[self.context.get_time(), pose.translation(), pose.rotation().ToQuaternion().wxyz(),
                     velocity.translational(), velocity.rotational()]

    def step(self, time_s):
        before = time.perf_counter()
        self.simulator.AdvanceTo(time_s)
        native_s = time.perf_counter() - before
        before = time.perf_counter()
        state = self.state()
        results = self.plant.get_contact_results_output_port().Eval(self.plant_context)
        if (results.num_deformable_contacts()
                or (self.point_contact and results.num_hydroelastic_contacts())
                or (not self.point_contact and results.num_point_pair_contacts())):
            raise ValueError('Unexpected effective contact path')
        contacts, force = [], np.zeros(3)
        for index in range(results.num_point_pair_contacts()):
            info = results.point_pair_contact_info(index)
            pair = info.point_pair()
            if ({pair.id_A, pair.id_B} != {self.cube_id, self.plane_id}
                    or {info.bodyA_index(), info.bodyB_index()} != {
                        self.body.index(), self.plant.world_body().index()}):
                raise ValueError('Unexpected point contact pair')
            cube_is_A = pair.id_A == self.cube_id
            if cube_is_A != (info.bodyA_index() == self.body.index()):
                raise ValueError('Body and geometry contact ordering disagree')
            linear = (-1 if cube_is_A else 1) * info.contact_force()
            force += linear
            contacts.append(dict(
                kind='point', force_on_cube_world=linear.tolist(),
                force_on_B_world=info.contact_force().tolist(), cube_is_A=cube_is_A,
                contact_point_world=info.contact_point().tolist(),
                witness_A_world=pair.p_WCa.tolist(), witness_B_world=pair.p_WCb.tolist(),
                normal_BA_world=pair.nhat_BA_W.tolist(), depth_m=pair.depth,
                slip_speed_m_s=info.slip_speed(), separation_speed_m_s=info.separation_speed()))
        for index in range(results.num_hydroelastic_contacts()):
            info = results.hydroelastic_contact_info(index)
            surface = info.contact_surface()
            if {surface.id_M(), surface.id_N()} != {self.cube_id, self.plane_id}:
                raise ValueError('Unexpected contact pair')
            sign = 1 if surface.id_M() == self.cube_id else -1
            spatial = info.F_Ac_W()
            linear = sign * spatial.translational()
            force += linear
            contacts.append(dict(kind='hydroelastic', force_on_cube_world=linear.tolist(),
                                 torque_on_cube_at_centroid_world=(sign * spatial.rotational()).tolist(),
                                 centroid_world=surface.centroid().tolist(),
                                 area_m2=surface.total_area()))
            if self.record_surface_geometry:
                field = surface.tri_e_MN() if surface.is_triangle() else surface.poly_e_MN()
                faces = []
                for face in range(surface.num_faces()):
                    centroid = surface.centroid(face)
                    faces.append(dict(
                        area_m2=surface.area(face), centroid_world=centroid.tolist(),
                        normal_into_cube_world=(sign * surface.face_normal(face)).tolist(),
                        pressure_pa=(field.Evaluate(face, np.full(3, 1 / 3)) if surface.is_triangle()
                                     else field.EvaluateCartesian(face, centroid)),
                        plane_pressure_gradient_world=(surface.EvaluateGradE_N_W(face) if sign == 1
                                                       else surface.EvaluateGradE_M_W(face)).tolist()))
                contacts[-1]['faces'] = faces
        generalized = self.plant.get_generalized_contact_forces_output_port(self.instance).Eval(self.plant_context)
        return state, force, np.array(generalized), contacts, native_s, time.perf_counter() - before


def run_case(protocol, case, destination, *, admission_only=False):
    from dexlab.drake_incline_score import validate_admission

    destination.mkdir(exist_ok=False)
    start = time.perf_counter()
    native = DrakeIncline(protocol, case)
    write_json(destination / 'admission.json', native.admission)
    validate_admission(protocol, case, native.admission)
    if admission_only:
        return
    setup_s = time.perf_counter() - start
    steps = round(protocol['duration_s'] / case['timestep'])
    states = np.zeros((steps + 1, 14))
    states[0] = native.state()
    forces, generalized = np.zeros((steps, 3)), np.zeros((steps, 6))
    counts = np.zeros(steps, dtype=int)
    step_s = observation_s = 0.
    completed = 0
    error = None
    try:
        with gzip.open(destination / 'contacts.jsonl.gz', 'xt') as stream:
            for i in range(steps):
                state, force, native_force, contacts, physics_s, read_s = native.step((i + 1) * case['timestep'])
                states[i + 1], forces[i], generalized[i], counts[i] = state, force, native_force, len(contacts)
                stream.write(json.dumps(dict(interval_start_s=i * case['timestep'],
                                            interval_end_s=state[0], contacts=contacts), allow_nan=False) + '\n')
                completed = i + 1
                step_s += physics_s
                observation_s += read_s
    except BaseException as exc:
        error = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        # Preserve partial records on native exceptions; never pad missing physics with zeroes.
        np.savez_compressed(destination / 'trace.npz', states=states[:completed + 1],
                            forces=forces[:completed], generalized_contact_forces=generalized[:completed],
                            contact_count=counts[:completed], force_times=states[:completed, 0])
        write_json(destination / 'metadata.json', dict(
            case=case, completed_steps=completed, error=error,
            state_writes_after_initialization=0, setup_s=setup_s, native_step_s=step_s,
            observation_s=observation_s, total_case_wall_s=time.perf_counter() - start,
            force_epoch='Sampled dynamics from the update [states[i].time, states[i+1].time]; no fresh end-state solve',
            contact_geometry_epoch='Geometry used by that update; centroid is not a new end-state query',
            force_scope=('Point-pair force on B signed onto cube' if protocol['drake'].get('effective_contact') == 'point'
                         else 'Integrated hydroelastic surface force; quadrature forces and achieved iterations unavailable'),
            hashes={name: file_hash(destination / name) for name in ('admission.json', 'trace.npz', 'contacts.jsonl.gz')},
        ))


def main():
    from dexlab.drake_incline_score import score_record, validate_runtime

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', required=True, type=Path)
    parser.add_argument('--proof', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--admission-only', action='store_true')
    parser.add_argument('--record-only', action='store_true', help='Defer independent physical scoring until acquisition ends')
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'protocol.json').write_bytes(args.protocol.read_bytes())
    (args.output / 'official-proof.json').write_bytes(args.proof.read_bytes())
    proof = json.loads(args.proof.read_bytes())
    runtime = runtime_identity(proof)
    validate_runtime(protocol, proof, runtime)
    write_json(args.output / 'runtime.json', runtime)
    sources = args.output / 'source'
    sources.mkdir()
    source_hashes = {}
    for name in ('drake_incline.py', 'drake_incline_score.py', 'incline_score.py'):
        source = Path(__file__).with_name(name)
        (sources / name).write_bytes(source.read_bytes())
        source_hashes[name] = file_hash(sources / name)
    results, error = [], None
    try:
        for case in protocol['cases']:
            if any(file_hash(Path(__file__).with_name(name)) != digest for name, digest in source_hashes.items()):
                raise ValueError('Source changed during the frozen batch')
            run_case(protocol, case, args.output / case['id'], admission_only=args.admission_only)
            if not args.admission_only:
                result = (dict(id=case['id'], recorded=True) if args.record_only else
                          score_record(protocol, case, args.output / case['id']))
                results.append(result)
                print(case['id'], result.get('passed', 'recorded'), flush=True)
    except BaseException as exc:
        error = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        write_json(args.output / 'campaign.json', dict(
            protocol_sha256=file_hash(args.protocol), official_proof_sha256=file_hash(args.proof),
            runtime_sha256=file_hash(args.output / 'runtime.json'), admission_only=args.admission_only,
            completed_cases=len(results), results=results, error=error,
            source_hashes=source_hashes,
        ))


if __name__ == '__main__':
    main()
