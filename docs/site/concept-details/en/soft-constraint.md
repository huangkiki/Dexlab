## What happens when a ball hits a table?

Consider one active normal contact. Let $r$ be its position error and $v$ its normal relative velocity. With zero contact margin, a ball sinking into the table has $r<0$ and an approaching ball has $v<0$. MuJoCo computes a spring-and-damper reference acceleration, so penetration and continued approach can both contribute a separating correction.

$$
a_\mathrm{ref}=-bv-kr
$$

Here $b$ and $k$ are the damping and stiffness in constraint space. For a single scalar constraint, the following relation shows how dimensionless impedance $d$ combines the free acceleration $a_\mathrm{free}$ with that target to produce the constrained acceleration $a_\mathrm{c}$.

$$
a_\mathrm{c}=(1-d)a_\mathrm{free}+d\,a_\mathrm{ref}
$$

As $d$ approaches 1, the response follows the reference more strongly. Several contacts couple through the same body's mass and inertia, so this single-constraint relation alone cannot predict the contact forces in an entire hand. [MuJoCo constraint dynamics](https://mujoco.readthedocs.io/en/4.0.0/computation/index.html#solver-parameters)

(soft-constraint-solref)=
## The two solref formats

- **Positive format `timeconst dampratio`**, for example `solref="0.02 1"`. The recovery time constant is 20 ms, and a damping ratio of 1 corresponds to critical damping. At a fixed damping ratio, a shorter time constant generally makes recovery faster and contact harder. Changing the damping ratio also changes internal stiffness.
- **Direct format `-stiffness -damping`**, for example `solref="-4000 -80"`. The magnitudes of the two nonpositive inputs specify stiffness and damping in constraint space. MuJoCo scales these inputs with impedance. Calibrate material stiffness in N/m from the relationship between force and displacement.

With the default `refsafe` protection, the effective positive-format `timeconst` is at least twice the simulation timestep. At a 2 ms timestep, requests of 3 ms and 4 ms both use 4 ms. The contact's `solref` readback can still show the requested 3 ms, so also inspect the timestep and protection flag. [MuJoCo `refsafe` rule](https://mujoco.readthedocs.io/en/4.0.0/XMLreference.html#option-flag-refsafe)

(soft-constraint-solimp)=
## The five solimp values

The default is `solimp="0.9 0.95 0.001 0.5 2"`. It controls how impedance varies with the magnitude of the position error $|r|$.

| Position | Parameter | Role |
| --- | --- | --- |
| 1 | `d0` | Impedance at zero error. |
| 2 | `dwidth` | Impedance at and beyond the transition width. |
| 3 | `width` | The error span of the transition. If normal distance is measured in metres, 0.001 is 1 mm. |
| 4 | `midpoint` | Relative location of the curve's inflection within the width. A value of 0.5 puts it in the middle. |
| 5 | `power` | Shape of the transition. A value of 1 gives a linear transition. |

Setting both end values to `0.9` makes impedance constant. Using `0.2 0.95` makes the onset softer and applies stronger correction once the error reaches `width`. **Width defines the impedance transition. Geometry and settings such as `margin` and `gap` determine when contact is detected and when it can generate force.**

The friction dimensions of an elliptic contact cone and joint or tendon dry-friction constraints have zero position error, so they sample the impedance curve at $d(0)$. In these friction constraints, the positive-format time constant controls velocity decay and the damping ratio is ignored. The direct format uses damping and ignores stiffness. An explicit contact pair can set `solreffriction` separately for the friction dimensions of an elliptic cone. [MuJoCo friction constraints](https://mujoco.readthedocs.io/en/4.0.0/modeling.html#friction) · [`solreffriction` in MJCF](https://mujoco.readthedocs.io/en/4.0.0/XMLreference.html#contact-pair-solreffriction)

(soft-constraint-readback)=
## Why does changing the parameter seem to do nothing?

1. **Confirm the contact participates in the solve.** Read its `dist` and `efc_address`. An `efc_address` of −1 means the contact has no active constraint row. If the pair is missing, check collision shapes, filtering, and when detection runs.
2. **Check the values assigned to the contact.** For generated geom contacts, the higher-priority geom supplies `solref` and `solimp`. Equal priorities use `solmix` weights, while `solref` uses elementwise minima if either geom uses the direct format. Also check explicit `contact/pair` settings and the global `override`. Check timestep and `refsafe` alongside `data.contact[i].solref` and `solimp`.
3. **Change one variable at a time.** For a ball on a table, fix the initial height, mass, geometry and integration settings. Change only `timeconst` or the impedance curve. Align observations to contact onset and the same sample phase, then compare normal force, peak penetration, rebound height and settling time. For sliding along the table, check normal load, friction and `condim` before tuning friction response.

[MuJoCo contact readback fields](https://mujoco.readthedocs.io/en/4.0.0/APIreference/APItypes.html#mjcontact) · [DexLab lesson on contact, friction and solving](../mujoco-learning/contact.md) · [DexLab normal contact response comparison](../contact-response.md)
