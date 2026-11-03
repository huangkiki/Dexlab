import { TOYS } from "./claw-toys";
const models = import.meta.glob<string>("./assets/nai/*.glb", { eager: true, query: "?url", import: "default" });
const portraits = import.meta.glob<string>("./assets/nai/inputs/*.png", { eager: true, query: "?url", import: "default" });
export const toyModelUrls = TOYS.map((toy) => models[`./assets/nai/${toy.kind}.glb`]!);
export const toyPortraitUrls = TOYS.map((toy) => portraits[`./assets/nai/inputs/${toy.kind}.png`]!);
