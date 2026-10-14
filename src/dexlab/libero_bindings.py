"""Bind pinned LIBERO declarations to native bodies, sites and joint addresses.

Resolution reads model metadata only. It never queries a success predicate or
mistakes a region/site for a free rigid body. Bind after the final native reset.
"""

from copy import deepcopy

from dexlab.libero_goals import goal_atoms


# Attributes used by the six problem/arena classes in the pinned LIBERO source.
WORKSPACE_BODY_ATTRIBUTES = {
    "main_table": "table_body", "kitchen_table": "table_body",
    "floor": "floor_body", "coffee_table": "coffee_table_body",
    "living_room_table": "living_room_table_body", "study_table": "table_body",
}
# MuJoCo mjtJoint values, with qpos and velocity widths (quaternions differ).
JOINT_LAYOUT = {0: ("free", 7, 6), 1: ("ball", 4, 3),
                2: ("slide", 1, 1), 3: ("hinge", 1, 1)}


def _native_id(model, kind, name):
    value = int(getattr(model, kind + "_name2id")(name))
    count = int(getattr(model, "n" + ("jnt" if kind == "joint" else kind)))
    if not 0 <= value < count or getattr(model, kind + "_id2name")(value) != name:
        raise ValueError(f"Native {kind} identity does not round-trip: {name}")
    return value


def _descendants(model, root):
    bodies = {root}
    for body in range(root + 1, model.nbody):
        parent = int(model.body_parentid[body])
        if parent >= body:
            raise ValueError("Native body parent order is invalid")
        if parent in bodies:
            bodies.add(body)
    return sorted(bodies)


def _joint(model, joint):
    kind = int(model.jnt_type[joint])
    if kind not in JOINT_LAYOUT:
        raise ValueError("Unknown native joint type")
    name, nq, nv = JOINT_LAYOUT[kind]
    qadr, dadr = int(model.jnt_qposadr[joint]), int(model.jnt_dofadr[joint])
    qend = int(model.jnt_qposadr[joint + 1]) if joint + 1 < model.njnt else model.nq
    dend = int(model.jnt_dofadr[joint + 1]) if joint + 1 < model.njnt else model.nv
    if qadr < 0 or dadr < 0 or qend != qadr + nq or dend != dadr + nv:
        raise ValueError("Native joint addresses disagree with its coordinate widths")
    return {"joint_id": joint, "joint_name": model.joint_id2name(joint),
            "type": name, "body_id": int(model.jnt_bodyid[joint]),
            "qpos_indices": list(range(qadr, qend)), "dof_indices": list(range(dadr, dend))}


def _query_joints(model, names, body_ids):
    names = list(names or [])
    if len(set(names)) != len(names):
        raise ValueError("Duplicate native predicate joint")
    joints = [_native_id(model, "joint", name) for name in names]
    if any(int(model.jnt_bodyid[joint]) not in body_ids for joint in joints):
        raise ValueError("Predicate joint belongs to another entity")
    return joints


def _body_binding(model, root_name, kind):
    root = _native_id(model, "body", root_name)
    if root == 0:
        raise ValueError("A declared LIBERO entity cannot alias the world body")
    bodies = _descendants(model, root)
    return {"kind": kind, "status": "bound", "body_id": root, "body_name": root_name,
            "body_ids": bodies,
            "geom_ids": [i for i in range(model.ngeom) if int(model.geom_bodyid[i]) in bodies],
            "joints": [_joint(model, i) for i in range(model.njnt)
                       if int(model.jnt_bodyid[i]) in bodies]}


def bind_task(env, definition):
    """Resolve every declared entity, requiring all interests and goal arguments.

    Non-materialized, unused regions remain explicit rows. All physical objects
    and fixtures must resolve, including the arena's workspace body. Regions
    record both their declared owner and the actual native site's body.
    """
    atoms = goal_atoms(definition)
    if env.parsed_problem["goal_state"] != atoms:
        raise ValueError("Native goals differ from the pinned task")
    if env.parsed_problem["obj_of_interest"] != definition["objects_of_interest"]:
        raise ValueError("Native objects of interest differ from the pinned task")
    for field in ("objects", "fixtures"):
        native = {name: category for category, names in env.parsed_problem[field].items()
                  for name in names}
        if native != definition[field]:
            raise ValueError(f"Native {field} differ from the pinned task")
    required = set(definition["objects_of_interest"])
    required.update(name for atom in atoms for name in atom[1:])
    model = env.sim.model
    entities = {}
    workspace = env.workspace_name
    if workspace not in definition["fixtures"] or workspace not in WORKSPACE_BODY_ATTRIBUTES:
        raise ValueError("Workspace fixture has no pinned arena binding")
    if (set(env.objects_dict) != set(definition["objects"])
            or set(env.fixtures_dict) != set(definition["fixtures"]) - {workspace}):
        raise ValueError("Native object/fixture providers differ from task declarations")
    for field, providers in (("objects", env.objects_dict), ("fixtures", env.fixtures_dict)):
        for name, provider in providers.items():
            binding = _body_binding(model, provider.root_body, "object" if field == "objects" else "fixture")
            state = env.object_states_dict[name]
            if (int(env.obj_body_id[name]) != binding["body_id"]
                    or state.object_state_type != "object" or state.object_name != name
                    or state.is_fixture is not (field == "fixtures")):
                raise ValueError("Native object-state/body binding disagrees with its provider")
            binding["query_joint_ids"] = _query_joints(model, provider.joints, binding["body_ids"])
            entities[name] = binding
    arena = env.model.mujoco_arena
    element = getattr(arena, WORKSPACE_BODY_ATTRIBUTES[workspace])
    if element is None or element.tag != "body" or not element.get("name"):
        raise ValueError("Workspace arena has no named native body")
    entities[workspace] = _body_binding(model, element.get("name"), "arena")
    entities[workspace]["query_joint_ids"] = []
    owned = set()
    for binding in entities.values():
        if owned.intersection(binding["body_ids"]):
            raise ValueError("Distinct declared entities alias native bodies")
        owned.update(binding["body_ids"])
    for name, region in definition["regions"].items():
        target = region["target"]
        provider = env.object_sites_dict.get(name)
        if not region["target_declared"] or provider is None:
            if name in required:
                raise ValueError("A required task region has no native site binding")
            if provider is not None or name in env.object_states_dict:
                raise ValueError("Unexpected native binding for an unresolved source region")
            entities[name] = {"kind": "region", "declared_target": target,
                              "status": "unresolved-source-target" if not region["target_declared"]
                              else "not-materialized"}
            continue
        site = _native_id(model, "site", name)
        body = int(model.site_bodyid[site])
        state = env.object_states_dict[name]
        parent = provider.parent_name
        if (body not in entities[target]["body_ids"] or provider.name != name
                or state.object_name != name or state.object_state_type != "site"
                or state.parent_name != parent
                or (parent is not None and parent != target)
                or (parent is None and target != workspace)):
            raise ValueError("Native site owner disagrees with the declared region")
        joints = _query_joints(model, provider.joints, entities[target]["body_ids"])
        ancestors = {body}
        ancestor = body
        while ancestor:
            ancestor = int(model.body_parentid[ancestor])
            ancestors.add(ancestor)
        if any(int(model.jnt_bodyid[j]) not in ancestors for j in joints):
            raise ValueError("Site predicate joint does not drive its native body")
        entities[name] = {"kind": "region", "status": "bound", "declared_target": target,
                          "native_parent_name": parent, "site_id": site, "site_name": name,
                          "body_id": body, "body_name": model.body_id2name(body),
                          "query_joint_ids": joints}
    for name in required:
        if name not in entities or entities[name]["status"] != "bound":
            raise ValueError("Task interest or goal argument is not bound")
        if name not in env.object_states_dict:
            raise ValueError("Required entity lacks native predicate state")
    for atom in atoms:
        if atom[0] in ("open", "close", "turnon", "turnoff"):
            if not entities[atom[1]]["query_joint_ids"]:
                raise ValueError("Articulated goal lacks native predicate joints")
    return {"schema_version": 2, "entities": entities,
            "objects_of_interest": deepcopy(definition["objects_of_interest"]),
            "goal": deepcopy(definition["goal"]),
            "model_dimensions": {key: int(getattr(model, key))
                                 for key in ("nbody", "njnt", "nq", "nv", "nsite", "ngeom")},
            "scope": "Native identity and coordinate bindings; no goal query or physical qualification."}
