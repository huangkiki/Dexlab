import { TOYS } from "./claw-toys";
const models = import.meta.glob<string>("./assets/nai/display/*.glb", { eager: true, query: "?url", import: "default" });
const portraits = import.meta.glob<string>("./assets/nai/display/*.png", { eager: true, query: "?url", import: "default" });
export const toyModelUrls = TOYS.map((toy) => models[`./assets/nai/display/${toy.kind}.glb`]!);
export const toyPortraitUrls = TOYS.map((toy) => portraits[`./assets/nai/display/${toy.kind}.png`]!);
