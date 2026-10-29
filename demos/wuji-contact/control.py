"""PD evaluated at the predicted end of the actual zero-order control hold."""

import numpy as np


def sampled_pd(position, velocity, target, mass, bias, kp, kd, step_s, control_steps):
    """Solve endpoint PD; callers clip the resulting torque to native caps.

    Over N semi-implicit Euler steps with constant acceleration a:
    v_next = v + H*a; q_next = q + H*v + c*a,
    H=N*h, c=H*(H+h)/2. Substituting those endpoints into PD gives
    (M+c*K+H*D)*a = K*(target-q-H*v)-D*v.
    The prediction ignores contacts/limits and freezes M across the hold;
    actual native contacts, nonlinear dynamics and saturation remain measured.
    """
    period = control_steps * step_s
    position_factor = period * (period + step_s) / 2
    matrix = mass + np.eye(len(position)) * (position_factor * kp + period * kd)
    acceleration = np.linalg.solve(matrix, kp * (target-position-period*velocity)-kd*velocity)
    return mass @ acceleration + bias
