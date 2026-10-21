"""Keep a native setup error from cascading through data-dependent tests."""

import json


def require_completed_run(output):
    receipt = json.loads((output / "run.json").read_text())
    if receipt.get("status") != "completed":
        raise RuntimeError(
            f"Native fixture failed at {output} (status={receipt.get('status')!r}):\n"
            f"{receipt.get('error', 'Run did not complete; inspect run.json')}"
        )
