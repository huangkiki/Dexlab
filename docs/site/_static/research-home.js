// Keep published homepage fragments working after the global Sphinx labels
// moved to their destination pages.
if (document.documentElement.lang === "en" && location.hash === "#blog") {
  // Keep old links working without creating an English-CN history loop on Back.
  location.replace(new URL("../../zh-cn/latest/index.html#blog", location.href).href);
}

const legacyAnchorRoutes = {
  quickstart: 'quickstart.html',
  'live-lab': 'about.html#live-lab',
};
if (legacyAnchorRoutes[location.hash.slice(1)]) {
  location.replace(legacyAnchorRoutes[location.hash.slice(1)]);
}

// Topic navigation progressively enhances an otherwise complete reading index.
const controls = document.querySelector('.topic-controls');
if (controls) {
  const buttons = [...controls.querySelectorAll('button[data-topic]')];
  const panels = [...document.querySelectorAll('.topic-panel')];
  function selectTopic(button) {
    for (const item of buttons) {
      item.setAttribute('aria-pressed', String(item === button));
    }
    for (const panel of panels) {
      panel.hidden = panel.id !== button.getAttribute('aria-controls');
    }
  }
  controls.hidden = false;
  controls.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-topic]');
    if (button) selectTopic(button);
  });
  selectTopic(buttons[0]);
}
