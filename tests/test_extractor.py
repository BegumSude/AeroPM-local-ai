import pytest

from backend.core.embedder import FOUNDRY_LOCAL_AVAILABLE
from backend.core.extractor import (
    _parse_json_array,
    extract_decisions,
    extract_milestones,
    extract_requirements,
    extract_risks,
    extract_test_results,
)

requires_foundry_local = pytest.mark.skipif(
    not FOUNDRY_LOCAL_AVAILABLE, reason="foundry-local-sdk kurulu degil"
)

SAMPLE_CHUNKS = [
    {"document_name": "risk_register.pdf", "chunk_index": 0, "chunk_text": "Supplier delay may impact schedule."}
]


def test_parse_json_array_handles_valid_object_shape():
    raw = '{"items": [{"description": "risk 1"}]}'
    assert _parse_json_array(raw) == [{"description": "risk 1"}]


def test_parse_json_array_handles_markdown_code_fence():
    raw = '```json\n{"items": [{"description": "risk 1"}]}\n```'
    assert _parse_json_array(raw) == [{"description": "risk 1"}]


def test_parse_json_array_handles_leading_prose():
    raw = 'Here are the risks I found:\n{"items": [{"description": "risk 1"}]}'
    assert _parse_json_array(raw) == [{"description": "risk 1"}]


def test_parse_json_array_handles_empty_items():
    assert _parse_json_array('{"items": []}') == []


def test_parse_json_array_handles_bare_array():
    raw = '[{"description": "risk 1"}]'
    assert _parse_json_array(raw) == [{"description": "risk 1"}]


def test_parse_json_array_handles_malformed_json():
    raw = '{"items": [{"description": "incomplete"'
    assert _parse_json_array(raw) == []


def test_parse_json_array_repairs_unquoted_keys():
    raw = '{\n  "items": [\n    {\n      "description": "risk",\nrisk_level: "High",\nevidence_text: "text"\n    }\n  ]\n}'
    assert _parse_json_array(raw) == [{"description": "risk", "risk_level": "High", "evidence_text": "text"}]


def test_parse_json_array_repairs_real_foundry_local_unquoted_keys_quirk():
    # Captured verbatim from a real phi-3.5-mini response: several keys after
    # the first line of an object come back unquoted, and one key name is
    # corrupted ("dictate_risk_level" instead of "risk_level"). The repair
    # recovers every field except the corrupted key name itself.
    raw = (
        ' ```json\n{\n  "items": [\n    {\n      "description": "GPS antenna supplier reports a '
        '6-week manufacturing delay due to a component shortage.",\n      "probability": "High",\n'
        '      "impact": "High",\ndictate_risk_level: "Critical",\naffected_milestone: '
        '"Integration Testing",\nresponsible: "Procurement Team (Elena Kovacs)",\nevidence_text: '
        '"The GPS antenna supplier has reported a 6-week manufacturing delay due to a component '
        'shortage."\n    }\n  ]\n}\n```'
    )
    result = _parse_json_array(raw)
    assert len(result) == 1
    assert result[0]["description"] == "GPS antenna supplier reports a 6-week manufacturing delay due to a component shortage."
    assert result[0]["affected_milestone"] == "Integration Testing"
    assert result[0]["evidence_text"] == "The GPS antenna supplier has reported a 6-week manufacturing delay due to a component shortage."


def test_parse_json_array_handles_non_list_items():
    assert _parse_json_array('{"items": "not a list"}') == []


def test_parse_json_array_handles_non_json_text():
    assert _parse_json_array("I could not find any risks in this document.") == []


def test_parse_json_array_skips_non_dict_entries():
    raw = '{"items": [{"description": "risk 1"}, "not a dict", 5]}'
    assert _parse_json_array(raw) == [{"description": "risk 1"}]


def test_parse_json_array_recovers_valid_items_when_one_item_is_unrecoverably_corrupted():
    # Captured verbatim from a real phi-3.5-mini response extracting 5
    # requirements: item 1 is well-formed, item 2 has unquoted keys (fixed by
    # the bare-key repair), and items 3-5 have a colon swallowed inside a
    # quoted key with no value quotes at all ("evidence_text:\n..."), which
    # is not recoverable. The whole array is invalid JSON as a single
    # candidate; per-item recovery should still return the 2 good items
    # instead of losing all 5.
    raw = (
        ' {"items": [\n  {\n    "requirement_text": "The avionics system shall report GPS position '
        'accuracy within 2 meters CEP.",\n    "status": "In progress",\n    "evidence_text": '
        '"REQ-001: The avionics system shall report GPS position accuracy within 2 meters CEP '
        '(Circular Error Probable). Status: In progress."\n  },\n  {\n    "requirement_text": "The '
        'flight management system shall interface with the legacy autopilot module via an ARINC '
        '429 data bus.",\n    "status": "In progress",\noptionality: "null",\nevidence_text: '
        '"REQ-002: The flight management system shall interface with the legacy autopilot module '
        'via an ARINC 429 data bus. Status: In progress."\n  },\n  {\n    "requirement_text": "The '
        'system shall log all avionics events with timestamp accuracy of 10 milliseconds or '
        'better.",\n    "status": "Completed",\n    "evidence_text:\nREQ-003: The system shall log '
        'all avionics events with timestamp accuracy of 10 milliseconds or better. Status: '
        'Completed."\n  },\n  {\n    "requirement_text": "The cabin display unit shall support a '
        'night-vision-compatible lighting mode.",\n    "status": "Not started",\n    '
        '"evidence_text:\nREQ-004: The cabin display unit shall support a night-vision-compatible '
        'lighting mode. Status: Not started."\n  },\n  {\n    "requirement_text": "The system shall '
        'complete its cold boot sequence in under 45 seconds.",\n    "status": "In progress",\n    '
        '"evidence_text:\nREQ-005: The system shall complete its cold boot sequence in under 45 '
        'seconds. Status: In progress."\n  }\n]}'
    )
    result = _parse_json_array(raw)

    assert len(result) == 2
    assert result[0]["requirement_text"] == "The avionics system shall report GPS position accuracy within 2 meters CEP."
    assert result[1]["optionality"] == "null"
    assert result[1]["evidence_text"] == (
        "REQ-002: The flight management system shall interface with the legacy autopilot module "
        "via an ARINC 429 data bus. Status: In progress."
    )


def test_extract_risks_returns_empty_list_for_empty_chunks():
    assert extract_risks([]) == []


def test_extract_risks_calls_generate_structured_and_parses_result(monkeypatch):
    monkeypatch.setattr(
        "backend.core.extractor.generate_structured",
        lambda system_prompt, user_content: '{"items": [{"description": "supplier delay"}]}',
    )
    result = extract_risks(SAMPLE_CHUNKS)
    assert result == [{"description": "supplier delay"}]


def test_extract_risks_returns_empty_list_when_generate_structured_raises(monkeypatch):
    def raise_error(system_prompt, user_content):
        raise RuntimeError("Operation was cancelled")

    monkeypatch.setattr("backend.core.extractor.generate_structured", raise_error)
    assert extract_risks(SAMPLE_CHUNKS) == []


def test_extract_risks_includes_source_and_chunk_index_in_prompt_input(monkeypatch):
    captured = {}

    def fake_generate_structured(system_prompt, user_content):
        captured["user_content"] = user_content
        return '{"items": []}'

    monkeypatch.setattr("backend.core.extractor.generate_structured", fake_generate_structured)
    extract_risks(SAMPLE_CHUNKS)

    assert "risk_register.pdf" in captured["user_content"]
    assert "Supplier delay may impact schedule." in captured["user_content"]


@requires_foundry_local
def test_extract_risks_returns_list_with_real_foundry_local():
    result = extract_risks(SAMPLE_CHUNKS)
    assert isinstance(result, list)


@requires_foundry_local
def test_extract_decisions_returns_list_with_real_foundry_local():
    chunks = [{"document_name": "meeting_minutes.pdf", "chunk_index": 0, "chunk_text": "We decided to add a buffer."}]
    result = extract_decisions(chunks)
    assert isinstance(result, list)


@requires_foundry_local
def test_extract_requirements_returns_list_with_real_foundry_local():
    chunks = [{"document_name": "requirements.pdf", "chunk_index": 0, "chunk_text": "The system shall log all events."}]
    result = extract_requirements(chunks)
    assert isinstance(result, list)


@requires_foundry_local
def test_extract_milestones_returns_list_with_real_foundry_local():
    chunks = [{"document_name": "project_plan.pdf", "chunk_index": 0, "chunk_text": "Integration testing completes in March."}]
    result = extract_milestones(chunks)
    assert isinstance(result, list)


@requires_foundry_local
def test_extract_test_results_returns_list_with_real_foundry_local():
    chunks = [{"document_name": "test_report.pdf", "chunk_index": 0, "chunk_text": "Test TC-01 passed on the GPS module."}]
    result = extract_test_results(chunks)
    assert isinstance(result, list)
