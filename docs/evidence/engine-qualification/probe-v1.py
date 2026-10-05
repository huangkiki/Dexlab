"""Small GPU runtime/contact probe; not task or performance qualification."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

XML = """<mujoco>
  <option timestep="0.002" solver="Newton" iterations="50"/>
  <worldbody>
    <geom type="plane" size="2 2 .1"/>
    <body pos="0 0 .5"><freejoint/>
      <geom type="sphere" size=".05" mass=".1" friction=".8 .005 .0001"/>
    </body>
  </worldbody>
</mujoco>"""

EXPECTED = {"mujoco": "3.14.0", "mujoco-warp": "3.14.0", "warp-lang": "1.17.0"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True, help="Explicit Warp CUDA device")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Preserve prior receipts; choose a new output")
    import mujoco
    import mujoco_warp as mjw
    import numpy as np
    import warp as wp

    started = time.monotonic()
    receipt = {
        "scope": "GPU runtime/contact smoke only; not apple/cloth or speed qualification",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_sha256": hashlib.sha256(XML.encode()).hexdigest(),
        "versions": {n: importlib.metadata.version(n) for n in
                     ("mujoco", "mujoco-warp", "warp-lang")},
        "native_mujoco": mujoco.mj_versionString(),
        "worlds": 32,
        "steps": 1000,
        "timestep_s": .002,
        "parameter_source": "Synthetic 0.1 kg sphere, 0.05 m radius, gravity -9.81 m/s²; explicit smoke tolerances, no material calibration",
    }
    try:
        if receipt["versions"] != EXPECTED:
            raise ValueError("Runtime differs from this probe's frozen stable versions")
        if receipt["native_mujoco"] != EXPECTED["mujoco"]:
            raise ValueError("Loaded native library differs from the binding")
        wp.config.kernel_cache_dir = str(args.output.parent / ("warp-cache-" + args.device.replace(":", "-")))
        wp.init()
        device = wp.get_device(args.device)
        if not device.is_cuda:
            raise ValueError("GPU probe refuses CPU fallback")
        with wp.ScopedDevice(device):
            model = mujoco.MjModel.from_xml_string(XML)
            gpu_model = mjw.put_model(model)
            data = mjw.make_data(model, nworld=32, nconmax=8, njmax=32)
            # Compile and warm on disposable state, then reset before capture.
            mjw.step(gpu_model, data)
            wp.synchronize_device(device)
            data = mjw.make_data(model, nworld=32, nconmax=8, njmax=32)
            with wp.ScopedCapture() as capture:
                mjw.step(gpu_model, data)
            minimum = float("inf")
            finite = True
            for _ in range(1000):
                wp.capture_launch(capture.graph)
                # Every-step diagnostic sampling; deliberately not a speed test.
                qpos = data.qpos.numpy()
                finite &= bool(np.isfinite(qpos).all())
                minimum = min(minimum, float(qpos[:, 2].min()))
            wp.synchronize_device(device)
            qvel = data.qvel.numpy()
            times = data.time.numpy()
            receipt["metrics"] = {
                "minimum_center_height_m": minimum,
                "maximum_final_height_error_m": float(np.max(np.abs(qpos[:, 2] - .05))),
                "maximum_final_speed_m_s": float(np.linalg.norm(qvel[:, :3], axis=1).max()),
                "final_time_min_s": float(times.min()),
                "final_time_max_s": float(times.max()),
            }
            receipt["precision"] = str(qpos.dtype)
            receipt["solver"] = "MuJoCo Newton constraint solver; not Newton Physics"
            receipt["checks"] = {
                "native_matches_binding": receipt["native_mujoco"] == receipt["versions"]["mujoco"],
                "finite": finite and bool(np.isfinite(qvel).all()),
                "complete_time": bool(np.allclose(times, 2., rtol=0, atol=1e-4)),
                "no_gross_plane_crossing": minimum >= .045,
                "supported_final_height": bool(np.all(np.abs(qpos[:, 2] - .05) < .002)),
                "settled": bool(np.all(np.linalg.norm(qvel[:, :3], axis=1) < .02)),
            }
            receipt["passed"] = all(receipt["checks"].values())
    except Exception as exc:
        receipt.update(passed=False, error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        receipt["whole_probe_wall_s"] = time.monotonic() - started
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x") as stream:
            json.dump(receipt, stream, indent=2, allow_nan=False)
            stream.write("\n")
    if not receipt["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
