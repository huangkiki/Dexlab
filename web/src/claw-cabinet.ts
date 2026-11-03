import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";

// Decorative housing only. Native collision geometry and actuator motion stay in ClawTask.
export function buildCabinet(scene: THREE.Scene) {
  const enamel = new THREE.MeshStandardMaterial({ color: 0x30223f, metalness: .35, roughness: .28 });
  const mauve = new THREE.MeshStandardMaterial({ color: 0x885e93, metalness: .5, roughness: .3 });
  const silver = new THREE.MeshStandardMaterial({ color: 0xe2c2eb, metalness: .65, roughness: .24 });
  const rose = new THREE.MeshStandardMaterial({ color: 0xe8a5d5, emissive: 0x7c225d, emissiveIntensity: .65, roughness: .4 });
  const moon = new THREE.MeshStandardMaterial({ color: 0xffe3ad, emissive: 0x916322, emissiveIntensity: .4, metalness: .25, roughness: .4 });
  const box = (size: [number, number, number], position: [number, number, number], material = enamel, radius = .008) => {
    const mesh = new THREE.Mesh(new RoundedBoxGeometry(...size, 3, radius), material);
    mesh.position.set(...position);
    mesh.receiveShadow = true;
    scene.add(mesh);
    return mesh;
  };
  const emblem = (shape: THREE.Shape, material: THREE.Material, scale: number, position: [number, number, number]) => {
    const geometry = new THREE.ExtrudeGeometry(shape, { depth: .09, bevelEnabled: true, bevelSegments: 2, steps: 1, bevelSize: .025, bevelThickness: .025, curveSegments: 24 });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.x = Math.PI / 2;
    mesh.scale.setScalar(scale);
    mesh.position.set(...position);
    return mesh;
  };
  const star = new THREE.Shape();
  for (let i = 0; i < 10; i++) {
    const angle = Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? .44 : 1;
    if (i === 0) star.moveTo(Math.cos(angle) * r, Math.sin(angle) * r);
    else star.lineTo(Math.cos(angle) * r, Math.sin(angle) * r);
  }
  star.closePath();
  const crescent = new THREE.Shape();
  crescent.moveTo(.4, .92);
  crescent.bezierCurveTo(-1.2, 1.1, -1.2, -1.1, .4, -.92);
  crescent.bezierCurveTo(-.48, -.52, -.48, .52, .4, .92);
  crescent.closePath();

  // Lacquered rounded frame, open viewing face, luminous seams and a dark back panel.
  for (const x of [-.302, .302]) for (const y of [-.23, .23]) {
    box([.025, .025, .44], [x, y, .19]);
    box([.005, .005, .405], [x, y - .014, .19], rose, .002);
  }
  // Keep the chute open: the deck is already represented by native floor geometry.
  box([.44, .035, .06], [.075, -.235, -.03]);
  box([.64, .49, .045], [0, 0, -.64]);
  box([.43, .47, .60], [.075, 0, -.33]);
  box([.41, .012, .055], [.075, -.242, -.57], mauve);
  scene.add(emblem(crescent, mauve, .075, [.075, -.242, -.29]));
  for (const x of [-.04, .19]) scene.add(emblem(star, rose, .013, [x, -.244, -.30]));
  box([.59, .025, .315], [0, .238, .19]);
  box([.59, .006, .008], [0, .22, .045], rose, .002);
  box([.65, .045, .07], [0, -.232, .415]);
  box([.64, .035, .045], [0, .23, .402]);
  for (const x of [-.302, .302]) box([.03, .47, .035], [x, 0, .395]);
  box([.57, .006, .004], [0, -.258, .389], rose, .001);
  // Sculpted celestial marquee; these are mesh silhouettes, not flat image stickers.
  scene.add(emblem(crescent, moon, .023, [0, -.258, .418]));
  for (const [x, scale] of [[-.075, .011], [.075, .011], [-.18, .008], [.18, .008]] as const)
    scene.add(emblem(star, silver, scale, [x, -.258, .418]));
  for (const [x, z, scale] of [[-.20, .28, .014], [.19, .22, .009], [-.08, .17, .007], [.075, .32, .012]] as const)
    scene.add(emblem(star, mauve, scale, [x, .219, z]));
  scene.add(emblem(crescent, mauve, .044, [-.015, .218, .27]));
  // The gold opening remains unmistakable against the plum deck in both renderers.
  for (const x of [-.278, -.152]) box([.004, .13, .005], [x, -.135, .003], moon, .001);
  for (const y of [-.20, -.07]) box([.13, .004, .005], [-.215, y, .003], moon, .001);

  const crossbeam = box([.6, .014, .014], [0, 0, .365], silver, .004);
  const trolley = box([.065, .065, .028], [0, 0, .35], mauve);
  const charm = new THREE.Group();
  const face = emblem(crescent, moon, .012, [0, -.0265, 0]);
  charm.add(face);
  for (const x of [-.018, .018]) {
    const ear = new THREE.Mesh(new THREE.ConeGeometry(.009, .022, 3), mauve);
    ear.rotation.x = Math.PI / 2;
    ear.position.set(x, 0, .026);
    charm.add(ear);
  }
  scene.add(charm);
  return { crossbeam, trolley, charm };
}
