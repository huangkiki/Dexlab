// Keep published homepage fragments working after the global Sphinx labels
// moved to their destination pages.
if (location.hash === "#blog") {
  // Keep old links working without creating an English-CN history loop on Back.
  const blogPage = document.documentElement.lang === "en"
    ? "../../zh-cn/latest/blog.html"
    : "blog.html";
  location.replace(new URL(blogPage, location.href).href);
}

const legacyAnchorRoutes = {
  quickstart: 'quickstart.html',
  'live-lab': 'about.html#live-lab',
  'research-findings': 'about.html#research-findings',
  'research-diagnosis': 'about.html#research-diagnosis',
  'research-selection': 'about.html#research-selection',
  'research-scope': 'about.html#research-scope',
};
if (legacyAnchorRoutes[location.hash.slice(1)]) {
  location.replace(legacyAnchorRoutes[location.hash.slice(1)]);
}

const pageProgress = document.querySelector(".page-progress span");
const loopStory = document.querySelector(".loop-story");
const loopSteps = [...document.querySelectorAll("[data-loop-step]")];
const loopCurrent = document.querySelector("[data-loop-current]");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

let scheduled = 0;

function updateReadingProgress() {
  scheduled = 0;
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const pageRatio = scrollable > 0 ? clamp(window.scrollY / scrollable, 0, 1) : 0;
  if (pageProgress) {
    pageProgress.style.transform = `scaleX(${pageRatio})`;
  }

  if (!loopStory || !loopSteps.length || reduceMotion.matches) {
    return;
  }

  const bounds = loopStory.getBoundingClientRect();
  const sectionTop = bounds.top + window.scrollY;
  const leadIn = window.innerHeight * 0.15;
  const travel = Math.max(1, loopStory.offsetHeight - leadIn);
  const loopRatio = clamp((window.scrollY - sectionTop + leadIn) / travel, 0, 1);
  const activeIndex = Math.min(
    loopSteps.length - 1,
    Math.floor(loopRatio * loopSteps.length),
  );

  loopStory.style.setProperty("--loop-progress", loopRatio.toFixed(4));
  loopSteps.forEach((step, index) => {
    const active = index === activeIndex;
    step.classList.toggle("is-active", active);
    if (active) {
      step.setAttribute("aria-current", "step");
    } else {
      step.removeAttribute("aria-current");
    }
  });
  if (loopCurrent) {
    loopCurrent.textContent = loopSteps[activeIndex].dataset.loopLabel;
  }
}

function scheduleReadingProgress() {
  if (!scheduled) {
    scheduled = window.requestAnimationFrame(updateReadingProgress);
  }
}

if (pageProgress || loopStory) {
  if (loopStory && !reduceMotion.matches) {
    document.documentElement.classList.add("has-scroll-motion");
  }
  window.addEventListener("scroll", scheduleReadingProgress, { passive: true });
  window.addEventListener("resize", scheduleReadingProgress);
  updateReadingProgress();
}
