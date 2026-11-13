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
