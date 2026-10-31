"""Read-only RoboAPI adapter CLI.

The key is read from ``POKE_ROBOAPI_KEY`` so it never appears in shell history,
output files, or repository records. ``infer`` performs one non-executing policy
call and immediately reports an interrupted empty action, matching the upstream
quick-start contract.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dexlab.roboapi_poke import (
    DEFAULT_BASE_URL,
    PokeSession,
    RoboApiClient,
)


def _client(args: argparse.Namespace) -> RoboApiClient:
    key = os.environ.get("POKE_ROBOAPI_KEY")
    if not key:
        raise SystemExit("Set POKE_ROBOAPI_KEY before using the adapter")
    return RoboApiClient(key, base_url=args.base_url, timeout_s=args.timeout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=float, default=60.0)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("models")

    schema_parser = subparsers.add_parser("schema")
    schema_parser.add_argument("--model", required=True)

    infer_parser = subparsers.add_parser("infer")
    infer_parser.add_argument("--model", required=True)
    infer_parser.add_argument("--instruction", required=True)
    infer_parser.add_argument("--image", required=True, type=Path)
    infer_parser.add_argument("--state", required=True, type=Path)

    args = parser.parse_args(argv)
    client = _client(args)

    if args.command == "models":
        print(json.dumps({"data": client.models()}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "schema":
        print(json.dumps(client.model_schema(args.model), ensure_ascii=False, indent=2))
        return 0

    state = json.loads(args.state.read_text())
    session = PokeSession(client, args.model)
    session.start(args.instruction)
    try:
        actions = session.infer(state, args.image)
        print(
            json.dumps(
                {
                    "session_id": session.session_id,
                    "request_id": session.last_request_id,
                    "next_turn": session.next_turn,
                    "action_rows": len(actions),
                    "first_action": actions[0],
                    "executed_steps": 0,
                    "status": "interrupted",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    finally:
        session.close("stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
