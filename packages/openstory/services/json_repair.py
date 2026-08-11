import json
import re
from typing import Any

JSON_FENCE = re.compile(
    r"^```(?:json)?[ \t]*\r?\n(?P<body>.*)\r?\n```$",
    re.IGNORECASE | re.DOTALL,
)
OPEN_TO_CLOSE = {"{": "}", "[": "]"}


class StructuredOutputError(ValueError):
    def __init__(self, message: str, source_text: str) -> None:
        self.preview = source_text.strip()[:200]
        super().__init__(f"{message}. Preview: {self.preview!r}")


def extract_json_value(text: str) -> Any:
    stripped = text.strip()
    fence = JSON_FENCE.fullmatch(stripped)
    if fence is not None:
        stripped = fence.group("body").strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    for start, character in enumerate(stripped):
        if character not in OPEN_TO_CLOSE:
            continue
        end = _balanced_json_end(stripped, start)
        if end is None:
            continue
        try:
            return json.loads(stripped[start:end])
        except json.JSONDecodeError:
            continue

    raise StructuredOutputError("Could not extract a valid JSON object or array", text)


def _balanced_json_end(text: str, start: int) -> int | None:
    stack = [OPEN_TO_CLOSE[text[start]]]
    in_string = False
    escaped = False

    for index in range(start + 1, len(text)):
        character = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue

        if character == '"':
            in_string = True
        elif character in OPEN_TO_CLOSE:
            stack.append(OPEN_TO_CLOSE[character])
        elif character in "}]":
            if character != stack[-1]:
                return None
            stack.pop()
            if not stack:
                return index + 1
    return None
