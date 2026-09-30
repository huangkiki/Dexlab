"""Native PhysX surface cloth in the isolated, pinned Isaac Sim worker.

Uses UniSim's runtime discovery; owns a separate cloth scene because the pinned
UniSim robot adapter does not expose surface nodes or cloth boundary conditions.
"""

import json
import socket
import subprocess
import tempfile
from dataclasses import asdict
from multiprocessing.connection import Connection
from pathlib import Path

import numpy as np


class PhysXCloth:
    """One native step per request; only zero external nodal forces are supported."""

    def __init__(self, case, dt, *, device, iterations):
        if case.experiment == "extension":
            raise NotImplementedError(
                "PhysX 107.3 surface tensors have no nodal-force API; "
                "the prescribed-force extension protocol is unsupported"
            )
        if not device.startswith("cuda:") or not device[5:].isdigit():
            raise ValueError("PhysX surface cloth requires --device cuda:N")
        from unisim.backend.isaacsim.dependencies import (
            build_worker_env,
            resolve_isaacsim_runtime,
        )

        runtime = resolve_isaacsim_runtime()
        self._directory = tempfile.TemporaryDirectory(prefix="dexlab-physx-cloth-")
        self.artifacts = Path(self._directory.name)
        self._log = tempfile.TemporaryFile()  # noqa: SIM115 -- owned until close()
        self._process = None
        self._connection = None
        self.worker_log = ""
        self.shutdown = {"stopped": False, "exit_code": None}
        vertices, triangles, masses = case.mesh()
        self._shape = vertices.shape
        host, child = socket.socketpair()
        self._connection = Connection(host.detach())
        try:
            self._process = subprocess.Popen(
                [
                    str(runtime.python),
                    str(Path(__file__).with_name("physx_cloth_worker.py")),
                    str(child.fileno()),
                ],
                pass_fds=(child.fileno(),),
                env=build_worker_env(runtime),
                stdin=subprocess.DEVNULL,
                stdout=self._log,
                stderr=self._log,
            )
            child.close()
            answer = self._request(
                {
                    "op": "init",
                    "case": asdict(case),
                    "dt": dt,
                    "device": device,
                    "iterations": iterations,
                    "directory": str(self.artifacts),
                    "vertices": vertices.tolist(),
                    "triangles": triangles.tolist(),
                    "masses": masses.tolist(),
                    "pins": case.pins.tolist(),
                },
                timeout=120,
            )
            self.metadata = answer["metadata"]
            self._state = self._decode_state(answer)
        except BaseException as error:
            child.close()
            self.close()
            if isinstance(error, Exception):
                raise RuntimeError(  # noqa: TRY004 -- propagate a native failure, not a type error
                    f"{error}\nNative initialization log:\n{self.worker_log}"
                ) from error
            raise

    def _request(self, payload, *, timeout=20):
        self._connection.send_bytes(json.dumps(payload, allow_nan=False).encode())
        if not self._connection.poll(timeout):
            raise TimeoutError("Native PhysX cloth worker did not reply")
        answer = json.loads(self._connection.recv_bytes())
        if "error" in answer:
            raise RuntimeError(answer["error"])
        return answer

    def _decode_state(self, answer):
        state = tuple(
            np.asarray(answer[key], dtype=float) for key in ("positions", "velocities")
        )
        if any(
            array.shape != self._shape or not np.isfinite(array).all()
            for array in state
        ):
            raise ValueError("Malformed or nonfinite native cloth observation")
        return state

    def observe(self):
        return tuple(array.copy() for array in self._state)

    def step(self, forces):
        forces = np.asarray(forces)
        if forces.shape != self._shape or not np.isfinite(forces).all():
            raise ValueError("Expected finite per-node force array")
        if np.any(forces):
            raise NotImplementedError(
                "Native PhysX surface nodal-force upload is unavailable"
            )
        self._state = self._decode_state(self._request({"op": "step"}))

    def close(self):
        if self._process is not None:
            process = self._process
            if process.poll() is None:
                try:
                    self.shutdown["stopped"] = self._request({"op": "stop"}) == {
                        "stopped": True
                    }
                    process.wait(timeout=20)
                except (
                    OSError,
                    EOFError,
                    RuntimeError,
                    TimeoutError,
                    subprocess.TimeoutExpired,
                ):
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            self.shutdown["exit_code"] = process.returncode
            self._process = None
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if not self._log.closed:
            self._log.seek(0)
            self.worker_log = self._log.read().decode(errors="replace")
            self._log.close()
        self._directory.cleanup()
