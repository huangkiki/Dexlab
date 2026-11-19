/* Switch recorded GIF representations while keeping the same evidence card. */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.cutting-player').forEach((player) => {
    const image = player.querySelector('img');
    const buttons = [...player.querySelectorAll('[data-cutting-view]')];
    if (!image || !buttons.length) return;

    buttons.forEach((button) => {
      button.addEventListener('click', () => {
        if (button.getAttribute('aria-pressed') === 'true') return;
        buttons.forEach((item) => {
          item.setAttribute('aria-pressed', String(item === button));
        });
        image.src = button.dataset.src;
        image.alt = button.textContent.trim();
      });
    });
  });
});
