// Build display-only derivatives. Native collision geometry and source GLBs stay untouched.
import { readFile, writeFile, mkdir, readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { MeshoptSimplifier } from 'meshoptimizer';
const root = new URL('../src/assets/nai/', import.meta.url);
const output = new URL('display/', root);
await mkdir(output, { recursive: true });
await MeshoptSimplifier.ready;
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const manifest = { tool: 'meshoptimizer 0.25.0', targetTriangles: 6000, maxRelativeError: .005, textureSize: 512, assets: [] };
const resize = (bytes, size) => execFileSync(process.env.PYTHON ?? 'python3', ['-c',
  'from PIL import Image; from io import BytesIO; import sys; im=Image.open(BytesIO(sys.stdin.buffer.read())); im.thumbnail((int(sys.argv[1]),)*2,Image.Resampling.LANCZOS); im.save(sys.stdout.buffer,format="PNG",optimize=True)', String(size)], { input: bytes, maxBuffer: 8 * 1024 * 1024 });
for (const name of (await readdir(root)).filter(n => n.endsWith('.glb')).sort()) {
  const source = await readFile(new URL(name, root));
  const jsonLength = source.readUInt32LE(12);
  const doc = JSON.parse(source.subarray(20, 20 + jsonLength).toString());
  const binary = source.subarray(28 + jsonLength);
  const oldViews = doc.bufferViews, oldAccessors = doc.accessors;
  const chunks = [];
  doc.bufferViews = []; doc.accessors = [];
  let offset = 0, before = 0, after = 0, maxError = 0;
  function append(bytes, target) {
    const padding = (4 - offset % 4) % 4;
    if (padding) { chunks.push(Buffer.alloc(padding)); offset += padding; }
    const view = doc.bufferViews.push({ buffer: 0, byteOffset: offset, byteLength: bytes.length, ...(target ? { target } : {}) }) - 1;
    chunks.push(bytes); offset += bytes.length;
    return view;
  }
  function array(index) {
    const a = oldAccessors[index], v = oldViews[a.bufferView];
    const Type = ({5126: Float32Array, 5125: Uint32Array, 5123: Uint16Array})[a.componentType];
    if (!Type || v.byteStride || a.sparse) throw new Error('Unexpected source accessor');
    const width = ({SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4})[a.type];
    const start = (v.byteOffset ?? 0) + (a.byteOffset ?? 0);
    const bytes = Uint8Array.from(binary.subarray(start, start + a.count * width * Type.BYTES_PER_ELEMENT));
    return { values: new Type(bytes.buffer), width, definition: a };
  }
  for (const mesh of doc.meshes) for (const p of mesh.primitives) {
    const attributes = Object.fromEntries(Object.entries(p.attributes).map(([key,index]) => [key,array(index)]));
    const positions = attributes.POSITION.values;
    const oldIndices = Uint32Array.from(array(p.indices).values);
    before += oldIndices.length / 3;
    const streams = ['NORMAL','TEXCOORD_0'].filter(k => attributes[k]);
    const stride = streams.reduce((n,k) => n + attributes[k].width, 0);
    const features = new Float32Array(positions.length / 3 * stride);
    for (let v = 0; v < positions.length / 3; v++) {
      let cursor = 0;
      for (const key of streams) {
        const {values,width} = attributes[key];
        features.set(values.subarray(v * width, (v + 1) * width), v * stride + cursor); cursor += width;
      }
    }
    const weights = streams.flatMap(key => Array(attributes[key].width).fill(key === 'NORMAL' ? .5 : 1));
    const [indices,error] = MeshoptSimplifier.simplifyWithAttributes(oldIndices, positions, 3, features, stride, weights, null,
      Math.min(oldIndices.length, manifest.targetTriangles * 3), manifest.maxRelativeError);
    after += indices.length / 3; maxError = Math.max(maxError,error);
    const [remap,count] = MeshoptSimplifier.compactMesh(indices);
    for (const [key, {values,width,definition}] of Object.entries(attributes)) {
      const compact = new values.constructor(count * width);
      for (let v = 0; v < remap.length; v++) if (remap[v] !== 0xffffffff)
        compact.set(values.subarray(v * width, (v + 1) * width), remap[v] * width);
      const entry = { ...definition, bufferView: append(Buffer.from(compact.buffer),34962), byteOffset: 0, count };
      // Source bounds are conservative and retain the same normalized scale.
      p.attributes[key] = doc.accessors.push(entry) - 1;
    }
    const compactIndices = Uint16Array.from(indices);
    if (count > 65535) throw new Error('Display mesh exceeds uint16 index range');
    p.indices = doc.accessors.push({bufferView: append(Buffer.from(compactIndices.buffer),34963), componentType: 5123, count: indices.length, type:'SCALAR'}) - 1;
  }
  for (const image of doc.images ?? []) {
    const view = oldViews[image.bufferView];
    const png = resize(binary.subarray(view.byteOffset ?? 0, (view.byteOffset ?? 0) + view.byteLength),manifest.textureSize);
    image.bufferView = append(png); image.mimeType = 'image/png';
  }
  const bin = Buffer.concat([...chunks,Buffer.alloc((4 - offset % 4) % 4)]);
  doc.buffers = [{byteLength:bin.length}];
  const json = Buffer.from(JSON.stringify(doc));
  const padded = Buffer.concat([json,Buffer.alloc((4 - json.length % 4) % 4,32)]);
  const head = Buffer.alloc(20); head.write('glTF'); head.writeUInt32LE(2,4); head.writeUInt32LE(28+padded.length+bin.length,8); head.writeUInt32LE(padded.length,12); head.writeUInt32LE(0x4e4f534a,16);
  const binHead = Buffer.alloc(8); binHead.writeUInt32LE(bin.length); binHead.writeUInt32LE(0x004e4942,4);
  const derived = Buffer.concat([head,padded,binHead,bin]);
  await writeFile(new URL(name,output),derived);
  const portraitName = name.replace('.glb','.png');
  const portraitSource = await readFile(new URL('inputs/'+portraitName,root));
  const portrait = resize(portraitSource,128);
  await writeFile(new URL(portraitName,output),portrait);
  manifest.assets.push({name,sourceSha256:hash(source),sha256:hash(derived),sourceBytes:source.length,bytes:derived.length,beforeTriangles:before,triangles:after,relativeError:maxError,portraitSourceSha256:hash(portraitSource),portraitSha256:hash(portrait)});
  console.log(name, before, '→', after, 'triangles;', source.length, '→', derived.length, 'bytes');
}
await writeFile(new URL('manifest.json',output),JSON.stringify(manifest,null,2)+'\n');
