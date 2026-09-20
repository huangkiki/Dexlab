"""Render SuperDex poses with MuJoCo; no MuJoCo dynamics."""
from contextlib import contextmanager
import threading
import mujoco

@contextmanager
def open_viewer(model, data):
    """Wait for MuJoCo's render thread before Python unloads GLFW/X11.

    MuJoCo 3.11's Handle.close() only requests exit. Its public handle does not
    expose the thread, so identify the locally pinned launcher's thread target.
    """
    from mujoco import viewer as mj_viewer

    existing = set(threading.enumerate())
    handle = mj_viewer.launch_passive(model, data)
    owned = [
        thread
        for thread in threading.enumerate()
        if thread not in existing
        and getattr(thread, "_target", None) is mj_viewer._launch_internal
    ]
    try:
        yield handle
    finally:
        handle.close()
        for thread in owned:
            thread.join()

def set_frame(model, data, frame):
    data.mocap_pos[:] = frame[:, :3]
    data.mocap_quat[:] = frame[:, [6, 3, 4, 5]]
    mujoco.mj_forward(model, data)
