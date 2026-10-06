# Can the current model represent the damping target?

[English](DAMPING_REFERENCE.md) | [简体中文](DAMPING_REFERENCE.zh-CN.md)

**Check model compatibility before tuning.** This conditional analytic check is not a new physics experiment and does not change historical scores.

## Source and assumptions

The [official FP64 1.0.0 property documentation](../../docs/evidence/normal-damping-law.json) describes normal viscous force proportional to elastic normal force and normal velocity, with coefficient units s/m. We interpret this as `F_d = c F_el v_n`; internal regularization, clamping and actual per-contact parameters have not been directly verified.

Near a positive static preload L, assume pure translation along common contact normals, the same fixed effective coefficient c at every contact, and elastic resultant L at equilibrium. Linearization at zero velocity gives tangent damping `D_eff(L)=cL`. Rotation, varying normals, contact switching and time discretization are outside this derivation.

## Relation to the existing synthetic target

The existing target D=40 N·s/m is constant at 2,4,6 N. Exact individual matches require c=20,10,6.67 s/m; one fixed coefficient cannot satisfy all three.

For positive loads in [a,b], minimizing

`min(c≥0) max(|ca/D−1|, |cb/D−1|)`

gives `c*=2D/(a+b)` and minimum worst relative tangent error `(b−a)/(b+a)`. Between D/b and D/a the endpoint errors move in opposite directions and their maximum is minimized at equality. Outside that interval moving inward decreases the maximum. Convexity of absolute affine error bounds interior loads by the endpoint maximum.

| Preload | Target tangent damping | Conditional prediction with c=10 s/m | Relative difference |
|---|---|---|---|
| 2 N | 40 N·s/m | 20 N·s/m | −50% |
| 4 N | 40 N·s/m | 40 N·s/m | 0% |
| 6 N | 40 N·s/m | 60 N·s/m | +50% |

The existing c=10 is already the minimax solution of this conditional problem. Sweeping a single fixed c cannot eliminate the mismatch at every preload. **50% is not a trajectory RMS lower bound, measured engine error or real-material discrepancy.** Load-scheduled coefficients change the model; they are not calibration of the same fixed material parameter.

## Reproduction and remaining work

```bash
.venv/bin/python -m dexlab.damping_reference --loads-n 2 4 6 --target-damping-ns-m 40
# Positive control: a single preload can match exactly
.venv/bin/python -m dexlab.damping_reference --loads-n 4 --target-damping-ns-m 40
```

The checker rejects empty, zero, negative or nonfinite preloads and nonpositive targets. It imports no physics engine and changes no raw trajectory. Tests cover single-load matching, scaling, endpoint optimality and invalid inputs.

Native tangent identification has since been completed within its declared positive-load scope; see [TANGENT](TANGENT_IDENTIFICATION.md). It does not repair unloading or complete common-material calibration. The [acceptance audit](CONCLUSIONS.md) retains these open commitments; #10 remains open and measured material properties remain in #6.
