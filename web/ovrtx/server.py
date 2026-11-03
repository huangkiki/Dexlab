"""Local visual-only OVRTX bridge for DexLab. One client and one snapshot at a time."""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import struct
import tempfile
import threading
import time

import numpy as np
import ovrtx
from PIL import Image
from websockets.exceptions import ConnectionClosed
from websockets.sync.server import serve

from scene import build_scene

CLIENT = threading.Lock()
PRODUCTS = [f"/Render/Camera{i}" for i in range(3)]


def validate_request(request, count):
    worlds = np.asarray(request["worlds"], dtype=np.float64)
    camera = np.asarray(request["camera"], dtype=np.float64)
    if worlds.shape not in ((1, count, 16), (3, count, 16)) or camera.shape != (16,):
        raise ValueError("Invalid transform dimensions")
    if not np.isfinite(worlds).all() or not np.isfinite(camera).all():
        raise ValueError("Transforms must be finite")
    width, height, columns = (request[k] for k in ("width", "height", "columns"))
    if any(type(v) is not int or not 160 <= v <= 640 for v in (width, height)):
        raise ValueError("Render dimensions must be integers in [160, 640]")
    if type(columns) is not int or columns not in (1, len(worlds)):
        raise ValueError("Invalid viewport layout")
    fov, stamp = float(request["fov"]), float(request["time"])
    if not np.isfinite([fov, stamp]).all() or not 1 < fov < 170 or stamp < 0:
        raise ValueError("Invalid camera or timestamp")
    if type(request["sequence"]) is not int or request["sequence"] < 1:
        raise ValueError("Invalid sequence")
    return worlds.reshape(-1, count, 4, 4), camera.reshape(1, 4, 4)


def display_hdr(pixels):
    rgb = np.maximum(np.nan_to_num(pixels[..., :3]), 0.) * 4.
    rgb = np.clip((rgb * (2.51 * rgb + .03)) / (rgb * (2.43 * rgb + .59) + .14), 0, 1)
    srgb = np.where(rgb <= .0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - .055)
    return np.uint8(np.clip(srgb * 255 + .5, 0, 255))


def session(socket, output):
    if not CLIENT.acquire(blocking=False):
        socket.close(1013, "Renderer busy")
        return
    renderer = None
    try:
        with tempfile.TemporaryDirectory(prefix="claw-", dir=output) as directory:
            root = Path(directory)
            data = socket.recv(timeout=60)
            if not isinstance(data, bytes) or data[:4] != b"glTF":
                raise ValueError("First message must be a binary GLB scene")
            (root / "scene.glb").write_bytes(data)
            (output / "latest-scene.glb").write_bytes(data)
            paths = build_scene(root / "scene.glb", root)
            print(json.dumps({"event": "scene", "meshes": len(paths), "bytes": len(data)}), flush=True)
            renderer = ovrtx.Renderer()
            renderer.open_usd(str(root / "scene.usda"))
            socket.send(json.dumps({"type": "ready", "renderer": "OVRTX", "version": ovrtx.__version__}))
            frames = 0
            for payload in socket:
                request = json.loads(payload)
                worlds, camera = validate_request(request, len(paths))
                width, height, columns = (request[k] for k in ("width", "height", "columns"))
                started = time.perf_counter()
                products = PRODUCTS[:len(worlds)]
                camera_paths = ["/World/Camera", "/Lane1/Camera", "/Lane2/Camera"][:len(worlds)]
                renderer.write_attribute(products, "resolution", np.tile(np.array([[width, height]], dtype=np.int32), (len(worlds), 1)))
                vertical = 36 * np.tan(np.deg2rad(request["fov"]) / 2)
                for name, value in (("verticalAperture", vertical), ("horizontalAperture", vertical * width / height)):
                    renderer.write_attribute(camera_paths, name, np.full(len(worlds), value, dtype=np.float32))
                cameras = np.repeat(camera, len(worlds), axis=0)
                cameras[:, 3, 0] += np.arange(len(worlds)) * 4.
                renderer.write_attribute(camera_paths, "omni:xform", cameras, semantic=ovrtx.Semantic.XFORM_MAT4x4)
                composite = Image.new("RGB", (width * columns, height * (len(worlds) // columns)))
                for i, transforms in enumerate(worlds):
                    lane_paths = paths if i == 0 else [p.replace("/World/", f"/Lane{i}/") for p in paths]
                    transforms[:, 3, 0] += i * 4.
                    renderer.write_attribute(lane_paths, "omni:xform", transforms, semantic=ovrtx.Semantic.XFORM_MAT4x4)
                # Separate render products retain independent temporal histories.
                # All products consume the same accepted snapshot in one native step.
                for _ in range(8 if frames == 0 else 1):
                    result = renderer.step(render_products=set(products), delta_time=1 / 60)
                for i, product in enumerate(products):
                    frame = result[product].frames[-1]
                    if len(frame.render_vars) != 1:
                        raise RuntimeError(f"Expected one HDR output, got {list(frame.render_vars)}")
                    mapped = next(iter(frame.render_vars.values())).map(device=ovrtx.Device.CPU)
                    borrowed = np.from_dlpack(mapped)
                    hdr = borrowed.copy()
                    del borrowed
                    mapped.unmap()
                    del mapped, frame
                    image = Image.fromarray(display_hdr(hdr))
                    composite.paste(image, ((i % columns) * width, (i // columns) * height))
                del result
                metadata = {k: request[k] for k in ("sequence", "time")}
                metadata["render_ms"] = (time.perf_counter() - started) * 1000
                buffer = BytesIO()
                composite.save(buffer, format="JPEG", quality=90)
                header = json.dumps(metadata).encode()
                socket.send(struct.pack("<I", len(header)) + header + buffer.getvalue())
                frames += 1
                if frames == 1 or frames % 100 == 0:
                    print(json.dumps({"frames": frames, "views": len(worlds), **metadata}), flush=True)
                    composite.save(output / f"latest-{len(worlds)}-views.jpg", quality=95)
                    (output / "latest.json").write_text(json.dumps({"frames": frames, "views": len(worlds), **metadata}) + "\n")
    except ConnectionClosed:
        pass
    except Exception as error:
        print(json.dumps({"error": str(error)}), flush=True)
        try:
            socket.send(json.dumps({"error": str(error)}))
            socket.close(1011, "Renderer failed")
        except ConnectionClosed:
            pass
    finally:
        if renderer is not None:
            renderer.destroy()
        CLIENT.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    # Loopback and an exact origin list prevent arbitrary sites from using the GPU.
    origins = [f"http://{host}:{port}" for host in ("localhost", "127.0.0.1") for port in (8877, 8878)]
    with serve(lambda socket: session(socket, args.work_dir), "127.0.0.1", 8879,
               origins=origins, max_size=64 * 1024 * 1024, max_queue=1, ping_interval=None) as server:
        print("OVRTX bridge listening at ws://127.0.0.1:8879", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
