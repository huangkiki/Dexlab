# Native geometry qualification

[简体中文](NATIVE_GEOMETRY.zh-CN.md)

The basic SuperDex contact fixture uses native **BOX–PLANE** colliders. Its input triangle mesh and native reference surface are not SDF cooking evidence. This does not describe the separate apple-stem SDF demo.

`SuperDexPlane.record_geometry()` copies the native reference surface, local shape AABB, actual collider types and actual pose/velocity. Seven fixed local points are transformed into world coordinates using actual pose and queried with `get_points_distance_to_surface`. The independent checker uses an analytic box distance and a separate rotation implementation. It rejects missing fields, wrong frame/scale/type, unsigned interior distance and incomplete probes. The 1e-12 m arithmetic tolerance is not a material or penetration acceptance threshold. Sampled agreement does not prove the whole collision surface or combined contact law.

Enable explicitly with `contact_indent_run.run(..., record_native_geometry=True)` for SuperDex. The default remains off; other backends reject this query profile. The run receipt saves the observation, and independent verification checks it when requested.

Development evidence: the official FP64 runtime returned BOX/PLANE, 8 vertices, 12 triangles and ±0.02 m bounds. A fixed 0.8 s normal-load trajectory (0.5 ms steps) was executed once with queries off and once on. Every recorded state array and the full contact ledger were exactly equal. The original driver failed after both completed runs because its offline comparison omitted the contact-reader receipt argument. Offline-only recovery succeeded; neither simulation was retried or overwritten. This is one noninterference pair, not hardware validation or statistical reproducibility.

Raw evidence and complete regression results were published in [v0.26.0](https://github.com/huangkiki/Dexlab/releases/tag/v0.26.0). No new geometry accuracy claim for SDF is made.

Both trajectories still fail the original `no_tensile_normal_force` check. Observation noninterference does not repair that contact failure. Run `python demos/contact-benchmark/report_geometry.py EXTRACTED_PAIR` to rescore geometry, archive integrity, exact state/contact equality and all original acceptance failures offline.

The prepared archive was extracted: 165 file hashes and the full offline report match. [Size, hash and all outcomes](../../docs/evidence/native-geometry-v1.json). The archive is available in the linked v0.26.0 Release.
