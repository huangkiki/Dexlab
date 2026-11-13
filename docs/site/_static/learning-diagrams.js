// Course diagrams use the upstream Mermaid definitions. Plain text remains
// readable if the renderer cannot load; unrelated pages fetch no library.
const diagrams = document.querySelectorAll('pre.mermaid');
if (diagrams.length) {
  const originals = [...diagrams].map(node => node.textContent);
  try {
    const {default: mermaid} = await import('https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs');
    mermaid.initialize({startOnLoad: false, securityLevel: 'strict'});
    await mermaid.run({nodes: diagrams});
  } catch (error) {
    diagrams.forEach((node, index) => { node.textContent = originals[index]; });
    console.warn('Course diagram renderer unavailable; showing diagram source.', error);
  }
}
