from sentence_transformers import SentenceTransformer

_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _model


def embed_text(text: str) -> list[float]:
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=True)
    return embeddings.tolist()


def warm_up_embedding_model():
    embed_text("warm up")
