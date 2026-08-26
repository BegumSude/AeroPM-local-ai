import json
import re

from backend.core.generator import generate_structured
from backend.prompts.system_prompts import (
    DECISION_EXTRACTION_PROMPT,
    MILESTONE_EXTRACTION_PROMPT,
    REQUIREMENT_EXTRACTION_PROMPT,
    RISK_EXTRACTION_PROMPT,
    TEST_RESULT_EXTRACTION_PROMPT,
)

_JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)
_JSON_ARRAY_PATTERN = re.compile(r"\[.*\]", re.DOTALL)
_BARE_KEY_PATTERN = re.compile(r'(?m)^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:')
_ITEMS_ARRAY_PATTERN = re.compile(r'"items"\s*:\s*\[(.*)\]', re.DOTALL)


def _quote_bare_keys(text: str) -> str:
    # Small local models occasionally emit unquoted object keys (e.g.
    # `risk_level: "High"` instead of `"risk_level": "High"`); this repairs
    # that specific, commonly observed quirk without touching already-valid JSON.
    return _BARE_KEY_PATTERN.sub(r'\1"\2":', text)


def _try_parse_full(text: str) -> list[dict] | None:
    for candidate in (text, _quote_bare_keys(text)):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict):
            items = parsed.get("items", [])
        elif isinstance(parsed, list):
            items = parsed
        else:
            continue

        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]

    return None


def _split_top_level_objects(text: str) -> list[str]:
    objects = []
    depth = 0
    start = None
    in_string = False
    escape = False
    for i, char in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = i
            depth += 1
        elif char == "}":
            depth = max(depth - 1, 0)
            if depth == 0 and start is not None:
                objects.append(text[start:i + 1])
                start = None
    return objects


def _extract_items_array_content(text: str) -> str:
    match = _ITEMS_ARRAY_PATTERN.search(text)
    if match is not None:
        return match.group(1)
    array_match = _JSON_ARRAY_PATTERN.search(text)
    if array_match is not None:
        return array_match.group(0)[1:-1]
    return ""


def _recover_items_individually(text: str) -> list[dict]:
    # A single corrupted item (a common small-model quirk: a stray colon or
    # missing quote inside one array entry) makes the whole array invalid
    # JSON, which would otherwise lose every item in the batch. Recover
    # whatever individual items still parse rather than discarding all of them.
    items = []
    for candidate_object in _split_top_level_objects(text):
        for attempt in (candidate_object, _quote_bare_keys(candidate_object)):
            try:
                parsed = json.loads(attempt)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                items.append(parsed)
                break
    return items


def _parse_json_array(raw: str) -> list[dict]:
    stripped = raw.strip()
    candidates = [stripped]

    object_match = _JSON_OBJECT_PATTERN.search(stripped)
    if object_match is not None:
        candidates.append(object_match.group(0))

    array_match = _JSON_ARRAY_PATTERN.search(stripped)
    if array_match is not None:
        candidates.append(array_match.group(0))

    for candidate in candidates:
        result = _try_parse_full(candidate)
        if result is not None:
            return result

    items_content = _extract_items_array_content(candidates[-1])
    return _recover_items_individually(items_content)


def _build_extraction_input(chunks: list[dict]) -> str:
    parts = []
    for chunk in chunks:
        document_name = chunk.get("document_name", "unknown")
        chunk_index = chunk.get("chunk_index", "?")
        chunk_text = chunk.get("chunk_text", "")
        parts.append(f"[Source: {document_name}, chunk {chunk_index}]\n{chunk_text}")
    return "\n\n".join(parts)


def _extract(system_prompt: str, chunks: list[dict]) -> list[dict]:
    if not chunks:
        return []

    user_content = _build_extraction_input(chunks)
    try:
        raw = generate_structured(system_prompt, user_content)
    except Exception:
        # Foundry Local can raise transport/runtime errors (e.g. a cancelled
        # completion) independent of malformed output; treat either the same
        # way as unparseable output: no items found for this batch.
        return []
    return _parse_json_array(raw)


def extract_risks(chunks: list[dict]) -> list[dict]:
    return _extract(RISK_EXTRACTION_PROMPT, chunks)


def extract_decisions(chunks: list[dict]) -> list[dict]:
    return _extract(DECISION_EXTRACTION_PROMPT, chunks)


def extract_requirements(chunks: list[dict]) -> list[dict]:
    return _extract(REQUIREMENT_EXTRACTION_PROMPT, chunks)


def extract_milestones(chunks: list[dict]) -> list[dict]:
    return _extract(MILESTONE_EXTRACTION_PROMPT, chunks)


def extract_test_results(chunks: list[dict]) -> list[dict]:
    return _extract(TEST_RESULT_EXTRACTION_PROMPT, chunks)
