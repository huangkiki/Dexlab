import "./styles.css";
import {
  experiments,
  groupLabels,
  type Experiment,
  type ExperimentMode,
} from "./experiments";
import {
  SolverLab,
  type CaseId,
  type SolverLabSnapshot,
  solverCases,
} from "./solver-lab";

function requireElement<T extends Element>(selector: string): T {
  const element = document.querySelector<T>(selector);
  if (!element) throw new Error(`Missing ${selector}`);
  return element;
}

const app = requireElement<HTMLDivElement>("#app");
const embedded =
  new URLSearchParams(window.location.search).has("embed") ||
  window.self !== window.top;

app.innerHTML = `
  <div class="page-shell ${embedded ? "is-embedded" : ""}">
    <header class="topbar">
      <a class="brand" href="/">
        <span class="brand-mark">D</span>
        <span>DexLab</span>
      </a>
      <nav aria-label="主导航">
        <a href="#live">Live Lab</a>
        <a href="#experiments">Experiments</a>
        <a href="https://github.com/huangkiki/Dexlab">GitHub</a>
      </nav>
    </header>

    <main>
      <section class="hero">
        <p class="eyebrow">Browser-native dexterous contact lab</p>
        <h1>同一场景，同一动作，直接看见 solver 差异。</h1>
        <p class="hero-copy">
          DexLab 在浏览器本地运行 MuJoCo WASM。无需安装 Python、CUDA 或 MuJoCo，
          选择接触条件后同时观察三套求解配置。
        </p>
        <div class="hero-actions">
          <a class="primary-action" href="#live">打开 Live Lab</a>
          <a class="secondary-action" href="#experiments">浏览全部实验</a>
        </div>
      </section>

      <section id="live" class="live-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Live · local only</p>
            <h2>Contact Solver Lab</h2>
          </div>
          <p class="section-copy">
            40 mm · 64 g 方块。三套配置共享初态、重力、摩擦和时间步长。
          </p>
        </div>

        <div class="lab-shell">
          <div class="lab-toolbar">
            <div class="case-tabs" role="tablist" aria-label="接触条件">
              ${Object.values(solverCases)
                .map(
                  (item, index) => `
                    <button
                      class="case-tab ${index === 0 ? "is-active" : ""}"
                      type="button"
                      data-case="${item.id}"
                    >${item.label}</button>
                  `,
                )
                .join("")}
            </div>
            <div class="lab-actions">
              <label class="speed-control">
                <span>速度</span>
                <select id="speed">
                  <option value="0.25">0.25×</option>
                  <option value="1" selected>1×</option>
                  <option value="2">2×</option>
                </select>
              </label>
              <button id="pause" class="control-button" type="button">运行</button>
              <button id="reset" class="control-button" type="button">重置</button>
            </div>
          </div>

          <div class="case-copy" id="case-copy"></div>

          <div class="viewport-shell">
            <canvas id="solver-canvas" aria-label="三种 solver 的实时仿真画面"></canvas>
            <div class="viewport-labels" aria-hidden="true">
              <span>Newton / elliptic</span>
              <span>CG / elliptic</span>
              <span>PGS / pyramidal</span>
            </div>
          </div>

          <div class="runtime-strip" id="runtime-strip">
            <span>正在加载 MuJoCo WASM…</span>
          </div>
          <div class="metrics-grid" id="metrics-grid"></div>
        </div>
      </section>

      <section id="experiments" class="experiments-section">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Experiment catalogue</p>
            <h2>做过的实验，全部放进同一个入口。</h2>
          </div>
          <p class="section-copy">
            Live 表示浏览器本地运行；Recorded 表示当前打开的是已冻结记录和独立报告。
          </p>
        </div>
        <div class="experiment-filters" id="experiment-filters"></div>
        <div class="experiment-grid" id="experiment-grid"></div>
      </section>

      <section class="boundary-section">
        <div>
          <p class="eyebrow">Evidence boundary</p>
          <h2>网页不是原生命令行的替代品。</h2>
        </div>
        <p>
          Live 页面记录浏览器、WebGPU/WebGL 后端、MuJoCo 版本、solver 配置和实际运行速度。
          它适合交互诊断和展示，不自动继承仓库中冻结的原生实验成绩。
        </p>
      </section>
    </main>
  </div>
`;

const canvas = requireElement<HTMLCanvasElement>("#solver-canvas");
const metricsGrid = requireElement<HTMLDivElement>("#metrics-grid");
const runtimeStrip = requireElement<HTMLDivElement>("#runtime-strip");
const caseCopy = requireElement<HTMLDivElement>("#case-copy");
const pauseButton = requireElement<HTMLButtonElement>("#pause");
const resetButton = requireElement<HTMLButtonElement>("#reset");
const speedSelect = requireElement<HTMLSelectElement>("#speed");

let paused = true;
let complete = false;
let lab: SolverLab | undefined;

function renderSnapshot(snapshot: SolverLabSnapshot) {
  complete =
    snapshot.metrics.length > 0 &&
    snapshot.metrics.every((metric) => metric.status === "complete");
  if (complete) {
    paused = true;
    pauseButton.textContent = "再次运行";
  }
  runtimeStrip.innerHTML = `
    <span><strong>${snapshot.webBackend}</strong> render</span>
    <span><strong>${snapshot.physicsBackend}</strong></span>
    <span>MuJoCo ${snapshot.mujocoVersion}</span>
    <span>${snapshot.renderFps.toFixed(0)} FPS</span>
    <span>${snapshot.simulationSpeed}× target · ${snapshot.actualSpeed.toFixed(
      2,
    )}× actual</span>
  `;
  metricsGrid.innerHTML = snapshot.metrics
    .map(
      (metric) => `
        <article class="metric-card" data-solver="${metric.id}">
          <div class="metric-heading">
            <div>
              <strong>${metric.label}</strong>
              <span>${metric.cone}</span>
            </div>
            <span class="metric-status">${metric.status}</span>
          </div>
          <dl>
            <div><dt>切向位移</dt><dd>${metric.displacementMm.toFixed(2)} mm</dd></div>
            <div><dt>估算速度</dt><dd>${metric.speedMmS.toFixed(1)} mm/s</dd></div>
            <div><dt>接触数</dt><dd>${metric.contacts}</dd></div>
            <div><dt>solver iterations</dt><dd>${metric.iterations}</dd></div>
          </dl>
          <div class="metric-time">sim ${metric.simulationTime.toFixed(2)} s</div>
        </article>
      `,
    )
    .join("");
}

function selectCase(caseId: CaseId) {
  const spec = solverCases[caseId];
  caseCopy.textContent = spec.description;
  document.querySelectorAll<HTMLButtonElement>("[data-case]").forEach((button) => {
    const active = button.dataset.case === caseId;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
  });
  lab?.setCase(caseId);
  lab?.setRunning(false);
  paused = true;
  pauseButton.textContent = "运行";
}

document.querySelectorAll<HTMLButtonElement>("[data-case]").forEach((button) => {
  button.addEventListener("click", () => selectCase(button.dataset.case as CaseId));
});

pauseButton.addEventListener("click", () => {
  if (complete) {
    paused = false;
    complete = false;
    pauseButton.textContent = "暂停";
    lab?.reset();
    lab?.setRunning(true);
    return;
  }
  paused = !paused;
  pauseButton.textContent = paused ? "继续" : "暂停";
  lab?.setRunning(!paused);
});

resetButton.addEventListener("click", () => {
  paused = true;
  complete = false;
  pauseButton.textContent = "运行";
  lab?.reset();
});

speedSelect.addEventListener("change", () => {
  lab?.setSimulationSpeed(Number(speedSelect.value));
});

selectCase("static");

try {
  lab = await SolverLab.create(canvas, renderSnapshot);
  lab.setRunning(false);
} catch (error) {
  runtimeStrip.innerHTML = `<span class="error">Live Lab 启动失败：${escapeHtml(
    error instanceof Error ? error.message : String(error),
  )}</span>`;
}

const filterLabels: Record<"all" | ExperimentMode, string> = {
  all: "全部",
  live: "Live",
  recorded: "Recorded",
};
let activeFilter: "all" | ExperimentMode = "all";

const filters = requireElement<HTMLDivElement>("#experiment-filters");
const grid = requireElement<HTMLDivElement>("#experiment-grid");

filters.innerHTML = (Object.entries(filterLabels) as Array<
  ["all" | ExperimentMode, string]
>)
  .map(
    ([id, label], index) =>
      `<button type="button" class="filter-button ${
        index === 0 ? "is-active" : ""
      }" data-filter="${id}">${label}</button>`,
  )
  .join("");

function renderExperiments() {
  const visible = experiments.filter(
    (experiment) => activeFilter === "all" || experiment.mode === activeFilter,
  );
  grid.innerHTML = `${
    (["contact", "grasp", "soft"] as const)
      .map((group) => {
        const rows = visible.filter((experiment) => experiment.group === group);
        if (!rows.length) return "";
        return `
          <div class="experiment-group">
            <h3>${groupLabels[group]}</h3>
            <div class="experiment-cards">
              ${rows.map(experimentCard).join("")}
            </div>
          </div>
        `;
      })
      .join("")
  }`;
}

function experimentCard(experiment: Experiment) {
  const href = experiment.mode === "live" ? "#live" : experiment.report;
  return `
    <article class="experiment-card ${experiment.accent ? "is-accent" : ""}">
      <div class="experiment-card-top">
        <span class="mode-tag mode-${experiment.mode}">${experiment.mode}</span>
        <span class="engine-list">${experiment.engines.join(" · ")}</span>
      </div>
      <h4>${escapeHtml(experiment.title)}</h4>
      <p class="experiment-question">${escapeHtml(experiment.question)}</p>
      <p class="experiment-summary">${escapeHtml(experiment.summary)}</p>
      <a href="${href}" ${experiment.mode === "recorded" ? 'target="_blank" rel="noreferrer"' : ""}>
        ${experiment.mode === "live" ? "打开实时实验" : "打开冻结记录"} <span>↗</span>
      </a>
    </article>
  `;
}

filters.addEventListener("click", (event) => {
  const target = event.target as HTMLElement;
  const button = target.closest<HTMLButtonElement>("[data-filter]");
  if (!button) return;
  activeFilter = button.dataset.filter as "all" | ExperimentMode;
  filters.querySelectorAll<HTMLButtonElement>("[data-filter]").forEach((candidate) => {
    candidate.classList.toggle("is-active", candidate === button);
  });
  renderExperiments();
});

renderExperiments();

function escapeHtml(value: string) {
  return value.replace(/[&<>"']/g, (character) => {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return entities[character] ?? character;
  });
}
