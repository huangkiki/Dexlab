import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

/** Release decoded image textures as well as GPU resources, including failed loads. */
export function disposeMeshes(root: THREE.Object3D) {
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  const textures = new Set<THREE.Texture>();
  root.traverse((node) => {
    if (!(node instanceof THREE.Mesh || node instanceof THREE.Line)) return;
    geometries.add(node.geometry);
    for (const material of Array.isArray(node.material)
      ? node.material
      : [node.material]) {
      materials.add(material);
      for (const value of Object.values(material))
        if (value instanceof THREE.Texture) textures.add(value);
    }
  });
  for (const texture of textures) {
    texture.dispose();
    if (
      typeof ImageBitmap !== "undefined" &&
      texture.image instanceof ImageBitmap
    )
      texture.image.close();
  }
  for (const material of materials) material.dispose();
  for (const geometry of geometries) geometry.dispose();
}

export async function loadToyModels(urls: readonly string[]) {
  const loader = new GLTFLoader();
  const results = await Promise.allSettled(
    urls.map((url) => loader.loadAsync(url)),
  );
  const failed = results.find((result) => result.status === "rejected");
  if (failed) {
    for (const result of results)
      if (result.status === "fulfilled") disposeMeshes(result.value.scene);
    throw new Error("Unable to load the toy models. Reload to try again.", {
      cause: failed.reason,
    });
  }
  return results.map((result) => {
    if (result.status !== "fulfilled")
      throw new Error("Unreachable asset state");
    const model = result.value.scene;
    model.rotation.x = Math.PI / 2;
    model.traverse((node) => {
      if (!(node instanceof THREE.Mesh)) return;
      node.castShadow = node.receiveShadow = true;
      const material = node.material as THREE.MeshStandardMaterial;
      material.roughness = 0.92;
      material.metalness = 0;
    });
    const body = new THREE.Group();
    body.add(model);
    return body;
  });
}
