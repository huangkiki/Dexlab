"""Dependency-free contract tests for the Poke RoboAPI adapter."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dexlab.roboapi_poke import (
    PokeSession,
    RoboApiClient,
    validate_output,
    validate_state,
)


def _png_bytes() -> bytes:
    # One-pixel transparent PNG used only to exercise the data URL path.
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c626001000000ffff03000006000557bfabd40000000049454e44ae426082"
    )


class _Handler(BaseHTTPRequestHandler):
    def _send(self, status, payload, request_id=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if request_id:
            self.send_header("X-Request-ID", request_id)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        if self.path == "/models":
            self._send(200, {"data": [{"id": "poke-aurora-preview"}]})
        elif self.path.startswith("/models/") and self.path.endswith("/schema"):
            self._send(200, {"id": "vision-input-v1", "model": "poke-aurora-preview"})
        else:
            self._send(404, {"error": {"message": "not found"}})

    def do_POST(self):
        payload = self._body()
        if self.path == "/sessions":
            self.server.calls.append(("create_session", payload))
            self._send(200, {"id": "session_1", "model": payload["model"], "status": "open", "next_turn": 1})
            return
        if self.path == "/chat/completions":
            self.server.calls.append(("chat_completion", payload))
            turn = int(payload["metadata"]["turn"])
            tool_call_id = f"call_{turn:032x}"
            response = {
                "id": "chatcmpl-test",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "tool_calls",
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": tool_call_id,
                                    "type": "function",
                                    "function": {
                                        "name": "execute_actions",
                                        "arguments": json.dumps(
                                            {"output": [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.5]]}
                                        ),
                                    },
                                }
                            ],
                        },
                    }
                ],
                "metadata": {
                    "session_id": payload["metadata"]["session_id"],
                    "turn": str(turn),
                    "next_turn": str(turn + 1),
                },
            }
            self._send(200, response, request_id="a" * 32)
            return
        if self.path.startswith("/sessions/") and self.path.endswith("/close"):
            self.server.calls.append(("close_session", payload))
            self._send(200, {"id": "session_1", "status": "closed", "messages": payload.get("messages", [])})
            return
        self._send(404, {"error": {"message": "not found"}})

    def log_message(self, *_):
        return


class RoboApiPokeTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.server.calls = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        port = self.server.server_address[1]
        self.client = RoboApiClient("sk-test", base_url=f"http://127.0.0.1:{port}")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def test_state_and_output_validation(self):
        self.assertEqual(validate_state([0, 0, 0, 0, 0, 0, 1, 0.5]), [0, 0, 0, 0, 0, 0, 1, 0.5])
        with self.assertRaises(ValueError):
            validate_state([0, 0, 0, 0, 0, 0, 0, 0.5])
        self.assertEqual(
            validate_output([[0, 0, 0, 0, 0, 0, 1, 0.5]]),
            [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.5]],
        )

    def test_models_schema_and_session_roundtrip(self):
        self.assertEqual(self.client.models(), [{"id": "poke-aurora-preview"}])
        self.assertIn("model", self.client.model_schema("poke-aurora-preview"))

        session = PokeSession(self.client, "poke-aurora-preview")
        session.start("Pick up the block")
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "input.png"
            image.write_bytes(_png_bytes())
            actions = session.infer([0, 0, 0, 0, 0, 0, 1, 0.5], image)
        self.assertEqual(actions, [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.5]])
        session.report_execution(executed_steps=1, status="completed")
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "input.png"
            image.write_bytes(_png_bytes())
            session.infer([0, 0, 0, 0, 0, 0, 1, 0.5], image)
        chat_payload = next(
            call
            for name, call in self.server.calls
            if name == "chat_completion" and call["metadata"]["turn"] == "2"
        )
        roles = [message["role"] for message in chat_payload["messages"]]
        self.assertEqual(roles, ["assistant", "tool", "user"])
        closed = session.close()
        self.assertEqual(closed["status"], "closed")


if __name__ == "__main__":
    unittest.main()
