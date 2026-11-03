import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { loadPhysics } from "./mujoco-loader";
import { loadToyModels, disposeMeshes } from "./claw-meshes";
import { toyModelUrls } from "./claw-model-urls";
import { STEP, BIN, type ClawSnapshot, type MoveAxis } from "./claw-task";

import { ClawComparison, type ClawFrame } from "./claw-comparison";
import type { ClawTask } from "./claw-task";

export class ClawLab {
  get task() {
    return this.comparison.reference;
  }
  speed = 1;
  readonly input = new Map<string, { axis: MoveAxis; direction: number }>();
  private renderer: THREE.WebGLRenderer;
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(37, 1, 0.01, 5);
  private controls: OrbitControls;
  private observer: ResizeObserver;
  private geoms = new Map<number, THREE.Mesh>();
  private overhead: THREE.Mesh[] = [];
  private cable: THREE.Mesh;
  private trolley: THREE.Mesh;
  private aim: THREE.Mesh;
  private frame = 0;
  private active = true;
  private failed = false;
  private disposed = false;
  private lastTime = performance.now();
  private accumulator = 0;
  private lastEmit = 0;
  private layout = 0;
  private compactView = false;
  private topView = false;
  private angledFov = 37;
  private normalView: [number, number, number] = [0.3, -0.83, 0.66];

  private constructor(
    private canvas: HTMLCanvasElement,
    readonly comparison: ClawComparison,
    private readonly toys: THREE.Group[],
    private onSnapshot: (s: ClawSnapshot) => void,
    private onError: (e: unknown) => void,
    private onComparison: (comparison: ClawComparison) => void,
  ) {
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.setClearColor(0x17212b);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;
    this.camera.up.set(0, 0, 1);
    this.camera.position.set(...this.normalView);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.target.set(0, 0, 0.13);
    this.controls.enablePan = false;
    this.controls.minDistance = 0.8;
    this.controls.maxDistance = 1.65;
    this.controls.minPolarAngle = 0.08;
    this.controls.maxPolarAngle = Math.PI / 2.1;
    this.controls.update();
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    const fill = new THREE.HemisphereLight(0xfff8e9, 0x68747b, 2.5);
    fill.position.set(0, 0, 1);
    this.scene.add(fill, new THREE.AmbientLight(0xfff8ef, 0.7));
    const light = new THREE.DirectionalLight(0xfff5e7, 2.5);
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
    // The crossbeam rides on the two side rails; all trim is decorative.
    for (const x of [-0.3, 0.3])
      for (const y of [-0.225, 0.225]) {
        const post = this.box([0.01, 0.01, 0.4], [x, y, 0.17], 0x8aa4b1);
        if (y < 0) {
          const material = post.material as THREE.MeshStandardMaterial;
          material.transparent = true;
          material.opacity = 0.22;
          material.depthWrite = false;
          post.castShadow = false;
        }
      }
    this.box([0.62, 0.022, 0.026], [0, 0.225, 0.375], 0x93b6b9);
    for (const x of [-0.3, 0.3])
      this.box([0.024, 0.47, 0.028], [x, 0, 0.375], 0x93b6b9);
    this.overhead.push(this.box([0.6, 0.018, 0.018], [0, 0, 0.365], 0xd7e3e5));
    this.trolley = this.box([0.065, 0.065, 0.028], [0, 0, 0.35], 0xf4cc79);
    this.cable = new THREE.Mesh(
      new THREE.CylinderGeometry(0.003, 0.003, 1, 12),
      new THREE.MeshStandardMaterial({
        color: 0x9eb0b8,
        metalness: 0.7,
        roughness: 0.35,
      }),
    );
    this.cable.rotation.x = Math.PI / 2;
    this.scene.add(this.cable);
    const ring = new THREE.RingGeometry(0.035, 0.037, 48);
    this.aim = new THREE.Mesh(
      ring,
      new THREE.MeshBasicMaterial({
        color: 0x20745b,
        side: THREE.DoubleSide,
        depthTest: false,
      }),
    );
    this.aim.renderOrder = 10;
    this.aim.position.z = 0.002;
    this.scene.add(this.aim);
    const rim = new THREE.LineLoop(
      new THREE.BufferGeometry().setFromPoints(
        [
          [-1, -1],
          [1, -1],
          [1, 1],
          [-1, 1],
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
    this.observer = new ResizeObserver(() => this.resize(canvas));
    this.observer.observe(canvas);
    this.resize(canvas);
    this.animate();
  }
  static async create(
    canvas: HTMLCanvasElement,
    onSnapshot: (s: ClawSnapshot) => void,
    onError: (e: unknown) => void,
    onComparison: (comparison: ClawComparison) => void,
  ) {
    const toys = await loadToyModels(toyModelUrls);
    let comparison: ClawComparison | undefined;
    try {
      comparison = new ClawComparison(await loadPhysics());
      return new ClawLab(
        canvas,
        comparison,
        toys,
        onSnapshot,
        onError,
        onComparison,
      );
    } catch (error) {
      for (const toy of toys) disposeMeshes(toy);
      comparison?.dispose();
      throw error;
    }
  }
  private box(
    size: [number, number, number],
    p: [number, number, number],
    color: number,
  ) {
    const mesh = new THREE.Mesh(
      new THREE.BoxGeometry(...size),
      new THREE.MeshStandardMaterial({
        color,
        roughness: 0.6,
        metalness: 0.15,
      }),
    );
    mesh.position.set(...p);
    // Thin cabinet beams should not lay hard stripes over the small prizes.
    mesh.castShadow = false;
    mesh.receiveShadow = true;
    this.scene.add(mesh);
    return mesh;
  }
  private buildNativeGeoms() {
    const m = this.task.model;
    for (let i = 0; i < m.ngeom; i++) {
      if (this.task.toyBodies.includes(m.geom_bodyid[i])) continue;
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
      const claw = this.task.clawParts.includes(i);
      const material = new THREE.MeshPhysicalMaterial({
        color: claw
          ? 0xd9e3e6
          : wall
            ? 0xb3d7e7
            : i < 3
              ? 0xe1e3dd
              : i >= 4 && i <= 7
                ? 0xc99c51
                : 0x718696,
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
    // Fit the full gantry and deep prize bin, even below a square aspect ratio.
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
      this.normalView = compact ? [0, -1, 0.66] : [0.3, -0.83, 0.66];
      this.setTopView(this.topView);
    }
    this.camera.fov = this.topView ? 37 : this.angledFov;
    this.camera.updateProjectionMatrix();
  }
  clearInput() {
    this.input.clear();
  }
  setActive(active: boolean) {
    if (this.disposed || this.failed) return;
    this.clearInput();
    this.accumulator = 0;
    if (active === this.active) return;
    this.active = active;
    if (active) {
      this.lastTime = performance.now();
      this.animate();
    } else cancelAnimationFrame(this.frame);
  }
  reset() {
    this.clearInput();
    this.comparison.reset(++this.layout);
    this.onComparison(this.comparison);
    this.accumulator = 0;
    this.onSnapshot(this.task.snapshot());
  }
  startComparison(iterations: number, repeat = false) {
    this.clearInput();
    this.comparison.start(iterations, repeat);
    this.accumulator = 0;
    this.onComparison(this.comparison);
    this.resize(this.canvas);
    this.onSnapshot(this.task.snapshot());
  }
  reaim() {
    this.comparison.aim();
    this.accumulator = 0;
    this.onComparison(this.comparison);
    this.resize(this.canvas);
    this.onSnapshot(this.task.snapshot());
  }
  setTopView(top: boolean) {
    this.topView = top;
    this.camera.fov = top ? 37 : this.angledFov;
    this.camera.updateProjectionMatrix();
    this.controls.target.set(0, 0, this.compactView && !top ? 0.1 : 0.13);
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
    for (const id of this.task.clawParts) {
      const material = this.geoms.get(id)!
        .material as THREE.MeshStandardMaterial;
      material.transparent = top;
      material.opacity = top ? 0.22 : 1;
      material.depthWrite = !top;
    }
  }
  private animate = () => {
    if (this.disposed || !this.active || this.failed) return;
    try {
      const now = performance.now();
      this.accumulator +=
        Math.min((now - this.lastTime) / 1000, 0.05) *
        (this.comparison.started ? this.speed : 1);
      this.lastTime = now;
      while (this.accumulator >= STEP) {
        if (this.comparison.started) {
          this.comparison.step();
          this.accumulator -= STEP;
          continue;
        }
        const v = { x: 0, y: 0 };
        for (const value of this.input.values())
          v[value.axis] += value.direction;
        for (const axis of ["x", "y"] as const)
          this.task.move(
            axis,
            Math.max(-1, Math.min(1, v[axis])) * 0.11 * STEP,
          );
        this.task.step();
        this.accumulator -= STEP;
      }
      this.render();
      if (now - this.lastEmit > 100) {
        this.lastEmit = now;
        this.onSnapshot(this.task.snapshot());
        this.onComparison(this.comparison);
      }
      this.frame = requestAnimationFrame(this.animate);
    } catch (e) {
      this.failed = true;
      this.clearInput();
      this.onError(e);
    }
  };
  private draw(task: ClawTask, pose?: ClawFrame) {
    const r = new THREE.Matrix4(),
      positions = pose?.geomPosition ?? task.data.geom_xpos,
      matrices = pose?.geomMatrix ?? task.data.geom_xmat;
    for (const [i, mesh] of this.geoms) {
      mesh.position.set(
        positions[i * 3],
        positions[i * 3 + 1],
        positions[i * 3 + 2],
      );
      const k = i * 9;
      r.set(
        matrices[k],
        matrices[k + 1],
        matrices[k + 2],
        0,
        matrices[k + 3],
        matrices[k + 4],
        matrices[k + 5],
        0,
        matrices[k + 6],
        matrices[k + 7],
        matrices[k + 8],
        0,
        0,
        0,
        0,
        1,
      );
      mesh.quaternion.setFromRotationMatrix(r);
    }
    this.toys.forEach((toy, i) => {
      const body = task.toyBodies[i]!;
      const p = body * 3,
        q = body * 4;
      const position = pose?.bodyPosition ?? task.data.xpos,
        rotation = pose?.bodyQuaternion ?? task.data.xquat;
      toy.position.set(position[p], position[p + 1], position[p + 2]);
      toy.quaternion.set(
        rotation[q + 1],
        rotation[q + 2],
        rotation[q + 3],
        rotation[q],
      );
    });
    const hub = this.geoms.get(task.hub)!.position;
    this.trolley.position.set(hub.x, hub.y, 0.35);
    this.overhead[0]!.position.y = hub.y;
    const length = Math.max(0.01, 0.335 - hub.z);
    this.cable.scale.y = length;
    this.cable.position.set(hub.x, hub.y, hub.z + length / 2);
    this.aim.position.x = hub.x;
    this.aim.position.y = hub.y;
    this.aim.visible = !this.comparison.started;
    this.renderer.render(this.scene, this.camera);
  }
  private render() {
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
      this.draw(
        this.comparison.tasks[i]!,
        this.comparison.started
          ? this.comparison.current?.worlds[i]
          : undefined,
      );
    }
    this.renderer.setScissorTest(false);
  }
  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    cancelAnimationFrame(this.frame);
    this.observer.disconnect();
    this.controls.dispose();
    disposeMeshes(this.scene);
    this.renderer.dispose();
    this.comparison.dispose();
  }
}
