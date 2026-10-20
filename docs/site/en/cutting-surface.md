# Cutting-surface reconstruction: matched mechanisms and remaining gaps

This page evaluates visual topology and motion binding only. A visible kerf is not evidence of correct mechanical separation; native particle connectivity, contact and momentum remain independently scored.

## Implemented from paper III-F

Tofu and banana now share one reference-configuration surface reconstruction:

1. primal links of a uniform reference grid store Hermite intersection points and unit normals for the original boundary and recorded blade surfaces;
2. a candidate link disconnects only after native particle histories locally contain side digits 1 and 2 for that cut, so unassigned material below a partial cut remains connected;
3. while material remains connected, remaining-link components are computed per cell with one QEF dual vertex per local region; once saved native mechanical components are disjoint, each is rebuilt as a closed local volume clipped by its recorded cut half-spaces, so a triangle cannot share incompatible motion fields;
4. a complete cut creates coincident faces with opposing normals for adjacent components;
5. every surface representative inherits a native mechanical component and persistent cut code, then follows a compatible TLMPM motion field through fixed trilinear weights.

Analytical acceptance covers original Hermite points on the zero level set, unit normals, a closed uncut surface, two components after a complete cut, four components after orthogonal intersecting cuts, a connected lower bridge for partial cuts, opposing cap normals, no open edges and no degenerate triangles. Replay adds no visual opening; the currently published parallel complete-cut tasks also do not mix native mechanical components within one triangle.

## Remaining differences from the paper

| Paper capability | Current boundary |
| --- | --- |
| The finite blade edge sweeps each substep and disconnects the reference links it actually intersects online. | Replay recovers axis-aligned x/y planes from the saved blade path and combines them with persistent side labels. Lateral sweep beyond half a material-sampling spacing is rejected; arbitrary curved or tilted paths are unsupported. |
| Only cells affected during the current step are updated. | CPU replay rebuilds the active cells and does not implement the authors' local GPU update path. |
| Surface representatives embed directly in the compatible TLMPM motion field at that time. | Historical records did not save logical-grid motion fields. DexLab reconstructs compatible nodal motion from saved particle positions and deformation; missing boundary nodes use local multi-particle affine extrapolation from the same mechanical component only. Once a saved state is disconnected, this implementation also rebuilds each native mechanical component as a closed local volume instead of exactly reproducing the paper's online per-cell update. Topology follows native history, while coarse particle deformation can still produce small spikes on the outer surface. |
| The authors' surface-grid resolution and geometry assets. | These are unpublished. DexLab independently uses surface spacing equal to one quarter of the mechanical grid spacing; the banana remains an authored shape rather than the authors' asset or a scanned specimen. |
| Independent motion after fully intersecting through-cuts. | Analytical tests cover four independent closed regions, but no formal record and public video yet qualify motion around the intersection line. The current crossed-scoring task covers shallow cuts whose lower bridge remains connected. |
| A new partial crack forming inside an already separated piece. | Complete cuts remain closed and split again when the next cut completes. The intermediate state where a later cut has started but not passed through a piece separated by an earlier cut is not independently qualified, so the final frame does not establish exact frame-by-frame equivalence to the paper. |
| Compact active states on GPU and real-time performance. | Unimplemented. This is an offline NumPy/SciPy/VTK CPU replay and cannot reproduce the paper's timing result. |

The supported straight-cut tasks may therefore be described as using paper-style linked volumes, Hermite data and local dual contouring. They are not a complete reproduction of the BladeMaster surface system. Each public media directory records source hashes, renderer hashes, resolution, frame mapping and these limits in `provenance.json`.

[Cutting-fidelity matrix](cutting-fidelity.md) · [Crossed shallow scoring](tofu-scoring.md) · [Continuous cutting and blade pushing](cut-push.md) · [BladeMaster III-F](https://arxiv.org/html/2609.27342v2#S3.SS6)
