from backend.core.config import CHAT_MODEL_ALIAS
from backend.prompts.system_prompts import SYSTEM_PROMPT

try:
    from foundry_local_sdk import Configuration, FoundryLocalManager
    FOUNDRY_LOCAL_AVAILABLE = True
except ImportError:
    FOUNDRY_LOCAL_AVAILABLE = False

NO_CONTEXT_ANSWER = "Yuklenen belgelerde bu soruyla ilgili bilgi bulunamadi."

_chat_client = None


def _get_chat_client():
    global _chat_client
    if _chat_client is not None:
        return _chat_client

    if not FOUNDRY_LOCAL_AVAILABLE:
        raise RuntimeError("foundry-local-sdk kurulu degil")

    if FoundryLocalManager.instance is None:
        FoundryLocalManager.initialize(Configuration(app_name="local-rag"))
    manager = FoundryLocalManager.instance

    model = manager.catalog.get_model(CHAT_MODEL_ALIAS)
    model.download()
    model.load()

    _chat_client = model.get_chat_client()
    return _chat_client


def _build_context_text(context_chunks: list[dict]) -> str:
    parts = []
    for chunk in context_chunks:
        document_name = chunk.get("document_name", "bilinmiyor")
        chunk_index = chunk.get("chunk_index", "?")
        chunk_text = chunk.get("chunk_text", "")
        parts.append(f"[Kaynak: {document_name}, chunk {chunk_index}]\n{chunk_text}")
    return "\n\n".join(parts)


def build_messages(question: str, context_chunks: list[dict]) -> list[dict]:
    context_text = _build_context_text(context_chunks)
    user_message = f"Baglam:\n{context_text}\n\nSoru:\n{question}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def generate_answer(question: str, context_chunks: list[dict]) -> str:
    if not context_chunks:
        return NO_CONTEXT_ANSWER

    messages = build_messages(question, context_chunks)
    client = _get_chat_client()
    completion = client.complete_chat(messages)
    return completion.choices[0].message.content
