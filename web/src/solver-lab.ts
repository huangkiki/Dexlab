import loadMujoco, { type MainModule } from "@mujoco/mujoco";
import mujocoWasmUrl from "@mujoco/mujoco/mujoco.wasm?url";
import * as THREE from "three";
import { WebGPURenderer } from "three/webgpu";

export type CaseId = "static" | "sliding" | "frictionless";

interface SolverSpec {
  id: string;
  label: string;
  solver: "Newton" | "CG" | "PGS";
  cone: "elliptic" | "pyramidal";
  color: number;
}

interface CaseSpec {
  id: CaseId;
  label: string;
  angleDeg: number;
  friction: number;
  description: string;
}

export interface SolverMetric {
  id: string;
  label: string;
  solver: string;
  cone: string;
  displacementMm: number;
  speedMmS: number;
  contacts: number;
  iterations: number;
  simulationTime: number;
  status: string;
}

export interface SolverLabSnapshot {
  webBackend: string;
  physicsBackend: string;
  mujocoVersion: string;
  simulationSpeed: number;
  actualSpeed: number;
  renderFps: number;
  metrics: SolverMetric[];
}

const SOLVERS: SolverSpec[] = [
  {
    id: "newton-elliptic",
    label: "Newton",
    solver: "Newton",
    cone: "elliptic",
    color: 0x74a7ff,
  },
  {
    id: "cg-elliptic",
    label: "CG",
    solver: "CG",
    cone: "elliptic",
    color: 0x65d1aa,
  },
  {
    id: "pgs-pyramidal",
    label: "PGS",
    solver: "PGS",
    cone: "pyramidal",
    color: 0xffb36a,
  },
];

const CASES: Record<CaseId, CaseSpec> = {
  static: {
    id: "static",
    label: "15° 静止",
    angleDeg: 15,
    friction: 0.5,
    description: "静摩擦足够，关注微小漂移和保持。",
  },
  sliding: {
    id: "sliding",
    label: "35° 滑动",
    angleDeg: 35,
    friction: 0.5,
    description: "重力超过摩擦上限，关注滑动轨迹和支撑。",
  },
  frictionless: {
    id: "frictionless",
    label: "15° 无摩擦",
    angleDeg: 15,
    friction: 0,
    description: "名义无摩擦，检查原生下限和横向漂移。",
  },
};

const SIDE_M = 0.04;
const HALF = SIDE_M / 2;
const MASS_KG = 0.064;
const GRAVITY = 9.81;
const TIMESTEP = 0.002;
const DURATION_S = 2;
const IMPEDANCE = 0.9;

function axis(angleDeg: number) {
  const angle = THREE.MathUtils.degToRad(angleDeg);
  return {
    tangent: [Math.cos(angle), 0, -Math.sin(angle)] as const,
    normal: [Math.sin(angle), 0, Math.cos(angle)] as const,
    quaternion: [Math.cos(angle / 2), 0, Math.sin(angle / 2), 0] as const,
  };
}

function modelXml(caseSpec: CaseSpec, solver: SolverSpec): string {
  const { normal, quaternion } = axis(caseSpec.angleDeg);
  const inertia = (MASS_KG * SIDE_M * SIDE_M) / 6;
  return `<mujoco model="dexlab-browser-incline">
  <option timestep="${TIMESTEP}" gravity="0 0 -${GRAVITY}" integrator="Euler"
    solver="${solver.solver}" cone="${solver.cone}" impratio="1"
    iterations="100" tolerance="1e-10"/>
  <default>
    <geom condim="3" friction="${caseSpec.friction} 0 0"
      solref="0.02 1" solimp="${IMPEDANCE} ${IMPEDANCE} 0.001 0.5 2"/>
  </default>
  <worldbody>
    <geom name="plane" type="plane" size="2 2 0.1"
      quat="${quaternion.join(" ")}"/>
    <body name="box" pos="${normal.map((value) => value * HALF).join(" ")}"
      quat="${quaternion.join(" ")}">
      <freejoint/>
      <inertial pos="0 0 0" mass="${MASS_KG}"
        diaginertia="${inertia} ${inertia} ${inertia}"/>
      <geom name="box" type="box" size="${HALF} ${HALF} ${HALF}"/>
    </body>
  </worldbody>
</mujoco>`;
}

class Simulation {
  model: InstanceType<MainModule["MjModel"]>;
  data: InstanceType<MainModule["MjData"]>;
  boxBody: number;
  planeGeom: number;
  boxGeom: number;
  initialPosition: THREE.Vector3;
  previousPosition: THREE.Vector3;
  displacementMm = 0;
  speedMmS = 0;
  contacts = 0;
  iterations = 0;
  status = "ready";

  constructor(
    private readonly module: MainModule,
    private readonly caseSpec: CaseSpec,
    private readonly solver: SolverSpec,
  ) {
    this.model = module.MjModel.from_xml_string(modelXml(caseSpec, solver));
    this.data = new module.MjData(this.model);
    this.boxBody = module.mj_name2id(
      this.model,
      module.mjtObj.mjOBJ_BODY.value,
      "box",
    );
    this.planeGeom = module.mj_name2id(
      this.model,
      module.mjtObj.mjOBJ_GEOM.value,
      "plane",
    );
    this.boxGeom = module.mj_name2id(
      this.model,
      module.mjtObj.mjOBJ_GEOM.value,
      "box",
    );
    if (this.boxBody < 0 || this.planeGeom < 0 || this.boxGeom < 0) {
      throw new Error("The compiled scene is missing box/plane identifiers");
    }
    module.mj_forward(this.model, this.data);
    this.contacts = this.data.ncon;
    this.iterations = Math.max(0, ...Array.from(this.data.solver_niter as ArrayLike<number>));
    this.initialPosition = this.readBodyPosition();
    this.previousPosition = this.initialPosition.clone();
  }

  reset() {
    this.module.mj_resetData(this.model, this.data);
    this.module.mj_forward(this.model, this.data);
    this.initialPosition = this.readBodyPosition();
    this.previousPosition = this.initialPosition.clone();
    this.displacementMm = 0;
    this.speedMmS = 0;
    this.contacts = this.data.ncon;
    this.iterations = Math.max(0, ...Array.from(this.data.solver_niter as ArrayLike<number>));
    this.status = "ready";
  }

  step() {
    this.module.mj_step(this.model, this.data);
    const position = this.readBodyPosition();
    const tangent = new THREE.Vector3(...axis(this.caseSpec.angleDeg).tangent);
    this.displacementMm = Math.abs(position.clone().sub(this.initialPosition).dot(tangent)) * 1000;
    this.speedMmS =
      (position.distanceTo(this.previousPosition) / TIMESTEP) * 1000;
    this.previousPosition.copy(position);
    this.contacts = this.data.ncon;
    this.iterations = Math.max(0, ...Array.from(this.data.solver_niter as ArrayLike<number>));
    this.status = this.data.time >= DURATION_S ? "complete" : "running";
  }

  readBodyPosition() {
    const x = Number(this.data.xpos[this.boxBody * 3]);
    const y = Number(this.data.xpos[this.boxBody * 3 + 1]);
    const z = Number(this.data.xpos[this.boxBody * 3 + 2]);
    return new THREE.Vector3(x, y, z);
  }

  readBodyQuaternion(target: THREE.Quaternion) {
    const q = this.data.xquat;
    target.set(
      Number(q[this.boxBody * 4 + 1]),
      Number(q[this.boxBody * 4 + 2]),
      Number(q[this.boxBody * 4 + 3]),
      Number(q[this.boxBody * 4]),
    );
  }

  readPlanePosition(target: THREE.Vector3) {
    target.set(
      Number(this.data.geom_xpos[this.planeGeom * 3]),
      Number(this.data.geom_xpos[this.planeGeom * 3 + 1]),
      Number(this.data.geom_xpos[this.planeGeom * 3 + 2]),
    );
  }

  dispose() {
    this.data.delete();
    this.model.delete();
  }
}

interface RenderPair {
  group: THREE.Group;
  ramp: THREE.Mesh;
  box: THREE.Mesh;
}

export class SolverLab {
  private running = false;
  private simulationSpeed = 1;
  private actualSpeed = 0;
  private accumulator = 0;
  private lastFrameTime = performance.now();
  private runStartedAt: number | null = null;
  private renderFps = 60;
  private alpha = 0;
  private sessions: Simulation[] = [];
  private renderPairs: RenderPair[] = [];
  private renderer!: WebGPURenderer | THREE.WebGLRenderer;
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(40, 1, 0.001, 20);
  private resizeObserver?: ResizeObserver;
  private disposed = false;
  private backend = "WebGPU";
  private caseId: CaseId = "static";

  private constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly module: MainModule,
    private readonly onSnapshot: (snapshot: SolverLabSnapshot) => void,
  ) {}

  static async create(
    canvas: HTMLCanvasElement,
    onSnapshot: (snapshot: SolverLabSnapshot) => void,
  ): Promise<SolverLab> {
    const module = await loadMujoco({
      locateFile: (path: string) =>
        path.endsWith(".wasm") ? mujocoWasmUrl : path,
    });
    const lab = new SolverLab(canvas, module, onSnapshot);
    await lab.initializeRenderer();
    lab.initializeScene();
    lab.rebuild();
    lab.observeResize();
    lab.animate();
    return lab;
  }

  setCase(caseId: CaseId) {
    if (caseId === this.caseId) return;
    this.caseId = caseId;
    this.rebuild();
    this.running = false;
    this.emit();
  }

  setRunning(running: boolean) {
    this.running = running;
    if (running) {
      this.runStartedAt ??= performance.now();
    }
    this.emit();
  }

  toggleRunning() {
    this.setRunning(!this.running);
  }

  reset() {
    this.accumulator = 0;
    this.alpha = 0;
    this.actualSpeed = 0;
    this.runStartedAt = null;
    for (const session of this.sessions) session.reset();
    this.syncMeshes();
    this.running = false;
    this.emit();
  }

  setSimulationSpeed(speed: number) {
    this.simulationSpeed = speed;
    this.emit();
  }

  dispose() {
    this.disposed = true;
    this.resizeObserver?.disconnect();
    for (const session of this.sessions) session.dispose();
    this.sessions = [];
    if ("setAnimationLoop" in this.renderer) {
      this.renderer.setAnimationLoop(null);
    }
    this.renderer.dispose();
  }

  private async initializeRenderer() {
    if (navigator.gpu) {
      try {
        const renderer = new WebGPURenderer({
          canvas: this.canvas,
          antialias: true,
          alpha: false,
        });
        await renderer.init();
        this.renderer = renderer;
        this.backend = "WebGPU";
        return;
      } catch {
        // Fall through to the broadly supported renderer.
      }
    }
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: false,
    });
    this.backend = "WebGL";
  }

  private initializeScene() {
    this.scene.background = new THREE.Color(0x0e1116);
    this.scene.add(new THREE.HemisphereLight(0xe6f0ff, 0x262b34, 1.8));
    const key = new THREE.DirectionalLight(0xffffff, 2.4);
    key.position.set(0.6, -0.8, 1.4);
    this.scene.add(key);

    this.camera.position.set(0.25, -0.42, 0.2);
    this.camera.lookAt(0, 0, 0.06);

    for (const solver of SOLVERS) {
      const group = new THREE.Group();
      const ramp = new THREE.Mesh(
        new THREE.BoxGeometry(1.1, 1.1, 0.02),
        new THREE.MeshStandardMaterial({
          color: 0x46515e,
          roughness: 0.72,
          metalness: 0.05,
        }),
      );
      const box = new THREE.Mesh(
        new THREE.BoxGeometry(SIDE_M, SIDE_M, SIDE_M),
        new THREE.MeshStandardMaterial({
          color: solver.color,
          roughness: 0.34,
          metalness: 0.08,
        }),
      );
      const edges = new THREE.LineSegments(
        new THREE.EdgesGeometry(ramp.geometry),
        new THREE.LineBasicMaterial({
          color: 0xa6b2c1,
          transparent: true,
          opacity: 0.9,
        }),
      );
      const grid = new THREE.GridHelper(1.1, 22, 0x8191a5, 0x33404d);
      grid.rotation.x = Math.PI / 2;
      grid.position.z = 0.011;
      grid.material.transparent = true;
      grid.material.opacity = 0.42;
      ramp.add(edges, grid);
      group.add(ramp, box);
      this.scene.add(group);
      this.renderPairs.push({ group, ramp, box });
    }
  }

  private rebuild() {
    for (const session of this.sessions) session.dispose();
    this.sessions = SOLVERS.map(
      (solver) => new Simulation(this.module, CASES[this.caseId], solver),
    );
    this.accumulator = 0;
    this.actualSpeed = 0;
    this.runStartedAt = null;
    this.syncMeshes();
  }

  private observeResize() {
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(this.canvas);
    this.resize();
  }

  private resize() {
    const rect = this.canvas.getBoundingClientRect();
    const width = Math.max(1, Math.floor(rect.width));
    const height = Math.max(1, Math.floor(rect.height));
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(width, height, false);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
  }

  private animate = () => {
    if (this.disposed) return;
    const now = performance.now();
    const frameSeconds = Math.min((now - this.lastFrameTime) / 1000, 0.1);
    this.lastFrameTime = now;
    this.renderFps = 0.9 * this.renderFps + 0.1 / Math.max(frameSeconds, 1e-6);

    if (this.running) {
      this.accumulator += frameSeconds * this.simulationSpeed;
      const maxSteps = 180;
      let steps = 0;
      while (this.accumulator >= TIMESTEP && steps < maxSteps) {
        let active = false;
        for (const session of this.sessions) {
          if (session.data.time < DURATION_S - TIMESTEP / 2) {
            session.step();
            active = true;
          }
        }
        this.accumulator -= TIMESTEP;
        steps += 1;
        if (!active) {
          this.running = false;
          break;
        }
      }
      const simulationTime = this.sessions[0]?.data.time ?? 0;
      if (this.runStartedAt !== null) {
        this.actualSpeed =
          simulationTime / Math.max((now - this.runStartedAt) / 1000, 1e-6);
      }
    }

    this.alpha = this.sessions[0]
      ? this.sessions[0].data.time / TIMESTEP
      : 0;
    this.syncMeshes();
    this.renderViewports();
    this.emitThrottled();
    requestAnimationFrame(this.animate);
  };

  private syncMeshes() {
    const rampPosition = new THREE.Vector3();
    const quaternion = new THREE.Quaternion();
    const matrix = new THREE.Matrix4();
    this.sessions.forEach((session, index) => {
      const pair = this.renderPairs[index];
      if (!pair) return;
      session.readPlanePosition(rampPosition);
      pair.ramp.position.copy(rampPosition);
      matrix.fromArray(Array.from(session.data.geom_xmat.slice(session.planeGeom * 9, session.planeGeom * 9 + 9)) as number[]);
      pair.ramp.quaternion.setFromRotationMatrix(matrix);

      const position = session.readBodyPosition();
      pair.box.position.copy(position);
      session.readBodyQuaternion(quaternion);
      pair.box.quaternion.copy(quaternion);
    });
  }

  private renderViewports() {
    const size = new THREE.Vector2();
    this.renderer.getSize(size);
    const narrow = size.x < 640;
    const columns = narrow ? 1 : 3;
    const rows = narrow ? 3 : 1;
    const cellWidth = Math.floor(size.x / columns);
    const cellHeight = Math.floor(size.y / rows);
    this.renderer.setScissorTest(true);
    this.camera.aspect = cellWidth / cellHeight;
    this.camera.updateProjectionMatrix();

    this.renderPairs.forEach((pair, index) => {
      this.renderPairs.forEach((candidate, candidateIndex) => {
        candidate.group.visible = candidateIndex === index;
      });
      const column = index % columns;
      const row = Math.floor(index / columns);
      const x = column * cellWidth;
      const y = size.y - (row + 1) * cellHeight;
      this.renderer.setViewport(x, y, cellWidth, cellHeight);
      this.renderer.setScissor(x, y, cellWidth, cellHeight);
      this.renderer.render(this.scene, this.camera);
    });
    this.renderer.setScissorTest(false);
    this.renderer.setViewport(0, 0, size.x, size.y);
  }

  private lastEmit = 0;

  private emitThrottled() {
    const now = performance.now();
    if (now - this.lastEmit < 120) return;
    this.lastEmit = now;
    this.emit();
  }

  private emit() {
    this.onSnapshot({
      webBackend: this.backend,
      physicsBackend: "MuJoCo WASM · CPU",
      mujocoVersion: this.module.mj_versionString(),
      simulationSpeed: this.simulationSpeed,
      actualSpeed: this.actualSpeed,
      renderFps: this.renderFps,
      metrics: this.sessions.map((session, index) => ({
        id: SOLVERS[index]!.id,
        label: SOLVERS[index]!.label,
        solver: SOLVERS[index]!.solver,
        cone: SOLVERS[index]!.cone,
        displacementMm: session.displacementMm,
        speedMmS: session.speedMmS,
        contacts: session.contacts,
        iterations: session.iterations,
        simulationTime: session.data.time,
        status: session.status,
      })),
    });
  }
}

export const solverCases = CASES;
