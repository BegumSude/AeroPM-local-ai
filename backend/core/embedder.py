import numpy as np

from backend.core.config import EMBEDDING_MODEL_ALIAS

try:
    from foundry_local_sdk import Configuration, FoundryLocalManager
    FOUNDRY_LOCAL_AVAILABLE = True
except ImportError:
    FOUNDRY_LOCAL_AVAILABLE = False

_embedding_client = None


def _get_embedding_client():
    global _embedding_client
    if _embedding_client is not None:
        return _embedding_client

    if not FOUNDRY_LOCAL_AVAILABLE:
        raise RuntimeError("foundry-local-sdk kurulu degil")

    if FoundryLocalManager.instance is None:
        FoundryLocalManager.initialize(Configuration(app_name="local-rag"))
    manager = FoundryLocalManager.instance

    model = manager.catalog.get_model(EMBEDDING_MODEL_ALIAS)
    model.download()
    model.load()

    _embedding_client = model.get_embedding_client()
    return _embedding_client


def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    client = _get_embedding_client()
    response = client.generate_embeddings(texts)
    embeddings = [item.embedding for item in response.data]
    return np.array(embeddings, dtype=np.float32)
