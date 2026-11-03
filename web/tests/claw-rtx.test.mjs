import test from "node:test";
import assert from "node:assert/strict";
import { ClawRtx } from "../src/claw-rtx.ts";

test("an RTX response already decoding cannot repaint after a replay jump", async () => {
  const client = Object.create(ClawRtx.prototype);
  let draws = 0, closed = 0, resolve;
  Object.assign(client, { epoch: 0, requestedEpoch: 0, sequence: 1, closed: false,
    pending: true, image: { hidden: false }, context: { drawImage() { draws++; } } });
  const previous = globalThis.createImageBitmap;
  globalThis.createImageBitmap = () => new Promise(r => { resolve = r; });
  try {
    const header = new TextEncoder().encode(JSON.stringify({ sequence: 1, time: 7, render_ms: 40 }));
    const payload = new ArrayBuffer(4 + header.length);
    new DataView(payload).setUint32(0, header.length, true);
    new Uint8Array(payload, 4).set(header);
    const response = client.receive(payload);
    client.invalidate();
    resolve({ width: 1, height: 1, close() { closed++; } });
    await response;
    assert.equal(draws, 0);
    assert.equal(closed, 1);
    assert.equal(client.image.hidden, true);
    assert.equal(client.pending, false);
  } finally { globalThis.createImageBitmap = previous; }
});
