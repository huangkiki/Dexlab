// Size only our same-origin lab frame; unrelated messages cannot resize the page.
window.addEventListener("message", (event) => {
  if (
    event.origin !== window.location.origin ||
    event.data?.type !== "dexlab-lab-height"
  )
    return;
  const height = event.data.height;
  if (typeof height !== "number" || !Number.isFinite(height)) return;
  document.querySelectorAll(".dexlab-live-lab iframe").forEach((frame) => {
    if (event.source === frame.contentWindow)
      frame.style.height = `${Math.max(500, Math.min(1600, Math.ceil(height) + 2))}px`;
  });
});
