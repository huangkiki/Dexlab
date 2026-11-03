# Nai-family art assets

The maintainer's Nai-family chart is the identity reference. OpenAI ImageGen produced a plush interpretation and individual modeling inputs on 2026-11-02/03; the source chart is not redistributed. Microsoft TRELLIS v1 generated the textured 3D meshes locally. No assets were copied from another claw-machine project.

角色沿用维护者提供的奶家族谱。2D 毛绒形象由 ImageGen 生成，3D 网格在本地通过 TRELLIS v1 生成；网页加载预先导出的模型。物理上采用近似的刚体碰撞外形，不模拟毛绒变形。

- `nai-family-atlas.png`: three columns by two rows, frog / mouse / bean / chicken / cat / rabbit. Retained as the original six-character design reference.
- `nai/*.glb`: 16 textured Y-up models, normalized in meters with their front along +Z. The renderer rotates them to MuJoCo's Z-up frame and reads each body's measured pose.
- `nai/collisions.json`: separate convex parts derived from those meshes with CoACD 1.0.14. They are rigid collision approximations, not exact surface collisions. The 16-part cap exceeded the requested concavity target for mouse, chicken, cat and rabbit; the actual warnings are retained in the manifest.
- `nai/inputs/*.png` and `nai/prompts.json`: exact generation inputs and prompts. Each copied PNG embeds its prompt; the manifest distinguishes the original generation-input hash from the metadata-bearing source copy.
- `nai/manifest.json`: model/source revisions, seeds, dimensions, transforms, export settings, collider settings and hashes. Every toy weighs a synthetic 80 g. Frog and chicken use 60% foot ballast to stabilize their sloped generated soles; other masses follow convex-part volume. These are gameplay parameters, not measurements of real plush toys.

Generation used the official [TRELLIS source](https://github.com/microsoft/TRELLIS/tree/193e0502b5cb3eb5997ec457d5340e95d09b158e) and `microsoft/TRELLIS-image-large` revision `25e0d31ffbebe4b5a97464dd851910efc3002d96`, with the upstream 25-step samplers and guidance 5. The original six exports use `simplify=0.94`, 1024-pixel textures and hole filling. The ten additional characters use seed 1, `simplify=0.90` and 2048-pixel textures; per-asset settings override the legacy defaults in the manifest. The final GLBs explicitly set `metallicFactor=0` and use rough fabric (`roughnessFactor=1` in the original six assets, `0.92` in the additions and the live material): the source exporter omitted metallicity, which otherwise loads as fully metallic. This metadata correction preserves texture and geometry bytes. Frog uses seed 1; mouse, bean, chicken and rabbit use seed 1; cat uses seed 0 after rejecting duplicated eyes in its first output. Duplicated-face frog variants were also rejected before integration. This is offline asset generation, not a model executed in the browser.

The original compound-primitive visual candidate and its bump map were replaced. Native contact, actuator-only motion and independent bin scoring remain the gameplay mechanism.

## Initial atlas prompt

```text
Use case: stylized-concept. Asset type: a production prize-character atlas for the DexLab 3D claw-machine game. The attached image is the character identity reference only, not an image to retouch. Create six separate plush collectible characters inspired closely by these exact reference identities, in a perfectly regular 3-column by 2-row atlas. Reading order: top left 奶蛙 (the original tall pear-bodied pale yellow frog with tiny eyes, small arms resting around its round belly and short feet); top middle 奶鼠 (pale yellow chubby mouse with very large round ears, little paws and slender tail); top right 奶豆 (round pale yellow bean-like creature with large black bead eyes, tiny smile, tiny feet); bottom left 奶鸡 (plump yellow chicken with small red comb, yellow beak, raised feathered tail and feet); bottom middle 奶猫 (pear-shaped pale yellow cat with triangular ears, little paws, tiny smile); bottom right 奶兔 (pale yellow rabbit with two long upright ears, round belly and tiny paws). Preserve the recognizable silhouettes and simple sweet faces from the reference. All six are soft premium short-pile plush toys with fine fabric texture and restrained seams, not shiny plastic. Full body, front three-quarter view, consistent scale, soft even studio light, every character completely isolated and centered in its own equal rectangular cell with generous clear padding. Transparent background with real alpha, no shadows outside the toy, no text, no labels, no grid lines, no badges, no added characters or watermark. This atlas will be used for the game's prize collection thumbnails and as a shape/material reference for matching fully 3D physics toys.

```

## Final atlas background edit

```text
Edit only the background of this six-character 3 by 2 plush atlas. Replace every checkerboard square with one perfectly uniform opaque warm ivory background, color #f6f2e6. Keep all six toys, their order, poses, proportions, detailed fabric texture, eye and face details, lighting and exact grid placement unchanged. No text, labels, grid lines, extra items or checkerboard. The output is an opaque production thumbnail atlas, not a transparency preview.

```

新增十款为奶蛋、小奶蛙、奶狗、奶粉、奶屎、豆奶、奶鱼、奶茶、奶瓶、西格玛奶蛙。它们沿用相同本地 TRELLIS 模型和默认推理参数，采用 2048 像素贴图与 `simplify=0.90`。三组柜子覆盖全部角色，每组六只。原六款碰撞数据保持原样；新款碰撞形状从各自归一化后的网格分解得到，总质量仍为合成 80 g，按凸块体积分配。
