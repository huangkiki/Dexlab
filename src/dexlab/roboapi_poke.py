"""Minimal, dependency-free client and control loop for the Poke RoboAPI.

The module deliberately avoids the ``openai`` SDK and external HTTP packages so
that a DexLab task can connect to a policy server with only the Python standard
library. API keys are read at runtime and are never written to output, records,
or configuration files.
"""

from __future__ import annotations

import base64
import json
import math
import mimetypes
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


DEFAULT_BASE_URL = "https://api.pokebot.com/v1"
STATE_LENGTH = 8
GRIPPER_INDEX = 7
QUATERNION_SLICE = slice(3, 7)


class RoboApiError(RuntimeError):
    """An upstream HTTP or protocol error with the status and response body."""

    def __init__(self, message: str, *, status: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status = status
        self.payload = payload


class PokeProtocolError(RoboApiError):
    """The response passed HTTP but does not satisfy the Poke action contract."""


def validate_state(state: Sequence[float]) -> list[float]:
    values = [float(value) for value in state]
    if len(values) != STATE_LENGTH:
        raise ValueError(f"state must contain {STATE_LENGTH} numbers, got {len(values)}")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("state must contain only finite numbers")
    quaternion_norm = math.sqrt(sum(value * value for value in values[QUATERNION_SLICE]))
    if not math.isclose(quaternion_norm, 1.0, abs_tol=1e-3):
        raise ValueError("state quaternion must be normalized")
    if not 0.0 <= values[GRIPPER_INDEX] <= 1.0:
        raise ValueError("state gripper value must be in [0, 1]")
    return values


def validate_output(output: Any) -> list[list[float]]:
    if not isinstance(output, list) or not output:
        raise PokeProtocolError("execute_actions output must be a nonempty list")
    rows: list[list[float]] = []
    for row in output:
        if not isinstance(row, list) or len(row) != STATE_LENGTH:
            raise PokeProtocolError(
                f"each action row must contain {STATE_LENGTH} numbers"
            )
        values = [float(value) for value in row]
        if not all(math.isfinite(value) for value in values):
            raise PokeProtocolError("action rows must contain only finite numbers")
        if not math.isclose(math.sqrt(sum(v * v for v in values[QUATERNION_SLICE])), 1.0, abs_tol=1e-3):
            raise PokeProtocolError("action quaternions must be normalized")
        if not -0.01 <= values[GRIPPER_INDEX] <= 1.01:
            raise PokeProtocolError("action gripper values are outside the allowed range")
        rows.append(values)
    return rows


def _image_data_url(path: str | Path) -> str:
    image = Path(path)
    mime_type = mimetypes.guess_type(image.name)[0]
    if mime_type not in ("image/png", "image/jpeg"):
        raise ValueError("RoboAPI images must be PNG or JPEG")
    encoded = base64.b64encode(image.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _user_message(instruction: str, state: Sequence[float], image_path: str | Path) -> dict[str, Any]:
    text = json.dumps({"instruction": instruction, "state": validate_state(state)})
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": _image_data_url(image_path)}},
        ],
    }


class RoboApiClient:
    """Thin HTTP client for the Poke RoboAPI cloud contract."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout_s: float = 60.0,
    ):
        if not api_key:
            raise ValueError("Poke RoboAPI key must not be empty")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _request(self, method: str, path: str, body: Any = None) -> tuple[Any, str | None]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload, response.headers.get("X-Request-ID")
        except urllib.error.HTTPError as error:
            raw = error.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = raw
            raise RoboApiError(
                f"Poke RoboAPI request failed with HTTP {error.code}",
                status=error.code,
                payload=payload,
            ) from error
        except urllib.error.URLError as error:
            raise RoboApiError(f"Poke RoboAPI request failed: {error.reason}") from error

    def models(self) -> list[dict[str, Any]]:
        payload, _ = self._request("GET", "/models")
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            raise PokeProtocolError("/models did not return a data list")
        return data

    def model_schema(self, model_id: str) -> dict[str, Any]:
        payload, _ = self._request("GET", f"/models/{model_id}/schema")
        if not isinstance(payload, dict):
            raise PokeProtocolError("/models schema did not return an object")
        return payload

    def create_session(self, model_id: str) -> dict[str, Any]:
        payload, _ = self._request("POST", "/sessions", {"model": model_id})
        if not isinstance(payload, dict) or not payload.get("id"):
            raise PokeProtocolError("/sessions did not return a session id")
        return payload

    def chat_completion(
        self,
        *,
        model_id: str,
        session_id: str,
        turn: int,
        instruction: str,
        state: Sequence[float],
        image_path: str | Path,
        preceding_messages: Iterable[dict[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], str | None]:
        messages = list(preceding_messages or [])
        messages.append(_user_message(instruction, state, image_path))
        payload = {
            "model": model_id,
            "metadata": {"session_id": session_id, "turn": str(turn)},
            "messages": messages,
        }
        return self._request("POST", "/chat/completions", payload)

    def close_session(
        self,
        session_id: str,
        *,
        reason: str,
        messages: Sequence[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload, _ = self._request(
            "POST",
            f"/sessions/{session_id}/close",
            {"reason": reason, "messages": list(messages or [])},
        )
        if not isinstance(payload, dict):
            raise PokeProtocolError("/sessions close did not return an object")
        return payload


def parse_actions(response: dict[str, Any]) -> tuple[list[list[float]], dict[str, Any], str]:
    """Return the validated action chunk, assistant message, and tool call id."""

    try:
        message = response["choices"][0]["message"]
        calls = message.get("tool_calls") or []
    except (KeyError, IndexError, TypeError) as error:
        raise PokeProtocolError("completion response is missing choices[0].message") from error
    execute = [call for call in calls if call.get("function", {}).get("name") == "execute_actions"]
    if len(execute) != 1:
        raise PokeProtocolError("expected exactly one execute_actions tool call")
    call = execute[0]
    try:
        arguments = json.loads(call["function"]["arguments"])
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise PokeProtocolError("execute_actions arguments are not valid JSON") from error
    output = validate_output(arguments.get("output"))
    return output, message, call["id"]


class PokeSession:
    """Stateful Poke RoboAPI session that owns assistant/tool message history."""

    def __init__(self, client: RoboApiClient, model_id: str):
        self.client = client
        self.model_id = model_id
        self.session_id: str | None = None
        self.instruction: str | None = None
        self.next_turn: int | None = None
        self.last_assistant: dict[str, Any] | None = None
        self.last_tool_call_id: str | None = None
        self.last_request_id: str | None = None
        self._pending_feedback: list[dict[str, Any]] = []

    def start(self, instruction: str) -> str:
        if not instruction.strip():
            raise ValueError("task instruction must not be empty")
        session = self.client.create_session(self.model_id)
        self.session_id = session["id"]
        self.next_turn = int(session.get("next_turn", 1))
        self.instruction = instruction
        self.last_assistant = None
        self.last_tool_call_id = None
        self._pending_feedback = []
        return self.session_id

    def infer(self, state: Sequence[float], image_path: str | Path) -> list[list[float]]:
        if self.session_id is None or self.next_turn is None or self.instruction is None:
            raise RuntimeError("start() must be called before infer()")
        response, request_id = self.client.chat_completion(
            model_id=self.model_id,
            session_id=self.session_id,
            turn=self.next_turn,
            instruction=self.instruction,
            state=state,
            image_path=image_path,
            preceding_messages=self._pending_feedback,
        )
        actions, assistant, tool_call_id = parse_actions(response)
        try:
            self.next_turn = int(response["metadata"]["next_turn"])
        except (KeyError, TypeError, ValueError) as error:
            raise PokeProtocolError("completion response is missing metadata.next_turn") from error
        self.last_assistant = assistant
        self.last_tool_call_id = tool_call_id
        self.last_request_id = request_id
        self._pending_feedback = []
        return actions

    def report_execution(self, *, executed_steps: int, status: str) -> None:
        if self.last_assistant is None or self.last_tool_call_id is None:
            raise RuntimeError("infer() must produce actions before report_execution()")
        if status not in ("completed", "interrupted"):
            raise ValueError("execution status must be completed or interrupted")
        if executed_steps < 0:
            raise ValueError("executed_steps cannot be negative")
        tool_message = {
            "role": "tool",
            "tool_call_id": self.last_tool_call_id,
            "content": json.dumps(
                {"executed_steps": executed_steps, "status": status}
            ),
        }
        self._pending_feedback = [self.last_assistant, tool_message]

    def close(self, reason: str = "stopped") -> dict[str, Any]:
        if self.session_id is None:
            raise RuntimeError("start() must be called before close()")
        messages = self._pending_feedback
        if self.last_assistant is not None and self.last_tool_call_id is not None and not messages:
            self.report_execution(executed_steps=0, status="interrupted")
            messages = self._pending_feedback
        return self.client.close_session(self.session_id, reason=reason, messages=messages)


@dataclass(frozen=True)
class PokeActionChunk:
    actions: tuple[tuple[float, ...], ...]
    request_id: str | None
