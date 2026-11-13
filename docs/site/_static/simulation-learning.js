/* Progressive enhancements; lesson text and navigation work without JavaScript. */
(() => {
  "use strict";
  const zh = document.documentElement.lang === "zh-CN";
  const say = (cn, en) => (zh ? cn : en);
  const lesson = document.body.dataset.lesson;
  const links = [...document.querySelectorAll("[data-lesson-link]")];
  const ids = links.map((link) => link.dataset.lessonLink);
  const key = "dexlab-mujoco-reading-v1";
  const status = document.getElementById("save-status");
  let completed = new Set();
  let last = null;
  let writable = true;
  try {
    const saved = JSON.parse(localStorage.getItem(key) || "{}");
    if (saved && Array.isArray(saved.completed)) {
      completed = new Set(saved.completed.filter((id) => ids.includes(id)));
    }
    if (saved && ids.includes(saved.last)) last = saved.last;
  } catch {
    writable = false;
  }

  function save() {
    try {
      localStorage.setItem(
        key,
        JSON.stringify({ completed: [...completed], last: lesson }),
      );
      writable = true;
    } catch {
      writable = false;
    }
    status.textContent = writable
      ? say(
          "进度仅保存在此浏览器，可随时取消。",
          "Progress stays in this browser. You can unmark a lesson.",
        )
      : say(
          "此浏览器无法保存进度；本页仍可正常学习。",
          "This browser cannot save progress. You can still read and interact with this page.",
        );
  }

  const mark = document.getElementById("mark-read");
  function showProgress() {
    document.getElementById("read-count").textContent = say(
      `已读 ${completed.size} / ${ids.length} 课`,
      `${completed.size} / ${ids.length} lessons read`,
    );
    document.getElementById("read-progress").value = completed.size;
    links.forEach((link) => {
      link.querySelector(".read-state").hidden = !completed.has(
        link.dataset.lessonLink,
      );
    });
    const done = completed.has(lesson);
    mark.setAttribute("aria-pressed", String(done));
    mark.textContent = done
      ? say("已读 · 点击取消", "Read · unmark")
      : say("标记为已读", "Mark as read");
  }
  if (last && last !== lesson) {
    const source = links.find((link) => link.dataset.lessonLink === last);
    const resume = document.getElementById("resume-learning");
    resume.href = source.href;
    resume.textContent = say("继续上次阅读", "Continue last lesson");
    resume.hidden = false;
  }
  mark.addEventListener("click", () => {
    if (completed.has(lesson)) completed.delete(lesson);
    else completed.add(lesson);
    save();
    showProgress();
  });
  showProgress();
  save();

  const menu = document.querySelector(".chapter-menu");
  menu.open = !window.matchMedia("(max-width: 800px)").matches;
  const mode = document.getElementById("detail-mode");
  const explanations = [...document.querySelectorAll("details.explanation")];
  mode.hidden = explanations.length === 0;
  mode.addEventListener("click", () => {
    const expand = mode.getAttribute("aria-pressed") !== "true";
    explanations.forEach((detail) => {
      detail.open = expand;
    });
    mode.setAttribute("aria-pressed", String(expand));
    mode.textContent = expand
      ? say("收起深入讲解", "Collapse explanations")
      : say("展开深入讲解", "Expand explanations");
  });

  document.querySelectorAll(".quiz").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const answer = form.querySelector("input:checked");
      const feedback = form.querySelector(".quiz-feedback");
      feedback.hidden = false;
      if (!answer) {
        feedback.textContent = say(
          "先选一个答案，再检查你的判断。",
          "Choose an answer, then check your reasoning.",
        );
        return;
      }
      feedback.textContent =
        answer.value === form.dataset.answer
          ? form.dataset.correct
          : form.dataset.incorrect;
    });
  });

  const lab = document.getElementById("time-lab");
  if (lab) {
    const step = document.getElementById("physics-step");
    const repeat = document.getElementById("control-repeat");
    const plot = document.getElementById("time-ticks");
    const svgNS = "http://www.w3.org/2000/svg";
    function drawTiming() {
      const h = Number(step.value),
        n = Number(repeat.value),
        period = h * n;
      document.getElementById("step-value").textContent = `${h} ms`;
      document.getElementById("repeat-value").textContent = String(n);
      document.getElementById("control-period").textContent = `${period} ms`;
      document.getElementById("control-frequency").textContent =
        `${(1000 / period).toFixed(1)} Hz`;
      document.getElementById("time-explanation").textContent = say(
        `每 ${n} 个物理步更新一次控制：${h} × ${n} = ${period} ms。示意窗口为 100 ms；它不表示墙钟耗时。`,
        `Control updates every ${n} physics steps: ${h} × ${n} = ${period} ms. The plot spans 100 ms of simulated time, not wall time.`,
      );
      plot.replaceChildren();
      for (let t = 0; t <= 100; t += h) {
        const line = document.createElementNS(svgNS, "line");
        line.setAttribute("x1", String(30 + t * 4.8));
        line.setAttribute("x2", String(30 + t * 4.8));
        line.setAttribute("y1", "35");
        line.setAttribute("y2", "47");
        line.setAttribute("class", "physics-tick");
        plot.append(line);
      }
      for (let t = 0; t <= 100; t += period) {
        const line = document.createElementNS(svgNS, "line");
        line.setAttribute("x1", String(30 + t * 4.8));
        line.setAttribute("x2", String(30 + t * 4.8));
        line.setAttribute("y1", "75");
        line.setAttribute("y2", "97");
        line.setAttribute("class", "control-tick");
        plot.append(line);
      }
    }
    step.addEventListener("input", drawTiming);
    repeat.addEventListener("input", drawTiming);
    drawTiming();
  }
  document.querySelectorAll("[data-enhanced]").forEach((element) => {
    element.hidden = false;
  });
})();
