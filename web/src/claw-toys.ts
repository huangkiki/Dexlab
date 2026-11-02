import collisions from "./assets/nai/collisions.json" with { type: "json" };

/** Visual assets and convex collision parts come from the same generated meshes. */
export const TOYS = [
  {
    name: "Nai Frog",
    zh: "奶蛙",
    kind: "frog",
    x: -0.085,
    y: -0.075,
    color: 0xf6d56f,
  },
  {
    name: "Nai Mouse",
    zh: "奶鼠",
    kind: "mouse",
    x: 0.075,
    y: -0.07,
    color: 0xf7dc89,
  },
  {
    name: "Nai Bean",
    zh: "奶豆",
    kind: "bean",
    x: 0.19,
    y: 0.055,
    color: 0xffdf65,
  },
  {
    name: "Nai Chicken",
    zh: "奶鸡",
    kind: "chicken",
    x: -0.17,
    y: 0.075,
    color: 0xf6cc55,
  },
  {
    name: "Nai Cat",
    zh: "奶猫",
    kind: "cat",
    x: -0.025,
    y: 0.085,
    color: 0xf5db87,
  },
  {
    name: "Nai Rabbit",
    zh: "奶兔",
    kind: "rabbit",
    x: 0.1,
    y: 0.11,
    color: 0xf8df94,
  },
] as const;

export const TOY_ASSETS = collisions
  .map((parts, i) =>
    parts
      .map(
        (part, j) =>
          `<mesh name="toy_mesh${i}_${j}" vertex="${part.vertices.join(" ")}" face="${part.faces.join(" ")}"/>`,
      )
      .join(""),
  )
  .join("");

export function toyXml(index: number) {
  const toy = TOYS[index]!;
  const geoms = collisions[index]!.map(
    (part, j) =>
      `<geom name="${j === 0 ? `toy_geom${index}` : `toy${index}_part${j}`}" type="mesh" mesh="toy_mesh${index}_${j}" mass="${part.mass}"/>`,
  ).join("");
  return `<body name="toy${index}" pos="${toy.x} ${toy.y} 0.038"><freejoint name="toy_joint${index}"/>${geoms}</body>`;
}
