import "./claw.css";
import { toyPortraitUrls } from "./claw-model-urls";
import { CABINET, CABINETS } from "./claw-toys";
import { ClawLab } from "./claw-lab";
import { clawExplainer } from "./claw-explainer";
import type { ClawComparison } from "./claw-comparison";
import {
  TOYS,
  CLAW_SOLVERS,
  type ClawPhase,
  type ClawSnapshot,
  type MoveAxis,
} from "./claw-task";
const en = new URLSearchParams(location.search).get("lang") === "en";
const t = (zh: string, english: string) => (en ? english : zh);
const arrow =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 19V5m-6 6 6-6 6 6"/></svg>';
const prizeGroups = [...new Set(TOYS.map(toy => toy.kind))].map(kind => ({
  kind, indices: TOYS.flatMap((toy, i) => toy.kind === kind ? [i] : []),
}));
const messages: Record<ClawPhase, string> = {
  aim: t(
    "把光圈移到玩偶正上方，准备好了就下爪。",
    "Move the ring over a toy. Drop when you are ready.",
  ),
  descend: t(
    "下爪中……看看这次对准了没有。",
    "Going down… let’s see how you lined it up.",
  ),
  close: t("合爪！", "Closing the claw!"),
  lift: t("提起来……抓稳了吗？", "Lifting… will the grip hold?"),
  carry: t("送往金色取物口，别掉呀。", "Heading for the gold chute. Hang on!"),
  release: t(
    "松爪，等它落进取物盒。",
    "Letting go. Wait for it to land in the prize bin.",
  ),
  return: t("爪子回位中。", "Returning the claw."),
  result: "",
};
export async function startClawPage() {
  const app = document.querySelector<HTMLDivElement>("#app")!;
  app.innerHTML = `<main class="claw-page">
    <header class="game-heading"><div><h1>${t("DexLab 抓娃娃", "DexLab Claw Machine")}</h1><p>${t("你来瞄准，让三个求解器抓同一只娃娃。", "You aim. Three solvers try the same grab.")}</p></div>
      <button type="button" id="new-cabinet" class="quiet-button">${t("换一柜", "New cabinet")}</button></header>
    <div class="machine-layout">
      <section class="scene-panel" aria-label="${t("抓娃娃机", "Claw machine")}">
        <div class="scene-tools"><span>${t("金色口：领奖处", "Gold chute: prize bin")}</span><button type="button" id="view" class="quiet-button" aria-pressed="false">${t("俯视瞄准", "Top view")}</button></div>
        <canvas id="claw-canvas" tabindex="0" aria-label="${t("抓娃娃场景。方向键或 WASD 移动，空格下爪。", "Claw machine. Arrow keys or WASD move; Space drops the claw.")}"></canvas>
        <div id="world-labels" class="world-labels" hidden>${CLAW_SOLVERS.map((solver, i) => `<article class="world-label"><h2>${solver}<small>${[t("牛顿法", "Newton method"), t("非线性共轭梯度", "Nonlinear CG"), t("投影高斯–赛德尔", "Projected Gauss–Seidel")][i]}</small></h2><div><strong id="world-result-${i}"></strong><p id="world-metrics-${i}"></p></div></article>`).join("")}</div>
        <p class="camera-help">${t("拖动画面转动视角 · 滚轮缩放", "Drag to orbit · Scroll to zoom")}</p>
      </section>
      <section class="controls" aria-label="${t("操作台", "Control panel")}">
        <div class="round-stats"><span>${t("本柜收藏 · Newton", "Cabinet · Newton")} <strong id="score">0 / ${TOYS.length}</strong></span><span id="attempts">${t("尚未下爪", "First try awaits")}</span></div>
        <label class="iteration-control" for="cabinet">${t("选择娃娃 · 16 款", "Prizes · 16 characters")}<select id="cabinet">${Object.entries(CABINETS).map(([key, value]) => `<option value="${key}" ${key === CABINET ? "selected" : ""}>${en ? value.name : value.zh}</option>`).join("")}</select></label>
        <p class="input-help">${t("每柜 16 只 · 切换组合重新开始。", "16 prizes per cabinet. Changing lineup starts fresh.")}</p>
        <label class="iteration-control" for="iterations">${t("每步迭代上限", "Iterations per step")}<select id="iterations"><option value="5">5</option><option value="20">20</option><option value="60" selected>60</option><option value="100">100</option></select></label>
        <label class="iteration-control" for="renderer">${t("画面渲染", "Renderer")}<select id="renderer"><option value="webgl">WebGL</option><option value="ovrtx">OVRTX · ${t("本机 RTX", "local RTX")}</option></select></label>
        <p id="renderer-help" class="input-help" hidden>${t("OVRTX 需要本机渲染服务。", "OVRTX needs the local render service.")} <a href="https://github.com/huangkiki/Dexlab/tree/main/web/ovrtx">${t("启动说明", "Setup")}</a></p>
        <div class="play-controls"><div class="direction-pad" aria-label="${t("移动爪子", "Move the claw")}">
          ${[
            ["forward", "y", 1, t("向前", "Forward")],
            ["left", "x", -1, t("向左", "Left")],
            ["back", "y", -1, t("向后", "Back")],
            ["right", "x", 1, t("向右", "Right")],
          ]
            .map(
              ([name, axis, sign, label]) =>
                `<button type="button" class="move-button ${name}" data-axis="${axis}" data-direction="${sign}" aria-label="${label}">${arrow}<span>${label}</span></button>`,
            )
            .join("")}
        </div><button type="button" id="drop" class="drop-button">${t("下爪", "Drop claw")}<kbd>Space</kbd></button></div>
        <p class="input-help">${t("按住方向移动，点按微调。", "Hold a direction to move. Tap to fine-tune.")}<br><span>${t("方向键 / WASD · 空格下爪", "Arrow keys / WASD · Space to drop")}</span></p>
        <div class="toy-collection"><h2>${t("这一柜的小伙伴", "Meet the prizes")}</h2><p class="input-help">${t("点头像近看 · 俯视按钮回到全景", "Click a portrait to inspect · Top view restores the overview")}</p><ul>${prizeGroups.map(({kind, indices}) => { const i = indices[0]!, toy = TOYS[i]!; return `<li data-kind="${kind}"><button type="button" class="toy-portrait-button" data-look="${i}" aria-label="${t("近看", "Look at")} ${en ? toy.name : toy.zh}"><img class="toy-portrait" src="${toyPortraitUrls[i]}" alt="" /></button><span>${en ? toy.name : toy.zh}</span><span class="toy-status">0 / ${indices.length}</span></li>`; }).join("")}</ul></div>
      </section>
    </div>
    <div class="round-feedback" id="feedback"><p id="hint" role="status" aria-live="polite">${messages.aim}</p><span id="live-contact"></span></div>
    <section id="comparison-tools" class="comparison-tools" aria-label="${t("同步回放", "Synchronized replay")}" hidden>
      <div class="transport"><button type="button" id="play-pause" class="quiet-button">${t("暂停", "Pause")}</button><label for="speed">${t("播放速度", "Speed")} <select id="speed"><option value="1">1×</option><option value="0.5">0.5×</option><option value="0.25">0.25×</option></select></label><output id="comparison-time">0.00 s</output><button type="button" id="repeat-grab" class="quiet-button">${t("原局重试", "Repeat this grab")}</button></div>
      <label class="timeline-label" for="timeline">${t("共同时间轴 · 抓取结束后可拖动复盘", "Shared timeline · Scrub after the grab finishes")}</label><input id="timeline" type="range" min="0" max="1" value="0" step="1" disabled>
      <div class="spread-row"><span id="spread"></span><button type="button" id="first-difference" class="quiet-button" disabled>${t("查看首次位置差 > 1 mm", "First spread > 1 mm")}</button></div>
      <p class="comparison-note">${t("同一起点 · 同一指令 · elliptic · implicitfast · 2 ms。重新瞄准会继续 Newton 那一柜。", "Same start · same commands · elliptic · implicitfast · 2 ms. Re-aim continues the Newton cabinet.")}</p>
    </section>
    ${clawExplainer(en)}
    <footer><span>${t("MuJoCo 本地物理 · 免费玩，随时重来", "Local MuJoCo physics · Free play, unlimited tries")}</span><a href="?mode=solver&embed=1&lang=${en ? "en" : "zh"}">${t("简化场景对比", "Simple-scene comparison")}</a>
      <details><summary>${t("里面的物理是怎么回事？", "What drives the physics?")}</summary><p>${t("每柜 16 只奶家族玩偶采用毛绒外观，物理上仍是刚体；三指爪由关节驱动。抓取、滑落和落入取物盒由 MuJoCo 接触计算决定；没有吸附、随机中奖或保底抓取。玩偶进入取物盒并停稳后才计分。这是互动教学场景，不代表软体玩偶或真机验证。", "Each cabinet has 16 Nai-family toys with plush materials but rigid-body physics, with an actuated three-finger claw. MuJoCo contact determines grasping, slipping and landing; there is no attachment, random win or guaranteed catch. A toy scores after settling inside the actual bin. This is an interactive teaching scene, not deformable-plush or hardware validation.")}</p><p>MuJoCo 3.17 WASM / CPU · WebGL / local OVRTX · Newton / CG / PGS · elliptic · implicitfast · 2 ms</p></details>
    </footer></main>`;
  const el = <T extends HTMLElement>(id: string) =>
    document.getElementById(id) as T;
  const canvas = el<HTMLCanvasElement>("claw-canvas"),
    drop = el<HTMLButtonElement>("drop");
  const moves = [...app.querySelectorAll<HTMLButtonElement>("[data-axis]")];
  const buttons = [...app.querySelectorAll<HTMLButtonElement>("button")];
  buttons.forEach((b) => (b.disabled = true));
  let lastMessage = "";
  let failed = false;
  function update(s: ClawSnapshot) {
    if (failed) return;
    el("score").textContent = `${s.score} / ${TOYS.length}`;
    el("attempts").textContent = s.attempts
      ? t(
          `已下爪 ${s.attempts} 次`,
          `${s.attempts} ${s.attempts === 1 ? "attempt" : "attempts"}`,
        )
      : t("尚未下爪", "First try awaits");
    let message = messages[s.phase];
    if (s.phase === "result")
      message = t(
        "三路抓取结束。拖动时间轴复盘，或调整迭代上限后原局重试。",
        "All three grabs finished. Scrub the replay, or change the iteration cap and repeat.",
      );
    if (s.score === TOYS.length)
      message = t(
        "这一柜全抓到了！换一柜再玩。",
        "You collected the whole cabinet! Start a new one.",
      );
    if (message !== lastMessage) {
      el("hint").textContent = message;
      lastMessage = message;
    }
    const ready = s.phase === "aim",
      result = s.phase === "result";
    moves.forEach((b) => (b.disabled = !ready));
    drop.disabled = !(ready || result);
    drop.innerHTML = `${s.score === TOYS.length ? t("再玩一柜", "Play a new cabinet") : result ? t("重新瞄准", "Re-aim") : ready ? t("下爪", "Drop claw") : t("抓取中…", "Grabbing…")}<kbd>Space</kbd>`;
    el<HTMLSelectElement>("iterations").disabled = !(ready || result);
    el("feedback").classList.toggle("is-win", s.roundWon > 0 && result);
    el("live-contact").textContent = "";
    for (const { kind, indices } of prizeGroups) {
      const node = app.querySelector<HTMLElement>(`[data-kind="${kind}"]`)!;
      const count = indices.filter(i => s.won.includes(i)).length;
      node.classList.toggle("is-won", count === indices.length);
      node.querySelector(".toy-status")!.textContent = `${count} / ${indices.length} ${t("已抓到", "collected")}`;
      node.querySelector<HTMLButtonElement>("[data-look]")!.dataset.look = String(indices.find(i => !s.won.includes(i)) ?? indices[0]);
    }
  }
  function updateComparison(comparison: ClawComparison) {
    app
      .querySelector(".machine-layout")!
      .classList.toggle("is-comparing", comparison.started);
    el("world-labels").hidden = el("comparison-tools").hidden =
      !comparison.started;
    if (!comparison.started || !comparison.current) return;
    const frame = comparison.current;
    el("comparison-time").textContent = `${frame.time.toFixed(2)} s`;
    frame.worlds.forEach((world, i) => {
      const phase = world.snapshot.phase;
      el(`world-result-${i}`).textContent =
        phase === "result"
          ? t(
              `本轮入盒 ${world.snapshot.roundWon} 只`,
              `${world.snapshot.roundWon} prizes this grab`,
            )
          : messages[phase];
      el(`world-metrics-${i}`).textContent = t(
        `抬升 ${world.liftMm.toFixed(0)} mm · ${world.meanIterations.toFixed(1)} 次/步 · ${world.meanStepMs.toFixed(2)} ms/步`,
        `Lift ${world.liftMm.toFixed(0)} mm · ${world.meanIterations.toFixed(1)} it/step · ${world.meanStepMs.toFixed(2)} ms/step`,
      );
    });
    el<HTMLButtonElement>("repeat-grab").disabled = !comparison.complete;
    const timeline = el<HTMLInputElement>("timeline");
    timeline.disabled = !comparison.complete;
    timeline.max = String(Math.max(1, comparison.frames.length - 1));
    timeline.value = String(comparison.cursor);
    timeline.setAttribute("aria-valuetext", `${frame.time.toFixed(2)} s`);
    el("play-pause").textContent = comparison.paused
      ? t("播放", "Play")
      : t("暂停", "Pause");
    el<HTMLButtonElement>("first-difference").disabled =
      !comparison.complete || comparison.firstDifference === null;
    el("spread").textContent = t(
      `此刻最大位置差 ${frame.spreadMm.toFixed(2)} mm`,
      `Current max position spread ${frame.spreadMm.toFixed(2)} mm`,
    );
  }
  const lab = await ClawLab.create(
    canvas,
    update,
    (e) => {
      failed = true;
      el("hint").textContent = t(
        "仿真暂停了，重新加载再玩。",
        "Simulation stopped. Reload to play again.",
      );
      el("live-contact").textContent =
        e instanceof Error ? e.message : String(e);
      buttons.forEach((b) => (b.disabled = true));
      const reload = document.createElement("a");
      reload.href = location.href;
      reload.className = "quiet-button";
      reload.textContent = t("重新加载", "Reload");
      el("feedback").append(reload);
      app
        .querySelectorAll<HTMLInputElement | HTMLSelectElement>("input,select")
        .forEach((control) => (control.disabled = true));
    },
    updateComparison,
  );
  // The first animation frame can fail synchronously during construction.
  if (failed) {
    lab.dispose();
    return;
  }
  buttons.forEach((b) => (b.disabled = false));
  el<HTMLSelectElement>("cabinet").addEventListener("change", (event) => {
    const url = new URL(location.href);
    url.searchParams.set("cabinet", (event.target as HTMLSelectElement).value);
    location.assign(url.href);
  });
  const renderer = el<HTMLSelectElement>("renderer");
  const local = ["127.0.0.1", "localhost"].includes(location.hostname);
  const chooseRenderer = () => {
    const rtx = renderer.value === "ovrtx";
    const url = new URL(location.href);
    url.searchParams.set("renderer", renderer.value);
    history.replaceState(null, "", url);
    el("renderer-help").hidden = !rtx;
    lab.setRtx(rtx && local, en);
    if (rtx && !local) el("renderer-help").firstChild!.textContent = t(
      "请在本机启动页面和 OVRTX 服务；公网页面当前仍显示 WebGL。 ",
      "Start the page and OVRTX service locally; this public page still uses WebGL. ");
  };
  renderer.addEventListener("change", chooseRenderer);
  if (new URLSearchParams(location.search).get("renderer") === "ovrtx") {
    renderer.value = "ovrtx";
    chooseRenderer();
  }
  app.querySelectorAll<HTMLButtonElement>("[data-look]").forEach((button) => {
    button.addEventListener("click", () => {
      lab.focusToy(Number(button.dataset.look));
      top = false;
      el("view").setAttribute("aria-pressed", "false");
      el("view").textContent = t("俯视瞄准", "Top view");
    });
  });
  update(lab.task.snapshot());
  const iterationLimit = () =>
    Number(el<HTMLSelectElement>("iterations").value);
  el("repeat-grab").addEventListener("click", () =>
    lab.startComparison(iterationLimit(), true),
  );
  el("play-pause").addEventListener("click", () => {
    lab.togglePlayback();
    updateComparison(lab.comparison);
  });
  el("speed").addEventListener("change", () => {
    lab.speed = Number(el<HTMLSelectElement>("speed").value);
  });
  el("timeline").addEventListener("input", () => {
    lab.seek(Number(el<HTMLInputElement>("timeline").value));
    updateComparison(lab.comparison);
  });
  el("first-difference").addEventListener("click", () => {
    if (lab.comparison.firstDifference !== null)
      lab.seek(lab.comparison.firstDifference);
    updateComparison(lab.comparison);
  });
  const clear = () => {
    lab.clearInput();
    app
      .querySelectorAll(".is-held")
      .forEach((node) => node.classList.remove("is-held"));
  };
  const action = () => {
    if (failed) return;
    clear();
    if (lab.task.won.size === TOYS.length) lab.reset();
    else if (lab.task.phase === "result") lab.reaim();
    else lab.startComparison(iterationLimit());
  };
  drop.addEventListener("click", action);
  el("new-cabinet").addEventListener("click", () => {
    clear();
    lab.reset();
  });
  let top = false;
  el("view").addEventListener("click", () => {
    top = !top;
    lab.setTopView(top);
    el("view").setAttribute("aria-pressed", String(top));
    el("view").textContent = top
      ? t("斜视", "Angled view")
      : t("俯视瞄准", "Top view");
  });
  moves.forEach((button) => {
    const axis = button.dataset.axis as MoveAxis,
      direction = Number(button.dataset.direction);
    let downAt = 0;
    button.addEventListener("pointerdown", (event) => {
      if (event.button !== 0 || button.disabled) return;
      event.preventDefault();
      canvas.focus({ preventScroll: true });
      downAt = performance.now();
      button.setPointerCapture(event.pointerId);
      lab.input.set(`pointer-${event.pointerId}`, { axis, direction });
      button.classList.add("is-held");
    });
    button.addEventListener("pointerup", (event) => {
      const held = lab.input.delete(`pointer-${event.pointerId}`);
      button.classList.remove("is-held");
      if (held && performance.now() - downAt < 130)
        lab.task.move(axis, direction * 0.005);
    });
    for (const name of ["pointercancel", "lostpointercapture"])
      button.addEventListener(name, (event) => {
        lab.input.delete(`pointer-${(event as PointerEvent).pointerId}`);
        button.classList.remove("is-held");
      });
    button.addEventListener("click", (event) => {
      if (event.detail === 0) lab.task.move(axis, direction * 0.005);
    });
  });
  const keys: Record<string, { axis: MoveAxis; direction: number }> = {
    ArrowLeft: { axis: "x", direction: -1 },
    KeyA: { axis: "x", direction: -1 },
    ArrowRight: { axis: "x", direction: 1 },
    KeyD: { axis: "x", direction: 1 },
    ArrowUp: { axis: "y", direction: 1 },
    KeyW: { axis: "y", direction: 1 },
    ArrowDown: { axis: "y", direction: -1 },
    KeyS: { axis: "y", direction: -1 },
  };
  window.addEventListener("keydown", (event) => {
    if (
      failed ||
      event.ctrlKey ||
      event.altKey ||
      event.metaKey ||
      (event.target as HTMLElement).matches("input, select, textarea, summary")
    )
      return;
    if (keys[event.code]) {
      event.preventDefault();
      lab.input.set(event.code, keys[event.code]!);
    }
    if (
      event.code === "Space" &&
      !(event.target as HTMLElement).closest("button,a")
    ) {
      event.preventDefault();
      if (!event.repeat) action();
    }
  });
  window.addEventListener("keyup", (event) => lab.input.delete(event.code));
  window.addEventListener("blur", clear);
  document.addEventListener("visibilitychange", () => {
    clear();
    lab.setActive(!document.hidden);
  });
  // BFCache keeps the scene alive but paused; Back resumes the same cabinet.
  window.addEventListener("pagehide", (event) => {
    clear();
    if (event.persisted) lab.setActive(false);
    else lab.dispose();
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) lab.setActive(!document.hidden);
  });
  if (window.parent !== window)
    new ResizeObserver(() =>
      window.parent.postMessage(
        { type: "dexlab-lab-height", height: app.scrollHeight },
        location.origin,
      ),
    ).observe(app);
}
