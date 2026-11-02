export {};
const boot = document.querySelector<HTMLElement>("#boot-status")!;
const bootMessage = document.querySelector<HTMLElement>("#boot-message")!;
const retry = document.querySelector<HTMLAnchorElement>("#boot-retry")!;
const english = new URLSearchParams(location.search).get("lang") === "en";
if (english) {
  document.documentElement.lang = "en";
  document.querySelector("#boot-title")!.textContent =
    "Your turn at the claw machine";
  bootMessage.textContent = "Loading the interactive lab…";
  retry.textContent = "Reload";
}

const timeout = window.setTimeout(() => {
  bootMessage.textContent = english
    ? "Loading is taking longer than expected. You can reload and try again."
    : "加载时间较长。可以重新加载再试一次。";
  retry.hidden = false;
}, 20000);
try {
  if (new URLSearchParams(location.search).get("mode") === "solver") {
    await import("./solver-page");
  } else {
    const { startClawPage } = await import("./claw-page");
    await startClawPage();
  }
  boot.remove();
} catch (error) {
  document.querySelector("#app")!.replaceChildren();
  bootMessage.textContent = english
    ? "The lab could not start. Check your connection and browser graphics support, then reload."
    : "实验未能启动。请检查网络与浏览器图形支持后重新加载。";
  retry.hidden = false;
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = english ? "Technical details" : "错误详情";
  const message = document.createElement("p");
  message.textContent = error instanceof Error ? error.message : String(error);
  details.append(summary, message);
  boot.append(details);
} finally {
  clearTimeout(timeout);
}
