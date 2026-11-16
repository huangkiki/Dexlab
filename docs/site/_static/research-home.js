// Keep published homepage fragments working after the global Sphinx labels
// moved to their destination pages.
if (location.hash === "#blog") {
  location.replace(new URL("#experiments", location.href).href);
}

const legacyAnchorRoutes = {
  quickstart: 'quickstart.html',
  'live-lab': 'about.html#live-lab',
};
if (legacyAnchorRoutes[location.hash.slice(1)]) {
  location.replace(legacyAnchorRoutes[location.hash.slice(1)]);
}

const pageProgress = document.querySelector(".page-progress span");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

const revealGroups = [...document.querySelectorAll("[data-reveal-group]")];

function setUpRevealGroup(group) {
  const items = [...group.querySelectorAll("[data-reveal-item]")];
  if (!items.length) {
    return;
  }
  group.classList.add("is-reveal-ready");
  items.forEach((item, index) => item.style.setProperty("--reveal-order", index));

  if (!("IntersectionObserver" in window)) {
    requestAnimationFrame(() => requestAnimationFrame(() => {
      items.forEach((item) => item.classList.add("is-revealed"));
    }));
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) {
        continue;
      }
      entry.target.classList.add("is-revealed");
      observer.unobserve(entry.target);
    }
  }, {
    threshold: 0.12,
    rootMargin: "0px 0px -8% 0px",
  });

  items.forEach((item) => observer.observe(item));
}

if (!reduceMotion) {
  revealGroups.forEach(setUpRevealGroup);
}

let scheduled = 0;

function updateReadingProgress() {
  scheduled = 0;
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const pageRatio = scrollable > 0 ? clamp(window.scrollY / scrollable, 0, 1) : 0;
  if (pageProgress) {
    pageProgress.style.transform = `scaleX(${pageRatio})`;
  }
}

function scheduleReadingProgress() {
  if (!scheduled) {
    scheduled = window.requestAnimationFrame(updateReadingProgress);
  }
}

if (pageProgress) {
  window.addEventListener("scroll", scheduleReadingProgress, { passive: true });
  window.addEventListener("resize", scheduleReadingProgress);
  updateReadingProgress();
}
