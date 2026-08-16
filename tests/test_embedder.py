import numpy as np
import pytest

from backend.core.embedder import FOUNDRY_LOCAL_AVAILABLE, embed_texts

requires_foundry_local = pytest.mark.skipif(
    not FOUNDRY_LOCAL_AVAILABLE, reason="foundry-local-sdk kurulu degil"
)


def test_empty_input_returns_empty_ndarray_without_foundry_local():
    result = embed_texts([])
    assert isinstance(result, np.ndarray)
    assert result.shape == (0, 0)


def test_foundry_local_availability_flag_is_bool():
    assert isinstance(FOUNDRY_LOCAL_AVAILABLE, bool)


@requires_foundry_local
def test_embed_texts_returns_ndarray_for_valid_input():
    result = embed_texts(["merhaba dunya"])
    assert isinstance(result, np.ndarray)


@requires_foundry_local
def test_embed_texts_returns_one_embedding_per_text():
    texts = ["merhaba dunya", "ikinci metin", "ucuncu metin"]
    result = embed_texts(texts)
    assert result.shape[0] == len(texts)


@requires_foundry_local
def test_embed_texts_dimension_is_consistent_across_texts():
    texts = ["merhaba dunya", "ikinci metin", "ucuncu metin"]
    result = embed_texts(texts)
    dimension = result.shape[1]
    assert dimension > 0
    assert all(len(row) == dimension for row in result)
