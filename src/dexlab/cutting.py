"""Persistent-cut TLMPM reference implementation of BladeMaster, arXiv:2609.27342v2.

This is independent CPU code, not the authors' implementation. SI units, FP64,
trilinear reference basis, fixed-corotated elasticity with optional perfect-J2
plasticity and Newtonian viscosity, MUSL and PIC/FLIP.
The blade translates dynamically; a guide constrains its attitude. See the
experiment document for the equation mapping and unimplemented paper features.
"""

from dataclasses import asdict, dataclass
from itertools import product

import numpy as np
from numba import njit
from scipy.spatial import cKDTree

from dexlab.cutting_geometry import material_points


@dataclass(frozen=True)
class CutConfig:
    size: tuple[float, float, float] = (0.06, 0.03, 0.03)
    grid_spacing: float = 0.0075
    dt: float = 0.0005
    density: float = 1100.0
    young_modulus: float = 6000.0
    poisson_ratio: float = 0.35
    yield_stress: float = 0.0  # Pa; zero retains the elastic baseline.
    dynamic_viscosity: float = 0.0  # Pa s; zero retains the elastic baseline.
    flip_fraction: float = 0.95
    normal_scale: float = 0.1
    friction_static: float = 0.3
    friction_dynamic: float = 0.2
    tangent_stiffness: float = 0.05
    tangent_damping: float = 0.1
    cutting_energy: float = 0.5
    sharpness: float = 0.9
    blade_mass: float = 0.2
    blade_half_size: tuple[float, float, float] = (0.0005, 0.025, 0.02)
    drive_stiffness: float = 250.0
    drive_damping: float = 14.0
    drive_force_limit: float = 10.0
    shape: str = 'block'
    blade_bevel_height: float = 0.0

    def __post_init__(self):
        if self.shape not in ('block', 'banana'):
            raise ValueError('Unknown material shape')
        values = np.array([v for key, value in asdict(self).items()
                           if key not in ('shape', 'blade_bevel_height', 'dynamic_viscosity',
                                          'yield_stress')
                           for v in (value if isinstance(value, tuple) else (value,))])
        if not np.isfinite(values).all() or (values <= 0).any():
            raise ValueError("All configuration values must be finite and positive")
        if not np.isfinite(self.dynamic_viscosity) or self.dynamic_viscosity < 0:
            raise ValueError('Dynamic viscosity must be finite and nonnegative (Pa s)')
        if not np.isfinite(self.yield_stress) or self.yield_stress < 0:
            raise ValueError('Yield stress must be finite and nonnegative (Pa)')
        if not 0 < self.poisson_ratio < 0.5 or not 0 < self.sharpness < 1:
            raise ValueError("Invalid Poisson ratio or blade sharpness")
        if self.flip_fraction > 1 or self.friction_dynamic > self.friction_static:
            raise ValueError("Invalid transfer/friction coefficient")
        if not np.isfinite(self.blade_bevel_height) or not 0 <= self.blade_bevel_height < 2 * self.blade_half_size[2]:
            raise ValueError("Invalid blade bevel height")
        cells = np.asarray(self.size) / self.grid_spacing
        if not np.allclose(cells, np.rint(cells), rtol=0, atol=1e-10):
            raise ValueError("Each dimension must contain an integer number of cells")
        if cells.min() < 2:
            raise ValueError("At least two cells per dimension are required")


def reference_stencil(reference, origin, spacing, cells):
    """Eight trilinear weights and material gradients, fixed for the whole run."""
    fractional = (reference - origin) / spacing
    base = np.floor(fractional).astype(np.int64)
    local = fractional - base
    offsets = np.array(list(product((0, 1), repeat=3)))
    factors = np.where(offsets[None, :, :] == 1, local[:, None, :],
                       1 - local[:, None, :])
    weights = factors.prod(axis=2)
    gradients = np.empty((*weights.shape, 3))
    for axis in range(3):
        others = [a for a in range(3) if a != axis]
        gradients[:, :, axis] = ((2 * offsets[:, axis] - 1)[None, :]
                                 * factors[:, :, others].prod(axis=2) / spacing)
    indices = base[:, None, :] + offsets[None, :, :]
    nodes = np.ravel_multi_index(indices.transpose(2, 0, 1), tuple(cells + 1))
    return nodes, weights, gradients


@njit(cache=True)
def corotated_stress(deformation, mu, lam):
    """First Piola stress; no damage scaling or undocumented plastic clamping."""
    u, _, vt = np.linalg.svd(deformation)
    rotation = u @ vt
    determinant = np.linalg.det(deformation)
    if determinant <= 0:
        raise ValueError("Inverted material point; retain this failed run")
    return (2 * mu * (deformation - rotation)
            + lam * (determinant - 1) * determinant * np.linalg.inv(deformation).T)


@njit(cache=True)
def corotated_energy(deformation, mu, lam):
    """Fixed-corotated elastic energy density per reference volume (J/m^3)."""
    u, _, vt = np.linalg.svd(deformation)
    rotation = u @ vt
    determinant = np.linalg.det(deformation)
    if determinant <= 0:
        raise ValueError('Inverted material point; retain this failed run')
    return mu * np.sum((deformation - rotation)**2) + .5 * lam * (determinant - 1)**2


@njit(cache=True)
def von_mises_project(deformation, mu, yield_stress):
    """Project principal logarithmic elastic strain onto a perfect-J2 surface.

    BladeMaster specifies only a ``von Mises-type plasticity projection``. This
    independent choice uses the conventional equivalent-stress definition
    q=sqrt(3/2)||s||, giving ||dev(log sigma)|| <= yield/(sqrt(6) mu).
    The hydrostatic logarithmic strain is retained, so the projection preserves
    det(F). The returned scalar is the removed deviatoric log-strain norm.
    """
    if yield_stress <= 0:
        return deformation.copy(), 0.
    u, stretches, vt = np.linalg.svd(deformation)
    if np.linalg.det(deformation) <= 0 or np.min(stretches) <= 0:
        raise ValueError('Inverted material point; retain this failed run')
    logarithmic = np.log(stretches)
    mean = logarithmic.sum() / 3
    deviatoric = logarithmic - mean
    norm = np.linalg.norm(deviatoric)
    limit = yield_stress / (np.sqrt(6.) * mu)
    if norm <= limit:
        return deformation.copy(), 0.
    projected = mean + deviatoric * (limit / norm)
    return u @ np.diag(np.exp(projected)) @ vt, norm - limit


@njit(cache=True)
def newtonian_stress(deformation, reference_velocity_gradient, viscosity):
    """Viscous first Piola stress J eta (L + L.T) F^-T, in Pa.

    L = grad_X(v) F^-1 is the spatial velocity gradient. This chooses zero
    second-viscosity coefficient (bulk viscosity 2 eta / 3), not a calibrated
    food law. Rigid spin has zero symmetric rate; uniform translation has
    zero gradient. V0 P_v : grad_X(v) = 2 eta V0 J D:D is nonnegative.
    """
    determinant = np.linalg.det(deformation)
    if determinant <= 0:
        raise ValueError('Inverted material point; retain this failed run')
    inverse = np.linalg.inv(deformation)
    spatial_gradient = reference_velocity_gradient @ inverse
    return viscosity * determinant * (spatial_gradient + spatial_gradient.T) @ inverse.T


@njit(cache=True)
def codes_compatible(a, b):
    """Two histories conflict if any assigned ternary digit has opposite sides."""
    while a or b:
        left, right = a % 3, b % 3
        if left and right and left != right:
            return False
        a, b = a // 3, b // 3
    return True


@njit(cache=True)
def couple_grids(mass, state):
    """Eq. 8: simultaneous antisymmetric exchanges between compatible codes.

    Every exchange uses the original states, not sequentially mutated states.
    Works for either momentum or accumulated impulse. Mass remains unchanged.
    """
    result = state.copy()
    for node in range(mass.shape[1]):
        total = mass[:, node].sum()
        if total > 0:
            for a in range(len(mass)):
                if mass[a, node] == 0:
                    continue
                for b in range(a + 1, len(mass)):
                    if mass[b, node] == 0 or not codes_compatible(a, b):
                        continue
                    for axis in range(3):
                        exchange = (mass[a, node] * state[b, node, axis]
                                    - mass[b, node] * state[a, node, axis]) / total
                        result[a, node, axis] += exchange
                        result[b, node, axis] -= exchange
    return result


@njit(cache=True)
def material_step(x, velocity, deformation, sides, nodes, weights, gradients,
                  particle_impulse, mass, volume, mu, lam, dt, flip, node_count,
                  viscosity=0.0, yield_stress=0.0):
    """Eq. 1–2, 8–9; return viscous and plastic constitutive dissipation (J)."""
    code_count = int(sides.max()) + 1
    gm = np.zeros((code_count, node_count))
    momentum = np.zeros((code_count, node_count, 3))
    impulse = np.zeros_like(momentum)
    plastic_dissipation = 0.0
    for p in range(len(x)):
        if yield_stress > 0:
            trial_energy = corotated_energy(deformation[p], mu, lam)
            projected, plastic_increment = von_mises_project(deformation[p], mu, yield_stress)
            deformation[p] = projected
            projected_energy = corotated_energy(projected, mu, lam)
            if plastic_increment > 0:
                plastic_dissipation += volume * (trial_energy - projected_energy)
        stress = corotated_stress(deformation[p], mu, lam)
        side = sides[p]
        for a in range(8):
            node, w = nodes[p, a], weights[p, a]
            gm[side, node] += mass * w
            for j in range(3):
                momentum[side, node, j] += mass * w * velocity[p, j]
                internal = 0.0
                for k in range(3):
                    internal -= dt * volume * stress[j, k] * gradients[p, a, k]
                impulse[side, node, j] += internal + w * particle_impulse[p, j]
    coupled = couple_grids(gm, momentum)
    old_gv = np.zeros_like(momentum)
    for side in range(code_count):
        for node in range(node_count):
            if gm[side, node] > 0:
                old_gv[side, node] = coupled[side, node] / gm[side, node]
    dissipation = 0.0
    if viscosity > 0:
        # Use current, compatibility-filtered velocity, before external and
        # internal impulses. Opposing cut histories never share this gradient.
        for p in range(len(x)):
            rate = np.zeros((3, 3))
            side = sides[p]
            for a in range(8):
                for j in range(3):
                    for k in range(3):
                        rate[j, k] += old_gv[side, nodes[p, a], j] * gradients[p, a, k]
            stress = newtonian_stress(deformation[p], rate, viscosity)
            dissipation += dt * volume * np.sum(stress * rate)
            for a in range(8):
                for j in range(3):
                    internal = 0.0
                    for k in range(3):
                        internal -= dt * volume * stress[j, k] * gradients[p, a, k]
                    impulse[side, nodes[p, a], j] += internal
    coupled_impulse = couple_grids(gm, impulse)
    gv = np.zeros_like(momentum)
    for side in range(code_count):
        for node in range(node_count):
            if gm[side, node] > 0:
                gv[side, node] = (coupled[side, node] + coupled_impulse[side, node]) / gm[side, node]
    for p in range(len(x)):
        pic = np.zeros(3)
        increment = np.zeros(3)
        for a in range(8):
            node, w = nodes[p, a], weights[p, a]
            pic += w * gv[sides[p], node]
            increment += w * (gv[sides[p], node] - old_gv[sides[p], node])
        velocity[p] = (1 - flip) * pic + flip * (velocity[p] + increment)
        x[p] += dt * velocity[p]
    remapped = np.zeros_like(momentum)
    for p in range(len(x)):
        for a in range(8):
            remapped[sides[p], nodes[p, a]] += mass * weights[p, a] * velocity[p]
    remapped = couple_grids(gm, remapped)
    for side in range(code_count):
        for node in range(node_count):
            if gm[side, node] > 0:
                remapped[side, node] /= gm[side, node]
    for p in range(len(x)):
        for a in range(8):
            for j in range(3):
                for k in range(3):
                    deformation[p, j, k] += (dt * remapped[sides[p], nodes[p, a], j]
                                              * gradients[p, a, k])
    return dissipation, plastic_dissipation


@njit(cache=True)
def friction_impulse(normal, relative_velocity, normal_impulse, history,
                     effective_mass, dt, mu_s, mu_d, gamma_k, gamma_c):
    """Eq. 12: persistent tangential history with Coulomb slip projection."""
    tangential = relative_velocity - np.dot(relative_velocity, normal) * normal
    transported = history - np.dot(history, normal) * normal
    stiffness = gamma_k * effective_mass / dt**2
    damping = 2 * gamma_c * np.sqrt(effective_mass * stiffness)
    trial = (-stiffness * transported - damping * tangential) * dt
    magnitude = np.linalg.norm(trial)
    if magnitude <= mu_s * normal_impulse:
        return trial, transported + dt * tangential
    applied = trial * (mu_d * normal_impulse / magnitude)
    return applied, -(applied / dt + damping * tangential) / stiffness


@njit(cache=True)
def box_query(point, center, half_size):
    """Closest point and outward normal for the translation-only blade box."""
    local = point - center
    closest = np.minimum(np.maximum(local, -half_size), half_size)
    difference = local - closest
    distance = np.linalg.norm(difference)
    if distance > 1e-14:
        return center + closest, difference / distance, distance
    margins = half_size - np.abs(local)
    axis = np.argmin(margins)
    normal = np.zeros(3)
    normal[axis] = 1 if local[axis] >= 0 else -1
    closest[axis] = normal[axis] * half_size[axis]
    return center + closest, normal, -margins[axis]


@njit(cache=True)
def blade_query(point, center, half_size, bevel_height=0.0):
    """Closest point on a convex beveled prism, extruded along blade width.

    Zero bevel preserves the original rectangular tofu blade. The nonzero
    bevel is collision geometry, not a force correction or penetration clamp.
    """
    if bevel_height == 0:
        return box_query(point, center, half_size)
    local = point - center
    hx, hy, hz = half_size
    polygon = np.array([[0., -hz], [hx, -hz + bevel_height], [hx, hz],
                        [-hx, hz], [-hx, -hz + bevel_height]])
    query = np.array([local[0], local[2]])
    inside = True
    best_distance = np.inf
    closest = np.zeros(2)
    outward = np.zeros(2)
    for i in range(5):
        start, end = polygon[i], polygon[(i + 1) % 5]
        edge = end - start
        offset = query - start
        inside = inside and edge[0] * offset[1] - edge[1] * offset[0] >= 0
        fraction = min(1., max(0., np.dot(offset, edge) / np.dot(edge, edge)))
        candidate = start + fraction * edge
        distance = np.linalg.norm(query - candidate)
        if distance < best_distance:
            best_distance = distance
            closest = candidate
            outward = np.array([edge[1], -edge[0]]) / np.linalg.norm(edge)
    nearest = np.array([closest[0], min(hy, max(-hy, local[1])), closest[1]])
    if inside and abs(local[1]) <= hy:
        normal = np.array([outward[0], 0., outward[1]])
        distance = best_distance
        if hy - abs(local[1]) < distance:
            nearest = local.copy()
            nearest[1] = hy if local[1] >= 0 else -hy
            normal = np.array([0., 1. if local[1] >= 0 else -1., 0.])
            distance = hy - abs(local[1])
        return center + nearest, normal, -distance
    if inside:
        nearest[0], nearest[2] = local[0], local[2]
    delta = local - nearest
    distance = np.linalg.norm(delta)
    normal = delta / distance if distance > 1e-14 else np.array([outward[0], 0., outward[1]])
    return center + nearest, normal, distance


@njit(cache=True)
def oriented_blade_query(point, center, half_size, bevel_height, yaw):
    """Query a guided blade in its local frame and return world-frame contact."""
    if yaw == 0.:
        return blade_query(point, center, half_size, bevel_height)
    cosine, sine = np.cos(yaw), np.sin(yaw)
    rotation = np.array([[cosine, -sine, 0.], [sine, cosine, 0.], [0., 0., 1.]])
    local = rotation.T @ (point - center)
    closest, normal, distance = blade_query(local, np.zeros(3), half_size, bevel_height)
    return center + rotation @ closest, rotation @ normal, distance


@njit(cache=True)
def rigid_contacts(x, velocity, blade_x, blade_v, half_size, radius, mass,
                   blade_mass, dt, normal_scale, mu_s, mu_d, gamma_k, gamma_c,
                   histories, damage, work_threshold, cutting, bevel_height=0.0, yaw=0.0):
    """Eq. 14–16. One impulse feeds both material and rigid reaction."""
    impulses = np.zeros_like(x)
    reaction = np.zeros(3)
    torque = np.zeros(3)
    board_impulse = np.zeros(3)
    maximum_overlap = 0.0
    work = 0.0
    for p in range(len(x)):
        for body in range(2):
            if body == 0:
                normal = np.array([0., 0., 1.])
                gap = x[p, 2] - radius
                relative = velocity[p].copy()
                effective = mass
                point = x[p].copy()
                point[2] = 0
            else:
                point, normal, distance = oriented_blade_query(x[p], blade_x, half_size, bevel_height, yaw)
                gap = distance - radius
                relative = velocity[p] - blade_v
                effective = 1 / (1 / mass + 1 / blade_mass)
            maximum_overlap = max(maximum_overlap, -gap)
            predicted = gap + dt * min(np.dot(relative, normal), 0)
            if predicted >= 0:
                histories[body, p] *= 0
                continue
            jn = normal_scale * effective / dt * (-predicted)
            tangent, updated = friction_impulse(normal, relative, jn,
                                                 histories[body, p], effective, dt,
                                                 mu_s, mu_d, gamma_k, gamma_c)
            histories[body, p] = updated
            impulse = jn * normal + tangent
            if body == 1 and cutting:
                # Cutting front is -z; resistance is released only after the
                # empirical contact-work threshold. Topology is geometric.
                front = blade_x[2] - half_size[2] - x[p, 2]
                advance = velocity[p, 2] - blade_v[2]
                if 0 <= front <= 2 * radius and advance > 0:
                    positive = max(-impulse[2], 0)
                    if damage[p] >= 1:
                        impulse[2] += positive
                    else:
                        increment = positive * advance
                        work += increment
                        damage[p] = min(1., damage[p] + increment / work_threshold)
            impulses[p] += impulse
            if body == 0:
                board_impulse += impulse
            else:
                reaction -= impulse
                torque -= np.cross(point - blade_x, impulse)
    return impulses, reaction, torque, board_impulse, maximum_overlap, work


@njit(cache=True)
def particle_contacts(x, reference, velocity, sides, pairs, radius, spacing,
                      mass, dt, normal_scale, mu_s, mu_d, gamma_k, gamma_c,
                      history, seen, step):
    """Eq. 10–13; reference-neighbor exclusion is lifted across cut faces."""
    impulses = np.zeros_like(x)
    maximum_overlap = 0.0
    for p, q in pairs:
        conflict = not codes_compatible(sides[p], sides[q])
        if not conflict and np.linalg.norm(reference[p] - reference[q]) < 2 * spacing:
            continue
        delta = x[p] - x[q]
        distance = np.linalg.norm(delta)
        if distance < 1e-14:
            raise ValueError("Coincident contact proxies; undefined normal")
        normal = delta / distance
        relative = velocity[p] - velocity[q]
        overlap = 2 * radius - distance
        predicted = overlap - dt * min(np.dot(relative, normal), 0)
        if predicted <= 0:
            continue
        maximum_overlap = max(maximum_overlap, overlap)
        previous = history[p, q] if seen[p, q] == step - 1 else np.zeros(3)
        jn = normal_scale * (mass / 2) / dt * predicted
        tangent, updated = friction_impulse(normal, relative, jn, previous,
                                             mass / 2, dt, mu_s, mu_d, gamma_k, gamma_c)
        history[p, q] = updated
        seen[p, q] = step
        impulse = jn * normal + tangent
        impulses[p] += impulse
        impulses[q] -= impulse
    return impulses, maximum_overlap


@njit(cache=True)
def assign_cut_sides(x, velocity, sides, blade_x, blade_v, half_size, spacing, dt, cut_index=0, yaw=0.0):
    """Eq. 3–7: assign 0→1/2 behind the swept finite edge, never reset."""
    edge_z = blade_x[2] - half_size[2]
    digit = 3**cut_index
    cosine, sine = np.cos(yaw), np.sin(yaw)
    for p in range(len(x)):
        dx, dy = x[p, 0] - blade_x[0], x[p, 1] - blade_x[1]
        signed = cosine * dx + sine * dy
        along = -sine * dx + cosine * dy
        front = edge_z - x[p, 2]
        back = 2 * spacing + max((velocity[p, 2] - blade_v[2]) * dt, 0)
        if ((sides[p] // digit) % 3 == 0 and abs(signed) <= 6 * spacing
                and abs(along) <= half_size[1]
                and -back <= front <= 0):
            sides[p] += digit * (1 if signed < 0 else 2)


class CuttingSimulation:
    """One material body, a guided dynamic blade, persistent cuts and a board."""

    def __init__(self, config=CutConfig()):
        self.config = config
        cells = np.rint(np.asarray(config.size) / config.grid_spacing).astype(int)
        self.origin = -np.array([config.size[0] / 2, config.size[1] / 2, 0.])
        particle_spacing = config.grid_spacing / 2
        self.reference = material_points(config.size, config.grid_spacing, config.shape)
        self.x = self.reference.copy()
        self.velocity = np.zeros_like(self.x)
        self.deformation = np.tile(np.eye(3), (len(self.x), 1, 1))
        self.sides = np.zeros(len(self.x), dtype=np.int64)
        self.damage = np.zeros(len(self.x))
        self.volume = particle_spacing**3
        self.mass = config.density * self.volume
        self.radius = particle_spacing / 2
        self.nodes, self.weights, self.gradients = reference_stencil(
            self.reference, self.origin, config.grid_spacing, cells)
        self.node_count = int(np.prod(cells + 1))
        self.half_size = np.array(config.blade_half_size)
        self.blade_x = np.array([0., 0., config.size[2] + .012 + self.half_size[2]])
        self.blade_v = np.zeros(3)
        self.blade_yaw = 0.
        self.rigid_history = np.zeros((2, len(self.x), 3))
        self.pair_history = np.zeros((len(self.x), len(self.x), 3))
        self.pair_seen = np.full((len(self.x), len(self.x)), -2, dtype=np.int32)
        self.step_count = 0

    def momentum(self):
        return self.mass * self.velocity.sum(axis=0) + self.config.blade_mass * self.blade_v

    def step(self, target_edge, *, cutting=True, probe_velocity=None, probe_mask=None, cut_index=0,
             blade_yaw=0.):
        c = self.config
        if not np.isfinite(blade_yaw):
            raise ValueError('Blade yaw must be finite')
        if blade_yaw != self.blade_yaw:
            # Attitude is an external guide, not free rotational dynamics.
            # Reorientation is allowed only with the whole blade above material.
            if self.blade_x[2] - self.half_size[2] <= self.x[:, 2].max() + self.radius:
                raise ValueError('Withdraw the blade before changing its guided attitude')
            self.blade_yaw = float(blade_yaw)
        before = self.momentum()
        external = np.zeros(3)
        if probe_velocity is not None:
            selected = self.reference[:, 0] > 0 if probe_mask is None else probe_mask
            impulse = self.mass * np.asarray(probe_velocity)
            self.velocity[selected] += np.asarray(probe_velocity)
            external += selected.sum() * impulse
        target = np.asarray(target_edge) + np.array([0, 0, self.half_size[2]])
        drive = c.drive_stiffness * (target - self.blade_x) - c.drive_damping * self.blade_v
        norm = np.linalg.norm(drive)
        if norm > c.drive_force_limit:
            drive *= c.drive_force_limit / norm
        impulses, reaction, torque, board, overlap, work = rigid_contacts(
            self.x, self.velocity, self.blade_x, self.blade_v, self.half_size,
            self.radius, self.mass, c.blade_mass, c.dt, c.normal_scale,
            c.friction_static, c.friction_dynamic, c.tangent_stiffness,
            c.tangent_damping, self.rigid_history, self.damage,
            c.cutting_energy * self.volume**(2 / 3) * (1 - c.sharpness) / c.sharpness,
            cutting, c.blade_bevel_height, self.blade_yaw)
        pair_radius = 2 * self.radius + 2 * np.linalg.norm(self.velocity, axis=1).max() * c.dt
        pairs = cKDTree(self.x).query_pairs(pair_radius, output_type='ndarray')
        contact, pair_overlap = particle_contacts(
            self.x, self.reference, self.velocity, self.sides, pairs, self.radius,
            c.grid_spacing, self.mass, c.dt, c.normal_scale, c.friction_static,
            c.friction_dynamic, c.tangent_stiffness, c.tangent_damping,
            self.pair_history, self.pair_seen, self.step_count)
        gravity = np.array([0., 0., -9.81]) * self.mass * c.dt
        viscous_dissipation, plastic_dissipation = material_step(
                      self.x, self.velocity, self.deformation, self.sides,
                      self.nodes, self.weights, self.gradients,
                      impulses + contact + gravity, self.mass, self.volume,
                      c.young_modulus / (2 * (1 + c.poisson_ratio)),
                      c.young_modulus * c.poisson_ratio / ((1 + c.poisson_ratio) * (1 - 2 * c.poisson_ratio)),
                      c.dt, c.flip_fraction, self.node_count, c.dynamic_viscosity, c.yield_stress)
        self.blade_v += (c.dt * drive + reaction) / c.blade_mass
        self.blade_x += c.dt * self.blade_v
        # Unilateral board stop on the guided blade. Its support impulse is
        # external and logged separately from the material reaction.
        blade_board = np.zeros(3)
        if self.blade_x[2] < self.half_size[2]:
            self.blade_x[2] = self.half_size[2]
            if self.blade_v[2] < 0:
                blade_board[2] = -c.blade_mass * self.blade_v[2]
                self.blade_v[2] = 0
        if cutting:
            assign_cut_sides(self.x, self.velocity, self.sides, self.blade_x, self.blade_v,
                             self.half_size, c.grid_spacing, c.dt, cut_index, self.blade_yaw)
        external += board + blade_board + gravity * len(self.x) + c.dt * drive
        residual = self.momentum() - before - external
        self.step_count += 1
        determinant = np.linalg.det(self.deformation)
        if not np.isfinite(self.x).all() or determinant.min() <= 0:
            raise ValueError("Non-finite/inverted material state")
        return {
            'time_s': self.step_count * c.dt,
            'blade_position_m': self.blade_x.copy(), 'blade_velocity_m_s': self.blade_v.copy(),
            'blade_yaw_rad': self.blade_yaw,
            'target_edge_m': np.asarray(target_edge), 'drive_force_n': drive,
            'material_reaction_n': reaction / c.dt, 'guide_reaction_torque_nm': -torque / c.dt,
            'board_impulse_ns': board, 'blade_board_impulse_ns': blade_board,
            'external_impulse_ns': external,
            'momentum_ns': self.momentum(), 'momentum_residual_ns': residual,
            'maximum_proxy_overlap_m': max(overlap, pair_overlap),
            'maximum_rigid_overlap_m': overlap, 'maximum_material_overlap_m': pair_overlap,
            'minimum_det_f': determinant.min(), 'maximum_det_f': determinant.max(),
            'labelled_particles': int(np.count_nonzero(self.sides)),
            'contact_work_j': work,
            **({'viscous_dissipation_j': viscous_dissipation} if c.dynamic_viscosity > 0 else {}),
            **({'plastic_dissipation_j': plastic_dissipation} if c.yield_stress > 0 else {}),
        }
