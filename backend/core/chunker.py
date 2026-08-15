from backend.core.config import CHUNK_OVERLAP, CHUNK_SIZE


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    if chunk_size <= 0:
        raise ValueError("chunk_size pozitif bir tam sayi olmalidir")
    if overlap < 0:
        raise ValueError("overlap negatif olamaz")
    if overlap >= chunk_size:
        raise ValueError("overlap, chunk_size'dan kucuk olmalidir")

    if not text:
        return []

    step = chunk_size - overlap
    text_length = len(text)

    chunks = []
    start = 0
    chunk_index = 0
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunks.append({
            "chunk_index": chunk_index,
            "chunk_text": text[start:end],
            "start_char": start,
            "end_char": end,
        })
        if end == text_length:
            break
        chunk_index += 1
        start += step

    return chunks
