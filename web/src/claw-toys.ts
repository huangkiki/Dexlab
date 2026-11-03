import allCollisions from "./assets/nai/collisions.json" with { type: "json" };

/** Visual assets and convex collision parts come from the same generated meshes. */
const classic = [
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

export const CATALOG = [
  ...classic,
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
export const CABINETS = {
  classic: { zh: "经典六只", name: "Original six", toys: [0, 1, 2, 3, 4, 5] },
  friends: { zh: "新朋友", name: "New friends", toys: [6, 7, 8, 9, 10, 11] },
  curios: { zh: "奇妙小队", name: "Curious crew", toys: [12, 13, 14, 15, 0, 4] },
} as const;
export function cabinetFromSearch(search: string): keyof typeof CABINETS {
  const key = new URLSearchParams(search).get("cabinet");
  return key === "friends" || key === "curios" ? key : "classic";
}
// A cabinet is immutable for the lifetime of a page and shared by all three worlds.
// Choosing another cabinet explicitly reloads the page and starts a fresh collection.
export const CABINET = cabinetFromSearch(typeof location === "undefined" ? "" : location.search);
export const TOYS = CABINETS[CABINET].toys.map((index, slot) => ({
  ...classic[slot]!, ...CATALOG[index],
}));
const collisions = CABINETS[CABINET].toys.map((index) => allCollisions[index]!);

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
