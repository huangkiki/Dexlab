# Asset provenance

The root [Apache-2.0 license](../LICENSE) applies to DexLab project code. Third-party assets retain their original terms and are not relicensed by this project. Demo images and videos include those assets and do not grant an Apache-2.0 license to the underlying models or textures.

| Asset | Source and local changes | Attribution and terms |
|---|---|---|
| OpenArm V20 and Wuji Hand 2 Beta1 | [Project SuperDex](https://github.com/unilabsim/project_superdex), reference commit `f216dace36464d70f224caa4253074ec365ed14f` | OpenArm: [Apache-2.0](asset-licenses/openarm-arm-LICENSE), [notice](asset-licenses/openarm-arm-NOTICE); Wuji: [MIT](asset-licenses/wuji-hand-LICENSE), [notice](asset-licenses/wuji-hand-NOTICE). Original notices are included in the downloaded archive |
| Robot mounting and display geometry | Cropped OpenArm mounting plate, fixed mounting transforms, and OBJ conversions for display; no ZGWS body or legs | Local changes are recorded in [NOTICE](../NOTICE) |
| Apple and stem | Converted from NVIDIA Isaac Sim 5.1 `Apple.usd` and textures, including collision meshes and rigid-body SDF inputs | [Original URLs and SHA256 hashes](../demos/apple-stem-grasp/assets/apple/sources.json), [Isaac Sim licensing](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/common/legal.html) |

Reference robot and apple file hashes are recorded in [asset-sha256.json](../demos/apple-stem-grasp/evidence/asset-sha256.json). SuperDex and MuJoCo are installed from their official PyPI distributions; their native binaries are not redistributed by DexLab. MuJoCo is used only for rendering and requires no source changes.

## Distribution

Large robot assets are downloaded from the `apple-stem-assets-v1` GitHub Release. The archive preserves the exact validated files, plus license and attribution notices. [assets.json](../demos/apple-stem-grasp/assets.json) pins the archive SHA-256 and every installed file.

Apple textures are not mirrored in the Release. The downloader fetches only the albedo texture needed by this demo directly from NVIDIA, using its original URL and SHA-256. NVIDIA source terms continue to apply; the source record is not a grant of redistribution rights. Existing small task-specific derived apple meshes remain in Git and are unchanged by this asset-pack migration.
