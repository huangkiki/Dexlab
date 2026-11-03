import allCollisions from "./assets/nai/collisions.json" with { type: "json" };

/** Visual assets and convex collision parts come from the same generated meshes. */
export const CATALOG = [
  { name: "Nai Frog", zh: "奶蛙", kind: "frog" },
  { name: "Nai Mouse", zh: "奶鼠", kind: "mouse" },
  { name: "Nai Bean", zh: "奶豆", kind: "bean" },
  { name: "Nai Chicken", zh: "奶鸡", kind: "chicken" },
  { name: "Nai Cat", zh: "奶猫", kind: "cat" },
  { name: "Nai Rabbit", zh: "奶兔", kind: "rabbit" },
  { name: "Nai Egg", zh: "奶蛋", kind: "egg" },
  { name: "Baby Nai Frog", zh: "小奶蛙", kind: "baby-frog" },
  { name: "Nai Dog", zh: "奶狗", kind: "dog" },
  { name: "Pink Nai Frog", zh: "奶粉", kind: "pink-frog" },
  { name: "Nai Swirl", zh: "奶屎", kind: "poop" },
  { name: "Soy Milk", zh: "豆奶", kind: "soy-milk" },
  { name: "Nai Fish", zh: "奶鱼", kind: "fish" },
  { name: "Nai Tea", zh: "奶茶", kind: "tea-cup" },
  { name: "Nai Bottle", zh: "奶瓶", kind: "bottle" },
  { name: "Sigma Nai Frog", zh: "西格玛奶蛙", kind: "sigma-frog" },
] as const;
export const TOY_SCALE = 1.6;
// Ten columns, three layers. Gravity and contact settle the 30 prizes into a pile.
// Leave the front-left delivery chute clear; no in-round attachment or pose edits.
const columns = [-.14, .02, .18].flatMap((y, row) =>
  [-.225, -.075, .075, .225].flatMap((x, column) =>
    row === 0 && column < 2 ? [] : [{ x, y }]),
);
const slots = Array.from({ length: 3 }, (_, layer) =>
  columns.map((column) => ({ ...column, z: .09 + layer * .19 })),
).flat();
export const TOYS = slots.map((slot, i) => ({ ...CATALOG[(i * 7) % CATALOG.length]!, ...slot }));

export const TOY_ASSETS = allCollisions
  .map((parts, i) =>
    parts
      .map(
        (part, j) =>
          `<mesh name="toy_mesh${i}_${j}" scale="${TOY_SCALE} ${TOY_SCALE} ${TOY_SCALE}" vertex="${part.vertices.join(" ")}" face="${part.faces.join(" ")}"/>`,
      )
      .join(""),
  )
  .join("");

export function toyXml(index: number) {
  const toy = TOYS[index]!;
  const asset = CATALOG.findIndex(character => character.kind === toy.kind);
  const geoms = allCollisions[asset]!.map(
    (part, j) =>
      `<geom name="${j === 0 ? `toy_geom${index}` : `toy${index}_part${j}`}" type="mesh" group="1" mesh="toy_mesh${asset}_${j}" mass="${part.mass}"/>`,
  ).join("");
  return `<body name="toy${index}" pos="${toy.x} ${toy.y} ${toy.z}"><freejoint name="toy_joint${index}"/>${geoms}</body>`;
}
