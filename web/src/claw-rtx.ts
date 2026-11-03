import * as THREE from "three";
import { GLTFExporter } from "three/addons/exporters/GLTFExporter.js";

/** One in-flight snapshot: slow rendering never queues old controls or advances physics. */
export class ClawRtx {
  private socket: WebSocket;
  private meshes: THREE.Mesh[] = [];
  private pending = false;
  private ready = false;
  private closed = false;
  private sequence = 0;
  private epoch = 0;
  private requestedEpoch = 0;
  private lastFrame = 0;
  private lastRequest = 0;
  private openedAt = performance.now();
  private timer: ReturnType<typeof setInterval>;
  private image = document.createElement("canvas");
  private status = document.createElement("span");
  private context: CanvasRenderingContext2D;

  private canvas: HTMLCanvasElement;
  private scene: THREE.Scene;
  private en: boolean;
  constructor(canvas: HTMLCanvasElement, scene: THREE.Scene, en: boolean) {
    this.canvas = canvas;
    this.scene = scene;
    this.en = en;
    this.image.className = "rtx-frame";
    this.image.hidden = true;
    this.image.setAttribute("aria-hidden", "true");
    canvas.insertAdjacentElement("afterend", this.image);
    this.status.className = "rtx-status";
    this.status.setAttribute("role", "status");
    canvas.parentElement!.append(this.status);
    this.context = this.image.getContext("2d")!;
    this.setStatus("正在连接本机 OVRTX…", "Connecting to local OVRTX…");
    this.socket = new WebSocket("ws://127.0.0.1:8879");
    this.socket.binaryType = "arraybuffer";
    this.socket.onopen = () => { void this.initialize().catch(() => this.fail()); };
    this.socket.onerror = () => this.fail();
    this.socket.onclose = () => this.fail();
    this.socket.onmessage = (event) => { void this.receive(event.data).catch(() => this.fail()); };
    this.timer = setInterval(() => {
      if ((!this.ready && !this.lastFrame && performance.now() - this.openedAt > 90000) ||
          (this.pending && performance.now() - this.lastRequest > 15000)) {
        this.fail();
        this.socket.close();
      }
      if (this.lastFrame && performance.now() - this.lastFrame > 2500) {
        this.image.hidden = true;
        this.setStatus("RTX 画面延迟 · 当前显示 WebGL", "RTX delayed · showing WebGL");
      }
    }, 1000);
  }

  private setStatus(zh: string, en: string) { this.status.textContent = this.en ? en : zh; }
  private async initialize() {
    this.scene.updateMatrixWorld(true);
    const flat = new THREE.Scene();
    this.scene.traverse((node) => {
      if (!(node instanceof THREE.Mesh) || node.material instanceof THREE.MeshBasicMaterial) return;
      // Very faint cabinet panels are an orbit aid, not physical glass.
      if (!Array.isArray(node.material) && node.material.opacity < 0.1) return;
      this.meshes.push(node);
      const copy = new THREE.Mesh(node.geometry, node.material);
      copy.name = `part_${this.meshes.length - 1}`;
      copy.matrixAutoUpdate = false;
      copy.matrix.copy(node.matrixWorld);
      flat.add(copy);
    });
    const glb = await new GLTFExporter().parseAsync(flat, { binary: true, onlyVisible: false });
    if (!this.closed && glb instanceof ArrayBuffer) {
      this.socket.send(glb);
      this.setStatus("OVRTX 正在加载场景和着色器…", "OVRTX is loading the scene and shaders…");
    }
  }
  capture() {
    this.scene.updateMatrixWorld(true);
    return this.meshes.map((mesh) => {
      const m = mesh.matrixWorld.clone();
      const material = mesh.material as THREE.Material;
      let visible = true;
      for (let node: THREE.Object3D | null = mesh; node; node = node.parent) visible &&= node.visible;
      if (!visible || (material.transparent && material.opacity < 0.3))
        m.scale(new THREE.Vector3(0, 0, 0));
      return m.toArray();
    });
  }
  get canRequest() { return this.ready && !this.pending && !this.closed; }
  request(worlds: number[][][], camera: THREE.PerspectiveCamera, time: number, columns: number) {
    if (!this.canRequest) return;
    const rows = worlds.length / columns;
    this.image.style.height = `${this.canvas.clientHeight}px`;
    const width = Math.max(160, Math.min(640, Math.round(this.canvas.clientWidth / columns)));
    const height = Math.max(160, Math.min(640, Math.round(width / camera.aspect)));
    this.requestedEpoch = this.epoch;
    this.pending = true;
    this.lastRequest = performance.now();
    camera.updateMatrixWorld();
    this.socket.send(JSON.stringify({ sequence: ++this.sequence, time, worlds, columns, width, height,
      camera: camera.matrixWorld.toArray(), fov: camera.fov, rows }));
  }
  private async receive(data: string | ArrayBuffer) {
    if (typeof data === "string") {
      const message = JSON.parse(data);
      if (message.type === "ready") this.ready = true;
      else throw new Error(message.error ?? "OVRTX error");
      return;
    }
    const view = new DataView(data);
    const size = view.getUint32(0, true);
    const info = JSON.parse(new TextDecoder().decode(new Uint8Array(data, 4, size)));
    const bitmap = await createImageBitmap(new Blob([data.slice(4 + size)], { type: "image/jpeg" }));
    try {
      if (this.closed || info.sequence !== this.sequence || this.epoch !== this.requestedEpoch) return;
      this.image.width = bitmap.width;
      this.image.height = bitmap.height;
      this.context.drawImage(bitmap, 0, 0);
      this.lastFrame = performance.now();
      this.image.hidden = false;
      this.setStatus(`OVRTX · ${info.time.toFixed(2)} s · ${info.render_ms.toFixed(0)} ms/帧`,
        `OVRTX · ${info.time.toFixed(2)} s · ${info.render_ms.toFixed(0)} ms/frame`);
    } finally { bitmap.close(); this.pending = false; }
  }
  invalidate() { this.epoch++; this.image.hidden = true; }
  private fail() {
    this.image.hidden = true;
    this.ready = false;
    this.lastFrame = 0;
    this.pending = false;
    this.setStatus("OVRTX 未连接 · 当前显示 WebGL", "OVRTX disconnected · showing WebGL");
  }
  dispose() {
    this.closed = true;
    clearInterval(this.timer);
    this.socket.onclose = null;
    this.socket.close();
    this.image.remove(); this.status.remove();
  }
}
