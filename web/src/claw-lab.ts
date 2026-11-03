import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { WebGPURenderer } from "three/webgpu";
import { ClawSimulation, type ClawSimulationState } from "./claw-simulation";
import { loadToyModels, disposeMeshes } from "./claw-meshes";
import { toyModelUrls } from "./claw-model-urls";
import { BIN, CLAW_SCALE, CHUTE_LIP, type ClawSnapshot, type MoveAxis } from "./claw-task";

import type { ClawFrame } from "./claw-comparison";
import { buildCabinet } from "./claw-cabinet";

export class ClawLab {
  get snapshot() { return this.simulation.state.reference.snapshot; }
  get comparison() { return this.simulation.state; }
  get rendererName() {
    return (this.renderer.backend as { isWebGPUBackend?: boolean }).isWebGPUBackend ? "WebGPU" : "WebGL 2";
  }
  speed = 1;
  readonly input = new Map<string, { axis: MoveAxis; direction: number }>();
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(37, 1, 0.01, 5);
  private controls: OrbitControls;
  private observer: ResizeObserver;
  private visibility: IntersectionObserver;
  private visible = new Set<Element>();
  private viewLabels: Element[];
  private page: Element;
  private geoms = new Map<number, THREE.Mesh>();
  private overhead: THREE.Mesh[] = [];
  private cable: THREE.Mesh;
  private charm: THREE.Group;
  private trolley: THREE.Mesh;
  private aim: THREE.Mesh;
  private frame = 0;
  private active = true;
  private failed = false;
  private disposed = false;
  private lastTime = performance.now();
  private lastPhysics = performance.now();
  private lastEmit = 0;
  private comparing = false;
  private layout = 0;
  private compactView = false;
  private topView = false;
  private angledFov = 37;
  private normalView: [number, number, number] = [0.45, -1.25, 0.63];
  private mobile = matchMedia("(pointer: coarse)").matches || innerWidth < 600;

  private constructor(
    private canvas: HTMLCanvasElement,
    private readonly simulation: ClawSimulation,
    private readonly renderer: WebGPURenderer,
    private readonly toys: THREE.Group[],
    private onSnapshot: (s: ClawSnapshot) => void,
    private onError: (e: unknown) => void,
    private onComparison: (comparison: ClawSimulationState) => void,
  ) {
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, this.mobile ? 1 : 1.5));
    this.renderer.setClearColor(0x181322);
    this.renderer.shadowMap.enabled = !this.mobile;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    this.camera.up.set(0, 0, 1);
    this.camera.position.set(...this.normalView);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.target.set(0, 0, 0.20);
    this.controls.enablePan = false;
    this.controls.minDistance = 0.25;
    this.controls.maxDistance = 1.65;
    this.controls.minPolarAngle = 0.08;
    this.controls.maxPolarAngle = Math.PI / 2.1;
    this.controls.update();
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    const fill = new THREE.HemisphereLight(0xf9e8ff, 0x44314c, 2.1);
    fill.position.set(0, 0, 1);
    this.scene.add(fill, new THREE.AmbientLight(0xf7e6f3, 0.65));
    const light = new THREE.DirectionalLight(0xffeedd, 3);
    light.position.set(-0.3, -0.6, 1.2);
    light.castShadow = true;
    light.shadow.mapSize.set(1024, 1024);
    Object.assign(light.shadow.camera, {
      left: -0.6,
      right: 0.6,
      top: 0.6,
      bottom: -0.6,
      near: 0.1,
      far: 3,
    });
    light.shadow.bias = -0.0004;
    light.shadow.radius = 4;
    this.scene.add(light);
    this.buildNativeGeoms();
    const cabinet = buildCabinet(this.scene);
    this.overhead.push(cabinet.crossbeam);
    this.trolley = cabinet.trolley;
    this.charm = cabinet.charm;
    this.cable = new THREE.Mesh(
      new THREE.CylinderGeometry(0.003, 0.003, 1, 12),
      new THREE.MeshStandardMaterial({
        color: 0x9b82ad,
        metalness: 0.7,
        roughness: 0.35,
      }),
    );
    this.cable.rotation.x = Math.PI / 2;
    this.scene.add(this.cable);
    const ring = new THREE.RingGeometry(0.035 * CLAW_SCALE, 0.037 * CLAW_SCALE, 48);
    this.aim = new THREE.Mesh(
      ring,
      new THREE.MeshStandardMaterial({
        color: 0xf0b7ed,
        emissive: 0xe385d8,
        emissiveIntensity: 1.2,
        roughness: .7,
        side: THREE.DoubleSide,
        depthTest: false,
      }),
    );
    this.aim.renderOrder = 10;
    this.aim.position.z = 0.002;
    this.scene.add(this.aim);
    const rim = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(
        [
          [-1, -1],
          [1, -1],
          [1, 1],
          [-1, 1],
          [-1, -1],
        ].map(
          ([x, y]) =>
            new THREE.Vector3(
              BIN.x + x! * BIN.half,
              BIN.y + y! * BIN.half,
              0.002,
            ),
        ),
      ),
      new THREE.LineBasicMaterial({ color: 0xf4cc79 }),
    );
    this.scene.add(rim);
    this.scene.add(...this.toys);
    this.page = canvas.closest(".claw-page")!;
    this.viewLabels = [...canvas.parentElement!.querySelectorAll(".world-label")];
    // IntersectionObserver includes the embedding page's clip, unlike innerHeight.
    this.visibility = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) this.visible.add(entry.target);
        else this.visible.delete(entry.target);
      }
    });
    for (const element of [this.page, canvas, ...this.viewLabels]) this.visibility.observe(element);
    this.observer = new ResizeObserver(() => this.resize(canvas));
    this.observer.observe(canvas);
    this.resize(canvas);
    this.animate();
  }
  static async create(
    canvas: HTMLCanvasElement,
    onSnapshot: (s: ClawSnapshot) => void,
    onError: (e: unknown) => void,
    onComparison: (comparison: ClawSimulationState) => void,
  ) {
    const mobile = matchMedia("(pointer: coarse)").matches || innerWidth < 600;
    const renderer = new WebGPURenderer({ canvas, antialias: !mobile });
    let simulation: ClawSimulation | undefined;
    let toys: THREE.Group[] = [];
    let lab: ClawLab | undefined;
    try {
      await renderer.init();
      simulation = await ClawSimulation.create(() => lab?.receive(),
        error => lab ? lab.fail(error) : onError(error));
      toys = await loadToyModels(toyModelUrls);
      lab = new ClawLab(canvas, simulation, renderer, toys, onSnapshot, onError, onComparison);
      return lab;
    } catch (error) {
      for (const toy of toys) disposeMeshes(toy);
      simulation?.dispose();
      renderer.dispose();
      throw error;
    }
  }
  private receive() {
    const changed = this.comparing !== this.comparison.started;
    this.comparing = this.comparison.started;
    this.onComparison(this.comparison);
    if (changed) this.resize(this.canvas);
    const now = performance.now();
    if (now - this.lastEmit > 100) {
      this.lastEmit = now;
      this.onSnapshot(this.snapshot);
    }
  }
  private buildNativeGeoms() {
    const m = this.simulation.model;
    for (let i = 0; i < m.ngeom; i++) {
      if (this.simulation.model.toyBodies.includes(m.geom_bodyid[i]!)) continue;
      const size = Array.from(m.geom_size.slice(i * 3, i * 3 + 3)) as number[];
      const type = m.geom_type[i];
      let geometry: THREE.BufferGeometry;
      if (type === 2) geometry = new THREE.SphereGeometry(size[0], 24, 16);
      else if (type === 3) {
        geometry = new THREE.CapsuleGeometry(size[0], size[1]! * 2, 6, 12);
        geometry.rotateX(Math.PI / 2);
      } else if (type === 5) {
        geometry = new THREE.CylinderGeometry(
          size[0],
          size[0],
          size[1]! * 2,
          24,
        );
        geometry.rotateX(Math.PI / 2);
      } else if (type === 6)
        geometry = new THREE.BoxGeometry(
          size[0]! * 2,
          size[1]! * 2,
          size[2]! * 2,
        );
      else throw new Error(`Unsupported cabinet geometry: ${type}`);
      const wall = i >= 8 && i <= 11;
      const claw = this.simulation.model.clawParts.includes(i);
      const material = new THREE.MeshPhysicalMaterial({
        color: claw
          ? (i === this.simulation.model.hub ? 0x775180 : 0xd7b6df)
          : wall
            ? 0x6b4779
            : i < 3
              ? 0x62506f
              : i >= 4 && i <= 7
                ? 0x49344f
                : 0x38293e,
        roughness: claw ? 0.26 : 0.65,
        metalness: claw ? 0.65 : 0.05,
        transparent: wall,
        opacity: wall ? 0.06 : 1,
        depthWrite: !wall,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.castShadow = !wall;
      mesh.receiveShadow = !wall;
      this.geoms.set(i, mesh);
      this.scene.add(mesh);
    }
  }
  private resize(canvas: HTMLCanvasElement) {
    const r = canvas.getBoundingClientRect();
    this.renderer.setSize(Math.max(1, r.width), Math.max(1, r.height), false);
    const columns = this.comparison.started && r.width >= 700 ? 3 : 1;
    const rows = this.comparison.started && columns === 1 ? 3 : 1;
    this.camera.aspect =
      Math.max(1, r.width / columns) / Math.max(1, r.height / rows);
    const compact =
      this.comparison.started || r.width < 600 || this.camera.aspect < 1.55;
    // Frame the pile and complete claw; the deep collection well extends below the play bay.
    this.angledFov = compact
      ? THREE.MathUtils.radToDeg(
          2 *
            Math.atan(
              Math.tan(THREE.MathUtils.degToRad(46 / 2)) *
                Math.max(1, 1 / this.camera.aspect),
            ),
        )
      : 37;
    if (compact !== this.compactView) {
      this.compactView = compact;
      this.normalView = compact ? [0, -1.3, 0.63] : [0.45, -1.25, 0.63];
      this.setTopView(this.topView);
    }
    this.camera.fov = this.topView ? 37 : this.angledFov;
    this.camera.updateProjectionMatrix();
  }
  clearInput() {
    this.input.clear();
  }
  focusToy(index: number) {
    const id = this.simulation.model.toyBodies[index]! * 3;
    const positions = this.simulation.state.reference.bodyPosition;
    const p = { x: positions[id]!, y: positions[id+1]!, z: positions[id+2]! };
    this.setTopView(false);
    this.controls.target.set(p.x, p.y, p.z + 0.015);
    this.camera.position.set(p.x + 0.07, p.y - 0.27, p.z + 0.11);
    this.controls.update();
  }
  seek(frame: number) {
    this.simulation.send({ type: "seek", frame });
  }
  togglePlayback() {
    this.simulation.send({ type: "play" });
  }
  setActive(active: boolean) {
    if (this.disposed || this.failed) return;
    this.clearInput();
    this.lastPhysics = performance.now();
    if (active === this.active) return;
    this.active = active;
    if (active) {
      this.lastTime = performance.now();
      this.animate();
    } else cancelAnimationFrame(this.frame);
  }
  reset() {
    this.clearInput();
    this.simulation.send({ type: "reset", layout: ++this.layout });
    this.onComparison(this.comparison);
    this.lastPhysics = performance.now();
    this.onSnapshot(this.snapshot);
  }
  startComparison(iterations: number, repeat = false) {
    this.clearInput();
    this.simulation.send({ type: "start", iterations, repeat });
    this.lastPhysics = performance.now();
    this.onComparison(this.comparison);
    this.resize(this.canvas);
    this.onSnapshot(this.snapshot);
  }
  reaim() {
    this.simulation.send({ type: "aim" });
    this.lastPhysics = performance.now();
    this.onComparison(this.comparison);
    this.resize(this.canvas);
    this.onSnapshot(this.snapshot);
  }
  setTopView(top: boolean) {
    this.topView = top;
    this.camera.fov = top ? 37 : this.angledFov;
    this.camera.updateProjectionMatrix();
    this.controls.target.set(0, 0, !top ? 0.20 : 0.13);
    this.camera.position.set(
      ...((top ? [0, -0.03, 1.15] : this.normalView) as [
        number,
        number,
        number,
      ]),
    );
    this.controls.update();
    [...this.overhead, this.trolley, this.cable].forEach(
      (mesh) => (mesh.visible = !top),
    );
    for (const id of this.simulation.model.clawParts) {
      const material = this.geoms.get(id)!
        .material as THREE.MeshStandardMaterial;
      material.transparent = top;
      material.opacity = top ? 0.22 : 1;
      material.depthWrite = !top;
    }
  }
  move(axis: MoveAxis, distance: number) { this.simulation.send({ type: "move", axis, distance }); }
  private fail(error: unknown) {
    if (this.failed || this.disposed) return;
    this.failed = true;
    cancelAnimationFrame(this.frame);
    this.clearInput();
    this.simulation.dispose();
    this.onError(error);
  }
  private animate = () => {
    if (this.disposed || !this.active || this.failed) return;
    try {
      const now = performance.now();
      const v = { x: 0, y: 0 };
      for (const value of this.input.values()) v[value.axis] += value.direction;
      if (!this.visible.has(this.page)) this.lastPhysics = now;
      else if (this.simulation.advance((now - this.lastPhysics) / 1000, this.speed,
        Math.max(-1, Math.min(1, v.x)), Math.max(-1, Math.min(1, v.y)))) this.lastPhysics = now;
      const interval = this.mobile ? 1000 / 30 : 1000 / 60;
      if (now - this.lastTime >= interval) {
        this.lastTime = now - (now - this.lastTime) % interval;
        this.render();
      }
      this.frame = requestAnimationFrame(this.animate);
    } catch (e) {
      this.fail(e);
    }
  };
  private draw(pose: ClawFrame) {
    const model = this.simulation.model;
    const r = new THREE.Matrix4(), positions = pose.geomPosition, matrices = pose.geomMatrix;
    for (const [i, mesh] of this.geoms) {
      mesh.position.set(
        positions[i * 3]!,
        positions[i * 3 + 1]!,
        positions[i * 3 + 2]!,
      );
      const k = i * 9;
      r.set(
        matrices[k]!,
        matrices[k + 1]!,
        matrices[k + 2]!,
        0,
        matrices[k + 3]!,
        matrices[k + 4]!,
        matrices[k + 5]!,
        0,
        matrices[k + 6]!,
        matrices[k + 7]!,
        matrices[k + 8]!,
        0,
        0,
        0,
        0,
        1,
      );
      mesh.quaternion.setFromRotationMatrix(r);
    }
    this.toys.forEach((toy, i) => {
      const body = model.toyBodies[i]!;
      const p = body * 3,
        q = body * 4;
      const position = pose.bodyPosition, rotation = pose.bodyQuaternion;
      toy.position.set(position[p]!, position[p + 1]!, position[p + 2]!);
      toy.quaternion.set(
        rotation[q + 1]!,
        rotation[q + 2]!,
        rotation[q + 3]!,
        rotation[q]!,
      );
    });
    const hub = this.geoms.get(model.hub)!.position;
    this.charm.position.copy(hub);
    this.charm.visible = !this.topView;
    this.trolley.position.set(hub.x, hub.y, 0.51);
    this.overhead[0]!.position.y = hub.y;
    const length = Math.max(0.01, 0.495 - hub.z);
    this.cable.scale.y = length;
    this.cable.position.set(hub.x, hub.y, hub.z + length / 2);
    this.aim.position.x = hub.x;
    this.aim.position.y = hub.y;
    if (!this.comparison.started) {
      const overChute = Math.abs(hub.x - BIN.x) < BIN.half && Math.abs(hub.y - BIN.y) < BIN.half;
      this.aim.position.z = Math.max(this.simulation.state.surfaceHeight, overChute ? CHUTE_LIP : 0) + .004;
    }
    this.aim.visible = !this.comparison.started;
    this.renderer.render(this.scene, this.camera);
  }
  private render() {
    if (!this.visible.has(this.canvas)) return;
    const size = this.renderer.getSize(new THREE.Vector2());
    const count = this.comparison.started ? 3 : 1;
    const columns = count === 3 && size.x >= 700 ? 3 : 1;
    const rows = count / columns;
    this.renderer.setScissorTest(true);
    for (let i = 0; i < count; i++) {
      const x = ((i % columns) * size.x) / columns;
      const y = ((rows - 1 - Math.floor(i / columns)) * size.y) / rows;
      this.renderer.setViewport(x, y, size.x / columns, size.y / rows);
      this.renderer.setScissor(x, y, size.x / columns, size.y / rows);
      if (count === 3 && !this.visible.has(this.viewLabels[i]!)) continue;
      this.draw(this.comparison.started
        ? this.comparison.current!.worlds[i]! : this.simulation.state.reference);
    }
    this.renderer.setScissorTest(false);
  }
  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    cancelAnimationFrame(this.frame);
    this.observer.disconnect();
    this.visibility.disconnect();
    this.controls.dispose();
    disposeMeshes(this.scene);
    this.renderer.dispose();
    this.simulation.dispose();
  }
}
