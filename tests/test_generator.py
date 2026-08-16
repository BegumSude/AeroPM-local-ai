import pytest

from backend.core.generator import (
    FOUNDRY_LOCAL_AVAILABLE,
    NO_CONTEXT_ANSWER,
    build_messages,
    generate_answer,
)
from backend.prompts.system_prompts import SYSTEM_PROMPT

requires_foundry_local = pytest.mark.skipif(
    not FOUNDRY_LOCAL_AVAILABLE, reason="foundry-local-sdk kurulu degil"
)


def test_system_prompt_is_used_as_system_message():
    context_chunks = [{"document_name": "a.txt", "chunk_index": 0, "chunk_text": "metin"}]
    messages = build_messages("soru", context_chunks)
    assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}


def test_question_is_included_in_prompt():
    context_chunks = [{"document_name": "a.txt", "chunk_index": 0, "chunk_text": "metin"}]
    messages = build_messages("bu bir soru mu?", context_chunks)
    assert "bu bir soru mu?" in messages[1]["content"]


def test_multiple_context_chunks_are_included_in_prompt():
    context_chunks = [
        {"document_name": "a.txt", "chunk_index": 0, "chunk_text": "birinci parca"},
        {"document_name": "b.txt", "chunk_index": 1, "chunk_text": "ikinci parca"},
    ]
    messages = build_messages("soru", context_chunks)
    user_content = messages[1]["content"]
    assert "birinci parca" in user_content
    assert "ikinci parca" in user_content
    assert "a.txt" in user_content
    assert "b.txt" in user_content


def test_empty_context_returns_no_context_answer_without_foundry_local():
    result = generate_answer("soru", [])
    assert result == NO_CONTEXT_ANSWER


def test_foundry_local_availability_flag_is_bool():
    assert isinstance(FOUNDRY_LOCAL_AVAILABLE, bool)


@requires_foundry_local
def test_generate_answer_returns_answer_for_question_with_context():
    context_chunks = [{"document_name": "a.txt", "chunk_index": 0, "chunk_text": "test icerigi"}]
    result = generate_answer("test sorusu", context_chunks)
    assert isinstance(result, str)
    assert result != ""
